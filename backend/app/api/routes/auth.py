from datetime import timedelta
from typing import Literal
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, Field, SecretStr, ConfigDict
from sqlalchemy import select, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool
from app.api.deps import get_db, commit_inventory
from app.models.security import User, LoginSession, AuditEvent
from app.protected_route import ProtectedRoute
from app.security import COOKIE, CSRF_COOKIE, now, digest, hash_password, verify_password, check_origin, authenticate
from app.config import settings
import secrets
import uuid

router = APIRouter(route_class=ProtectedRoute, tags=['accounts'])


class LoginInput(BaseModel):
    username: str = Field(min_length=1, max_length=64)
    password: SecretStr = Field(min_length=1, max_length=128)


class CreateUser(BaseModel):
    username: str = Field(min_length=3, max_length=64, pattern=r'^[a-z0-9][a-z0-9_.-]*$')
    password: SecretStr = Field(min_length=12, max_length=128)
    role: Literal['viewer', 'operator', 'admin'] = 'viewer'


class UpdateUser(BaseModel):
    role: Literal['viewer', 'operator', 'admin'] | None = None
    is_active: bool | None = None
    password: SecretStr | None = Field(default=None, min_length=12, max_length=128)


class ChangePassword(BaseModel):
    current_password: SecretStr = Field(min_length=1, max_length=128)
    new_password: SecretStr = Field(min_length=12, max_length=128)


def user_json(user):
    return {'id': str(user.id), 'username': user.username, 'role': user.role, 'is_active': user.is_active}


async def login_event(db, username, user_id, succeeded):
    db.add(AuditEvent(actor_id=user_id, actor_name=username[:64], action='POST /api/auth/login', target_name='Sign in',
        created_at=now(), updated_at=now(), outcome='succeeded' if succeeded else 'failed', status_code=200 if succeeded else 401,
        message='Signed in.' if succeeded else 'Sign-in attempt rejected.', changed_fields=[]))
    await db.commit()


@router.get('/auth/setup-status')
async def setup_status(db: AsyncSession = Depends(get_db, scope="function")):
    return {'needs_setup': not bool(await db.scalar(select(func.count()).select_from(User)))}


@router.post('/auth/login')
async def login(payload: LoginInput, request: Request, response: Response, db: AsyncSession = Depends(get_db, scope="function")):
    check_origin(request)
    username = payload.username.strip().lower()
    user = await db.scalar(select(User).where(User.username == username).with_for_update())
    # Use equal password-hash work for unknown usernames.
    dummy = 'scrypt$' + ('0' * 32) + '$' + ('0' * 64)
    valid = await run_in_threadpool(verify_password, payload.password.get_secret_value(), user.password_hash if user else dummy)
    allowed = user and user.is_active and (user.locked_until is None or user.locked_until <= now())
    if not valid or not allowed:
        if user:
            user.failed_logins += 1
            if user.failed_logins >= 5:
                user.locked_until = now() + timedelta(minutes=5)
        await login_event(db, username, user.id if user else None, False)
        raise HTTPException(401, 'Invalid credentials or sign-in temporarily unavailable. Try again later.')
    user.failed_logins = 0
    user.locked_until = None
    raw, csrf = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
    # Replacing a login must not leave the previous browser session usable.
    previous = request.cookies.get(COOKIE)
    if previous:
        await db.execute(delete(LoginSession).where(LoginSession.token_hash == digest(previous)))
    await db.execute(delete(LoginSession).where(LoginSession.expires_at <= now()))
    db.add(LoginSession(user_id=user.id, token_hash=digest(raw), csrf_hash=digest(csrf), expires_at=now() + timedelta(hours=settings.session_hours)))
    await login_event(db, username, user.id, True)
    response.set_cookie(COOKIE, raw, httponly=True, secure=settings.session_cookie_secure, samesite='strict', max_age=settings.session_hours * 3600, path='/')
    response.set_cookie(CSRF_COOKIE, csrf, httponly=False, secure=settings.session_cookie_secure, samesite='strict', max_age=settings.session_hours * 3600, path='/')
    return user_json(user)


@router.get('/auth/me')
async def me(request: Request, db: AsyncSession = Depends(get_db, scope="function")):
    principal, session = await authenticate(request, db)
    return user_json(await db.get(User, principal.id))


@router.post('/auth/logout', status_code=204)
async def logout(request: Request, response: Response, db: AsyncSession = Depends(get_db, scope="function")):
    await db.execute(delete(LoginSession).where(LoginSession.token_hash == digest(request.cookies.get(COOKIE, ''))))
    await db.commit()
    response.delete_cookie(COOKIE, path='/')
    response.delete_cookie(CSRF_COOKIE, path='/')


@router.post('/auth/password', status_code=204)
async def change_password(payload: ChangePassword, request: Request, response: Response, db: AsyncSession = Depends(get_db, scope="function")):
    user = await db.get(User, request.state.principal.id)
    if not await run_in_threadpool(verify_password, payload.current_password.get_secret_value(), user.password_hash):
        raise HTTPException(403, 'Current password is incorrect')
    user.password_hash = await run_in_threadpool(hash_password, payload.new_password.get_secret_value())
    await db.execute(delete(LoginSession).where(LoginSession.user_id == user.id))
    await db.commit()
    response.delete_cookie(COOKIE, path='/')
    response.delete_cookie(CSRF_COOKIE, path='/')


@router.get('/users')
async def list_users(db: AsyncSession = Depends(get_db, scope="function")):
    users = (await db.execute(select(User).order_by(User.username))).scalars().all()
    return [user_json(user) for user in users]


@router.post('/users', status_code=201)
async def create_user(payload: CreateUser, db: AsyncSession = Depends(get_db, scope="function")):
    user = User(username=payload.username, role=payload.role, password_hash=await run_in_threadpool(hash_password, payload.password.get_secret_value()))
    db.add(user)
    await commit_inventory(db)
    await db.refresh(user)
    return user_json(user)


@router.patch('/users/{user_id}')
async def update_user(user_id: uuid.UUID, payload: UpdateUser, db: AsyncSession = Depends(get_db, scope="function")):
    # Serialize account changes so concurrent demotions cannot remove all admins.
    users = (await db.execute(select(User).order_by(User.id).with_for_update())).scalars().all()
    user = next((u for u in users if u.id == user_id), None)
    if not user:
        raise HTTPException(404, 'User not found')
    role = payload.role if payload.role is not None else user.role
    active = payload.is_active if payload.is_active is not None else user.is_active
    if user.role == 'admin' and user.is_active and (role != 'admin' or not active):
        if not any(u.id != user.id and u.role == 'admin' and u.is_active for u in users):
            raise HTTPException(409, 'At least one active administrator is required')
    user.role, user.is_active = role, active
    if payload.password is not None:
        user.password_hash = await run_in_threadpool(hash_password, payload.password.get_secret_value())
        user.failed_logins, user.locked_until = 0, None
    await db.execute(delete(LoginSession).where(LoginSession.user_id == user.id))
    await db.commit()
    return user_json(user)

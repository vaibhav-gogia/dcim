"""Local accounts and revocable cookie sessions; no default users or signing secret."""
import hashlib
import hmac
import secrets
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from dataclasses import dataclass
import uuid
from fastapi import Request, HTTPException
from sqlalchemy import select
from app.database import get_db
from app.models.security import User, LoginSession
from app.config import settings

COOKIE = 'dcim_session'
CSRF_COOKIE = 'dcim_csrf'


def now():
    return datetime.now(timezone.utc)


def digest(value: str):
    return hashlib.sha256(value.encode()).hexdigest()


def hash_password(password: str):
    salt = secrets.token_hex(16)
    value = hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt), n=2**14, r=8, p=5, dklen=32).hex()
    return f'scrypt${salt}${value}'


def verify_password(password: str, encoded: str):
    try:
        algorithm, salt, expected = encoded.split('$')
        if algorithm != 'scrypt':
            return False
        value = hashlib.scrypt(password.encode(), salt=bytes.fromhex(salt), n=2**14, r=8, p=5, dklen=32).hex()
        return hmac.compare_digest(value, expected)
    except (ValueError, TypeError):
        return False


@dataclass
class Principal:
    id: uuid.UUID
    username: str
    role: str


@asynccontextmanager
async def request_db(request: Request):
    provider = request.app.dependency_overrides.get(get_db, get_db)
    generator = provider()
    try:
        db = await anext(generator)
        yield db
    finally:
        await generator.aclose()


def check_origin(request: Request):
    # Explicit allowlist also prevents login CSRF and untrusted Host-based origins.
    if request.headers.get('origin') not in settings.cors_origins:
        raise HTTPException(403, 'Request origin is not allowed')


async def authenticate(request: Request, db, *, csrf=True):
    raw = request.cookies.get(COOKIE, '')
    if not raw or len(raw) > 256:
        raise HTTPException(401, 'Please sign in')
    result = await db.execute(select(LoginSession, User).join(User).where(LoginSession.token_hash == digest(raw), LoginSession.expires_at > now(), User.is_active.is_(True)))
    row = result.first()
    if row is None:
        raise HTTPException(401, 'Session expired. Please sign in again.')
    session, user = row
    principal = Principal(user.id, user.username, user.role)
    request.state.principal = principal
    if csrf and request.method not in ('GET', 'HEAD', 'OPTIONS'):
        check_origin(request)
        value = request.headers.get('x-csrf-token', '')
        if not value or not hmac.compare_digest(digest(value), session.csrf_hash):
            raise HTTPException(403, 'Invalid request token. Refresh and try again.')
    return principal, session


def can_mutate(principal: Principal, path: str, method: str):
    if principal.role == 'admin':
        return True
    return principal.role == 'operator' and method == 'POST' and (
        '/power/' in path or ('/outlets/' in path and path.rsplit('/', 1)[-1] in ('on', 'off', 'cycle')))

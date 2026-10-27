"""Run interactively: docker compose exec backend python -m app.bootstrap_admin"""
import asyncio
import getpass
import re
from sqlalchemy import select, func, text
from app.database import async_session_maker
from app.models.security import User, AuditEvent
from app.security import hash_password, now


async def main():
    username = input('First administrator username: ').strip().lower()
    if not re.fullmatch(r'[a-z0-9][a-z0-9_.-]{2,63}', username):
        raise SystemExit('Use 3–64 lowercase letters, digits, dots, hyphens or underscores.')
    password = getpass.getpass('Password (12–128 characters): ')
    if not 12 <= len(password) <= 128 or password != getpass.getpass('Confirm password: '):
        raise SystemExit('Password length invalid or confirmation does not match.')
    async with async_session_maker() as db:
        await db.execute(text('LOCK TABLE users IN EXCLUSIVE MODE'))
        if await db.scalar(select(func.count()).select_from(User)):
            raise SystemExit('Accounts already exist. Ask an administrator to manage accounts in the app.')
        user = User(username=username, role='admin', password_hash=hash_password(password))
        db.add(user)
        await db.flush()
        db.add(AuditEvent(actor_id=user.id, actor_name=username, action='bootstrap admin', target_id=user.id, target_name=username,
            created_at=now(), updated_at=now(), outcome='succeeded', message='Initial administrator created locally.', changed_fields=[]))
        await db.commit()
    print('Administrator created. Sign in through the app.')


if __name__ == '__main__':
    asyncio.run(main())

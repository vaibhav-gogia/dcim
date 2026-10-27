import uuid
from datetime import timedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db
from app.models.security import AuditEvent
from app.models.system import System
from app.services.power_service import resolve_power_state
from app.protected_route import ProtectedRoute
from app.security import now

router = APIRouter(route_class=ProtectedRoute, tags=['history'])


@router.get('/history')
async def history(rack_id: uuid.UUID | None = None, system_id: uuid.UUID | None = None,
    offset: int = Query(default=0, ge=0), limit: int = Query(default=25, ge=1, le=100), db: AsyncSession = Depends(get_db, scope="function")):
    stmt = select(AuditEvent)
    if rack_id:
        stmt = stmt.where(AuditEvent.rack_id == rack_id)
    if system_id:
        stmt = stmt.where(AuditEvent.system_id == system_id)
    total = await db.scalar(select(func.count()).select_from(stmt.subquery()))
    events = (await db.execute(stmt.order_by(AuditEvent.created_at.desc(), AuditEvent.id).offset(offset).limit(limit))).scalars().all()
    # Complete simulated transition records even when only the activity page is open.
    for system_id in {e.system_id for e in events if e.system_id and e.expected_state and e.outcome == 'pending'}:
        system = await db.get(System, system_id)
        if system and system.bmc_driver_type == 'simulated':
            await resolve_power_state(db, system)
    items = []
    for event in events:
        unresolved = event.outcome == 'pending' and event.updated_at < now() - timedelta(minutes=5)
        items.append({'id': event.id, 'actor': event.actor_name, 'action': event.action,
            'target': event.target_name, 'target_id': event.target_id, 'rack_id': event.rack_id, 'system_id': event.system_id,
            'created_at': event.created_at, 'updated_at': event.updated_at,
            'outcome': 'unknown' if unresolved else event.outcome,
            'message': 'No completion has been observed. Verify equipment before retrying.' if unresolved else event.message,
            'changed_fields': event.changed_fields, 'status_code': event.status_code})
    return {'total': total, 'items': items}

import json
import uuid
from fastapi import Request
from sqlalchemy import select, update
from app.models.security import AuditEvent, User
from app.models.system import System
from app.models.rack import Rack
from app.models.pdu import PDU
from app.models.pdu_outlet import PDUOutlet
from app.models.power_connection import PowerConnection
from app.models.data_hall import DataHall
from app.models.datacenter import DataCenter
from app.security import now, request_db


async def describe_target(db, params):
    for key, model in [('user_id', User), ('outlet_id', PDUOutlet), ('connection_id', PowerConnection), ('system_id', System), ('pdu_id', PDU), ('rack_id', Rack), ('data_hall_id', DataHall), ('datacenter_id', DataCenter)]:
        if key not in params:
            continue
        try:
            target_id = uuid.UUID(str(params[key]))
        except ValueError:
            continue
        entity = await db.get(model, target_id)
        if entity is None:
            return {'target_id': target_id, 'target_name': f'{key}: {target_id}'}
        rack_id = entity.id if model == Rack else getattr(entity, 'rack_id', None)
        system_id = entity.id if model == System else getattr(entity, 'system_id', None)
        name = getattr(entity, 'name', None) or getattr(entity, 'username', None)
        if model == PDUOutlet:
            pdu = await db.get(PDU, entity.pdu_id)
            rack_id = pdu.rack_id
            name = f'{pdu.name} / outlet {entity.outlet_number}'
            system_id = await db.scalar(select(PowerConnection.system_id).where(PowerConnection.pdu_outlet_id == entity.id))
        if system_id and not rack_id:
            system = await db.get(System, system_id)
            rack_id = system.rack_id if system else None
        return {'target_id': target_id, 'target_name': name or f'Power connection {target_id}', 'rack_id': rack_id, 'system_id': system_id}
    return {'target_name': 'Account administration'}


async def start_event(request, template):
    async with request_db(request) as db:
        target = await describe_target(db, request.path_params)
        fields = []
        if not request.url.path.startswith('/api/auth') and not request.url.path.startswith('/api/users'):
            try:
                body = await request.json()
                if isinstance(body, dict):
                    fields = sorted(k for k in body if k not in ('password', 'token', 'csrf_token'))
            except (ValueError, UnicodeDecodeError):
                pass
        actor = request.state.principal
        event = AuditEvent(actor_id=actor.id, actor_name=actor.username, action=f'{request.method} {template}',
            created_at=now(), updated_at=now(), outcome='pending', message='Request started; completion not yet recorded.', changed_fields=fields, **target)
        db.add(event)
        await db.commit()  # Fail closed: do not perform an unaudited mutation.
        return event.id


async def finish_event(request, event_id, response=None, status=500, detail=None):
    async with request_db(request) as db:
        event = await db.get(AuditEvent, event_id)
        event.status_code = status
        event.updated_at = now()
        event.outcome = 'succeeded' if status < 400 else ('failed' if status < 500 else 'unknown')
        event.message = 'Request completed.' if status < 400 else ('Request rejected.' if status < 500 else 'Completion could not be confirmed. Check equipment before retrying.')
        if detail is not None and status < 500:
            event.message = str(detail)[:400]
        if response is not None and status < 400:
            try:
                body = json.loads(response.body) if response.body else {}
            except (ValueError, AttributeError):
                body = {}
            if '/power/' in request.url.path and body.get('power_state') in ('booting', 'cycling', 'shutting_down'):
                event.outcome = 'pending'
                event.expected_state = 'off' if body['power_state'] == 'shutting_down' else 'on'
                event.message = 'Command accepted; waiting for the system transition to finish.'
            if status == 201 and isinstance(body, dict) and body.get('id'):
                # Retain the created entity's identity rather than only its parent.
                mapping = [('users', 'user_id'), ('power-connections', 'connection_id'), ('systems', 'system_id'), ('pdus', 'pdu_id'), ('racks', 'rack_id'), ('data-halls', 'data_hall_id'), ('datacenters', 'datacenter_id')]
                segment = request.url.path.rsplit('/', 1)[-1]
                for suffix, key in mapping:
                    if segment == suffix:
                        for field, value in (await describe_target(db, {key: body['id']})).items():
                            setattr(event, field, value)
                        break
        await db.commit()


async def settle_system_events(db, system_id, state, *, supply_lost=False):
    events = (await db.execute(select(AuditEvent).where(AuditEvent.system_id == system_id, AuditEvent.outcome == 'pending', AuditEvent.expected_state.is_not(None)))).scalars().all()
    for event in events:
        if state in ('on', 'off'):
            event.outcome = 'succeeded' if state == event.expected_state and not supply_lost else 'failed'
            event.message = 'System reached the requested power state.' if event.outcome == 'succeeded' else ('Power transition interrupted by loss of PDU supply.' if supply_lost else 'System did not reach the requested power state.')
            event.updated_at = now()
    if events:
        await db.commit()

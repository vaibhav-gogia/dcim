from fastapi import HTTPException
from fastapi.routing import APIRoute
from fastapi.exceptions import RequestValidationError
from starlette.responses import JSONResponse
from app.security import authenticate, can_mutate, request_db
from app.audit import start_event, finish_event


class ProtectedRoute(APIRoute):
    def get_route_handler(self):
        original = super().get_route_handler()
        async def handler(request):
            if self.path in ('/api/ping', '/ping', '/api/auth/login', '/auth/login', '/api/auth/setup-status', '/auth/setup-status'):
                response = await original(request)
                response.headers['Cache-Control'] = 'no-store'
                return response
            unsafe = request.method not in ('GET', 'HEAD', 'OPTIONS')
            event_id = None
            try:
                async with request_db(request) as db:
                    principal, _ = await authenticate(request, db, csrf=False)
                if unsafe:
                    event_id = await start_event(request, self.path)
                    async with request_db(request) as db:
                        await authenticate(request, db)
                    self_service = request.url.path in ('/api/auth/logout', '/api/auth/password')
                    if not self_service and not can_mutate(principal, request.url.path, request.method):
                        raise HTTPException(403, 'Your role does not permit this action')
                    if '/power/' in request.url.path or ('/outlets/' in request.url.path and request.url.path.endswith(('/off', '/cycle'))):
                        if request.url.path.endswith(('/off', '/cycle')) and request.headers.get('x-confirm-action') != 'yes':
                            raise HTTPException(409, 'Confirm this disruptive power action before continuing')
                if request.url.path.startswith('/api/users') and principal.role != 'admin':
                    raise HTTPException(403, 'Administrator access required')
                response = await original(request)
            except RequestValidationError as error:
                if event_id:
                    await finish_event(request, event_id, status=422)
                return JSONResponse({'detail': [{'loc': e['loc'], 'msg': e['msg'], 'type': e['type']} for e in error.errors()]}, status_code=422, headers={'Cache-Control': 'no-store'})
            except HTTPException as error:
                if event_id:
                    await finish_event(request, event_id, status=error.status_code, detail=error.detail)
                return JSONResponse({'detail': error.detail}, status_code=error.status_code, headers={'Cache-Control': 'no-store'})
            except Exception:
                if event_id:
                    await finish_event(request, event_id, status=500)
                raise
            if event_id:
                await finish_event(request, event_id, response, response.status_code)
            response.headers['Cache-Control'] = 'no-store'
            return response
        return handler

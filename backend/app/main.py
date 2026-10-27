from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import auth, history, inventory, data_halls, datacenters, health, pdus, power, racks, systems
from app.config import settings

app = FastAPI(title="DCIM API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for router in (auth.router, history.router, inventory.router, health.router, datacenters.router, data_halls.router, racks.router, systems.router, pdus.router, power.router):
    app.include_router(router, prefix="/api")


# Do not echo password/token input in validation errors.
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

@app.exception_handler(RequestValidationError)
async def validation_error(request, error):
    return JSONResponse(status_code=422, content={'detail': [{'loc': e['loc'], 'msg': e['msg'], 'type': e['type']} for e in error.errors()]}, headers={'Cache-Control': 'no-store'})

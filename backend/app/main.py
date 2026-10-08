from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import data_halls, datacenters, health, pdus, power, racks, systems
from app.config import settings

app = FastAPI(title="DCIM API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

for router in (health.router, datacenters.router, data_halls.router, racks.router, systems.router, pdus.router, power.router):
    app.include_router(router, prefix="/api")

from fastapi import APIRouter
from app.api.v1 import admin, appointments, auth, billing, catalog, encounters, kb, lab, pharmacy, triage

api_router = APIRouter()
for r in (auth.router, catalog.router, triage.router, appointments.router, encounters.router,
          lab.router, billing.router, pharmacy.router, kb.router, admin.router):
    api_router.include_router(r)

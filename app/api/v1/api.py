
from fastapi import APIRouter
from app.api.v1.endpoints import consultation, history

api_router = APIRouter()
api_router.include_router(consultation.router, tags=["Consultation"])
api_router.include_router(history.router, tags=["History"])


from fastapi import APIRouter
from app.api.v1.endpoints import consultation, history
from fastapi import APIRouter
from app.api.v1.endpoints import consultation, history, auth

api_router = APIRouter()
api_router.include_router(consultation.router, tags=["Consultation"])
api_router.include_router(history.router, tags=["History"])
api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
api_router = APIRouter()
api_router.include_router(consultation.router, tags=["Consultation"])
api_router.include_router(history.router, tags=["History"])

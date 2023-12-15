from fastapi import APIRouter
from .api import router as services

router = APIRouter()

router.include_router(services, prefix="/v1/services", tags=["services"])
# add more `router.include_router()` as needed for other files

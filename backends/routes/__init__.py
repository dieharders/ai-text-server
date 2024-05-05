from fastapi import APIRouter
from .api import router as services
from .embeddings import router as embeddings

router = APIRouter()

router.include_router(services, prefix="/v1/services", tags=["services"])
router.include_router(embeddings, prefix="/v1/memory", tags=["embeddings"])
# add more `router.include_router()` as needed for other files

# backend/app/routers/__init__.py

from app.routers.datasource import router as datasource_router
from app.routers.training import router as training_router
from app.routers.ask import router as ask_router
from app.routers.settings import router as settings_router

__all__ = [
    "datasource_router",
    "training_router",
    "ask_router",
    "settings_router",
]

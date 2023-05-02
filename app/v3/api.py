from fastapi import APIRouter

from .routers.store import store_router
from .routers.menu import menu_router
from .routers.food import food_router

v2_router = APIRouter(prefix="/api/v2", tags=["v2"])
v2_router.include_router(store_router)
v2_router.include_router(menu_router)
v2_router.include_router(food_router)

@v2_router.get("/")
async def hello():
    return {"message": "Hello 'api/v2'"}
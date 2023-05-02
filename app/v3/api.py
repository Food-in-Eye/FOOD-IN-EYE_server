from fastapi import APIRouter

from .routers.store import store_router
from .routers.menu import menu_router
from .routers.food import food_router

v3_router = APIRouter(prefix="/api/v3", tags=["v3"])
v3_router.include_router(store_router)
v3_router.include_router(menu_router)
v3_router.include_router(food_router)

@v3_router.get("/")
async def hello():
    return {"message": "Hello 'api/v3'"}
from fastapi import APIRouter

from .routers.store import store_router
from .routers.menu import menu_router
from .routers.food import food_router
from .routers.order import order_router
from .routers.websocket import websocket_router

v2_router = APIRouter(prefix="/api/v2", tags=["v2"])
v2_router.include_router(store_router)
v2_router.include_router(menu_router)
v2_router.include_router(food_router)
v2_router.include_router(order_router)
v2_router.include_router(websocket_router)

@v2_router.get("/")
async def hello():
    return {"message": "Hello 'api/v2'"}

from core.common.s3 import Storage

@v2_router.get("/s3/keys")
async def get_keys(prefix:str='/', extension:str=None):
    try:
        storage = Storage('foodineye2')

        return storage.get_list(prefix, extension)
    
    except:

        return "ERROR"


@v2_router.get("/s3/keys/gaze")
async def get_keys(prefix:str, key: str):
    try:
        storage = Storage('foodineye2')
        return storage.get_json(prefix + '/' + key)

    except:

        return "ERROR"

from v2.routers.src.meta import Meta
    
from pydantic import BaseModel
from datetime import datetime
class Item(BaseModel):
    content: dict

# @v2_router.post("/t")
# async def set_meta(body: Item):
#     Meta.create(body.content)

@v2_router.get("/test")
async def set_meta():

    meta = Meta.get_meta_detail(datetime.now())
    return meta




from datetime import datetime
from core.statistics.run import CallAnalysis

@v2_router.get("/anlz_test")
async def analysis_test():
    """
        하루동안의 통계를 내기 위해 세팅하는 함수이다.
        1. 분석 날짜(= 오늘)를 선정한다.
        2. execute_sale 함수를 실행한다. -> return sale_report
        3. 분석 보고서를 리턴한다.
    """
    # today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    today = datetime(2023, 7, 26)
    try:
        sale_report = await CallAnalysis.sale_stats(today)

        return sale_report
    except Exception as e:
        return e
from fastapi import APIRouter
from v2.routers.src.util import Util
from datetime import timedelta

from .routers.store import store_router
from .routers.menu import menu_router
from .routers.food import food_router
from .routers.order import order_router
from .routers.websocket import websocket_router
from .routers.user import user_router
from .routers.exhibition import exhibition_router

v2_router = APIRouter(prefix="/api/v2", tags=["v2"])
v2_router.include_router(store_router)
v2_router.include_router(menu_router)
v2_router.include_router(food_router)
v2_router.include_router(order_router)
v2_router.include_router(websocket_router)
v2_router.include_router(user_router)
v2_router.include_router(exhibition_router)


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
async def get_keys(key: str):
    try:
        storage = Storage('foodineye2')
        return storage.get_json(key)

    except:
        return "ERROR"


from datetime import datetime
from core.statistics.run import CallAnalysis

@v2_router.get("/daily")
async def get_report(date:str):
    new_date = Util.get_utc_time_by_str(date)
    return await CallAnalysis.daily_summary(new_date)

from core.common.mongo import MongodbController
from v2.routers.order import preprocess_and_update

DB = MongodbController('FIE_DB2')

@v2_router.get("/aoi_create")
async def get_report():
    start_date = Util.get_utc_time_by_str("2023-08-12")
    end_date = Util.get_utc_time_by_str("2023-08-15")

    pipeline = [
        { "$match": { "date": { "$gte": start_date, "$lt": end_date }}},
        { "$project": { "_id": 1, "fixation_path": 1 }}
    ]

    historys = DB.aggregate_pipline('order', pipeline)
    print(historys)

# from datetime import datetime
# from pytz import timezone
# from core.statistics.run import CallAnalysis

# @v2_router.get("/anlz_test")
# async def analysis_test():
#     """
#         하루동안의 통계를 내기 위해 세팅하는 함수이다.
#         1. 분석 날짜(= 오늘)를 선정한다.
#         2. execute_sale 함수를 실행한다. -> return sale_report
#         3. 분석 보고서를 리턴한다.
#     """
    
#     # today = Util.get_utc_time_by_datetime(datetime.now().replace(hour=0, minute=0, second=0, microsecond=0))
#     # today = datetime(2023, 7, 26)
#     today = datetime(2023, 8, 19)
#     try:
#         # sale_report = await CallAnalysis.sale_stats(today)

#         # return sale_report
        
#         # aoi_daily = await CallAnalysis.aoi_stats(today)
#         # return aoi_daily
#         object_id = await CallAnalysis.daily_summary()
#         if object_id != False:
#             return object_id
#         else:
#             return 'error'
#     except Exception as e:
#         return e

# history내의 모든 시선데이터에 대해서 filter와 aoi 통계를 일괄 적용(설정이 바뀐 경우에 한번에 적용하기에 유리)
from core.common.mongo import MongodbController
import os
from dotenv import load_dotenv
import httpx
from .routers.src.util import Util
from .routers.src.meta import Meta

@v2_router.get("/test")
async def testcode():
    DB = MongodbController('FIE_DB2')
    try:
        load_dotenv()

        filter_url = os.environ['ANALYSIS_BASE_URL'] + "/anlz/v1/filter/execute"
        aoi_url = os.environ['ANALYSIS_BASE_URL'] + "/anlz/v1/aoi/analysis"
        headers = {"Content-Type": "application/json"}
       
        datas = DB.read_all('history', {'date':{"$gte": datetime(2023, 9, 12, 4, 45)} , 'raw_gaze_path':{'$ne': None}}, {'_id':1, 'raw_gaze_path':1})
        result = []
        for d in datas:
            if 'raw_gaze_path' in d.keys() and d['raw_gaze_path'] != None:
                h_id = str(d['_id'])
                raw_data_key = d['raw_gaze_path']
                print(raw_data_key)

                async with httpx.AsyncClient() as client:
                    _id = Util.check_id(h_id)
                    doc = DB.read_one('history', {'_id':_id})
                    payload = {
                    "raw_data_key": raw_data_key,
                    "meta_info": Meta.get_meta_detail(doc['date'])
                    }
                    response = await client.post(filter_url, json=payload, headers=headers)
                    data = response.json()
                    fix_key = data["fixation_key"]

                    response = await client.get(aoi_url + f'?key={fix_key}')
                    data = response.json()
                    aoi_key = data["aoi_key"]
                    print(f'fixkey= {fix_key}, aoikey = {aoi_key}')
                
                DB.update_one('history', {'_id':_id}, {'fixation_path': fix_key, 'aoi_analysis': aoi_key})
                result.append({h_id:{'fixation_path': fix_key, 'aoi_analysis': aoi_key}})
        return result

    except Exception as e:
        print(e)
        return e

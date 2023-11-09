"""
exhibition_router
"""

from fastapi import APIRouter, Depends, Request
from datetime import timedelta, datetime
from core.common.mongo import MongodbController
from core.common.s3 import Storage
from .src.util import Util
from bson.objectid import ObjectId
import pandas as pd
import random

exhibition_router = APIRouter(prefix="/exhibition")

PREFIX = 'api/v2/exhibition'
DB = MongodbController('FIE_DB2')
TODAY_ID = '653d3bbdba45e3b9f51d7b58'
S_ID_Table = {'64a2d45c1fe80e3e4db82af9':'1', '64a2d49e1fe80e3e4db82afa':'2', '64a2d53f1fe80e3e4db82afb':'3', '64a2d56a1fe80e3e4db82afc':'4', '64a2d58f1fe80e3e4db82afd':'5'}

storage = Storage('foodineye2')


@exhibition_router.get("/hello")
async def hello():
    # DB.insert_one('exhibition', {
    #     'date': Util.get_utc_time_by_datetime(Util.get_local_time(datetime.now()).replace(hour=0, minute=0, second=0, microsecond=0)),
    #     'stores': {
    #         '1': {
    #             'dwell': [0 for _ in range(7)],
    #             'count': [0 for _ in range(7)],
    #         },
    #         '2': {
    #             'dwell': [0 for _ in range(8)],
    #             'count': [0 for _ in range(8)],
    #         },
    #         '3': {
    #             'dwell': [0 for _ in range(6)],
    #             'count': [0 for _ in range(6)],
    #         },
    #         '4':{
    #             'dwell': [0 for _ in range(6)],
    #             'count': [0 for _ in range(6)],
    #         },
    #         '5':{
    #             'dwell': [0 for _ in range(4)],
    #             'count': [0 for _ in range(4)],
    #         }
    #     }
    # })
    return {"message": f"Hello '{PREFIX}'"}

# @exhibition_router.get("/update")
# async def update_new_history(h_id:str):
#     print('update new order')
#     data = DB.read_one('exhibition', {'_id':ObjectId(TODAY_ID)})
#     del data['_id']

#     updated_data = update_data(data, h_id)

#     DB.replace_one('exhibition', {'_id':ObjectId(TODAY_ID)}, updated_data)

@exhibition_router.get('/history')
async def get_history(h_id:str):
    data = DB.read_one('exhibition', {'_id':ObjectId(TODAY_ID)})
    LEFT = get_status(data)
    RIGHT = get_detail(h_id)

    _id = Util.check_id(h_id)
    h_data = DB.read_one('history', {'_id':_id})
    personal = get_personal(h_data['aoi_analysis'])
    
    return {'left': LEFT, 'right': RIGHT, 'fix_key': h_data['fixation_path'], 'personal': personal}

@exhibition_router.get("/historys")
async def get_todat_history():
    today = Util.get_utc_time_by_datetime(Util.get_local_time(datetime.now()).replace(hour=0, minute=0, second=0, microsecond=0))
    # today = Util.get_utc_time_by_str("2023-09-20")

    pipeline = [
        { "$match": { "date": {"$gte": today, "$lt": today + timedelta(days=1)} } },
        { "$project": { "_id":1, "date":1, "fixation_path":1 }} 
    ]

    historys = DB.aggregate_pipline('history', pipeline)

    result = []
    for history in historys:
        date = Util.get_local_time(history['date']).strftime("%Y-%m-%d %H:%M:%S")
        h_id = str(history['_id'])
        result.append({date:h_id})
    return result

@exhibition_router.get("/visualize")
async def get_fixation_data(fix_key:str):
    fix_data = storage.get_json(fix_key)
    result = []
    
    for page in fix_data:
        new_fixs = []
        for fix in page['fixations']:
            new_fixs.append({
                'x':int(fix['cx']),
                'y':int(fix['cy']),
                'd':fix['et'] - fix['st']
            })
        result.append({
            "page": page['page'],
            "s_num": page['s_num'],
            "f_num": page['f_num'],
            "fixations": new_fixs
        })
        
    return result

@exhibition_router.get("/info")
async def get_food(s_num:int, f_num:int):
    s_id = find_key_by_value(s_num)
    food = DB.read_one('food', {'num':f_num, 's_id':s_id})
    return food['name']
        
def find_key_by_value(value):
    for k, v in S_ID_Table.items():
        if int(v) == value:
            return k

def get_status(data):
    labels = []
    dwells = []
    counts = []
    for s_num, store in data['stores'].items():
        name = str(s_num) + '-'
        for i in range(len(store['dwell'])):
            labels.append(name+str(i+1))
            # dwells.append(store['dwell'][i])
            # counts.append(store['count'][i])
            dwells.append(random.randint(0,100))
            counts.append(random.randint(0,50))

    df = pd.DataFrame({
        'labels': labels,
        'dwells': dwells,
        'counts': counts
    })

    df['ratio'] = df['dwells'] / df['counts']
    
    df_sorted = df.sort_values(by='ratio')

    filtered_df_sorted = df_sorted[(df_sorted['dwells'] != 0) & (df_sorted['counts'] != 0)]

    # 필터링된 데이터프레임에서 상위 3개 및 하위 3개 선택
    top3_high_dwell_time = filtered_df_sorted.tail(3)
    top3_low_dwell_time = filtered_df_sorted.head(3)

    # 'ratio' 열을 문자열로 변환
    top3_high_dwell_time['ratio'] = top3_high_dwell_time['ratio'].astype(str)
    top3_low_dwell_time['ratio'] = top3_low_dwell_time['ratio'].astype(str)

    return {
        'top3': top3_high_dwell_time.set_index('labels').to_dict(orient='index'),
        'low3': top3_low_dwell_time.set_index('labels').to_dict(orient='index')
    }
    

def update_data(data, h_id):
    _id = Util.check_id(h_id)
    h_data = DB.read_one('history', {'_id':_id})
    
    for o_id in h_data['orders']:
        _id = Util.check_id(o_id)
        o_data = DB.read_one('order', {'_id':_id})
        for food in o_data['f_list']:
            _id = Util.check_id(food['f_id'])
            f_data = DB.read_one('food', {'_id':_id})
            S_NUM = S_ID_Table[f_data['s_id']]
            F_NUM = f_data['num']
            COUNT = food['count']

            data['stores'][S_NUM]['count'][F_NUM] += COUNT
        
    aoi_report = storage.get_json(h_data['aoi_analysis'])
    for store, s_value in aoi_report.items():
        S_NUM = store[6:]
        for food, f_value  in s_value['food_report'].items():
            F_NUM = food[5:]
            if 'ETC' in food or 'TAB' in food or len(F_NUM) > 2:
                continue

            F_NUM = int(F_NUM)-1
            COUNT = f_value['gaze_count']
            data['stores'][S_NUM]['dwell'][F_NUM] += COUNT
        
    return data
            
def get_detail(id):
    _id = Util.check_id(id)     

    history = DB.read_one('history', {'_id':_id})

    order_list = []
    for o_id in history['orders']:
        _id = Util.check_id(o_id)  
        order = DB.read_one('order', {'_id':_id})
        s_name = order['s_name']
        for f in order['f_list']:
            if 'f_name' in f.keys(): f_name = f['f_name']
            else: f_name = 'unknown'
            order_list.append({
                "s_name": s_name,
                "f_name": f_name,
                "count": f['count'],
                "price": f['price']
            })
    
    return {
        'date': Util.get_local_time(history['date']),
        'order_list': order_list
    }

def get_gazeflow(fix_key):
    fix_data = storage.get_json(fix_key)
    result = []
    
    for page in fix_data:
        new_fixs = []
        for fix in page['fixations']:
            new_fixs.append({
                'x':int(fix['cx']),
                'y':int(fix['cy']),
                'd':fix['et'] - fix['st']
            })
        result.append({
            "page": page['page'],
            "s_num": page['s_num'],
            "f_num": page['f_num'],
            "fixations": new_fixs
        })
        
    return result

def get_personal(aoi_key):
    aoi_data = storage.get_json(aoi_key)
    total = {}
    for store, s_value in aoi_data.items():
        S_NUM = store[6:]
        for food, f_value  in s_value['food_report'].items():
            F_NUM = food[5:]
            if 'ETC' in food or len(F_NUM) > 2:
                continue
            
            title = S_NUM + '-' + F_NUM
            total[title] = f_value['gaze_count']
    
    sorted_data = sorted(total.items(), key=lambda x: x[1], reverse=True)
    return sorted_data[:3]

def update_new_history2(h_id:str):
    data = DB.read_one('exhibition', {'_id':ObjectId(TODAY_ID)})
    del data['_id']

    updated_data = update_data(data, h_id)

    DB.replace_one('exhibition', {'_id':ObjectId(TODAY_ID)}, updated_data)
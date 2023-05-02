"""
menu_router
"""

import operator
from datetime import datetime

from fastapi import APIRouter
from core.models.store import MenuModel
from core.common.mongo2 import MongodbController
from .src.util import Util

menu_router = APIRouter(prefix="/menus")

PREFIX = 'api/v2/menus'
DB = MongodbController('FIE_DB')

@menu_router.get("/hello")
async def hello():
    return {"message": f"Hello '{PREFIX}'"}

@menu_router.get("/")
async def read_menus_of_store(s_id:str):
    """ 주어진 가게 아이디의 모든 메뉴판들을 불러온다. """
    print('hi')
    try:
        Util.check_id(s_id)
        response = DB.read_all_by_feild('menu', 's_id', s_id) # menus -> menu로 수정 DB 이름 오류
        # 날짜별로 정리 or 가장 최신 것만 주는거 고민
    except Exception as e:
        print('ERROR', e)
        return {
            'request': f'GET {PREFIX}?s_id={s_id}',
            'status': 'ERROR',
            'message': f'ERROR {e}'
        }
    
    return {
        'request': f'GET {PREFIX}?s_id={s_id}',
        'status': 'OK',
        'response': response
    }

@menu_router.get("/menu")
async def read_menu(id:str):
    """ 해당하는 id의 menu 정보를 받아온다. """
    try:

        response = DB.read_by_id('menu', id)

    except Exception as e:
        print('ERROR', e)
        return {
            'request': f'GET {PREFIX}?id={id}',
            'status': 'ERROR',
            'message': f'ERROR {e}'
        }
    
    return {
        'request': f'GET {PREFIX}?id={id}',
        'status': 'OK',
        'response': response
    }

@menu_router.post("/menu")
async def create_menu(s_id:str, menu:MenuModel):
    """ 해당하는 가게에 새로운 메뉴판을 설정한다. """

    data = menu.dict()
    
    sotred_f_list = sorted(data['f_list'], key=operator.itemgetter("pos"))
    
    try:
        Util.check_id(s_id)

        new_menu = {
            's_id': s_id,
            'date': datetime.now(),
            'f_list': sotred_f_list
        }

        new_id = DB.create('menu', new_menu)

        if DB.update_field_by_id('store', s_id, 'm_id', new_id):
            return {
                'request': f'POST {PREFIX}/menu?s_id={s_id}',  # 경로 수정 s_id -> ?s_id
                'status': 'OK'
            }
        
        else:
            return {
            'request': f'POST {PREFIX}/menu?s_id={s_id}',
            'status': 'ERROR',
            'message': f'ERROR!! Please contact your administrator'
        }

    except Exception as e:
        print('ERROR', e)
        return {
            'request': f'POST {PREFIX}/menu?s_id={s_id}',
            'status': 'ERROR',
            'message': f'ERROR {e}'
        }

@menu_router.get('/menu/foods')
async def read_menu_with_foods(id:str):  
    """ 해당하는 id의 음식 정보를 포함한 메뉴판 정보를 받아온다. """

    try:
        Util.check_id(id)
        response = DB.read_by_id('menu', id)
        
        
        food_ids = [food['f_id'] for food in response['f_list']]
        food_list = []

        for id in food_ids:
            food = DB.read_by_id('food', id)
            food_list.append({
                "f_id": id,
                "name": food['name'],
                "price": food['price'],
                "img_key" : food['img_key'],
                "desc" : food['desc'],
                "allergy" : food['allergy'],
                "origin" : food['origin']
            })
        response['f_list'] = food_list

    except Exception as e:
        print('ERROR', e)
        return {
            'request': f'GET {PREFIX}/menu/foods?id={id}',
            'status': 'ERROR',
            'message': f'ERROR {e}'
        }
    
    return {
        'request': f'GET {PREFIX}/menu/foods?id={id}',
        'status': 'OK',
        'response': response
    }

"""
user_menu
:Android APP에서 메뉴 정보를 불러오기
"""

from fastapi import APIRouter
from core.models.store import MenuModel
from core.models.store import FoodModel
from core.common.mongo import MongodbController

mongo = MongodbController('menu')
mongo_food = MongodbController('food')
menu_router = APIRouter(prefix="/menus")

@menu_router.get("/hi")
async def hello():
    return {"message": "Hello 'api/v1/user/hi'"}

@menu_router.get('/{s_id}')
async def get_lastest_menu(s_id:str):
    """ 해당하는 id의 메뉴판 정보를 받아온다. """
    
    try:
        response = mongo.read_lastest_one(s_id)
    except Exception as e:
        print('ERROR', e)
        return {
            'request': f'api/v1/user/menus/{s_id}',
            'status': 'ERROR',
            'message': f'ERROR {e}'
        }
    
    return {
        'request': f'api/v1/user/menus/{s_id}',
        'status': 'OK',
        'response': response
    }
"""
menu_router
"""

import operator
from datetime import datetime

from fastapi import APIRouter, Depends, Request
from core.models.store import MenuModel
from core.common.authority import TokenManagement
from core.common.mongo import MongodbController
from .src.util import Util
from .src.meta import Meta


TokenManager = TokenManagement()

menu_router = APIRouter(prefix="/menus", dependencies=[Depends(TokenManager.dispatch)])


PREFIX = 'api/v2/menus'
DB = MongodbController('FIE_DB2')

@menu_router.get("/hello")
async def hello():
    return {"message": f"Hello '{PREFIX}'"}

@menu_router.get("/q")
async def read_menus_of_store(s_id:str, request:Request):
    """ 주어진 가게 아이디의 모든 메뉴판들을 불러온다. """
    assert TokenManager.is_seller(request.state.token_scope), 403.1

    Util.check_id(s_id)
    response = DB.read_all('menu', {'s_id': s_id}) 

    for menu in response:
        menu['date'] = Util.get_local_time(menu['date'])

    return {
        'menu_list' : response
    }

@menu_router.get("/menu")
async def read_menu(id:str):
    """ 해당하는 id의 menu 정보를 받아온다. """

    _id = Util.check_id(id)
    response = DB.read_one('menu', {'_id':_id})
    
    return {
        "_id": id,
        "s_id": response['s_id'],
        "s_num": response['s_num'],
        "date": Util.get_local_time(response['date']),
        "f_list" : response['f_list']
    }

@menu_router.post("/menu")
async def create_menu(s_id:str, menu:MenuModel, request:Request):
    """ 해당하는 가게에 새로운 메뉴판을 설정한다. """
    assert TokenManager.is_seller(request.state.token_scope), 403.1
    
    data = menu.dict()
    
    _id = Util.check_id(s_id)
    store = DB.read_one('store', {'_id':_id})

    new_menu = {
        's_id': s_id,
        's_num': store['num'],
        'date': Util.get_utc_time().now(),
        'f_list': data['f_list']
    }

    new_id = str(DB.insert_one('menu', new_menu))

    DB.update_one('store', {'_id': _id}, {'m_id': new_id})
    update_meta(s_id, new_id)

    return {
        'm_id': new_id
    }
    

@menu_router.get('/menu/foods')
async def read_menu_with_foods(id:str):  
    """ 해당하는 id의 음식 정보를 포함한 메뉴판 정보를 받아온다. """

    _id = Util.check_id(id)
    response = DB.read_one('menu', {'_id':_id})
    
    food_ids = [food['f_id'] for food in response['f_list']]
    food_list = []

    for f_id in food_ids:
        _id = Util.check_id(f_id)
        food = DB.read_one('food', {'_id': _id})
        food_list.append({
            "f_id": f_id,
            "name": food['name'],
            "price": food['price'],
            "img_key" : food['img_key'],
            "desc" : food['desc'],
            "allergy" : food['allergy'],
            "origin" : food['origin'],
            "num": food['num']
        })
    response['f_list'] = food_list
    s_id = Util.check_id(response['s_id'])
    store = DB.read_one('store', {'_id':s_id})

    return {
        "_id": id,
        "s_id": response['s_id'],
        "s_num": store['num'],
        's_name': store['name'],
        "date": Util.get_local_time(response['date']),
        "f_list" : response['f_list']
    }

def update_meta(s_id:str, new_m_id:str):
    cur = Meta.get_meta()
    content = cur['content']
    content[s_id] = new_m_id
    Meta.create(content)
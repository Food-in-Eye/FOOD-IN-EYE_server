"""
food_router
"""
import os

from fastapi import APIRouter, UploadFile
from fastapi.responses import FileResponse
from core.models.store import FoodModel
from core.common.mongo import MongodbController
from .src.util import Util

food_router = APIRouter(prefix="/foods")

PREFIX = 'api/v2/foods'
IMAGES_DIR = '../images'
DB = MongodbController('FIE_DB')

@food_router.get("/hello")
async def hello():
    return {"message": f"Hello '{PREFIX}'"}

@food_router.get("/")
async def read_all_food(s_id:str): 
    """ 주어진 가게에 속하는 음식 정보를 모두 받아온다. """

    try:
        Util.check_id(s_id)

        response = DB.read_all_by_feild('food', 's_id', s_id)

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

@food_router.get("/food")
async def read_food(id:str):
    """ 해당하는 id의 음식 정보를 받아온다. """

    try:
        Util.check_id(id)

        response = DB.read_by_id('food', id)
    except Exception as e:
        print('ERROR', e)
        return {
            'request': f'GET {PREFIX}/food?id={id}',
            'status': 'ERROR',
            'message': f'ERROR {e}'
        }
    
    return {
        'request': f'GET {PREFIX}/food?id={id}',
        'status': 'OK',
        'response': response
    }

@food_router.post("/food")
async def create_food(s_id:str, food:FoodModel):
    """ 해당하는 id의 음식 정보를 업데이트한다. """

    data = food.dict() # body에 s_id, img_key는 미포함

    # todo: 실제 존재하는 가게의 id인지 확인하면 좋을 듯 함.(사고 방지)
    data['s_id'] = s_id
    data['img_key'] = None
    try:
        id = str(DB.create('food', data))
        print(data)

    except Exception as e:
        print('ERROR', e)
        return {
            'request': f'POST {PREFIX}/food?s_id={s_id}',
            'status': 'ERROR',
            'message': f'ERROR {e}'
        }
    
    return {
        'request': f'POST {PREFIX}/food?s_id={s_id}',
        'status': 'OK',
        'document_id': id
    }

@food_router.put('/food')
async def update_food(id:str, food:FoodModel):
    """ 해당하는 id의 food 정보를 변경한다. """
    data = food.dict()

    try:
        Util.check_id(id)
        if DB.update_by_id('food', id, data):
            return {
                'request': f'PUT {PREFIX}/food?id={id}',
                'status': 'OK'
            }

    except Exception as e:
        print('ERROR', e)
        return {
            'request': f'PUT {PREFIX}/food?id={id}',
            'status': 'ERROR',
            'message': f'ERROR {e}'
        }


@food_router.put('/food/image')
async def update_food_image(id: str, file: UploadFile):
    try:
        Util.check_id(id)

        current = DB.read_by_id('food', id)

        if current['img_key'] is not None:
            os.remove(os.path.join(IMAGES_DIR, current['img_key']))

        image = await file.read()
        
        image, image_key = Util.resize_image(image)

        with open(os.path.join(IMAGES_DIR, image_key), "wb") as fp:
            fp.write(image)

        if DB.update_field_by_id('food', id, 'img_key', image_key):
            return {
                'request':f'PUT {PREFIX}/food/image?id={id}',
                'status': 'OK'
            }
        
    except Exception as e:
        print('ERROR', e)
        return {
            'request': f'PUT {PREFIX}/food/image?id={id}',
            'status': 'ERROR',
            'message': f'ERROR {e}'
        }

@food_router.get('/food/image')
async def get_food_image(id:str):
    try:
        Util.check_id(id)

        response = DB.read_by_id('food', id)

        path = os.path.join(IMAGES_DIR, response['img_key'])

        if os.path.isfile(path):
            return FileResponse(path)
        
        else:
            raise Exception(f'img key ERROR')
        
    except Exception as e:
        print('ERROR', e)
        return {
            'request': f'GET {PREFIX}/food/image?id={id}',
            'status': 'ERROR',
            'message': f'ERROR {e}'
        }
"""
food_router
"""
import io
from PIL import Image

from fastapi import APIRouter, UploadFile
from core.models.store import FoodModel
from core.common.mongo2 import MongodbController
from core.common.s3 import Storage
from .src.util import Util

food_router = APIRouter(prefix="/foods")

PREFIX = 'api/v2/foods'
DB = MongodbController('FIE_DB')
storage = Storage('foodineye')

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

# @food_router.post('/food/image')
# async def create_food_image(id: str, file: UploadFile):
#     try:
#         Util.check_id(id)
#         file_content = await file.read()
        
#         # re-size 기능 고민
#         if file.content_type not in ["image/jpeg", "image/jpg"]:
#             with Image.open(io.BytesIO(file_content)) as im:
#                 im = im.convert('RGB')
#                 with io.BytesIO() as output:
#                     im.save(output, format='JPEG')
#                     file_content = output.getvalue()
            
#         image_key = storage.upload(file_content, form='jpg', path='images')
        
#         # image_key를 데이터베이스에 업데이트
#         if DB.update_field_by_id('food', id, 'img_key', image_key):
#             return {
#                 'request':f'POST {PREFIX}/food/image?id={id}',
#                 'status': 'OK',
#                 'img_url': 'https://foodineye.s3.ap-northeast-2.amazonaws.com/' + image_key
#             }
        
#     except Exception as e:
#         print('ERROR', e)
#         return {
#             'request': f'POST {PREFIX}/food/image?id={id}',
#             'status': 'ERROR',
#             'message': f'ERROR {e}'
#         }

@food_router.put('/food/image')
async def update_food_image(id: str, file: UploadFile):
    try:
        Util.check_id(id)

        current = DB.read_by_id('food', id)

        if current['img_key'] is not None:
            storage.delete(current['img_key'])

        file_content = await file.read()
        
        # re-size 기능 고민
        if file.content_type not in ["image/jpeg", "image/jpg"]:
            with Image.open(io.BytesIO(file_content)) as im:
                im = im.convert('RGB')
                with io.BytesIO() as output:
                    im.save(output, format='JPEG')
                    file_content = output.getvalue()
            
        image_key = storage.upload(file_content, form='jpg', path='images')
        
        if DB.update_field_by_id('food', id, 'img_key', image_key):
            return {
                'request':f'PUT {PREFIX}/food/image?id={id}',
                'status': 'OK',
                'img_url': 'https://foodineye.s3.ap-northeast-2.amazonaws.com/' + image_key
            }
        
    except Exception as e:
        print('ERROR', e)
        return {
            'request': f'PUT {PREFIX}/food/image?id={id}',
            'status': 'ERROR',
            'message': f'ERROR {e}'
        }

"""
store_router
"""

from fastapi import APIRouter
from core.models.store import StoreModel
from core.common.mongo2 import MongodbController
from .src.util import Util

store_router = APIRouter(prefix="/stores")

PREFIX = 'api/v2/stores'
DB = MongodbController('FIE_DB')

@store_router.get("/hello")
async def hello():
    return {"message": f"Hello '{PREFIX}'"}


@store_router.get('/')
async def read_all_store():
    """ DB에 존재하는 모든 식당의 정보를 받아온다 """

    try:
        result = DB.read_all('store')
        response = []

        for r in result:
            response.append(r)
            

    except Exception as e:
        print('ERROR', e)
        return {
            'request': f'GET {PREFIX}',
            'status': 'ERROR',
            'message': f'ERROR {e}'
        }
    
    return {
        'request': f'GET {PREFIX}',
        'status': 'OK',
        'response': response
    }


@store_router.get('/store')
async def read_store(id:str):
    """ 특정 id의 가게 정보를 받아온다."""

    try:
        Util.check_id(id)

        response = DB.read_by_id('store', id)

    except Exception as e:
        print('ERROR', e)
        return {
            'request': f'GET {PREFIX}/store?id={id}',
            'status': 'ERROR',
            'message': f'ERROR {e}'
        }
    
    return {
        'request': f'GET {PREFIX}/store?id={id}',
        'status': 'OK',
        'response': response
    }


# ToDo: user id 같이 받아야 할 듯. 
@store_router.post("/store")
async def create_store(store:StoreModel):
    """ 입력받은 정보의 가게를 생성한다. (최초 가입시에만 가능) """

    data = store.dict()
    data['status'] = data['status'].value

    try:
        id = str(DB.create('store', data))

    except Exception as e:
        print('ERROR', e)
        return {
            'request': f'POST {PREFIX}/store',
            'status': 'ERROR',
            'message': f'ERROR {e}'
        }
    
    return {
        'request': f'POST {PREFIX}/store',
        'status': 'OK',
        'document_id': id
    }

@store_router.put('/store')
async def update_store(id:str, store: StoreModel):
    """ 해당하는 id의 document를 변경한다. """
    data = store.dict()
    data['status'] = data['status'].value
    
    try:
        Util.check_id(id)
        
        if DB.update_by_id('store', id, data):
            return {
                'request': f'PUT {PREFIX}/store?id={id}',
                'status': 'OK'
            }
        
        else:
            raise Exception(f'Update failed...')

    except Exception as e:
        print('ERROR', e)
        return {
            'request': f'PUT {PREFIX}/store?id={id}',
            'status': 'ERROR',
            'message': f'ERROR {e}'
        }
"""
user_router
"""

from .src.util import Util
from core.models import *
from core.common.mongo import MongodbController
from core.common.authority import AuthManagement, TokenManagement

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

user_router = APIRouter(prefix="/users")
AuthManager = AuthManagement()
TokenManager = TokenManagement()

PREFIX = 'api/v2/users'

DB = MongodbController('FIE_DB2')
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", scheme_name="JWT")


@user_router.get("/hello")
async def hello():
    return {"message": f"Hello '{PREFIX}'"}


@user_router.post('/idcheck')
async def check_duplicate_id(data: IdModel):
    try:
        if AuthManager.check_dup(data.id):
            state = 'unavailable'
        else:
            state = 'available'

    except HTTPException as e:
        raise HTTPException(status_code = e.status_code, detail = e.detail)
    return {
        'state': state
    }


"""
buyer API
"""

@user_router.post('/buyer/signup')
async def buyer_signup(data: BuyerModel):
    try:
        if AuthManager.check_dup(data.id) == False:
            user = {
                'id': data.id,
                'pw': AuthManager.get_hashed_pw(data.pw),
                'scope': "buyer",
                'name': data.name,
                'gender': data.gender.value,
                'age': data.age,
                'R_Token': ''
            }
            u_id = str(DB.insert_one('user', user))
        else:
            raise HTTPException(status_code = 409, detail = f'Duplicate ID')
        
    except HTTPException as e:
        raise HTTPException(status_code = e.status_code, detail = e.detail)
    return {
        'u_id': u_id
    }


@user_router.post('/buyer/login')
async def buyer_login(data: OAuth2PasswordRequestForm = Depends()):
    try:
        u_id = AuthManager.get_uid(data.username)

        user = AuthManager.auth_user(u_id, data.password)
        user['R_Token'] = TokenManager.init_r_token(u_id, "buyer")

        DB.update_one('user', {'u_id':u_id}, {'R_Token': user['R_Token']})

    except HTTPException as e:
        raise HTTPException(status_code = e.status_code, detail = e.detail)
    return {
        'u_id': u_id,
        'token_type': "bearer",
        'A_Token': TokenManager.ACCESS_TOKEN,
        'R_Token': user['R_Token']
    }


@user_router.post('/buyer/info')
async def get_user_info(u_id:str, data: PwModel):
    try:
        Util.check_id(u_id)

        user = AuthManager.auth_user(u_id, data.pw)
    
    except HTTPException as e:
        raise HTTPException(status_code = e.status_code, detail = e.detail)
    return {
        'id': user['id'],
        'name': user['name'],
        'gender': user['gender'],
        'age': user['age'],
    }
    
    
@user_router.put('/buyer/change')
async def change_buyer_info(u_id:str, data: BuyerModifyModel):
    try:
        Util.check_id(u_id)

        AuthManager.auth_user(u_id, data.old_pw)

        new_hashed_pw = AuthManager.get_hashed_pw(data.new_pw)

        new_data = {
            'pw': new_hashed_pw,
            'name': data.name,
            'gender': data.gender.value,
            'age': data.age
        }

        DB.update_one('user', {'u_id':u_id}, new_data)
    
    except HTTPException as e:
        raise HTTPException(status_code = e.status_code, detail = e.detail)


"""
seller API
"""

@user_router.post('/seller/signup')
async def seller_signup(data: SellerModel):
    try:
        if AuthManager.check_dup(data.id) == False:
            user = {
                "id": data.id,
                "pw": AuthManager.get_hashed_pw(data.pw),
                "scope": "seller",
                "s_id": '',
                "R_Token": ""
            }
            u_id = str(DB.insert_one('user', user))
        else:
            raise HTTPException(status_code = 409, detail = f'Duplicate ID')
        
    except HTTPException as e:
        raise HTTPException(status_code = e.status_code, detail = e.detail)
    return {
        "u_id": u_id
    }


@user_router.post('/seller/login')
async def seller_login(data: OAuth2PasswordRequestForm = Depends()):
    try:
        u_id = AuthManager.get_uid(data.username)

        user = AuthManager.auth_user(u_id, data.password)
        user['R_Token'] = TokenManager.init_r_token(user['_id'], "seller")

        DB.update_one('user', {'u_id':u_id}, {"R_Token": user['R_Token']})

    except HTTPException as e:
        raise HTTPException(status_code = e.status_code, detail = e.detail)
    return {
        'u_id': user['_id'],
        's_id': user['s_id'],
        'token_type': "bearer",
        'A_Token': TokenManager.ACCESS_TOKEN,
        'R_Token': user['R_Token']
    }


@user_router.post('/seller/info')
async def get_user_info(u_id:str, data: PwModel):
    try:
        Util.check_id(u_id)

        user = AuthManager.auth_user(u_id, data.pw)
    
    except HTTPException as e:
        raise HTTPException(status_code = e.status_code, detail = e.detail)
    return {
        'id': user['id'],
        's_id': user['s_id']
    }
    
@user_router.put('/seller/change')
async def change_seller_info(u_id:str, data: SellerModifyModel):
    try:
        Util.check_id(u_id)

        AuthManager.auth_user(u_id, data.old_pw)
    
        new_hashed_pw = AuthManager.get_hashed_pw(data.new_pw)

        new_data = {
            'pw': new_hashed_pw,
        }

        DB.update_one('user', {'u_id':u_id}, new_data)
    
    except HTTPException as e:
        raise HTTPException(status_code = e.status_code, detail = e.detail)


"""
Token renewal API
"""

@user_router.get('/issue/access')
async def get_access_token(u_id:str, payload: str = Depends(TokenManager.auth_r_token)):
    try:
        user = DB.read_one('user', {'_id':ObjectId(u_id)})
        if user['scope'] != payload['scope']:
            raise HTTPException(status_code = 401, detail = f'Scope verification failed.')
        
        response = TokenManager.recreate_a_token(user['scope'])

    except HTTPException as e:
        raise HTTPException(status_code = e.status_code, detail = e.detail)
    return {
        'A_Token': response
    }

@user_router.get('/issue/refresh')
async def get_refresh_token(u_id:str, payload: str = Depends(TokenManager.auth_r_token)):
    try:
        user = DB.read_one('user', {'_id':ObjectId(u_id)})
        if user['scope'] != payload['scope']:
            raise HTTPException(status_code = 401, detail = f'Scope verification failed.')
        
        response = TokenManager.recreate_r_token(payload, u_id, user['scope'])
        DB.update_one('user', {'u_id':u_id}, {"R_Token": response})

    except HTTPException as e:
        raise HTTPException(status_code = e.status_code, detail = e.detail)
    return {
        'R_Token': response
    }
    

@user_router.get('/test/a_token')
async def get_refresh_token(a_token: str = Depends(TokenManager.auth_a_token)):
    return {
        'request': f'GET {PREFIX}/test/a_token',
        'a_token': a_token
    }
    
@user_router.get('/test/r_token')
async def get_refresh_token(r_token: str = Depends(TokenManager.auth_r_token)):
    return {
        'r_token': r_token
    }
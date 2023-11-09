from bson.objectid import ObjectId
from datetime import datetime, timedelta
import pytz
from core.error.exception import CustomException
from core.common.mongo import MongodbController

class Util:

    @staticmethod
    def is_null(target:dict, fields:list[str]) -> bool :
        for field in fields:
            if target[field] is None:
                return True
            
        return False

    '''
        id 체크도 어떤 아이디가 안된건지 확인하고싶음
        예를들면 여기선 그냥 False로 두고 아님 걍 exception 발생시켜서 이 밖에서 'order_id'가 이상한지 'user_id'가 이상한지 알고싶음
    '''
    @staticmethod
    def check_id(id:str) -> ObjectId:
        if not ObjectId.is_valid(id):
            raise CustomException(503.71, f'id: \'{id}\'')
        else:
            return ObjectId(id)


    @staticmethod
    def get_utc_time() -> datetime:
        """ 현재 시간을 가져와 UTC timezone으로 리턴한다. """
        date = datetime.now(pytz.timezone('Asia/Seoul'))
        utc_time = date.astimezone(pytz.utc)
        return utc_time
    
    @staticmethod
    def get_utc_time_by_datetime(date:datetime) -> datetime:
        """ local 시간을 입력받아 UTC timezone으로 리턴한다. 
            * 주의. mongoDB 쿼리 결과를 변환할 때 사용하면 안 됨 """
        # timestamp = datetime.strptime(date, '%Y-%m-%d')
        utc_time = date.astimezone(pytz.utc)
        return utc_time
    
    @staticmethod
    def get_utc_time_by_str(date:str) -> datetime:
        """ local 시간("%Y%m%d")을 입력받아 UTC timezone으로 리턴한다. 
            * 주의. mongoDB 쿼리 결과를 변환할 때 사용 
            ** 주의. 실행 방법(local, docker)에 따라 수정이 필요함 """
        # local에서 실행할 때
        # timestamp = datetime.strptime(date, '%Y-%m-%d')
        # docker에서 실행할 때 
        timestamp = datetime.strptime(date, '%Y-%m-%d') - timedelta(hours=9)

        utc_time = timestamp.astimezone(pytz.utc)
        return utc_time
    
    @staticmethod
    def get_local_time(date:datetime) -> datetime:
        """ UTC 시간을 입력 받아 Asia/Seoul timezone으로 리턴한다. 
            * 주의. 실행 방법(local, docker)에 따라 수정이 필요함 """
        # local에서 실행할 때
        # local_time = date.astimezone(pytz.timezone('Asia/Seoul')) + timedelta(hours=9)
        # docker에서 실행할 때
        local_time = date.astimezone(pytz.timezone('Asia/Seoul'))
        return local_time


    @staticmethod
    def delete_user_hid(h_id:str) -> bool:
        """
            h_id를 받아서 user의 진행중인 주문 내역을 초기화한다.
        """
        DB = MongodbController('FIE_DB2')
        _id = Util.check_id(h_id)
        history = DB.read_one('history', {'_id': _id})
        _id = Util.check_id(history['u_id'])
        return DB.update_one('user', {'_id':_id}, {'h_id':""})

    @staticmethod
    def is_done(h_id:str) -> str:
        """
            해당 주문과 관련된 order들이 모두 완료되었는지 확인한다.
             - 만약 완료되었으면 사용자 정보에서 진행중인 주문을 삭제하고 True를 리턴한다.
             - 완료되지 않았으면 False를 리턴한다.
        """
        DB = MongodbController('FIE_DB2')
        _id = Util.check_id(h_id)
        history = DB.read_one('history', {'_id':_id})
        for o_id in history["orders"]:
            _id = Util.check_id(o_id)
            order = DB.read_one('order', {'_id':_id})
            if order['status'] !=2:
                return False
        
        if Util.delete_user_hid(h_id):
            return True
        else:
            pass
            # error 처리 추가....?
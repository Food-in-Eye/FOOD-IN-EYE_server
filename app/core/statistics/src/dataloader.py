
from core.common.mongo import MongodbController
from core.error.exception import CustomException
from v2.routers.src.util import Util
from datetime import timedelta, datetime

DB = MongodbController('FIE_DB2')

class DataLoader:
    
    @staticmethod
    def get_store_table():
        
        try:
            stores = DB.read_all('store', {}, {'_id': 1, 'num':1})
            result = {}
            for store in stores:
               result[store['_id']] = store['num']
            
            return result

        except CustomException as e:
            print(e)
    
    @staticmethod
    def get_food_table():
        
        try:
            foods = DB.read_all('food', {}, {'_id': 1, 'num':1})
            result = {}
            for food in foods:
               result[food['_id']] = food['num']
            return result

        except CustomException as e:
            print(e)


    ''' 오류가 있는 o_id를 걸러내기 위한 작업 
        - 주석처리된 코드: 원래 함수
        - 주석 아래 코드: 특수하게 생성한 함수 '''
    # def get_orders(query):

    #     try:
    #         orders = DB.read_all('order', query, {'s_id': 1, 'date':1, 'f_list':1})
    #         for order in orders:
    #             order['date'] = str(Util.get_local_time(order['date']))
    #         return orders

    #     except CustomException as e:
    #         print(e)
    def get_orders(pipeline):
        try:
            orders = DB.aggregate_pipline('order', pipeline)
            for order in orders:
                order['_id'] = str(order['_id'])
                order['date'] = str(Util.get_local_time(order['date']))
            return orders

        except CustomException as e:
            print(e)

    ''' 오류가 있는 h_id를 걸러내기 위한 작업 
        - 주석처리된 코드: 원래 함수
        - 주석 아래 코드: 특수하게 생성한 함수 '''
    # def get_aoi_reports(query):
    #     result = []
    #     try:
    #         historys = DB.read_all('history', query, {'date':1, 'aoi_analysis':1})
    #         for history in historys:
    #             result.append({
    #                 "date": str(Util.get_local_time(history['date'])),
    #                 "aoi_key": history['aoi_analysis']})
    #         return result

    #     except CustomException as e:
    #         print(e)
    def get_aoi_reports(pipeline):
        result = []
        try:
            historys = DB.aggregate_pipline('history', pipeline)
            for history in historys:
                result.append({
                    "date": str(Util.get_local_time(history['date'])),
                    "aoi_key": history['aoi_analysis']})
            return result

        except CustomException as e:
            print(e)



    def get_orders_oneday(pipeline):
        try:
            orders = DB.aggregate_pipline('order', pipeline)

            for order in orders:
                order['_id'] = str(order['_id'])
                
                hour = Util.get_local_time(order['date']).hour
                min = Util.get_local_time(order['date']).minute
                sec = Util.get_local_time(order['date']).second
                order['date'] = str(datetime(2022,11,1) + timedelta(hours=hour, minutes=min, seconds=sec))
            return orders
        except CustomException as e:
            print(e)

    def get_aoi_reports_oneday(pipeline):
        result = []
        try:
            historys = DB.aggregate_pipline('history', pipeline)
            for history in historys:
                history['_id'] = str(history['_id'])
                hour = Util.get_local_time(history['date']).hour                
                min = Util.get_local_time(history['date']).minute
                sec = Util.get_local_time(history['date']).second

                result.append({
                    "date": str(datetime(2022,11,1) + timedelta(hours=hour, minutes=min, seconds=sec)),
                    "aoi_key": history['aoi_analysis']})
            
            return result

        except CustomException as e:
            print(e)
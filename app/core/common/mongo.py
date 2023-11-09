import os
from dotenv import load_dotenv
from pymongo import MongoClient

from bson.objectid import ObjectId

from core.error.exception import CustomException

def objectIdToStr(d:dict) -> dict:
    for k, v in d.items():
        if type(v) is ObjectId:
            d[k] = str(v)

    return d
            
class MongodbController:
    """ 몽고디비를 통해 특정 DATABASE의 Collections에 CRUD를 하도록 돕는 클래스 """
    
    def __init__(self, DB:str) -> None:
        load_dotenv()

        client = MongoClient(os.environ['DATABASE_URL'])
        db_names = client.list_database_names()
        
        if DB in db_names:
            self.db = client[DB]
        else:
            raise CustomException(503.51, f'DB: \'{DB}\'')

        self.collections = self.db.list_collection_names()
    
    def get_collection(self, name:str):
        if name in self.collections:
            return self.db[name]
        else:
            raise CustomException(503.52, f'collection: \'{name}\'')
        
    def insert_one(self, collection:str, data:dict) -> ObjectId:
        """ 딕셔너리를 받아서 collection에 새로운 document를 추가한다. """
        assert collection, data is not None

        coll = self.get_collection(collection)
        
        result = coll.insert_one(data)

        if result.acknowledged is False:
            raise CustomException(503.53)

        return result.inserted_id

    def replace_one(self, collection:str, query:dict, data:dict) -> bool:
        """ query와 일치하는 document의 내용을 변경한다. """
        assert collection and data is not None

        coll = self.get_collection(collection)

        result = coll.replace_one(query, data)
        if result.acknowledged is False:
            raise CustomException(503.54)
        
        if result.modified_count != 1:
            raise CustomException(503.57)

        return True
    
    def update_one(self, collection:str, query:dict, fields:dict) -> bool:
        """ query와 일치하는 document의 내용을 변경한다. """
        assert collection and fields is not None

        coll = self.get_collection(collection)

        result = coll.update_one(query, {'$set':fields})

        if result.acknowledged is False:
            raise CustomException(503.54)
        
        if result.modified_count != 1:
            raise CustomException(503.57)

        return True
    

    def read_one(self, collection:str, query:dict) -> dict:
        """ query와 일치하는 document를 하나 읽어온다. """
        assert collection is not None
        coll = self.get_collection(collection)

        result = coll.find_one(query)
        if result is None:
            raise CustomException(503.55)
        
        return objectIdToStr(result)
    
    def read_all(self, collection:str, query:dict = {}, fields:dict = None, asc_by: str=None, asc:bool=True) -> dict:
        """ query와 일치하는 모든 문서들을 받아온다. 정렬 조건이 존재할 시 반영한다. """
        assert collection is not None
        coll = self.get_collection(collection)

        if fields == None:
            result = coll.find(query)
        else: 
            result = coll.find(query, fields)

        if asc_by:
            result.sort([(asc_by, 1 if asc else -1)])

        if result is None:
            raise CustomException(503.55)
        
        response = []
        for r in result:
            response.append(objectIdToStr(r))
        
        return response 

    # 고민중이니 주석처리
    # def delete(self, id:str) -> bool:
    #     """ id가 일치하는 document를 삭제한다. """
    #     assert id is not None

    #     result = self.coll.delete_one({'_id': ObjectId(id)})
    #     if result.acknowledged is False:
    #         raise CustomException(503.56, f'id: \'{id}\'')
        
    #     return True

    def aggregate_pipline(self, collection:str, pipeline:list):
        coll = self.get_collection(collection)

        return list(coll.aggregate(pipeline))
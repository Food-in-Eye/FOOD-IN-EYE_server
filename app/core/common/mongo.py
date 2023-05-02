import os
from dotenv import load_dotenv
from pymongo import MongoClient

from bson.objectid import ObjectId


def dictToStr(d:dict) -> dict:
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
            raise Exception(f'No DataBase exists with name \'{DB}\'')

        self.collections = self.db.list_collection_names()
    
    def get_collection(self, name:str):
        if name in self.collections:
            return self.db[name]
        else:
            raise Exception(f'No collection exists with name \'{name}\'')
        
    def create(self, collection:str, data:dict) -> ObjectId:
        """ 딕셔너리를 받아서 collection에 새로운 document를 추가한다. """
        assert collection, data is not None

        coll = self.get_collection(collection)
        
        result = coll.insert_one(data)
        if result.acknowledged is False:
            raise Exception(f'Failed to CREATE new document.')

        return result.inserted_id

    def update_by_id(self, collection:str, id:str, data:dict) -> bool:
        """ id가 일치하는 document의 내용을 변경한다. """
        assert collection and id and data is not None

        coll = self.get_collection(collection)

        result = coll.update_one({'_id': ObjectId(id)},
                                {'$set':data})
        if result.acknowledged is False:
            raise Exception(f'Failed to UPDATE document with id \'{id}\'')
        
        if result.modified_count > 1:
            raise Exception(f'Multiple documents have changed.')

        return True

    def update_field_by_id(self, collection:str, id:str, field:str, value) -> bool:
        assert collection and id and field and value is not None

        coll = self.get_collection(collection)

        result = coll.update_one({'_id': ObjectId(id)},
                                 {'$set': {field: value}})
        if result.acknowledged is False:
            raise Exception(f'Failed to UPDATE document with id \'{id}\' to set \'{field}:{value}\'')
        
        if result.modified_count != 1:
            return False
        
        return True

    def read_by_id(self, collection:str, id:str) -> dict:
        """ id가 일치하는 document를 읽어온다. """
        assert collection and id is not None
        coll = self.get_collection(collection)

        result = coll.find_one({'_id': ObjectId(id)})
        if result is None:
            raise Exception(f'Failed to READ document with id \'{id}\'')
        
        return dictToStr(result)
    
    def read_all(self, collection:str) -> list:
        """ collection의 모든 document를 읽어온다. """
        assert collection is not None
        coll = self.get_collection(collection)

        result = coll.find()
        if result is None:
            raise Exception(f'Failed to READ document')
        
        response = []
        for r in result:
            response.append(dictToStr(r))
        
        return response  
    
    # 이게 쓰이나?
    # def read_all_by_id(self, id:str) -> dict:
    #     """ id가 일치하는 document를 모두 읽어온다. """
    #     assert id is not None

    #     result = list(self.coll.find({'_id': ObjectId(id)}))
        
    #     if result is None:
    #         raise Exception(f'Failed to READ document with id \'{id}\'')
        
    #     if len(result) != 1:
    #         raise Exception(f'Duplicate ID Error')
        
    #     else:
    #         result = result[0]

    #     return dictToStr(result)
    
    def read_all_by_feild(self, collection:str, field:str, value:str) -> dict:
        """ field의 value가 일치하는 document를 모두 읽어온다. """
        assert collection and id is not None
        coll = self.get_collection(collection)

        result = list(coll.find({field: value}))
        
        if result is None:
            raise Exception(f'Failed to READ document with field \'{field}\'')

        response = []
        for r in result:
            response.append(dictToStr(r))
        
        return response  

    # 고민중이니 주석처리
    # def delete(self, id:str) -> bool:
    #     """ id가 일치하는 document를 삭제한다. """
    #     assert id is not None

    #     result = self.coll.delete_one({'_id': ObjectId(id)})
    #     if result.acknowledged is False:
    #         raise Exception(f'Failed to DELETE document with id \'{id}\'')
        
    #     return True
    
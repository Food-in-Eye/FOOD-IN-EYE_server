from bson.objectid import ObjectId

class Util:

    @staticmethod
    def is_null(target:dict, fields:list[str]) -> bool :
        for field in fields:
            if target[field] is None:
                return True
            
        return False

    @staticmethod
    def check_id(id:str):
        if not ObjectId.is_valid(id):
            raise Exception(f'The id format is not valid. Please check')

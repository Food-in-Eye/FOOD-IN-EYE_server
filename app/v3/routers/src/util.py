import io
import uuid
from PIL import Image
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
        
    @staticmethod
    def resize_image(file_content, size=1000):
        with Image.open(io.BytesIO(file_content)) as im:
            im.thumbnail((size, size))
            with io.BytesIO() as output:
                im.save(output, format='JPEG')
                file_content = output.getvalue()
            
        random_id = str(uuid.uuid4()) + ".jpg"
        return file_content, random_id

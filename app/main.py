from fastapi import FastAPI
from v2.api import v2_router
from v3.api import v3_router

app = FastAPI()

app.include_router(v2_router)
app.include_router(v3_router)
import os
def list_files(directory):
        try:
            files = os.listdir(directory)
            for file in files:
                print(file)
        except OSError as e:
            print(f"Error: {directory} - {e.strerror}.")

@app.get("/")
async def hello():
    list_files('../images')
    return {"message": "Hello World"}
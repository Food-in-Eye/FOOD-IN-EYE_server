from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import traceback

from core.error.exception import APIException,CustomException

from v2.api import v2_router

app = FastAPI()
app.include_router(v2_router)

# from apscheduler.schedulers.background import BackgroundScheduler
# from datetime import datetime
# from core.statistics.run import CallAnalysis


# scheduler = BackgroundScheduler()
# scheduler.add_job(CallAnalysis.daily_summary, 'cron', hour=0, minute=0)  # 매일 자정에 실행
# scheduler.start()


exmanager = APIException()

@app.exception_handler(CustomException)
async def custom_exception_handler(request:Request, ex:CustomException):
    status_code, detail = exmanager.get_status(ex)
    stack_trace = traceback.format_exc()

    print(f'# ERROR {ex.status_code}, {detail}')
    print(f"# ERROR path: {request.url.path}\n# {stack_trace}")
    return JSONResponse(
        status_code = status_code, 
        content = {'detail' : detail}
    )
    
@app.exception_handler(AssertionError)
async def assert_exception_handler(request:Request, ex:AssertionError):
    status_code, detail = exmanager.get_status_assert(ex)
    stack_trace = traceback.format_exc()

    print(f'# ERROR {ex.args[0]}, {detail}')
    print(f"# ERROR path: {request.url.path}\n# {stack_trace}")
    return JSONResponse(
        status_code = status_code, 
        content = {'detail' : detail}
    )

# Todo : traceback이 두 번 출려되는 문제가 발생하므로 여기서는 출력하지 않도록 했음. 해결 필요...
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, ex: Exception):
    stack_trace = traceback.format_exc()

    print(f'# ERROR {500}, {str(ex)}')
    print(f"# ERROR path: {request.url.path}")
    return JSONResponse(
        status_code = 500,
        content={'detail': "Please Call Admin"}
    )

@app.get("/")
async def hello():
    return {"message": "Hello World"}
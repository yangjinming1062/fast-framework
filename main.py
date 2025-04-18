import traceback

import uvicorn
from fastapi import FastAPI
from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from api import *
from components import *


def register_handler(_app):
    @_app.exception_handler(APIException)
    async def api_exception_handler(_: Request, ex: APIException):
        msg = {
            "code": ex.code,
            "message": ex.msg,
            "details": [{"reason": ex.msg, "metadata": {}}],
        }
        return JSONResponse(status_code=ex.status_code, content=msg)

    @_app.exception_handler(Exception)
    async def exception_handler(_: Request, ex: Exception):
        detail = traceback.format_exception(ex)
        logger.exception(ex)
        code, msg, sc = APICode.EXCEPTION.value
        content = {
            "code": code,
            "message": msg,
            "details": [{"reason": detail[-1].strip(), "metadata": {"location": detail[-2]}}],
        }
        return JSONResponse(status_code=sc, content=content)

    @_app.exception_handler(RequestValidationError)
    async def request_validation_handler(_: Request, ex: RequestValidationError):
        code, msg, sc = APICode.VALIDATION.value
        content = {
            "code": code,
            "message": msg,
            "details": (
                [
                    {
                        "reason": item["msg"],
                        "metadata": {
                            "type": item["type"],
                            "location": "→".join([str(x) for x in item["loc"]]),
                        },
                    }
                    for item in ex.args[0]
                ]
                if CONFIG.debug
                else []
            ),
        }
        return JSONResponse(status_code=sc, content=content)


def generate_id(api):
    """
    生成自定义格式的operationId

    Args:
        api (APIRoute):

    Returns:
        str: id
    """
    location = api.endpoint.__module__.split(".")[1:]
    location = ".".join(location)  # 去掉最顶层的api.只保留agent.v1.files这种
    return f"{location}.{api.endpoint.__name__}"


def create_app():
    """
    创建并配置FastAPI的APP。

    Returns:
        FastAPI: 添加上路由信息的APP。
    """
    _app = FastAPI(
        title="API",
        description="",
        version="main",
        generate_unique_id_function=generate_id,
        openapi_url="/openapi.json" if CONFIG.debug else None,
    )

    for router in ROUTERS:
        _app.include_router(router)

    register_handler(_app)

    return _app


app = create_app()

if __name__ == "__main__":  # Debug时使用该方法
    for x in APICode:
        c, m, s = x.value
        print(f"错误消息：{m}，错误码：{c}，状态码：{s}")
    if CONFIG.debug:
        logger.info("Debug mode")
    uvicorn.run(app, host="127.0.0.1", port=8080)

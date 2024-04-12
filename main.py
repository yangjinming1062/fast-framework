"""
- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
File Name   : main.py
Author      : jinming.yang
Description : 程序的入口位置，通过该文件启动app程序
- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
"""

import traceback

import uvicorn
from fastapi import FastAPI
from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from api import ROUTERS
from component import *
from definition import *


def register_handler(_app):
    @_app.exception_handler(APIException)
    async def error_handler(_: Request, ex: APIException):
        msg = {"code": ex.code, "message": ex.msg, "details": []}
        return JSONResponse(status_code=ex.status_code, content=msg)

    @_app.exception_handler(Exception)
    async def error_handler(_: Request, ex: Exception):
        detail = traceback.format_exception(ex)
        logger.exception(ex)
        msg = {
            "code": "9999",
            "message": str(ex),
            "details": [{"reason": detail[-1].strip(), "metadata": {"location": detail[-2]}}],
        }
        return JSONResponse(status_code=500, content=msg)

    @_app.exception_handler(RequestValidationError)
    async def error_handler(_: Request, ex: RequestValidationError):
        msg = {
            "code": "0422",
            "message": "入参不合法",
            "details": [
                {
                    "reason": item["msg"],
                    "metadata": {
                        "type": item["type"],
                        "location": "→".join([str(x) for x in item["loc"]]),
                    },
                }
                for item in ex.args[0]
            ],
        }
        return JSONResponse(status_code=422, content=msg)


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
        generate_unique_id_function=generate_key,
    )

    for router in ROUTERS:
        _app.include_router(router)

    register_handler(_app)

    return _app


app = create_app()

if __name__ == "__main__":  # Debug时使用该方法
    uvicorn.run(app, host="0.0.0.0", port=8080)

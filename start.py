"""
- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
File Name   : app.py
Author      : jinming.yang
Description : 程序的入口位置，通过该文件启动app程序
- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
"""
import uvicorn
from fastapi import FastAPI

from apis import *


def create_app():
    _app = FastAPI(
        title="FastAPICli",
        description='',
        version="0.0.1",
    )
    for router in Routers:
        _app.include_router(router)
    return _app


app = create_app()
if __name__ == '__main__':  # Debug时使用该方法
    uvicorn.run(app, host="0.0.0.0", port=8000)

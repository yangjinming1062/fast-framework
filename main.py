"""
- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
File Name   : main.py
Author      : jinming.yang
Description : 程序的入口位置，通过该文件启动app程序
- - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
"""
import uvicorn
from fastapi import FastAPI

from apis import ROUTERS
from utils import generate_key


def create_app():
    """
    Creates and configures the FastAPI application.

    Returns:
        FastAPI: The configured FastAPI application.
    """
    # Create the FastAPI application
    _app = FastAPI(title='FastAPICli', description='', version='main', generate_unique_id_function=generate_key)

    # Include the routers in the application
    for router in ROUTERS:
        _app.include_router(router)

    return _app


app = create_app()
if __name__ == '__main__':  # Debug时使用该方法
    uvicorn.run(app, host="0.0.0.0", port=8080)

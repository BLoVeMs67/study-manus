from fastapi import APIRouter

from . import status_routes, app_config_routes


def create_api_route() -> APIRouter:
    """创建API路由，涵盖整个项目的所有路由管理"""
    # 1.创建APIRouter实例
    api_router = APIRouter()

    # 2.将各个模块添加到api_router中
    api_router.include_router(status_routes.router)
    api_router.include_router(app_config_routes.router)
    # 3.返回api路由实例
    return api_router


router = create_api_route()

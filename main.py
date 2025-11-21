#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
医院层级扫查微服务
提供省市区医院数据的刷新、查询和管理接口
"""

import os
import logging
from datetime import datetime
from typing import Optional, Dict, Any, List
from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.openapi.utils import get_openapi

# 确保必要的目录存在
os.makedirs("data", exist_ok=True)
os.makedirs("logs", exist_ok=True)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/ai_debug.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 导入自定义模块
from db import db
from schemas import (
    ResponseModel, PaginatedResponse, Province, City, District, Hospital, Task
)
from tasks import TaskManager, TaskStatus

# 使用数据库实例
database = db

# 创建FastAPI应用
app = FastAPI(
    title="医院层级扫查微服务",
    description="提供省市区医院数据的刷新、查询和管理功能",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局任务管理器
task_manager = TaskManager()


def custom_openapi():
    """自定义OpenAPI文档"""
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="医院层级扫查微服务",
        version="1.0.0",
        description="提供省市区医院数据的刷新、查询和管理功能",
        routes=app.routes,
    )
    
    # 添加全局响应模型
    openapi_schema["components"]["schemas"]["ResponseModel"] = {
        "type": "object",
        "properties": {
            "code": {"type": "integer", "description": "响应码"},
            "message": {"type": "string", "description": "响应消息"},
            "data": {"type": "object", "description": "响应数据"}
        }
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


@app.middleware("http")
async def add_process_time_header(request, call_next):
    """添加响应时间头"""
    start_time = datetime.now()
    response = await call_next(request)
    process_time = datetime.now() - start_time
    response.headers["X-Process-Time"] = str(process_time.total_seconds())
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """全局异常处理"""
    logger.error(f"全局异常: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "code": 500,
            "message": f"服务器内部错误: {str(exc)}",
            "data": None
        }
    )


def create_response(code: int, message: str, data: Any = None) -> Dict[str, Any]:
    """创建标准响应"""
    return {
        "code": code,
        "message": message,
        "data": data
    }


@app.get("/", response_model=ResponseModel)
async def root():
    """根路径"""
    return create_response(200, "医院层级扫查微服务运行中", {
        "service": "医院层级扫查微服务",
        "version": "1.0.0",
        "docs": "/docs",
        "timestamp": datetime.now().isoformat()
    })


@app.get("/health", response_model=ResponseModel)
async def health_check():
    """健康检查"""
    try:
        # 检查数据库连接
        stats = database.get_statistics()
        
        return create_response(200, "服务健康", {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "database": "connected",
            "stats": {
                "provinces": stats.get('province_count', 0),
                "cities": stats.get('city_count', 0),
                "districts": stats.get('district_count', 0),
                "hospitals": stats.get('hospital_count', 0)
            }
        })
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        return create_response(503, f"服务不可用: {str(e)}", {
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat()
        })


# ==================== 刷新接口 ====================

@app.post("/refresh/all", response_model=ResponseModel)
async def refresh_all_data(background_tasks: BackgroundTasks):
    """全量刷新所有数据"""
    try:
        task_id = await task_manager.create_refresh_task("full")
        await task_manager.start_task(task_id)
        
        logger.info(f"全量刷新任务已启动: {task_id}")
        return create_response(200, "全量刷新任务已启动", {"task_id": task_id})
        
    except Exception as e:
        logger.error(f"启动全量刷新失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/refresh/province/{province_name}", response_model=ResponseModel)
async def refresh_province_data(province_name: str, background_tasks: BackgroundTasks):
    """刷新指定省份数据"""
    try:
        task_id = await task_manager.create_refresh_task("province", province_name)
        await task_manager.start_task(task_id)
        
        logger.info(f"省份刷新任务已启动: {province_name}, 任务ID: {task_id}")
        return create_response(200, f"省份 {province_name} 刷新任务已启动", {"task_id": task_id})
        
    except Exception as e:
        logger.error(f"启动省份刷新失败: {province_name}, {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 查询接口 ====================

@app.get("/provinces", response_model=ResponseModel)
async def get_provinces(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量")
):
    """获取省份列表"""
    try:
        data = database.get_all_provinces(page, page_size)
        return create_response(200, "获取省份列表成功", data)
        
    except Exception as e:
        logger.error(f"获取省份列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/cities", response_model=ResponseModel)
async def get_cities(
    province: str = Query(..., description="省份名称或编码"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量")
):
    """获取城市列表"""
    try:
        data = database.get_cities_by_province(province, page, page_size)
        return create_response(200, "获取城市列表成功", data)
        
    except Exception as e:
        logger.error(f"获取城市列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/districts", response_model=ResponseModel)
async def get_districts(
    city: str = Query(..., description="城市名称或编码"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量")
):
    """获取区县列表"""
    try:
        data = database.get_districts_by_city(city, page, page_size)
        return create_response(200, "获取区县列表成功", data)
        
    except Exception as e:
        logger.error(f"获取区县列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/hospitals", response_model=ResponseModel)
async def get_hospitals_by_district(
    district: str = Query(..., description="区县名称或编码"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量")
):
    """根据区县获取医院列表"""
    try:
        data = database.get_hospitals_by_district(district, page, page_size)
        return create_response(200, "获取医院列表成功", data)
        
    except Exception as e:
        logger.error(f"获取医院列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/hospitals/search", response_model=ResponseModel)
async def search_hospitals(
    q: str = Query(..., description="搜索关键词"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量")
):
    """搜索医院"""
    try:
        data = database.search_hospitals(q, page, page_size)
        return create_response(200, f"搜索医院 '{q}' 成功", data)
        
    except Exception as e:
        logger.error(f"搜索医院失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 任务状态接口 ====================

@app.get("/tasks/{task_id}", response_model=ResponseModel)
async def get_task_status(task_id: str):
    """获取任务状态"""
    try:
        task = task_manager.get_task_status(task_id)
        
        if not task:
            raise HTTPException(status_code=404, detail=f"任务不存在: {task_id}")
        
        return create_response(200, "获取任务状态成功", task)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取任务状态失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/tasks", response_model=ResponseModel)
async def list_tasks(
    status: Optional[TaskStatus] = Query(None, description="任务状态过滤"),
    limit: int = Query(50, ge=1, le=200, description="返回数量限制")
):
    """列出任务"""
    try:
        tasks = task_manager.list_tasks(status)
        
        # 限制返回数量
        tasks = tasks[:limit]
        
        return create_response(200, "获取任务列表成功", {
            "tasks": tasks,
            "total": len(tasks)
        })
        
    except Exception as e:
        logger.error(f"获取任务列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/tasks/active", response_model=ResponseModel)
async def get_active_tasks():
    """获取活跃任务"""
    try:
        active_tasks = task_manager.get_active_tasks()
        return create_response(200, "获取活跃任务成功", {
            "active_tasks": active_tasks,
            "count": len(active_tasks)
        })
        
    except Exception as e:
        logger.error(f"获取活跃任务失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/tasks/{task_id}", response_model=ResponseModel)
async def cancel_task(task_id: str):
    """取消任务"""
    try:
        success = await task_manager.cancel_task(task_id)
        
        if success:
            return create_response(200, "任务已取消", {"task_id": task_id})
        else:
            raise HTTPException(status_code=404, detail=f"任务不存在或无法取消: {task_id}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"取消任务失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/tasks/cleanup", response_model=ResponseModel)
async def cleanup_old_tasks(hours: int = Query(24, ge=1, le=168, description="保留最近多少小时的任务")):
    """清理旧任务"""
    try:
        cleaned_count = await task_manager.cleanup_old_tasks(hours)
        return create_response(200, "清理旧任务成功", {
            "cleaned_count": cleaned_count,
            "hours": hours
        })
        
    except Exception as e:
        logger.error(f"清理旧任务失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 统计接口 ====================

@app.get("/statistics", response_model=ResponseModel)
async def get_statistics():
    """获取数据统计信息"""
    try:
        stats = database.get_statistics()
        
        return create_response(200, "获取统计信息成功", {
            "provinces": stats.get('province_count', 0),
            "cities": stats.get('city_count', 0),
            "districts": stats.get('district_count', 0),
            "hospitals": stats.get('hospital_count', 0),
            "total_tasks": stats.get('task_count', 0),
            "active_tasks": 0,  # 需要从任务管理器获取
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"获取统计信息失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
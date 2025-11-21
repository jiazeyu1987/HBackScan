#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
医院层级扫查微服务 - FastAPI入口文件
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import logging
import uuid
from datetime import datetime
from contextlib import asynccontextmanager

from db import init_db, get_db
from schemas import (
    ScanTaskRequest, 
    ScanTaskResponse, 
    TaskStatus,
    ScanResult,
    HospitalInfo,
    RefreshTaskRequest,
    RefreshTaskResponse,
    Province,
    City,
    District,
    Hospital,
    PaginatedResponse,
    SearchRequest,
    DataLevel
)
from tasks import TaskManager
from llm_client import LLMClient

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/scanner.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 任务管理器
task_manager = TaskManager()
llm_client = LLMClient()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化
    logger.info("启动医院层级扫查微服务...")
    await init_db()
    yield
    # 关闭时清理
    logger.info("关闭医院层级扫查微服务...")

# 创建FastAPI应用
app = FastAPI(
    title="医院层级扫查微服务",
    description="基于大语言模型的医院层级结构自动扫查服务",
    version="1.0.0",
    lifespan=lifespan
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "医院层级扫查微服务",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy"}

@app.post("/scan", response_model=ScanTaskResponse)
async def create_scan_task(
    request: ScanTaskRequest,
    background_tasks: BackgroundTasks
):
    """创建扫查任务"""
    try:
        logger.info(f"接收到扫查任务: {request.hospital_name}")
        
        # 创建任务
        task_id = await task_manager.create_task(request)
        
        # 启动后台任务
        background_tasks.add_task(
            execute_scan_task,
            task_id,
            request
        )
        
        return ScanTaskResponse(
            task_id=task_id,
            status=TaskStatus.PENDING,
            message="扫查任务已创建，正在处理中..."
        )
        
    except Exception as e:
        logger.error(f"创建扫查任务失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/task/{task_id}", response_model=ScanResult)
async def get_task_status(task_id: str):
    """获取任务状态和结果"""
    try:
        result = await task_manager.get_task_result(task_id)
        if not result:
            raise HTTPException(status_code=404, detail="任务不存在")
        return result
    except HTTPException:
        # 重新抛出HTTPException
        raise
    except Exception as e:
        logger.error(f"获取任务状态失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/tasks")
async def list_tasks():
    """获取所有任务列表"""
    try:
        return await task_manager.list_tasks()
    except Exception as e:
        logger.error(f"获取任务列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# 新增的数据刷新和查询接口

@app.post("/refresh/all", response_model=RefreshTaskResponse)
async def refresh_all_data(background_tasks: BackgroundTasks):
    """触发完整数据刷新任务"""
    try:
        logger.info("接收到完整数据刷新请求")
        
        # 创建任务记录
        task_id = str(uuid.uuid4())
        db = await get_db()
        await db.create_task(
            task_id=task_id,
            hospital_name="完整数据刷新任务",
            query="刷新所有省份、城市、区县、医院数据",
            status=TaskStatus.PENDING.value
        )
        
        # 启动后台数据刷新任务
        background_tasks.add_task(execute_full_refresh_task, task_id)
        
        return RefreshTaskResponse(
            task_id=task_id,
            message="完整数据刷新任务已创建，正在后台处理中...",
            created_at=datetime.now()
        )
        
    except Exception as e:
        logger.error(f"创建完整数据刷新任务失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/refresh/province/{province_name}", response_model=RefreshTaskResponse)
async def refresh_province_data(province_name: str, background_tasks: BackgroundTasks):
    """刷新特定省份的数据"""
    try:
        logger.info(f"接收到省份数据刷新请求: {province_name}")
        
        # 创建任务记录
        task_id = str(uuid.uuid4())
        db = await get_db()
        await db.create_task(
            task_id=task_id,
            hospital_name=f"省份数据刷新: {province_name}",
            query=f"刷新省份 {province_name} 的城市、区县、医院数据",
            status=TaskStatus.PENDING.value
        )
        
        # 启动后台省份数据刷新任务
        background_tasks.add_task(execute_province_refresh_task, task_id, province_name)
        
        return RefreshTaskResponse(
            task_id=task_id,
            message=f"省份 {province_name} 数据刷新任务已创建，正在后台处理中...",
            created_at=datetime.now()
        )
        
    except Exception as e:
        logger.error(f"创建省份数据刷新任务失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/provinces", response_model=PaginatedResponse)
async def get_provinces(page: int = 1, page_size: int = 20):
    """获取省份列表（分页）"""
    try:
        db = await get_db()
        items, total = await db.get_provinces(page, page_size)
        
        pages = (total + page_size - 1) // page_size if page_size > 0 else 1
        
        return PaginatedResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
            has_next=page < pages,
            has_prev=page > 1
        )
        
    except Exception as e:
        logger.error(f"获取省份列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/cities", response_model=PaginatedResponse)
async def get_cities(province_id: int = None, page: int = 1, page_size: int = 20):
    """获取城市列表（分页）"""
    try:
        db = await get_db()
        items, total = await db.get_cities(province_id, page, page_size)
        
        pages = (total + page_size - 1) // page_size if page_size > 0 else 1
        
        return PaginatedResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
            has_next=page < pages,
            has_prev=page > 1
        )
        
    except Exception as e:
        logger.error(f"获取城市列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/districts", response_model=PaginatedResponse)
async def get_districts(city_id: int = None, page: int = 1, page_size: int = 20):
    """获取区县列表（分页）"""
    try:
        db = await get_db()
        items, total = await db.get_districts(city_id, page, page_size)
        
        pages = (total + page_size - 1) // page_size if page_size > 0 else 1
        
        return PaginatedResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
            has_next=page < pages,
            has_prev=page > 1
        )
        
    except Exception as e:
        logger.error(f"获取区县列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/hospitals", response_model=PaginatedResponse)
async def get_hospitals(district_id: int = None, page: int = 1, page_size: int = 20):
    """获取医院列表（分页）"""
    try:
        db = await get_db()
        items, total = await db.get_hospitals(district_id, page, page_size)
        
        pages = (total + page_size - 1) // page_size if page_size > 0 else 1
        
        return PaginatedResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            pages=pages,
            has_next=page < pages,
            has_prev=page > 1
        )
        
    except Exception as e:
        logger.error(f"获取医院列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/hospitals/search")
async def search_hospitals(q: str, limit: int = 20):
    """搜索医院"""
    try:
        db = await get_db()
        items = await db.search_hospitals(q, limit)
        
        return {
            "query": q,
            "limit": limit,
            "results": items,
            "count": len(items)
        }
        
    except Exception as e:
        logger.error(f"搜索医院失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def execute_scan_task(task_id: str, request: ScanTaskRequest):
    """执行扫查任务的实际逻辑"""
    try:
        await task_manager.update_task_status(task_id, TaskStatus.RUNNING)
        
        # 调用LLM进行医院层级结构分析
        hospital_info = await llm_client.analyze_hospital_hierarchy(
            hospital_name=request.hospital_name,
            query=request.query
        )
        
        # 保存结果
        result = ScanResult(
            task_id=task_id,
            status=TaskStatus.COMPLETED,
            hospital_info=hospital_info,
            created_at=request.created_at
        )
        
        await task_manager.save_task_result(task_id, result)
        
    except Exception as e:
        logger.error(f"执行扫查任务失败: {e}")
        await task_manager.update_task_status(task_id, TaskStatus.FAILED)

async def execute_full_refresh_task(task_id: str):
    """执行完整数据刷新任务"""
    try:
        await task_manager.update_task_status(task_id, TaskStatus.RUNNING)
        logger.info(f"开始执行完整数据刷新任务: {task_id}")
        
        db = await get_db()
        
        # 模拟数据刷新流程
        # 1. 刷新省份数据
        mock_provinces = [
            {"name": "北京市", "code": "110000"},
            {"name": "上海市", "code": "310000"},
            {"name": "广东省", "code": "440000"},
            {"name": "江苏省", "code": "320000"},
            {"name": "浙江省", "code": "330000"}
        ]
        
        for province_data in mock_provinces:
            province_id = await db.create_province(
                name=province_data["name"],
                code=province_data["code"]
            )
            
            # 2. 为每个省份创建城市
            mock_cities = [
                {"name": f"{province_data['name']}市", "code": f"{province_data['code']}01"},
                {"name": f"{province_data['name']}区", "code": f"{province_data['code']}02"}
            ]
            
            for city_data in mock_cities:
                city_id = await db.create_city(
                    name=city_data["name"],
                    province_id=province_id,
                    code=city_data["code"]
                )
                
                # 3. 为每个城市创建区县
                mock_districts = [
                    {"name": f"{city_data['name']}区1", "code": f"{city_data['code']}01"},
                    {"name": f"{city_data['name']}区2", "code": f"{city_data['code']}02"}
                ]
                
                for district_data in mock_districts:
                    district_id = await db.create_district(
                        name=district_data["name"],
                        city_id=city_id,
                        code=district_data["code"]
                    )
                    
                    # 4. 为每个区县创建医院
                    mock_hospitals = [
                        {"name": f"{district_data['name']}人民医院", "level": "三级甲等"},
                        {"name": f"{district_data['name']}中心医院", "level": "二级医院"},
                        {"name": f"{district_data['name']}社区医院", "level": "一级医院"}
                    ]
                    
                    for hospital_data in mock_hospitals:
                        await db.create_hospital(
                            name=hospital_data["name"],
                            district_id=district_id,
                            level=hospital_data["level"],
                            address=f"{district_data['name']}健康路123号",
                            phone="010-12345678",
                            beds_count=500 if "人民" in hospital_data["name"] else 200,
                            staff_count=800 if "人民" in hospital_data["name"] else 300,
                            departments=["内科", "外科", "妇产科", "儿科"],
                            specializations=["心血管科", "神经内科"]
                        )
        
        # 更新任务状态为完成
        await task_manager.update_task_status(task_id, TaskStatus.COMPLETED)
        logger.info(f"完整数据刷新任务完成: {task_id}")
        
    except Exception as e:
        logger.error(f"执行完整数据刷新任务失败: {e}")
        await task_manager.update_task_status(task_id, TaskStatus.FAILED, str(e))

async def execute_province_refresh_task(task_id: str, province_name: str):
    """执行特定省份数据刷新任务"""
    try:
        await task_manager.update_task_status(task_id, TaskStatus.RUNNING)
        logger.info(f"开始执行省份数据刷新任务: {province_name} - {task_id}")
        
        db = await get_db()
        
        # 创建省份
        province_id = await db.create_province(name=province_name)
        
        if province_id:
            # 为省份创建示例城市
            mock_cities = [
                {"name": f"{province_name}市", "code": f"110001"},
                {"name": f"{province_name}区", "code": "110002"}
            ]
            
            for city_data in mock_cities:
                city_id = await db.create_city(
                    name=city_data["name"],
                    province_id=province_id,
                    code=city_data["code"]
                )
                
                # 为城市创建区县和医院（简化示例）
                district_id = await db.create_district(
                    name=f"{city_data['name']}区1",
                    city_id=city_id
                )
                
                await db.create_hospital(
                    name=f"{city_data['name']}人民医院",
                    district_id=district_id,
                    level="二级医院",
                    address=f"{city_data['name']}区1健康路100号"
                )
        
        # 更新任务状态为完成
        await task_manager.update_task_status(task_id, TaskStatus.COMPLETED)
        logger.info(f"省份数据刷新任务完成: {province_name} - {task_id}")
        
    except Exception as e:
        logger.error(f"执行省份数据刷新任务失败: {e}")
        await task_manager.update_task_status(task_id, TaskStatus.FAILED, str(e))

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
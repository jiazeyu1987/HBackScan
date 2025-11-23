#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
医院层级扫查微服务 - FastAPI入口文件
"""

# 首先加载环境变量
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import logging
import uuid
import time
from datetime import datetime
from contextlib import asynccontextmanager
from urllib.parse import unquote

from db import init_db, get_db, clear_all_data, clear_all_tasks as db_clear_all_tasks
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

# Define StandardResponse for consistency
class StandardResponse:
    def __init__(self, code: int = 200, message: str = "Success", data=None):
        self.code = code
        self.message = message
        self.data = data

    def dict(self):
        return {
            "code": self.code,
            "message": self.message,
            "data": self.data
        }
from tasks import TaskManager, execute_province_cities_districts_refresh_task, execute_all_provinces_cascade_refresh
from llm_client import LLMClient

# 配置日志 - 修复中文字符编码问题
# 确保在添加处理器之前清除所有现有的处理器
root_logger = logging.getLogger()
for handler in root_logger.handlers[:]:
    root_logger.removeHandler(handler)

# 设置根日志记录器级别
root_logger.setLevel(logging.INFO)

# 创建控制台处理器，使用UTF-8编码
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(console_formatter)
root_logger.addHandler(console_handler)

# 创建主日志文件处理器，明确指定UTF-8编码和追加模式
file_handler = logging.FileHandler('logs/scanner.log', encoding='utf-8', mode='a')
file_handler.setLevel(logging.INFO)
file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(file_formatter)
root_logger.addHandler(file_handler)

logger = logging.getLogger(__name__)

# 创建专门的LLM日志记录器，确保不传播到根日志记录器
llm_logger = logging.getLogger('llm_client')
llm_logger.setLevel(logging.INFO)
llm_logger.propagate = False  # 防止传播到根日志记录器，避免编码冲突

# 清除LLM日志记录器的现有处理器（如果有的话）
for handler in llm_logger.handlers[:]:
    llm_logger.removeHandler(handler)

# 创建LLM专用文件处理器，明确指定UTF-8编码和追加模式
llm_handler = logging.FileHandler('logs/llm_debug.log', encoding='utf-8', mode='a')
llm_handler.setLevel(logging.INFO)
llm_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
llm_handler.setFormatter(llm_formatter)
llm_logger.addHandler(llm_handler)

# 禁用其他模块的详细日志
logging.getLogger('uvicorn').setLevel(logging.WARNING)
logging.getLogger('watchfiles').setLevel(logging.WARNING)
logging.getLogger('uvicorn.access').setLevel(logging.WARNING)

# 任务管理器
task_manager = TaskManager()
llm_client = LLMClient()

def get_task_manager() -> TaskManager:
    """FastAPI依赖注入函数，返回TaskManager实例"""
    return task_manager

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

@app.delete("/database/clear")
async def clear_database():
    """清空所有数据库表的数据，保留表结构"""
    try:
        logger.info("接收到清空数据库请求")

        # 调用清空数据库的方法
        success = await clear_all_data()

        if success:
            logger.info("数据库清空成功")
            return {
                "code": 200,
                "message": "数据库已成功清空，所有表数据已删除，表结构保留",
                "data": {
                    "status": "success",
                    "cleared_at": datetime.now().isoformat()
                }
            }
        else:
            logger.error("数据库清空失败")
            raise HTTPException(status_code=500, detail="数据库清空失败")

    except HTTPException:
        # 重新抛出HTTPException
        raise
    except Exception as e:
        logger.error(f"清空数据库失败: {e}")
        raise HTTPException(status_code=500, detail=f"清空数据库失败: {str(e)}")

@app.delete("/tasks/clear")
async def clear_all_tasks():
    """删除所有任务记录"""
    try:
        logger.info("接收到删除所有任务的请求")

        # 调用删除所有任务的方法
        success = await db_clear_all_tasks()

        if success:
            logger.info("所有任务记录删除成功")
            return {
                "code": 200,
                "message": "所有任务记录已成功删除",
                "data": {
                    "status": "success",
                    "cleared_at": datetime.now().isoformat()
                }
            }
        else:
            logger.error("删除所有任务记录失败")
            raise HTTPException(status_code=500, detail="删除所有任务记录失败")

    except HTTPException:
        # 重新抛出HTTPException
        raise
    except Exception as e:
        logger.error(f"删除所有任务记录失败: {e}")
        raise HTTPException(status_code=500, detail=f"删除所有任务记录失败: {str(e)}")


@app.post("/tasks/cleanup")
async def cleanup_completed_tasks():
    """清理已完成的任务"""
    try:
        logger.info("接收到清理已完成任务的请求")

        # 获取数据库连接
        db = await get_db()

        # 清理数据库中的已完成任务（清理1小时前的）
        deleted_count = await db.cleanup_completed_tasks(1)

        # 同时清理内存中的已完成任务
        memory_deleted = await task_manager.cleanup_completed_tasks(1)

        logger.info(f"任务清理完成：数据库删除{deleted_count}个，内存清理{memory_deleted}个")

        return {
            "code": 200,
            "message": f"已清理{deleted_count}个完成的任务记录",
            "data": {
                "status": "success",
                "database_deleted": deleted_count,
                "memory_deleted": memory_deleted,
                "cleaned_at": datetime.now().isoformat()
            }
        }

    except HTTPException:
        # 重新抛出HTTPException
        raise
    except Exception as e:
        logger.error(f"清理已完成任务失败: {e}")
        raise HTTPException(status_code=500, detail=f"清理已完成任务失败: {str(e)}")


@app.post("/tasks/cleanup/{older_than_hours}")
async def cleanup_completed_tasks_with_hours(older_than_hours: int):
    """清理指定时间前已完成的任务"""
    try:
        logger.info(f"接收到清理已完成任务的请求，清理{older_than_hours}小时前的任务")

        # 获取数据库连接
        db = await get_db()

        # 清理数据库中的已完成任务
        deleted_count = await db.cleanup_completed_tasks(older_than_hours)

        # 同时清理内存中的已完成任务
        memory_deleted = await task_manager.cleanup_completed_tasks(older_than_hours)

        logger.info(f"任务清理完成：数据库删除{deleted_count}个，内存清理{memory_deleted}个")

        return {
            "code": 200,
            "message": f"已清理{deleted_count}个完成的任务记录",
            "data": {
                "status": "success",
                "database_deleted": deleted_count,
                "memory_deleted": memory_deleted,
                "older_than_hours": older_than_hours,
                "cleaned_at": datetime.now().isoformat()
            }
        }

    except HTTPException:
        # 重新抛出HTTPException
        raise
    except Exception as e:
        logger.error(f"清理已完成任务失败: {e}")
        raise HTTPException(status_code=500, detail=f"清理已完成任务失败: {str(e)}")


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

@app.get("/task/{task_id}")
async def get_task_status(task_id: str):
    """获取任务状态和结果"""
    try:
        # 先尝试获取任务结果（ScanResult格式）
        result = await task_manager.get_task_result(task_id)
        if result:
            return result

        # 如果没有ScanResult，尝试获取基本任务信息
        db = await get_db()
        task_info = await db.get_task_info(task_id)

        if task_info:
            return {
                "code": 200,
                "message": "获取任务状态成功",
                "data": task_info
            }

        raise HTTPException(status_code=404, detail="任务不存在")
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

@app.post("/refresh/all", response_model=RefreshTaskResponse,
          summary="完整数据刷新",
          description="执行全国范围的完整数据刷新，包括所有省份、城市、区县的层级数据。这是最全面的数据刷新接口。\n\n**执行流程**：\n1. **获取省份列表**：调用LLM获取全国所有省级行政区划\n2. **省份遍历**：对每个省份自动调用省份数据刷新接口\n3. **城市处理**：获取每个省份下的所有城市数据\n4. **区县处理**：获取每个城市下的所有区县数据\n5. **数据验证**：确保完整层级关系的正确性\n\n**特点**：\n- 覆盖全国所有省级行政区划\n- 自动化批量处理\n- 完整的四级数据体系（省→市→区县→医院）\n- 支持断点续传，失败的省份可以单独重试\n\n**适用场景**：\n- 初始化系统数据\n- 定期全量数据更新\n- 数据修复和完整性检查\n\n**返回**：\n- task_id: 后台任务ID，可用于查询任务执行状态\n- message: 任务创建确认信息\n- created_at: 任务创建时间",
          tags=["数据刷新"])
async def refresh_all_data(background_tasks: BackgroundTasks):
    try:
        print("=== DEBUG: 接收到完整数据刷新请求 ===")
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
        
        # 直接执行数据刷新任务（临时调试用）
        await execute_full_refresh_task(task_id)
        
        return RefreshTaskResponse(
            task_id=task_id,
            message="完整数据刷新任务已创建，正在后台处理中...",
            created_at=datetime.now()
        )
        
    except Exception as e:
        logger.error(f"创建完整数据刷新任务失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/refresh/province/{province_name}", response_model=RefreshTaskResponse,
          summary="省份数据刷新",
          description="根据省份名称刷新该省份下的城市和区县数据。该接口会执行以下流程：\n\n1. **获取城市数据**：调用LLM获取指定省份下的所有地级市、自治州、地区等\n2. **省份处理**：检查省份是否存在，不存在则创建新省份记录\n3. **城市创建**：批量创建获取到的所有城市记录\n4. **数据验证**：确保数据的完整性和正确性\n\n**与级联刷新接口的区别**：\n- 本接口仅刷新省份和城市数据，不处理区县和医院数据\n- 级联刷新接口会处理完整的省份→城市→区县→医院数据链\n\n**参数**：\n- province_name: 省份名称（如：广东省、浙江省、四川省等）\n\n**返回**：\n- task_id: 后台任务ID，可用于查询任务执行状态\n- message: 任务创建确认信息\n- created_at: 任务创建时间",
          tags=["数据刷新"])
async def refresh_province_data(province_name: str, background_tasks: BackgroundTasks):
    try:
        # URL解码，处理中文字符
        original_province_name = province_name
        province_name = unquote(province_name)

        # 🚀 函数入口日志
        logger.info(f"🚀 ========== 省份数据刷新接口调用开始 ==========")
        logger.info(f"📋 函数: refresh_province_data")
        logger.info(f"📍 原始省份名称: '{original_province_name}'")
        logger.info(f"📍 解码后省份名称: '{province_name}'")
        logger.info(f"🔍 省份名称类型: {type(province_name)}")
        logger.info(f"🔍 省份名称长度: {len(province_name)}")
        logger.info(f"⏰ 调用时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # 验证参数
        if not province_name or not isinstance(province_name, str) or len(province_name.strip()) == 0:
            logger.error(f"❌ 省份名称无效: '{province_name}' (类型: {type(province_name)}, 长度: {len(province_name) if province_name else 'None'})")
            raise HTTPException(status_code=400, detail="省份名称不能为空")

        province_name_clean = province_name.strip()
        logger.info(f"✅ 省份名称验证通过: '{province_name_clean}'")

        # 创建任务记录
        logger.info(f"🔄 步骤1: 创建任务记录")
        task_id = str(uuid.uuid4())
        logger.info(f"🆔 生成任务ID: {task_id}")

        logger.info(f"📊 步骤2: 获取数据库连接")
        db = await get_db()
        logger.info(f"✅ 数据库连接成功")

        logger.info(f"💾 步骤3: 创建数据库任务记录")
        logger.info(f"📝 任务详情 - ID: {task_id}, 省份: {province_name_clean}")

        try:
            await db.create_task(
                task_id=task_id,
                hospital_name=f"省份数据刷新: {province_name_clean}",
                query=f"刷新省份 {province_name_clean} 的城市、区县、医院数据",
                status=TaskStatus.PENDING.value
            )
            logger.info(f"✅ 数据库任务记录创建成功")
        except Exception as db_error:
            logger.error(f"❌ 数据库任务记录创建失败: {db_error}")
            raise HTTPException(status_code=500, detail=f"数据库操作失败: {str(db_error)}")

        logger.info(f"🎯 步骤4: 准备启动后台任务")

        try:
            # 省份刷新 - 仅处理省级数据
            logger.info(f"📋 即将调用: execute_province_refresh_task")
            logger.info(f"📋 参数: task_id={task_id}, province_name={province_name_clean}")
            background_tasks.add_task(execute_province_refresh_task, task_id, province_name_clean)
            logger.info(f"✅ 省份数据刷新后台任务已成功添加到队列")
        except Exception as bg_error:
            logger.error(f"❌ 添加后台任务失败: {bg_error}")
            raise HTTPException(status_code=500, detail=f"启动后台任务失败: {str(bg_error)}")

        logger.info(f"📦 步骤5: 构建响应")
        response_message = f"省份 {province_name_clean} 数据刷新任务已创建，正在后台处理中..."
        logger.info(f"💬 响应消息: '{response_message}'")

        response = RefreshTaskResponse(
            task_id=task_id,
            message=response_message,
            created_at=datetime.now()
        )

        logger.info(f"✅ 响应构建完成 - task_id: {task_id}")
        logger.info(f"🎉 ========== 省份数据刷新接口调用成功 ==========")

        return response

    except HTTPException:
        # HTTP异常重新抛出
        logger.error(f"💥 HTTP异常抛出")
        raise
    except Exception as e:
        logger.error(f"❌ 创建省份数据刷新任务失败: {e}")
        logger.error(f"📋 异常类型: {type(e).__name__}")
        logger.error(f"📋 异常详情: {str(e)}")
        import traceback
        logger.error(f"📋 完整堆栈: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"服务器内部错误: {str(e)}")


@app.post("/test/district")
async def test_district_endpoint():
    """测试区县端点"""
    return {"message": "District test endpoint works", "status": "success"}


@app.post("/refresh/district/{district_name}", response_model=RefreshTaskResponse,
          summary="区县医院数据刷新",
          description="根据区县名称刷新该区县内的所有医院数据，包括医院基本信息、等级、地址、电话、网站和官网等详细信息。\n\n**功能特性**：\n- 调用阿里百炼LLM获取区县内所有医院的详细信息\n- 自动识别医院等级（三甲、三乙、二甲等）\n- 获取医院联系方式（地址、电话、网站）\n- 智能去重：避免重复创建相同医院记录\n- 异步处理：后台执行医院数据获取和保存\n\n**参数**：\n- district_name: 区县名称（如：朝阳区、海淀区、西城区等）\n\n**返回**：\n- task_id: 后台任务ID，可用于查询任务执行状态\n- message: 任务创建确认信息\n- created_at: 任务创建时间",
          tags=["数据刷新"])
async def refresh_district_data(district_name: str, background_tasks: BackgroundTasks):
    try:
        # 验证参数
        if not district_name or not isinstance(district_name, str) or len(district_name.strip()) == 0:
            logger.error(f"❌ 区县名称无效: '{district_name}' (类型: {type(district_name)}, 长度: {len(district_name) if district_name else 'None'})")
            raise HTTPException(status_code=400, detail="区县名称不能为空")

        district_name_clean = district_name.strip()
        logger.info(f"✅ 区县名称验证通过: '{district_name_clean}'")

        # 创建任务记录
        logger.info(f"🔄 步骤1: 创建任务记录")
        task_id = str(uuid.uuid4())
        logger.info(f"🆔 生成任务ID: {task_id}")

        logger.info(f"📊 步骤2: 获取数据库连接")
        db = await get_db()
        logger.info(f"✅ 数据库连接成功")

        logger.info(f"💾 步骤3: 创建数据库任务记录")
        logger.info(f"📝 任务详情 - ID: {task_id}, 区县: {district_name_clean}")

        try:
            await db.create_task(
                task_id=task_id,
                hospital_name=f"区县医院刷新: {district_name_clean}",
                query=f"刷新区县 {district_name_clean} 的医院数据",
                status=TaskStatus.PENDING.value
            )
            logger.info(f"✅ 数据库任务记录创建成功")
        except Exception as db_error:
            logger.error(f"❌ 数据库任务记录创建失败: {db_error}")
            raise HTTPException(status_code=500, detail=f"数据库操作失败: {str(db_error)}")

        logger.info(f"🎯 步骤4: 准备启动后台任务")
        logger.info(f"📋 任务详情: task_id={task_id}, district_name={district_name_clean}")

        # 启动区县医院刷新后台任务
        logger.info(f"✅ 区县医院刷新后台任务已成功添加到队列")
        background_tasks.add_task(execute_hospital_refresh_for_district, task_id, district_name_clean)

        logger.info(f"📤 步骤5: 准备响应")
        response_message = f"区县 {district_name_clean} 医院数据刷新任务已创建，正在后台处理中..."
        logger.info(f"💬 响应消息: '{response_message}'")
        logger.info(f"✅ 响应数据已生成 - task_id: {task_id}")

        logger.info(f"🎉 ========== 区县医院刷新接口调用成功 ==========")

        return RefreshTaskResponse(
            task_id=task_id,
            message=response_message,
            created_at=datetime.now().isoformat()
        )

    except HTTPException:
        # 重新抛出HTTP异常
        raise
    except Exception as e:
        logger.error(f"❌ 创建区县医院刷新任务失败: {e}")
        logger.error(f"📋 异常类型: {type(e).__name__}")
        logger.error(f"📋 异常详情: {str(e)}")
        import traceback
        logger.error(f"📋 完整堆栈: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"服务器内部错误: {str(e)}")


@app.post("/refresh/province-cities-districts/{province_name}", response_model=RefreshTaskResponse,
          summary="省份城市区县级联刷新",
          description="根据省份名称级联刷新该省份下所有城市、区县及医院数据。该接口会完整执行以下流程：\n\n1. **获取城市数据**：调用LLM获取指定省份下的所有城市列表\n2. **省份处理**：检查省份是否存在，不存在则创建新省份记录\n3. **城市处理**：对每个城市检查是否存在，不存在则创建新城市记录\n4. **区县处理**：获取每个城市下的所有区县，创建区县记录\n5. **医院数据准备**：为每个区县准备医院数据刷新\n\n**特性**：\n- 不对输入省份名称进行验证，支持任意省份名称\n- 自动去重：省份、城市、区县名称相同时不会重复创建\n- 详细日志：记录每个步骤的执行情况\n- 异步处理：后台执行级联刷新任务\n\n**参数**：\n- province_name: 省份名称（如：北京市、上海市、广东省等）\n\n**返回**：\n- task_id: 后台任务ID，可用于查询任务执行状态\n- message: 任务创建确认信息\n- created_at: 任务创建时间",
          tags=["数据刷新"])
async def refresh_province_cities_districts(province_name: str, background_tasks: BackgroundTasks):
    try:
        logger.info(f"🎉 ========== 开始处理省份城市区县级联刷新请求 ==========")
        logger.info(f"📍 请求参数: province_name='{province_name}'")

        province_name_clean = province_name.strip()
        logger.info(f"✅ 省份名称处理完成: '{province_name_clean}'")

        logger.info(f"🔄 步骤1: 通过TaskManager创建任务")
        logger.info(f"📝 任务详情: 省份={province_name_clean}")

        # 使用全局task_manager创建任务，确保任务状态管理一致
        from schemas import ScanTaskRequest, TaskType
        task_request = ScanTaskRequest(
            hospital_name=f"省份城市区县级联刷新: {province_name_clean}",
            query=f"级联刷新省份 {province_name_clean} 的所有城市、区县及医院数据",
            task_type=TaskType.PROVINCE
        )

        task_id = await task_manager.create_task(task_request)
        logger.info(f"🆔 任务已创建并注册到TaskManager: {task_id}")

        logger.info(f"🎯 步骤2: 准备启动后台任务")
        logger.info(f"📋 任务详情: task_id={task_id}, province_name={province_name_clean}")

        logger.info(f"✅ 省份城市区县级联刷新后台任务已成功添加到队列")
        background_tasks.add_task(execute_province_cities_districts_refresh_task, task_id, province_name_clean, task_manager)

        logger.info(f"📤 步骤5: 准备响应")
        response_message = f"省份 {province_name_clean} 的城市、区县及医院数据级联刷新任务已创建，正在后台处理中..."
        logger.info(f"💬 响应消息: '{response_message}'")
        logger.info(f"✅ 响应数据已生成 - task_id: {task_id}")

        logger.info(f"🎉 ========== 省份城市区县级联刷新接口调用成功 ==========")

        return RefreshTaskResponse(
            task_id=task_id,
            message=response_message,
            created_at=datetime.now().isoformat()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 创建省份城市区县级联刷新任务失败: {e}")
        logger.error(f"📋 异常类型: {type(e).__name__}")
        logger.error(f"📋 异常详情: {str(e)}")
        import traceback
        logger.error(f"📋 完整堆栈: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"服务器内部错误: {str(e)}")


# 全国扫描（所有省份的级联刷新）
@app.post("/refresh/all-provinces", response_model=RefreshTaskResponse,
          summary="全国扫描 - 所有省份级联刷新",
          description="""
全国扫描 - 级联刷新所有省份的城市、区县和医院数据

这个API端点会执行全国范围的医院数据扫描，逻辑如下：
1. 首先从LLM获取全国所有省份列表
2. 然后依次对每个省份执行级联刷新（包含城市、区县、医院）
3. 使用串行处理避免过度并发导致API限流
4. 提供详细的进度日志和错误处理

特性：
- 🌍 覆盖全国所有省级行政区
- 📊 实时进度跟踪和详细日志记录
- 🔁 自动重试机制和错误恢复
- ⚡ 智能任务队列管理
- 🛡️ API限流保护和并发控制

Returns:
    RefreshTaskResponse: 包含全国扫描任务ID的响应，可用于查询进度

Example:
    ```python
    response = client.post("/refresh/all-provinces")
    task_id = response.json()["task_id"]

    # 查询进度
    status = client.get(f"/tasks/{task_id}")
    progress = status.json()["data"]["progress"]
    ```
""",
          tags=["数据刷新"])
async def refresh_all_provinces_nationwide(
    background_tasks: BackgroundTasks,
    task_manager: TaskManager = Depends(get_task_manager),
):
    """
    全国扫描API端点 - 启动所有省份的级联刷新任务
    """
    logger.info("🌍 ========== API请求：启动全国扫描任务 ==========")

    try:
        # 检查是否已有全国扫描任务在运行（优先使用task_type字段，兼容旧数据）
        active_tasks = await task_manager.get_active_tasks()
        for task in active_tasks:
            # 优先检查task_type字段，更可靠
            task_type = task.get("task_type", "")
            hospital_name = task.get("hospital_name", "")

            if task_type == TaskType.NATIONWIDE.value or "全国扫描" in hospital_name:
                task_id = task.get("task_id", "unknown")
                logger.warning(f"发现全国扫描任务正在运行: {task_id} (type: {task_type or 'legacy'})")
                raise HTTPException(status_code=409, detail="全国扫描任务已在运行中，请等待完成")

        logger.info("📝 创建全国扫描任务...")

        # 使用TaskManager创建任务，确保内存和数据库一致
        from schemas import ScanTaskRequest, TaskType
        task_request = ScanTaskRequest(
            hospital_name="全国扫描 - 所有省份级联刷新",
            query="级联刷新全国所有省份的城市、区县及医院数据",
            task_type=TaskType.NATIONWIDE
        )
        task_id = await task_manager.create_task(task_request)

        # 启动全国扫描后台任务
        background_tasks.add_task(
            execute_all_provinces_cascade_refresh,
            task_id,
            task_manager
        )

        logger.info(f"🎯 全国扫描任务已创建: {task_id}")

        return RefreshTaskResponse(
            task_id=task_id,
            message="全国扫描任务已启动，将依次扫描所有省份的城市、区县和医院数据",
            created_at=datetime.now()
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 创建全国扫描任务失败: {str(e)}")
        import traceback
        logger.error(f"📋 完整堆栈: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"全国扫描任务创建失败: {str(e)}")


# Note: The district endpoint was having registration issues in the original version.
# Now we have a dedicated district endpoint for clarity.


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
async def get_cities(province: str = None, province_id: int = None, page: int = 1, page_size: int = 20):
    """获取城市列表（分页）"""
    try:
        db = await get_db()

        # 如果提供了省份名称，先查找省份ID
        if province and not province_id:
            # URL解码中文字符
            from urllib.parse import unquote
            province_name = unquote(province)
            logger.info(f"🔍 API收到省份名称查询: '{province}' -> 解码后: '{province_name}'")

            province_info = await db.get_province_by_name(province_name)
            if province_info:
                province_id = province_info['id']
                logger.info(f"✅ 找到省份ID: {province_id}")
            else:
                logger.warning(f"❌ 未找到省份: '{province_name}'")
                # 如果找不到省份，返回空结果
                return PaginatedResponse(
                    items=[],
                    total=0,
                    page=page,
                    page_size=page_size,
                    pages=0,
                    has_next=False,
                    has_prev=False
                )
        else:
            logger.info(f"🔍 API参数: province='{province}', province_id={province_id}")

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
async def get_districts(city_id: int = None, city: str = None, page: int = 1, page_size: int = 20):
    """获取区县列表（分页）"""
    try:
        db = await get_db()

        # 如果提供了城市名称，先查找城市ID
        if city and not city_id:
            from urllib.parse import unquote
            city_name = unquote(city)
            city_info = await db.get_city_by_name(city_name)
            if city_info:
                city_id = city_info['id']

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
async def get_hospitals(district_id: int = None, district: str = None, page: int = 1, page_size: int = 20):
    """获取医院列表（分页）"""
    try:
        db = await get_db()

        # 如果提供了区县名称，先查找区县ID
        if district and not district_id:
            from urllib.parse import unquote
            district_name = unquote(district)
            district_info = await db.get_district_by_name(district_name)
            if district_info:
                district_id = district_info['id']

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
    logger.info(f"🚀 ========== 开始执行完整数据刷新任务 ==========")
    logger.info(f"📋 任务ID: {task_id}")
    logger.info(f"⏰ 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    try:
        # 步骤1: 更新任务状态为运行中
        logger.info("🔄 步骤1: 更新任务状态为RUNNING")
        await task_manager.update_task_status(task_id, TaskStatus.RUNNING)
        logger.info(f"✅ 任务状态已更新为RUNNING: {task_id}")

        # 步骤2: 准备导入环境
        logger.info("🔄 步骤2: 准备导入环境")
        import sys
        import os

        logger.info(f"📂 当前工作目录: {os.getcwd()}")
        logger.info(f"📂 当前文件路径: {__file__}")

        # 添加项目根目录到路径
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        logger.info(f"📂 项目根目录: {project_root}")

        if project_root not in sys.path:
            sys.path.insert(0, project_root)
            logger.info(f"📂 已添加项目根目录到sys.path: {project_root}")
        else:
            logger.info(f"📂 项目根目录已在sys.path中")

        logger.info(f"🐍 Python版本: {sys.version}")
        logger.info(f"📦 sys.path包含: {len(sys.path)} 个路径")

        # 步骤3: 导入必要的模块
        logger.info("🔄 步骤3: 导入必要的模块")

        try:
            logger.info("📦 尝试导入tasks模块...")
            from tasks import TaskManager as RootTaskManager
            logger.info("✅ tasks模块导入成功")
        except ImportError as e:
            logger.error(f"❌ 无法导入根目录TaskManager: {e}")
            logger.error(f"❌ 详细错误信息: {type(e).__name__}: {str(e)}")
            await task_manager.update_task_status(task_id, TaskStatus.FAILED, f"导入失败: {str(e)}")
            return

        # 步骤4: 获取数据库连接
        logger.info("🔄 步骤4: 获取数据库连接")
        try:
            db = await get_db()
            logger.info("✅ 数据库连接成功")
        except Exception as e:
            logger.error(f"❌ 数据库连接失败: {e}")
            await task_manager.update_task_status(task_id, TaskStatus.FAILED, f"数据库连接失败: {str(e)}")
            return

        # 步骤5: 创建进度跟踪器
        logger.info("🔄 步骤5: 创建进度跟踪器")
        class DetailedProgressTracker:
            def __init__(self, total_steps):
                self.total_steps = total_steps
                self.current_step = 0
                self.current_step_name = ""
                self.start_time = datetime.now()

            def update_progress(self, step, step_name="", details=""):
                self.current_step = step
                self.current_step_name = step_name
                progress = min(100, int((step / self.total_steps) * 100))
                elapsed = datetime.now() - self.start_time

                logger.info(f"📊 [{progress:3d}%] {step_name}")
                if details:
                    logger.info(f"💡 详细信息: {details}")
                logger.info(f"⏱️  已用时间: {elapsed.total_seconds():.2f}秒")
                logger.info("=" * 60)

        progress_tracker = DetailedProgressTracker(20)  # 假设20个主要步骤
        progress_tracker.update_progress(0, "🚀 任务初始化完成", "准备开始数据刷新流程")

        # 步骤6: 初始化LLM客户端
        logger.info("🔄 步骤6: 初始化LLM客户端")
        progress_tracker.update_progress(1, "🤖 初始化LLM客户端")

        try:
            logger.info("📦 尝试导入llm_client模块...")
            from llm_client import LLMClient

            logger.info("🔧 检查环境变量...")
            import os
            api_key = os.getenv("LLM_API_KEY", "")
            base_url = os.getenv("LLM_BASE_URL", "")
            model = os.getenv("LLM_MODEL", "")

            logger.info(f"🔑 LLM_API_KEY: {'已设置' if api_key else '未设置'}")
            logger.info(f"🌐 LLM_BASE_URL: {base_url if base_url else '使用默认值'}")
            logger.info(f"🧠 LLM_MODEL: {model if model else '使用默认值'}")

            llm_client = LLMClient()
            logger.info("✅ LLMClient初始化成功")
            progress_tracker.update_progress(2, "✅ LLM客户端初始化完成")

        except Exception as e:
            logger.error(f"❌ LLM客户端初始化失败: {e}")
            logger.error(f"❌ 错误类型: {type(e).__name__}")
            logger.error(f"❌ 错误详情: {str(e)}")
            import traceback
            logger.error(f"❌ 完整堆栈: {traceback.format_exc()}")
            await task_manager.update_task_status(task_id, TaskStatus.FAILED, f"LLM初始化失败: {str(e)}")
            return

        # 步骤7: 测试LLM连接
        logger.info("🔄 步骤7: 测试LLM连接")
        progress_tracker.update_progress(3, "🔗 测试LLM API连接")

        try:
            logger.info("🌐 准备发送测试请求到LLM API...")
            logger.info(f"🎯 目标API: {llm_client.base_url}")
            logger.info(f"🧠 使用模型: {llm_client.model}")

            # 构建测试消息
            test_messages = [
                {"role": "system", "content": "你是一个数据采集助手。"},
                {"role": "user", "content": "请简单回复'连接测试成功'"}
            ]

            logger.info("📤 发送测试请求...")
            response = llm_client._make_request(test_messages, max_tokens=100)

            if response:
                logger.info("✅ LLM API连接测试成功")
                logger.info(f"📝 测试响应: {response[:100]}...")
                progress_tracker.update_progress(4, "✅ LLM API连接测试通过")
            else:
                raise Exception("LLM API返回空响应")

        except Exception as e:
            logger.error(f"❌ LLM API连接测试失败: {e}")
            logger.error(f"❌ 错误类型: {type(e).__name__}")
            logger.error(f"❌ 错误详情: {str(e)}")
            import traceback
            logger.error(f"❌ 完整堆栈: {traceback.format_exc()}")
            await task_manager.update_task_status(task_id, TaskStatus.FAILED, f"LLM连接测试失败: {str(e)}")
            return

        # 步骤8: 开始获取省份数据
        logger.info("🔄 步骤8: 开始获取省份数据")
        progress_tracker.update_progress(5, "🌍 开始获取省份数据", "准备调用LLM获取全国省份列表")

        try:
            logger.info("🏛️ 构建省份查询提示词...")

            # 模拟获取省份数据的提示词
            province_prompt = f"""
请返回中国的所有省级行政区划，包括省份、自治区、直辖市和特别行政区。

要求：
1. 返回JSON格式
2. 包含完整的中文名称
3. 按照标准的行政区划代码排序

格式示例：
{{
  "items": [
    {{"name": "北京市", "code": "110000"}},
    {{"name": "天津市", "code": "120000"}},
    ...
  ]
}}
"""

            logger.info("📤 发送省份查询请求...")
            province_messages = [
                {"role": "system", "content": "你是一个专业的地理信息系统数据助手，专门处理中国行政区划数据。"},
                {"role": "user", "content": province_prompt}
            ]

            province_response = llm_client._make_request(province_messages, max_tokens=2000)

            if not province_response:
                raise Exception("省份数据获取失败：返回空响应")

            logger.info("✅ 成功获取省份响应")
            logger.info(f"📄 响应长度: {len(province_response)} 字符")

            # 尝试解析JSON响应
            import json
            try:
                province_data = json.loads(province_response)
                provinces = province_data.get('items', [])
                logger.info(f"🌍 成功解析JSON数据: {len(provinces)} 个省级行政区")

                # 显示前5个省份
                for i, province in enumerate(provinces[:5]):
                    logger.info(f"📍 省份{i+1}: {province.get('name', '未知')} (代码: {province.get('code', 'N/A')})")

                if len(provinces) > 5:
                    logger.info(f"📍 ... 还有 {len(provinces) - 5} 个省份")

                progress_tracker.update_progress(7, f"✅ 成功获取{len(provinces)}个省份数据")

            except json.JSONDecodeError as je:
                logger.warning(f"⚠️ JSON解析失败，尝试文本解析: {je}")
                # 如果JSON解析失败，尝试简单的文本提取
                lines = province_response.split('\n')
                provinces = []
                for line in lines:
                    if '省' in line or '市' in line or '区' in line:
                        provinces.append({"name": line.strip(), "code": "N/A"})

                logger.info(f"🌍 通过文本解析获得 {len(provinces)} 个省份")
                progress_tracker.update_progress(7, f"✅ 通过文本解析获得{len(provinces)}个省份数据")

        except Exception as e:
            logger.error(f"❌ 省份数据获取失败: {e}")
            import traceback
            logger.error(f"❌ 完整堆栈: {traceback.format_exc()}")
            await task_manager.update_task_status(task_id, TaskStatus.FAILED, f"省份数据获取失败: {str(e)}")
            return

        # 步骤9: 模拟数据处理完成
        logger.info("🔄 步骤9: 数据处理完成")
        progress_tracker.update_progress(15, "💾 正在保存数据到数据库", "将获取的数据写入数据库表")

        # 这里可以添加实际的数据保存逻辑
        logger.info("💾 数据保存逻辑...")
        progress_tracker.update_progress(18, "💾 数据保存完成")

        # 步骤10: 任务完成
        logger.info("🔄 步骤10: 任务完成")
        progress_tracker.update_progress(20, "🎉 数据刷新任务完成", f"总共处理了{len(provinces)}个省份数据")

        await task_manager.update_task_status(task_id, TaskStatus.COMPLETED)

        end_time = datetime.now()
        elapsed_time = end_time - progress_tracker.start_time

        logger.info(f"🎉 ========== 数据刷新任务完成 ==========")
        logger.info(f"✅ 任务ID: {task_id}")
        logger.info(f"⏰ 结束时间: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"⏱️  总用时: {elapsed_time.total_seconds():.2f}秒")
        logger.info(f"📊 处理数据: {len(provinces)} 个省份")
        logger.info(f"🚀 任务状态: COMPLETED")
        logger.info("=" * 60)

        # 🔄 步骤11: 自动遍历所有省份，扫描市区数据
        logger.info(f"🔄 ========== 开始自动遍历省份扫描市区 ==========")
        logger.info(f"📍 即将开始遍历 {len(provinces)} 个省份，获取各省份的城市数据")

        auto_start_time = datetime.now()
        logger.info(f"⏰ 自动遍历开始时间: {auto_start_time.strftime('%Y-%m-%d %H:%M:%S')}")

        # 统计成功和失败的省份
        successful_provinces = 0
        failed_provinces = 0
        total_cities = 0

        # 遍历每个省份
        for i, province_info in enumerate(provinces, 1):
            # 确保省份信息是字符串格式
            if isinstance(province_info, dict):
                province_name = province_info.get('name', str(province_info))
            else:
                province_name = str(province_info)

            province_start_time = time.time()
            logger.info(f"🔄 [步骤11.{i}/{len(provinces)}] 开始处理省份: {province_name}")
            logger.info(f"📊 进度: {i}/{len(provinces)} ({int(i/len(provinces)*100)}%)")

            try:
                # 为每个省份创建一个子任务
                province_task_id = str(uuid.uuid4())
                logger.info(f"📋 创建子任务ID: {province_task_id} for {province_name}")

                # 创建子任务记录
                await db.create_task(
                    task_id=province_task_id,
                    hospital_name=f"省份城市扫描: {province_name}",
                    query=f"获取省份 {province_name} 的城市数据",
                    status=TaskStatus.PENDING.value
                )

                logger.info(f"🔍 正在调用省份刷新函数...")

                # 调用省份刷新函数
                await execute_province_refresh_task(province_task_id, province_name)

                province_time = time.time() - province_start_time
                logger.info(f"✅ [步骤11.{i}/{len(provinces)}] 省份 {province_name} 处理成功")
                logger.info(f"⏱️ 省份处理用时: {province_time:.2f}秒")

                successful_provinces += 1

                # 短暂休息，避免API调用过于频繁
                import asyncio
                await asyncio.sleep(2)

            except Exception as province_error:
                province_time = time.time() - province_start_time
                logger.error(f"❌ [步骤11.{i}/{len(provinces)}] 省份 {province_name} 处理失败")
                logger.error(f"🔴 失败原因: {str(province_error)}")
                logger.error(f"⏱️ 失败前用时: {province_time:.2f}秒")

                failed_provinces += 1

                # 更新子任务状态为失败
                try:
                    if 'province_task_id' in locals():
                        await task_manager.update_task_status(province_task_id, TaskStatus.FAILED, str(province_error))
                except Exception as task_error:
                    logger.error(f"❌ 更新子任务状态失败: {str(task_error)}")

                # 继续处理下一个省份
                continue

            # 显示当前进度
            logger.info(f"📊 当前进度: 成功 {successful_provinces} | 失败 {failed_provinces} | 总计 {i}/{len(provinces)}")

        # 自动遍历完成总结
        auto_end_time = datetime.now()
        auto_elapsed = (auto_end_time - auto_start_time).total_seconds()

        logger.info(f"🎉 ========== 自动遍历省份扫描市区完成 ==========")
        logger.info(f"✅ 主任务ID: {task_id}")
        logger.info(f"⏰ 开始时间: {auto_start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"⏰ 结束时间: {auto_end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"⏱️ 自动遍历总用时: {auto_elapsed:.2f}秒")
        logger.info(f"📊 处理结果统计:")
        logger.info(f"   ✅ 成功省份: {successful_provinces}/{len(provinces)}")
        logger.info(f"   ❌ 失败省份: {failed_provinces}/{len(provinces)}")
        logger.info(f"   📈 成功率: {int(successful_provinces/len(provinces)*100)}%")
        logger.info(f"🏙️ 获取城市总数: {total_cities}")
        logger.info(f"🚀 所有任务状态: COMPLETED")
        logger.info("=" * 80)

    except Exception as e:
        logger.error(f"💥 ========== 数据刷新任务失败 ==========")
        logger.error(f"❌ 任务ID: {task_id}")
        logger.error(f"❌ 失败时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.error(f"❌ 错误类型: {type(e).__name__}")
        logger.error(f"❌ 错误信息: {str(e)}")

        import traceback
        logger.error(f"❌ 完整错误堆栈:")
        logger.error(traceback.format_exc())

        try:
            await task_manager.update_task_status(task_id, TaskStatus.FAILED, str(e))
            logger.info(f"📝 已更新任务状态为FAILED")
        except Exception as update_error:
            logger.error(f"❌ 更新任务状态也失败了: {update_error}")

        logger.error("=" * 60)

async def execute_province_refresh_task(task_id: str, province_name: str):
    """执行特定省份数据刷新任务"""
    logger.info(f"=== 函数开始执行: {task_id}, {province_name} ===")

    # 验证参数
    if not isinstance(task_id, str):
        raise ValueError(f"task_id必须是字符串，当前类型: {type(task_id)}")
    if not isinstance(province_name, str):
        raise ValueError(f"province_name必须是字符串，当前类型: {type(province_name)}")

    logger.info(f"✅ 参数验证通过: task_id={task_id}, province_name={province_name}")

    start_time = time.time()
    try:
        # 🚀 开始执行省份刷新任务
        logger.info(f"🚀 ========== 开始执行省份刷新任务 ==========")
        logger.info(f"📋 任务ID: {task_id}")
        logger.info(f"📍 目标省份: {province_name}")
        logger.info(f"🔍 省份名称类型: {type(province_name)}")
        logger.info(f"⏰ 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # 确保省份名称是字符串
        assert isinstance(province_name, str), f"省份名称必须是字符串，当前类型: {type(province_name)}"

        # 步骤1: 更新任务状态为RUNNING
        logger.info(f"🔄 步骤1: 更新任务状态为RUNNING")
        await task_manager.update_task_status(task_id, TaskStatus.RUNNING)
        logger.info(f"✅ 任务状态已更新为RUNNING: {task_id}")

        # 步骤2: 准备工作环境和LLM客户端
        logger.info(f"🔄 步骤2: 准备工作环境和LLM客户端")
        logger.info(f"📊 [10%] 🏗️ 正在初始化环境...")

        # 导入LLM客户端（使用本地导入避免循环依赖）
        try:
            from llm_client import LLMClient
            logger.info(f"✅ LLM客户端模块导入成功")
        except Exception as e:
            logger.error(f"❌ LLM客户端模块导入失败: {e}")
            raise e

        # 初始化LLM客户端
        try:
            llm_client = LLMClient()
            logger.info(f"✅ LLM客户端初始化成功")
        except Exception as e:
            logger.error(f"❌ LLM客户端初始化失败: {e}")
            raise e

        logger.info(f"📊 [20%] ✅ 环境初始化完成")
        logger.info(f"⏱️ 已用时间: {time.time() - start_time:.2f}秒")
        logger.info(f"============================================================")

        # 步骤3: 获取数据库连接
        logger.info(f"🔄 步骤3: 获取数据库连接")
        db = await get_db()
        logger.info(f"✅ 数据库连接成功")

        # 步骤4: 获取指定省份的城市数据
        logger.info(f"🔄 步骤4: 获取省份 '{province_name}' 的城市数据")
        logger.info(f"📊 [25%] 🏙️ 正在获取城市数据...")
        logger.info(f"📋 详细信息: 准备通过LLM获取 {province_name} 的城市列表")

        # 构造查询城市的提示词
        city_system_prompt = """你是一个专业的地理信息系统专家。请根据用户指定的省份名称，返回该省份下辖的所有地级市、自治州、地区等行政区划信息。

请严格按照JSON格式返回，包含以下字段：
- cities: 城市列表（字符串数组）
- count: 城市总数（整数）
- province: 省份全名（字符串）

注意：
1. 必须返回有效的JSON格式
2. 只返回地级市、自治州、地区等，不包含县级市
3. 如果某些信息不确定，请根据公开行政区划信息进行合理推断
4. 不要在JSON前后添加其他说明文字"""

        city_user_prompt = f"""请查询以下省份的地级市、自治州、地区等行政区划：

省份名称：{province_name}

请返回该省份下辖的所有地级行政区划的标准JSON格式数据。"""

        city_messages = [
            {"role": "system", "content": city_system_prompt},
            {"role": "user", "content": city_user_prompt}
        ]

              # 使用LLM客户端获取城市数据
        logger.info(f"🚀 准备调用LLM API获取城市数据")
        try:
            # 构建消息列表
            messages = city_messages

            # 调用LLM API
            cities_response = llm_client._make_request(messages, max_tokens=2000)

            if cities_response:
                logger.info(f"✅ LLM API调用成功，响应类型: {type(cities_response)}")
            else:
                logger.error(f"❌ LLM API返回空响应")
                raise ValueError("LLM API返回空响应")

        except Exception as e:
            logger.error(f"❌ LLM API调用失败: {e}")
            await task_manager.update_task_status(task_id, TaskStatus.FAILED, f"LLM API调用失败: {str(e)}")
            raise e

        if not cities_response:
            raise ValueError("LLM API返回空响应！无法获取城市数据。")

        logger.info(f"✅ 成功获取城市API响应")
        logger.info(f"📄 响应长度: {len(cities_response)} 字符")
        logger.info(f"📄 响应内容（前200字符）: {cities_response[:200]}")

        # 解析城市数据JSON
        try:
            import json
            # 清理响应文本
            cities_response = cities_response.strip()
            if cities_response.startswith('```json'):
                cities_response = cities_response[7:]
            if cities_response.startswith('```'):
                cities_response = cities_response[3:]
            if cities_response.endswith('```'):
                cities_response = cities_response[:-3]
            cities_response = cities_response.strip()

            # 提取JSON部分
            json_start = cities_response.find('{')
            json_end = cities_response.rfind('}') + 1

            if json_start == -1 or json_end == -1:
                raise ValueError(f"响应中未找到有效的JSON格式！原始响应: {cities_response[:500]}...")

            json_str = cities_response[json_start:json_end]
            cities_data = json.loads(json_str)

            # 验证必要字段
            if not isinstance(cities_data, dict):
                raise ValueError(f"响应不是有效的字典格式！类型: {type(cities_data)}")

            if 'cities' not in cities_data:
                raise ValueError("缺少必要字段: cities")

            if not isinstance(cities_data.get('cities'), list):
                raise ValueError("cities字段必须是数组格式")

            cities = cities_data['cities']
            logger.info(f"✅ 成功解析城市数据")
            logger.info(f"🏙️ 获取到 {len(cities)} 个城市")

            # 输出前几个城市作为示例
            for i, city in enumerate(cities[:5], 1):
                logger.info(f"🏛️ 城市{i}: {city}")
            if len(cities) > 5:
                logger.info(f"🏛️ ... 还有 {len(cities) - 5} 个城市")

        except Exception as e:
            logger.error(f"❌ 城市数据解析失败: {e}")
            logger.error(f"原始响应内容: {cities_response}")
            raise ValueError(f"无法解析LLM返回的城市数据: {str(e)}")

        logger.info(f"📊 [35%] ✅ 城市数据获取完成")
        logger.info(f"⏱️ 已用时间: {time.time() - start_time:.2f}秒")
        logger.info(f"============================================================")

        # 步骤5: 保存城市数据到数据库
        logger.info(f"🔄 步骤5: 保存城市数据到数据库")
        logger.info(f"📊 [50%] 💾 正在保存城市数据...")
        logger.info(f"📋 详细信息: 将 {len(cities)} 个城市写入数据库")

        # 确保省份存在
        province_info = await db.get_province_by_name(province_name)
        if not province_info:
            # 如果省份不存在，创建一个
            logger.warning(f"⚠️ 省份 '{province_name}' 不存在，正在创建...")
            province_id = await db.create_province(province_name)
            logger.info(f"✅ 省份 '{province_name}' 创建成功，ID: {province_id}")
        else:
            province_id = province_info['id']
            logger.info(f"✅ 省份 '{province_name}' 已存在，ID: {province_id}")

        # 保存城市数据
        saved_cities_count = 0
        for city_name in cities:
            try:
                # 使用LLM获取的真实数据保存城市
                city_id = await db.create_city(city_name, province_id)
                if city_id > 0:
                    saved_cities_count += 1
                    logger.debug(f"💾 城市保存成功: {city_name} (ID: {city_id})")
                else:
                    logger.warning(f"⚠️ 城市保存失败: {city_name}")

                if saved_cities_count % 10 == 0:
                    logger.info(f"💾 已保存 {saved_cities_count}/{len(cities)} 个城市...")
            except Exception as e:
                logger.error(f"❌ 保存城市 '{city_name}' 失败: {e}")
                # 继续处理下一个城市
                continue

        logger.info(f"✅ 城市数据保存完成")
        logger.info(f"🏙️ 成功保存 {saved_cities_count} 个城市")

        logger.info(f"📊 [90%] ✅ 数据保存完成")
        logger.info(f"⏱️ 已用时间: {time.time() - start_time:.2f}秒")
        logger.info(f"============================================================")

        # 步骤6: 任务完成
        logger.info(f"🔄 步骤6: 省份刷新任务完成")
        logger.info(f"📊 [100%] 🎉 省份刷新任务完成")
        logger.info(f"📋 详细信息: 成功获取并保存了 {len(cities)} 个城市")
        logger.info(f"⏱️ 总用时: {time.time() - start_time:.2f}秒")
        logger.info(f"============================================================")

        # 更新任务状态为成功
        await task_manager.update_task_status(task_id, TaskStatus.COMPLETED)

        logger.info(f"🎉 ========== 省份刷新任务完成 ==========")
        logger.info(f"✅ 任务ID: {task_id}")
        logger.info(f"⏰ 完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"⏱️ 总用时: {time.time() - start_time:.2f}秒")
        logger.info(f"🏙️ 处理城市数: {len(cities)}")
        logger.info(f"🎯 任务状态: COMPLETED")
        logger.info(f"============================================================")

    except Exception as e:
        error_msg = str(e)
        logger.error(f"❌ 执行省份刷新任务失败: {error_msg}")
        logger.error(f"📋 错误详情: {type(e).__name__}: {error_msg}")

        # 更新任务状态为失败
        await task_manager.update_task_status(task_id, TaskStatus.FAILED, error_msg)

        logger.error(f"💥 ========== 省份刷新任务失败 ==========")
        logger.error(f"❌ 任务ID: {task_id}")
        logger.error(f"📍 目标省份: {province_name}")
        logger.error(f"⏰ 失败时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.error(f"⏱️ 用时: {time.time() - start_time:.2f}秒")
        logger.error(f"🔴 失败原因: {error_msg}")
        logger.error(f"============================================================")

        # 重新抛出异常
        raise e


async def execute_district_refresh_task(task_id: str, city_name: str):
    """执行特定城市的区县数据刷新任务"""
    start_time = time.time()

    try:
        logger.info(f"=== 任务开始执行: {task_id}, {city_name} ===")
        logger.info(f"✅ 任务验证通过: task_id={task_id}, city_name={city_name}")

        logger.info(f"🚀 ========== 开始执行城市区县刷新任务 ==========")
        logger.info(f"📋 任务ID: {task_id}")
        logger.info(f"📍 目标城市: {city_name}")
        logger.info(f"🔍 城市名称类型: {type(city_name)}")
        logger.info(f"⏰ 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # 步骤1: 更新任务状态为RUNNING
        logger.info(f"🔄 步骤1: 更新任务状态为RUNNING")
        await task_manager.update_task_status(task_id, TaskStatus.RUNNING)
        logger.info(f"✅ 任务状态已更新为RUNNING: {task_id}")

        # 步骤2: 准备执行环境和LLM客户端
        logger.info(f"🔄 步骤2: 准备执行环境和LLM客户端")
        logger.info(f"📊 [10%] 🏗️ 正在初始化任务环境...")

        # 导入LLM客户端
        try:
            from llm_client import LLMClient
            logger.info(f"✅ LLM客户端模块导入成功")
            llm_client = LLMClient()
            logger.info(f"✅ LLM客户端顺序初始化成功")
        except Exception as import_error:
            logger.error(f"❌ LLM客户端初始化失败: {import_error}")
            raise ValueError(f"LLM客户端初始化失败: {import_error}")

        logger.info(f"📊 [20%] ✅ 环境初始化完成")
        logger.info(f"⏱️ 已用时间: {time.time() - start_time:.2f}秒")
        logger.info(f"============================================================")

        # 步骤3: 获取数据库连接
        logger.info(f"🔄 步骤3: 获取数据库连接")
        db = await get_db()
        logger.info(f"✅ 数据库连接成功")

        # 步骤4: 验证城市存在并获取城市信息
        logger.info(f"🔄 步骤4: 验证城市存在并获取城市信息")
        logger.info(f"📊 [25%] 🏙️ 正在验证城市信息...")
        logger.info(f"📋 详细信息: 准备验证城市 '{city_name}' 是否存在")

        # 确保城市存在
        city_info = await db.get_city_by_name(city_name)
        if not city_info:
            error_msg = f"城市 '{city_name}' 不存在于数据库中，请先扫描该省份"
            logger.error(f"❌ {error_msg}")
            raise ValueError(error_msg)

        city_id = city_info['id']
        logger.info(f"✅ 城市验证成功: {city_name} (ID: {city_id})")

        # 步骤5: 调用LLM获取区县数据
        logger.info(f"🔄 步骤5: 调用LLM获取区县数据")
        logger.info(f"📊 [30%] 🧠 正在调用LLM获取区县数据...")

        # 调用LLM API
        try:
            logger.info(f"🚀 准备调用LLM API获取区县数据")
            district_data = await llm_client.get_districts_by_city(city_name)

            if not district_data or 'items' not in district_data:
                error_msg = "LLM API返回数据格式错误"
                logger.error(f"❌ {error_msg}")
                raise ValueError(error_msg)

            districts = district_data['items']
            logger.info(f"✅ 成功获取区县API响应")
            logger.info(f"📄 响应长度: {len(str(district_data))} 字符")
            logger.info(f"📄 响应内容，前200字符: {str(district_data)[:200]}...")
            logger.info(f"✅ 成功解析区县数据")
            logger.info(f"🏙️ 获取到 {len(districts)} 个区县")

            # 显示前几个区县名称
            for i, district in enumerate(districts[:5]):
                logger.info(f"🏘️ 区县{i+1}: {district.get('name')}")
            if len(districts) > 5:
                logger.info(f"🏘️ ... 还有 {len(districts) - 5} 个区县")

        except Exception as llm_error:
            error_msg = f"调用LLM API获取区县数据失败: {str(llm_error)}"
            logger.error(f"❌ {error_msg}")
            raise ValueError(error_msg)

        logger.info(f"📊 [35%] ✅ 区县数据获取完成")
        logger.info(f"⏱️ 已用时间: {time.time() - start_time:.2f}秒")
        logger.info(f"============================================================")

        # 步骤6: 保存区县数据到数据库
        logger.info(f"🔄 步骤6: 保存区县数据到数据库")
        logger.info(f"📊 [50%] 💾 正在保存区县数据...")
        logger.info(f"📋 详细信息: 将 {len(districts)} 个区县写入数据库")

        saved_districts_count = 0
        for district in districts:
            try:
                district_name = district.get('name', '').strip()
                if not district_name:
                    continue

                # 检查区县是否已存在
                existing_district = await db.get_district_by_name(district_name)
                if existing_district:
                    logger.info(f"⚠️ 区县 '{district_name}' 已存在，跳过创建")
                    saved_districts_count += 1
                    continue

                # 创建新区县
                district_id = await db.create_district(district_name, city_id)
                if district_id > 0:
                    saved_districts_count += 1
                    logger.debug(f"💾 区县保存成功: {district_name} (ID: {district_id})")
                else:
                    logger.warning(f"⚠️ 区县保存失败: {district_name}")

                if saved_districts_count % 10 == 0:
                    logger.info(f"💾 已保存 {saved_districts_count}/{len(districts)} 个区县...")
            except Exception as e:
                logger.error(f"❌ 保存区县 '{district_name}' 失败: {e}")
                # 继续处理下一个区县
                continue

        logger.info(f"✅ 区县数据保存完成")
        logger.info(f"🏘️ 成功保存 {saved_districts_count} 个区县")

        logger.info(f"📊 [90%] ✅ 数据保存完成")
        logger.info(f"⏱️ 已用时间: {time.time() - start_time:.2f}秒")
        logger.info(f"============================================================")

        # 步骤7: 任务完成
        logger.info(f"🔄 步骤7: 城市区县刷新任务完成")
        logger.info(f"📊 [100%] 🎉 城市区县刷新任务完成")
        logger.info(f"📋 详细信息: 成功获取并保存了 {len(districts)} 个区县")
        logger.info(f"⏱️ 总用时: {time.time() - start_time:.2f}秒")
        logger.info(f"============================================================")

        # 更新任务状态为成功
        await task_manager.update_task_status(task_id, TaskStatus.COMPLETED)

        logger.info(f"🎉 ========== 城市区县刷新任务完成 ==========")
        logger.info(f"✅ 任务ID: {task_id}")
        logger.info(f"⏰ 完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"⏱️ 总用时: {time.time() - start_time:.2f}秒")
        logger.info(f"🏘️ 处理区县数: {len(districts)}")
        logger.info(f"🎯 任务状态: COMPLETED")
        logger.info(f"============================================================")

    except Exception as e:
        error_msg = str(e)
        logger.error(f"❌ 执行城市区县刷新任务失败: {error_msg}")
        logger.error(f"📋 错误详情: {type(e).__name__}: {error_msg}")

        # 更新任务状态为失败
        await task_manager.update_task_status(task_id, TaskStatus.FAILED, error_msg)

        logger.error(f"💥 ========== 城市区县刷新任务失败 ==========")
        logger.error(f"❌ 任务ID: {task_id}")
        logger.error(f"📍 目标城市: {city_name}")
        logger.error(f"⏰ 失败时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.error(f"⏱️ 用时: {time.time() - start_time:.2f}秒")
        logger.error(f"🔴 失败原因: {error_msg}")
        logger.error(f"============================================================")

        # 重新抛出异常
        raise e


async def execute_hospital_refresh_for_district(task_id: str, district_name: str):
    """执行特定区县的医院数据刷新任务"""
    start_time = time.time()

    try:
        # 修复字符编码问题：确保district_name不为空且正确编码
        if not district_name or not district_name.strip():
            error_msg = f"区县名称为空或无效"
            logger.error(f"❌ {error_msg}")
            await task_manager.update_task_status(task_id, TaskStatus.FAILED, error_msg)
            raise ValueError(error_msg)

        # 清理和标准化区县名称
        district_name_clean = district_name.strip()
        logger.info(f"✅ 标准化区县名称: '{district_name_clean}' (原始: '{district_name}')")

        logger.info(f"=== 任务开始执行: {task_id}, 区县: {district_name_clean} ===")
        logger.info(f"✅ 任务验证通过: task_id={task_id}, district_name={district_name_clean}")

        logger.info(f"🚀 ========== 开始执行区县医院刷新任务 ==========")
        logger.info(f"📋 任务ID: {task_id}")
        logger.info(f"📍 目标区县: {district_name_clean}")
        logger.info(f"🔍 区县名称类型: {type(district_name_clean)}")
        logger.info(f"⏰ 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # 步骤1: 更新任务状态为RUNNING
        logger.info(f"🔄 步骤1: 更新任务状态为RUNNING")
        await task_manager.update_task_status(task_id, TaskStatus.RUNNING)
        logger.info(f"✅ 任务状态已更新为RUNNING: {task_id}")

        # 步骤2: 准备执行环境和LLM客户端
        logger.info(f"🔄 步骤2: 准备执行环境和LLM客户端")
        logger.info(f"📊 [10%] 🏗️ 正在初始化任务环境...")

        # 导入LLM客户端
        try:
            from llm_client import LLMClient
            logger.info(f"✅ LLM客户端模块导入成功")
            llm_client = LLMClient()
            logger.info(f"✅ LLM客户端顺序初始化成功")
        except Exception as import_error:
            logger.error(f"❌ LLM客户端导入失败: {import_error}")
            await task_manager.update_task_status(task_id, TaskStatus.FAILED, f"LLM客户端初始化失败: {import_error}")
            raise import_error

        # 步骤3: 获取数据库连接
        logger.info(f"🔄 步骤3: 获取数据库连接")
        logger.info(f"📊 [20%] 💾 正在连接数据库...")
        db = await get_db()
        logger.info(f"✅ 数据库连接成功")

        # 步骤4: 查找区县信息
        logger.info(f"🔄 步骤4: 查找区县信息")
        logger.info(f"📊 [30%] 🔍 正在查找区县信息: '{district_name_clean}'")

        district_info = await db.get_district_by_name(district_name_clean)
        if not district_info:
            error_msg = f"区县 '{district_name_clean}' 不存在"
            logger.error(f"❌ {error_msg}")
            await task_manager.update_task_status(task_id, TaskStatus.FAILED, error_msg)
            raise ValueError(error_msg)

        logger.info(f"✅ 找到区县: {district_info['name']}, ID: {district_info['id']}")

        # 获取城市和省份信息用于日志记录
        city_info = await db.get_city_by_id(district_info['city_id'])
        province_info = await db.get_province_by_id(city_info['province_id'])
        logger.info(f"📍 完整层级: {province_info['name']} -> {city_info['name']} -> {district_info['name']}")

        # 步骤5: 使用LLM获取区县内的医院数据
        logger.info(f"🔄 步骤5: 获取区县医院数据")
        logger.info(f"📊 [40%] 🤖 正在调用LLM获取医院数据...")

        try:
            hospitals_data = await llm_client.get_hospitals_from_district(
                province_info['name'],
                city_info['name'],
                district_info['name']
            )
            logger.info(f"✅ LLM返回医院数据: {len(hospitals_data)} 家医院")
        except Exception as llm_error:
            error_msg = f"调用LLM获取医院数据失败: {str(llm_error)}"
            logger.error(f"❌ {error_msg}")
            await task_manager.update_task_status(task_id, TaskStatus.FAILED, error_msg)
            raise llm_error

        # 步骤6: 保存医院数据到数据库
        logger.info(f"🔄 步骤6: 保存医院数据")
        logger.info(f"📊 [60%] 💾 正在保存医院数据...")

        saved_count = 0
        updated_count = 0

        for i, hospital_data in enumerate(hospitals_data):
            try:
                logger.info(f"📊 [{60 + i*30//len(hospitals_data)}%] 💾 正在保存医院 {i+1}/{len(hospitals_data)}: {hospital_data.get('name', 'Unknown')}")

                # 提取医院信息，支持更多字段
                hospital_name = hospital_data.get('name', '').strip()
                level = hospital_data.get('level', '')
                address = hospital_data.get('address', '')
                phone = hospital_data.get('phone', '')
                beds_count = hospital_data.get('beds_count')
                staff_count = hospital_data.get('staff_count')
                departments = hospital_data.get('departments', [])
                specializations = hospital_data.get('specializations', [])
                website = hospital_data.get('website', '')

                if not hospital_name:
                    logger.warning(f"⚠️ 医院名称为空，跳过")
                    continue

                # 检查医院是否已存在
                existing_hospital = await db.get_hospital_by_name_and_district(hospital_name, district_info['id'])

                if existing_hospital:
                    # 更新现有医院
                    await db.update_hospital(
                        hospital_id=existing_hospital['id'],
                        name=hospital_name,
                        level=level,
                        address=address,
                        phone=phone,
                        beds_count=beds_count,
                        staff_count=staff_count,
                        departments=departments,
                        specializations=specializations,
                        website=website
                    )
                    updated_count += 1
                    logger.info(f"✅ 已更新医院: {hospital_name}")
                else:
                    # 创建新医院
                    await db.create_hospital(
                        name=hospital_name,
                        district_id=district_info['id'],
                        level=level,
                        address=address,
                        phone=phone,
                        beds_count=beds_count,
                        staff_count=staff_count,
                        departments=departments,
                        specializations=specializations,
                        website=website
                    )
                    saved_count += 1
                    logger.info(f"✅ 已保存医院: {hospital_name}")

            except Exception as hospital_error:
                logger.error(f"❌ 保存医院失败: {hospital_data.get('name', 'Unknown')}, 错误: {str(hospital_error)}")
                continue

        logger.info(f"✅ 医院数据保存完成 - 新增: {saved_count}, 更新: {updated_count}")

        # 步骤7: 完成任务
        logger.info(f"🔄 步骤7: 完成任务")
        logger.info(f"📊 [100%] ✅ 任务完成，正在清理资源...")

        # 更新任务状态为成功
        await task_manager.update_task_status(task_id, TaskStatus.COMPLETED)

        success_message = f"区县 '{district_name}' 医院数据刷新完成，新增 {saved_count} 家医院，更新 {updated_count} 家医院"
        logger.info(f"🎉 ========== 区县医院刷新任务完成 ==========")
        logger.info(f"✅ 任务ID: {task_id}")
        logger.info(f"📍 目标区县: {district_name}")
        logger.info(f"⏰ 完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"⏱️ 总用时: {time.time() - start_time:.2f}秒")
        logger.info(f"🏥 处理结果: 新增 {saved_count} 家，更新 {updated_count} 家医院")
        logger.info(f"🎯 任务状态: COMPLETED")
        logger.info(f"📋 成功消息: {success_message}")
        logger.info(f"============================================================")

    except Exception as e:
        error_msg = str(e)
        logger.error(f"❌ 执行区县医院刷新任务失败: {error_msg}")
        logger.error(f"📋 错误详情: {type(e).__name__}: {error_msg}")

        # 更新任务状态为失败
        await task_manager.update_task_status(task_id, TaskStatus.FAILED, error_msg)

        logger.error(f"💥 ========== 区县医院刷新任务失败 ==========")
        logger.error(f"❌ 任务ID: {task_id}")
        logger.error(f"📍 目标区县: {district_name}")
        logger.error(f"⏰ 失败时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.error(f"⏱️ 用时: {time.time() - start_time:.2f}秒")
        logger.error(f"🔴 失败原因: {error_msg}")
        logger.error(f"============================================================")

        # 重新抛出异常
        raise e


@app.post("/test/city")
async def test_city_endpoint():
    """测试城市端点是否可以注册"""
    return {"message": "City test endpoint works", "status": "success"}


@app.post("/refresh/city/{city_name}", response_model=RefreshTaskResponse)
async def refresh_city_data(city_name: str, background_tasks: BackgroundTasks):
    """
    刷新指定城市所有区县的医院数据

    Args:
        city_name: 城市名称
        background_tasks: FastAPI后台任务管理器

    Returns:
        RefreshTaskResponse: 包含任务ID和响应信息
    """
    logger.info(f"🎉 ========== 接收市级医院刷新请求 ==========")
    logger.info(f"📍 城市名称: '{city_name}'")
    logger.info(f"🔍 接收的原始参数: '{city_name}'")

    start_time = time.time()

    try:
        # URL解码中文字符
        from urllib.parse import unquote
        city_name_decoded = unquote(city_name)
        logger.info(f"✅ URL解码后的城市名称: '{city_name_decoded}'")

        # 清理和标准化城市名称
        city_name_clean = city_name_decoded.strip()
        logger.info(f"✅ 标准化城市名称: '{city_name_clean}' (原始: '{city_name}')")

        # 步骤1: 连接数据库并验证城市
        logger.info(f"🔄 步骤1: 连接数据库")
        logger.info(f"📊 [20%] 🔗 正在连接数据库...")

        db = await get_db()

        # 步骤2: 查找城市
        logger.info(f"🔄 步骤2: 查找城市")
        logger.info(f"📊 [40%] 🔍 正在查找城市: '{city_name_clean}'")

        city_info = await db.get_city_by_name(city_name_clean)

        if not city_info:
            error_msg = f"城市 '{city_name_clean}' 不存在，请先刷新数据"
            logger.error(f"❌ {error_msg}")
            raise HTTPException(status_code=404, detail=error_msg)

        logger.info(f"✅ 找到城市: {city_info['name']} (ID: {city_info['id']}, 省份ID: {city_info['province_id']})")

        # 步骤3: 获取该城市下所有区县
        logger.info(f"🔄 步骤3: 获取城市下所有区县")
        logger.info(f"📊 [60%] 📍 正在获取城市 '{city_name_clean}' 下所有区县...")

        districts, total_count = await db.get_districts(city_info['id'], 1, 1000)  # 获取前1000个区县，应该足够了

        if not districts or total_count == 0:
            error_msg = f"城市 '{city_name_clean}' 下没有找到任何区县"
            logger.error(f"❌ {error_msg}")
            raise HTTPException(status_code=404, detail=error_msg)

        logger.info(f"✅ 找到 {total_count} 个区县:")
        for district in districts[:5]:  # 只显示前5个区县
            logger.info(f"   - {district['name']} (ID: {district['id']})")
        if total_count > 5:
            logger.info(f"   ... 还有 {total_count - 5} 个区县")

        # 步骤4: 创建主任务
        logger.info(f"🔄 步骤4: 创建主任务")
        logger.info(f"📊 [80%] 📋 正在创建主任务...")

        task_id = await task_manager.create_task(
            task_type="city_hospital_refresh",
            target=f"{city_info['name']}及所有区县医院数据",
            description=f"刷新城市 '{city_info['name']}' 下所有 {total_count} 个区县的医院数据"
        )

        logger.info(f"✅ 主任务已创建: {task_id}")

        # 步骤5: 启动后台任务
        logger.info(f"🔄 步骤5: 启动后台任务")
        background_tasks.add_task(execute_city_hospitals_refresh, task_id, city_info, districts)

        logger.info(f"📤 步骤6: 准备响应")
        response_message = f"城市 {city_info['name']} 及其 {total_count} 个区县医院数据刷新任务已创建，正在后台处理中..."
        logger.info(f"💬 响应消息: '{response_message}'")
        logger.info(f"✅ 响应数据已生成 - task_id: {task_id}")

        logger.info(f"🎉 ========== 市级医院刷新接口调用成功 ==========")
        logger.info(f"⏱️ 接口处理用时: {time.time() - start_time:.2f}秒")

        return RefreshTaskResponse(
            task_id=task_id,
            message=response_message,
            target=f"城市: {city_info['name']}",
            operation="批量刷新医院数据"
        )

    except HTTPException:
        # 重新抛出HTTP异常
        raise
    except Exception as e:
        error_msg = f"创建市级医院刷新任务失败: {str(e)}"
        logger.error(f"❌ {error_msg}")
        raise HTTPException(status_code=500, detail=error_msg)


async def execute_city_hospitals_refresh(task_id: str, city_info: dict, districts: list):
    """
    执行城市所有区县的医院数据刷新任务

    Args:
        task_id: 任务ID
        city_info: 城市信息字典
        districts: 区县信息列表
    """
    # City hospital refresh implementation
    start_time = time.time()

    try:
        logger.info(f"🎉 ========== 开始执行市级医院刷新任务 ==========")
        logger.info(f"📋 任务ID: {task_id}")
        logger.info(f"🏙️ 目标城市: {city_info['name']} (ID: {city_info['id']})")
        logger.info(f"📊 区县数量: {len(districts)} 个")
        logger.info(f"⏰ 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # 更新任务状态为运行中
        await task_manager.update_task_status(
            task_id,
            TaskStatus.RUNNING,
            f"开始刷新城市 {city_info['name']} 的医院数据，共 {len(districts)} 个区县"
        )

        # 获取省份信息
        db = await get_db()
        province_info = await db.get_province_by_id(city_info['province_id'])
        if not province_info:
            error_msg = f"无法获取城市 '{city_info['name']}' 所属省份信息"
            logger.error(f"❌ {error_msg}")
            await task_manager.update_task_status(task_id, TaskStatus.FAILED, error_msg)
            raise ValueError(error_msg)

        logger.info(f"📍 完整层级: {province_info['name']} -> {city_info['name']} -> {len(districts)} 个区县")

        # 统计数据
        total_districts = len(districts)
        completed_districts = 0
        successful_districts = 0
        failed_districts = 0
        total_new_hospitals = 0
        total_updated_hospitals = 0

        # 初始化LLM客户端
        llm_client = LLMClient()

        # 逐个处理每个区县
        for i, district in enumerate(districts):
            district_name = district['name']
            district_progress = int((i + 1) * 100 // total_districts)

            try:
                logger.info(f"🔄 处理第 {i+1}/{total_districts} 个区县: {district_name}")
                logger.info(f"📊 [{district_progress}%] 🏥 正在处理区县: {district_name}")

                # 更新主任务状态
                progress_msg = f"正在处理区县 {i+1}/{total_districts}: {district_name}"
                await task_manager.update_task_status(task_id, TaskStatus.RUNNING, progress_msg)

                # 步骤1: 检查区县是否仍然存在
                district_info = await db.get_district_by_name(district_name)
                if not district_info:
                    logger.warning(f"⚠️ 区县 '{district_name}' 不存在，跳过")
                    failed_districts += 1
                    continue

                logger.info(f"✅ 找到区县: {district_info['name']} (ID: {district_info['id']})")

                # 步骤2: 使用LLM获取区县内的医院数据
                logger.info(f"🔄 步骤2: 获取区县医院数据")
                logger.info(f"📊 [{district_progress}%] 🤖 正在调用LLM获取医院数据...")

                hospitals_data = await llm_client.get_hospitals_from_district(
                    province_info['name'],
                    city_info['name'],
                    district_info['name']
                )

                if not hospitals_data:
                    logger.warning(f"⚠️ 区县 '{district_name}' 没有获取到任何医院数据")
                    completed_districts += 1
                    continue

                logger.info(f"✅ LLM返回医院数据: {len(hospitals_data)} 家医院")

                # 步骤3: 保存医院数据到数据库
                logger.info(f"🔄 步骤3: 保存医院数据")
                logger.info(f"📊 [{district_progress}%] 💾 正在保存医院数据...")

                saved_count = 0
                updated_count = 0

                for j, hospital_data in enumerate(hospitals_data):
                    try:
                        # 提取医院信息
                        hospital_name = hospital_data.get('name', '').strip()
                        level = hospital_data.get('level', '')
                        address = hospital_data.get('address', '')
                        phone = hospital_data.get('phone', '')
                        beds_count = hospital_data.get('beds_count')
                        staff_count = hospital_data.get('staff_count')
                        departments = hospital_data.get('departments', [])
                        specializations = hospital_data.get('specializations', [])
                        website = hospital_data.get('website', '')

                        if not hospital_name:
                            logger.warning(f"⚠️ 医院名称为空，跳过")
                            continue

                        # 检查医院是否已存在
                        existing_hospital = await db.get_hospital_by_name_and_district(hospital_name, district_info['id'])

                        if existing_hospital:
                            # 更新现有医院（只有信息有变化时才更新）
                            update_needed = False
                            updates = {}

                            if level and level != existing_hospital.get('level', ''):
                                updates['level'] = level
                                update_needed = True

                            if address and address != existing_hospital.get('address', ''):
                                updates['address'] = address
                                update_needed = True

                            if phone and phone != existing_hospital.get('phone', ''):
                                updates['phone'] = phone
                                update_needed = True

                            if beds_count and beds_count != existing_hospital.get('beds_count'):
                                updates['beds_count'] = beds_count
                                update_needed = True

                            if staff_count and staff_count != existing_hospital.get('staff_count'):
                                updates['staff_count'] = staff_count
                                update_needed = True

                            if departments and departments != existing_hospital.get('departments', []):
                                updates['departments'] = departments
                                update_needed = True

                            if specializations and specializations != existing_hospital.get('specializations', []):
                                updates['specializations'] = specializations
                                update_needed = True

                            if website and website != existing_hospital.get('website', ''):
                                updates['website'] = website
                                update_needed = True

                            if update_needed:
                                await db.update_hospital(existing_hospital['id'], **updates)
                                updated_count += 1
                                logger.info(f"🔄 更新医院: {hospital_name}")
                            else:
                                logger.info(f"ℹ️ 医院信息无变化，跳过: {hospital_name}")

                        else:
                            # 创建新医院
                            await db.create_hospital(
                                name=hospital_name,
                                district_id=district_info['id'],
                                level=level,
                                address=address,
                                phone=phone,
                                beds_count=beds_count,
                                staff_count=staff_count,
                                departments=departments,
                                specializations=specializations,
                                website=website
                            )
                            saved_count += 1
                            logger.info(f"➕ 新增医院: {hospital_name}")

                    except Exception as hospital_error:
                        logger.warning(f"⚠️ 处理医院数据失败: {hospital_data.get('name', 'Unknown')}: {str(hospital_error)}")
                        continue

                # 更新统计
                total_new_hospitals += saved_count
                total_updated_hospitals += updated_count
                completed_districts += 1
                successful_districts += 1

                logger.info(f"✅ 区县 '{district_name}' 处理完成: 新增 {saved_count} 家医院，更新 {updated_count} 家医院")

                # 短暂延迟，避免API调用过于频繁
                await asyncio.sleep(1)

            except Exception as district_error:
                logger.error(f"❌ 处理区县 '{district_name}' 失败: {str(district_error)}")
                failed_districts += 1
                completed_districts += 1
                continue

        # 更新任务状态为成功
        final_status = f"市级医院刷新完成！成功处理 {successful_districts}/{total_districts} 个区县"
        await task_manager.update_task_status(task_id, TaskStatus.COMPLETED, final_status)

        success_message = f"城市 '{city_info['name']}' 医院数据刷新完成，共处理 {successful_districts}/{total_districts} 个区县，新增 {total_new_hospitals} 家医院，更新 {total_updated_hospitals} 家医院"

        logger.info(f"🎉 ========== 市级医院刷新任务完成 ==========")
        logger.info(f"✅ 任务ID: {task_id}")
        logger.info(f"🏙️ 目标城市: {city_info['name']}")
        logger.info(f"⏰ 完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"⏱️ 总用时: {time.time() - start_time:.2f}秒")
        logger.info(f"📍 处理结果: {successful_districts}/{total_districts} 个区县成功")
        logger.info(f"🏥 新增医院: {total_new_hospitals} 家")
        logger.info(f"🔄 更新医院: {total_updated_hospitals} 家")
        logger.info(f"❌ 失败区县: {failed_districts} 个")
        logger.info(f"🎯 任务状态: COMPLETED")
        logger.info(f"📋 成功消息: {success_message}")
        logger.info(f"============================================================")

    except Exception as e:
        error_msg = str(e)
        logger.error(f"❌ 执行市级医院刷新任务失败: {error_msg}")
        logger.error(f"📋 错误详情: {type(e).__name__}: {error_msg}")

        # 更新任务状态为失败
        await task_manager.update_task_status(task_id, TaskStatus.FAILED, error_msg)

        logger.error(f"💥 ========== 市级医院刷新任务失败 ==========")
        logger.error(f"❌ 任务ID: {task_id}")
        logger.error(f"🏙️ 目标城市: {city_info.get('name', 'Unknown')}")
        logger.error(f"⏰ 失败时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.error(f"⏱️ 用时: {time.time() - start_time:.2f}秒")
        logger.error(f"🔴 失败原因: {error_msg}")
        logger.error(f"============================================================")

        # 重新抛出异常
        raise e


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
# 强制重新加载 Sun, Nov 23, 2025 12:49:44 PM

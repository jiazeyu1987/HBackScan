#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
医院层级扫查微服务 - 任务管理
"""

import asyncio
import threading
import logging
import uuid
import os
from datetime import datetime
from typing import Dict, Any, Optional, List
from enum import Enum

from db import get_db
from schemas import TaskStatus, TaskType, ScanTaskRequest, ScanResult

logger = logging.getLogger(__name__)

class TaskManager:
    """任务管理器"""
    
    def __init__(self):
        self.tasks: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()
    
    async def create_task(self, request: ScanTaskRequest, custom_task_id: str = None) -> str:
        """创建任务"""
        with self._lock:
            # 使用自定义task_id或生成新的
            task_id = custom_task_id if custom_task_id else str(uuid.uuid4())

            task_data = {
                "task_id": task_id,
                "hospital_name": request.hospital_name,
                "query": request.query,
                "task_type": request.task_type.value if hasattr(request.task_type, 'value') else str(request.task_type),
                "status": TaskStatus.PENDING.value,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "result": None,
                "error_message": None
            }

            # 保存到内存
            self.tasks[task_id] = task_data

            # 保存到数据库
            db = await get_db()
            task_type_str = request.task_type.value if hasattr(request.task_type, 'value') else str(request.task_type)

            db_success = await db.create_task(
                task_id=task_id,
                hospital_name=request.hospital_name,
                query=request.query,
                status=TaskStatus.PENDING.value,
                task_type=task_type_str
            )

            if not db_success:
                # 数据库插入失败，从内存中移除任务
                del self.tasks[task_id]
                logger.error(f"数据库插入失败，任务创建失败: {task_id}")
                raise Exception(f"Failed to create task in database: {task_id}")

            logger.info(f"创建任务成功: {task_id} (type: {task_type_str}, {'自定义ID' if custom_task_id else '自动生成ID'})")
            return task_id
    
    async def update_task_status(self, task_id: str, status: TaskStatus, error_message: Optional[str] = None):
        """更新任务状态"""
        try:
            with self._lock:
                logger.info(f"📝 尝试更新任务状态: {task_id} -> {status.value}")

                # 始终更新数据库，无论任务是否在内存中
                try:
                    db = await get_db()
                    await db.update_task_status(task_id, status.value, error_message)
                    logger.info(f"✅ 数据库中的任务状态已更新: {task_id} -> {status.value}")
                except Exception as db_error:
                    logger.error(f"❌ 更新数据库任务状态失败: {db_error}")
                    # 数据库更新失败是严重错误，需要抛出
                    raise

                # 更新内存中的任务状态（如果存在）
                if task_id in self.tasks:
                    self.tasks[task_id]["status"] = status.value
                    self.tasks[task_id]["updated_at"] = datetime.now().isoformat()

                    if error_message:
                        self.tasks[task_id]["error_message"] = error_message

                    logger.info(f"✅ 内存中的任务状态已更新: {task_id} -> {status.value}")

                    # 判断是否为全国扫描任务，如果是则不自动删除（保留历史记录）
                    should_preserve_task = False
                    if status in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
                        task_type = self.tasks[task_id].get("task_type", "")
                        task_hospital_name = self.tasks[task_id].get("hospital_name", "")

                        # 优先使用task_type字段，兼容旧数据
                        if task_type == TaskType.NATIONWIDE.value or "全国扫描" in task_hospital_name:
                            should_preserve_task = True
                            logger.info(f"🏛️ 检测到全国扫描任务，将保留历史记录: {task_id} (type: {task_type or 'legacy'})")

                    # 如果任务已完成或失败，且不是全国扫描任务，则自动清理
                    if status in [TaskStatus.COMPLETED, TaskStatus.FAILED] and not should_preserve_task:
                        logger.info(f"🗑️ 任务已{status.value}，准备自动清理: {task_id}")
                        try:
                            delete_success = await db.delete_completed_task(task_id)
                            if delete_success:
                                logger.info(f"✅ 已自动删除完成的任务记录: {task_id}")

                                # 同时从内存中清理已完成任务，避免内存累积
                                if task_id in self.tasks:
                                    del self.tasks[task_id]
                                    logger.info(f"✅ 已从内存中清理完成的任务: {task_id}")
                            else:
                                logger.warning(f"⚠️ 自动删除任务记录失败: {task_id}")
                        except Exception as delete_error:
                            logger.error(f"❌ 自动删除任务记录时发生异常: {delete_error}")
                            # 删除失败不影响主流程
                else:
                    logger.warning(f"⚠️ 任务不存在于内存中，但数据库状态已更新: {task_id}")
                    logger.info(f"📋 当前内存中的任务列表: {list(self.tasks.keys())}")

                    # 对于不在内存中的任务，如果状态为完成/失败，也需要检查是否要删除
                    if status in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
                        # 查询数据库中的任务信息以判断是否为全国任务
                        try:
                            db = await get_db()
                            db_tasks = await db.list_tasks(1000)  # 获取足够多的任务
                            target_task = next((t for t in db_tasks if t.get("task_id") == task_id), None)

                            if target_task:
                                task_type = target_task.get("task_type", "")
                                task_hospital_name = target_task.get("hospital_name", "")

                                # 优先使用task_type字段，兼容旧数据
                                if task_type == TaskType.NATIONWIDE.value or "全国扫描" in task_hospital_name:
                                    logger.info(f"🏛️ 数据库中的全国扫描任务，将保留历史记录: {task_id} (type: {task_type or 'legacy'})")
                                else:
                                    # 非全国任务，可以删除（如果还没被delete_completed_task处理）
                                    logger.info(f"🗑️ 非全国任务已{status.value}，可清理: {task_id}")
                            else:
                                logger.warning(f"⚠️ 数据库中也未找到任务记录: {task_id}")
                        except Exception as query_error:
                            logger.warning(f"⚠️ 查询数据库任务信息失败: {query_error}")

                logger.info(f"🎉 任务状态更新完成: {task_id} -> {status.value}")

        except Exception as e:
            logger.error(f"❌ 更新任务状态时发生异常: {e}")
            logger.error(f"📋 异常详情: task_id={task_id}, status={status}, error_message={error_message}")
            raise
    
    async def save_task_result(self, task_id: str, result: ScanResult):
        """保存任务结果"""
        with self._lock:
            if task_id in self.tasks:
                self.tasks[task_id]["result"] = result.dict()
                self.tasks[task_id]["updated_at"] = datetime.now().isoformat()
                
                # 保存到数据库
                db = await get_db()
                await db.save_task_result(task_id, result.dict())
                
                # 保存医院详细信息
                if result.hospital_info:
                    await db.save_hospital_info(task_id, result.hospital_info.dict())
                
                logger.info(f"保存任务结果: {task_id}")
            else:
                logger.warning(f"任务不存在: {task_id}")
    
    async def get_task_result(self, task_id: str) -> Optional[ScanResult]:
        """获取任务结果"""
        # 先从内存查找
        if task_id in self.tasks:
            task_data = self.tasks[task_id]
            if task_data["result"]:
                try:
                    return ScanResult(**task_data["result"])
                except Exception as e:
                    logger.error(f"解析任务结果失败: {e}")
        
        # 从数据库查找
        db = await get_db()
        result_data = await db.get_task_result(task_id)
        
        if result_data:
            try:
                return ScanResult(**result_data)
            except Exception as e:
                logger.error(f"解析数据库任务结果失败: {e}")
        
        return None
    
    async def get_task_status(self, task_id: str) -> Optional[TaskStatus]:
        """获取任务状态"""
        # 先从内存查找
        if task_id in self.tasks:
            status_str = self.tasks[task_id]["status"]
            try:
                return TaskStatus(status_str)
            except ValueError:
                logger.error(f"无效的任务状态: {status_str}")
        
        # 从数据库查找
        db = await get_db()
        task_data = await db.get_task(task_id)
        
        if task_data:
            status_str = task_data.get("status", "")
            try:
                return TaskStatus(status_str)
            except ValueError:
                logger.error(f"无效的任务状态: {status_str}")
        
        return None
    
    async def list_tasks(self, limit: int = 100) -> List[Dict[str, Any]]:
        """获取任务列表"""
        # 从数据库获取任务列表
        db = await get_db()
        tasks = await db.list_tasks(limit)
        
        # 更新内存中的任务状态
        for task in tasks:
            task_id = task.get("task_id")
            if task_id and task_id not in self.tasks:
                self.tasks[task_id] = task
        
        return tasks
    
    async def delete_task(self, task_id: str) -> bool:
        """删除任务"""
        with self._lock:
            if task_id in self.tasks:
                del self.tasks[task_id]
                
                # TODO: 从数据库删除（如果需要）
                
                logger.info(f"删除任务: {task_id}")
                return True
            else:
                logger.warning(f"任务不存在: {task_id}")
                return False
    
    async def cleanup_completed_tasks(self, older_than_hours: int = 24) -> int:
        """清理已完成的任务"""
        cutoff_time = datetime.now().timestamp() - (older_than_hours * 3600)
        cleaned_count = 0
        
        with self._lock:
            completed_statuses = [
                TaskStatus.COMPLETED.value,
                TaskStatus.FAILED.value
            ]
            
            tasks_to_remove = []
            for task_id, task_data in self.tasks.items():
                created_at = datetime.fromisoformat(task_data["created_at"])
                if (created_at.timestamp() < cutoff_time and 
                    task_data["status"] in completed_statuses):
                    tasks_to_remove.append(task_id)
            
            for task_id in tasks_to_remove:
                del self.tasks[task_id]
                cleaned_count += 1
        
        logger.info(f"清理完成的任务: {cleaned_count}个")
        return cleaned_count
    
    async def get_active_tasks(self) -> List[Dict[str, Any]]:
        """获取当前活动的任务（运行中和等待中的任务）"""
        active_statuses = [TaskStatus.PENDING.value, TaskStatus.RUNNING.value]
        active_tasks = []

        # 从内存中获取活动任务
        memory_tasks = []
        for task_data in self.tasks.values():
            if task_data.get("status") in active_statuses:
                # 转换为字典对象，包含所有必要字段
                memory_tasks.append({
                    "task_id": task_data["task_id"],
                    "hospital_name": task_data["hospital_name"],
                    "status": task_data["status"],
                    "created_at": task_data["created_at"],
                    "updated_at": task_data["updated_at"],
                    "task_type": task_data.get("task_type", "hospital"),
                    "error_message": task_data.get("error_message")
                })

        # 总是从数据库获取最新的活动任务，确保数据的完整性和一致性
        try:
            db = await get_db()
            db_tasks = await db.list_tasks(1000)  # 获取最近1000个任务
            db_active_tasks = []
            for task in db_tasks:
                if task.get("status") in active_statuses:
                    db_active_tasks.append({
                        "task_id": task.get("task_id"),
                        "hospital_name": task.get("hospital_name"),
                        "status": task.get("status"),
                        "created_at": task.get("created_at"),
                        "updated_at": task.get("updated_at"),
                        "task_type": task.get("task_type", "hospital"),
                        "error_message": task.get("error_message")
                    })

            # 合并内存和数据库的任务，去重以task_id为准
            seen_task_ids = set()
            for task in memory_tasks:
                task_id = task.get("task_id")
                if task_id and task_id not in seen_task_ids:
                    active_tasks.append(task)
                    seen_task_ids.add(task_id)

            for task in db_active_tasks:
                task_id = task.get("task_id")
                if task_id and task_id not in seen_task_ids:
                    active_tasks.append(task)
                    seen_task_ids.add(task_id)

            logger.info(f"获取活动任务: 内存任务={len(memory_tasks)}, 数据库任务={len(db_active_tasks)}, 合并后={len(active_tasks)}")

        except Exception as e:
            logger.error(f"从数据库获取活动任务失败: {e}")
            # 如果数据库查询失败，只返回内存中的任务
            active_tasks = memory_tasks

        return active_tasks

    async def get_statistics(self) -> Dict[str, Any]:
        """获取任务统计信息"""
        stats = {
            "total_tasks": len(self.tasks),
            "pending_tasks": 0,
            "running_tasks": 0,
            "completed_tasks": 0,
            "failed_tasks": 0,
            "recent_tasks": []
        }

        for task_data in self.tasks.values():
            status = task_data.get("status", "")

            if status == TaskStatus.PENDING.value:
                stats["pending_tasks"] += 1
            elif status == TaskStatus.RUNNING.value:
                stats["running_tasks"] += 1
            elif status == TaskStatus.COMPLETED.value:
                stats["completed_tasks"] += 1
            elif status == TaskStatus.FAILED.value:
                stats["failed_tasks"] += 1

        # 获取最近的任务
        recent_tasks = sorted(
            self.tasks.values(),
            key=lambda x: x.get("created_at", ""),
            reverse=True
        )[:10]

        stats["recent_tasks"] = recent_tasks

        return stats


async def refresh_district_hospitals_internal(district_name: str, task_manager: TaskManager) -> dict:
    """
    内部区县医院刷新函数，直接调用业务逻辑而不通过HTTP

    Args:
        district_name: 区县名称
        task_manager: 任务管理器实例

    Returns:
        dict: 包含处理结果的字典
    """
    import time
    from datetime import datetime

    start_time = time.time()
    result = {
        "success": False,
        "saved_count": 0,
        "updated_count": 0,
        "error_message": None,
        "execution_time": 0
    }

    try:
        logger.info(f"🔄 [内部函数] 开始刷新区县医院数据: {district_name}")

        # 验证区县名称
        if not district_name or not district_name.strip():
            result["error_message"] = "区县名称为空或无效"
            logger.error(f"❌ {result['error_message']}")
            return result

        district_name_clean = district_name.strip()
        logger.info(f"✅ [内部函数] 标准化区县名称: '{district_name_clean}'")

        # 准备执行环境
        from llm_client import LLMClient
        llm_client = LLMClient()

        db = await get_db()

        # 查找区县信息
        district_info = await db.get_district_by_name(district_name_clean)
        if not district_info:
            result["error_message"] = f"区县 '{district_name_clean}' 不存在"
            logger.error(f"❌ {result['error_message']}")
            return result

        logger.info(f"✅ [内部函数] 找到区县: {district_info['name']}, ID: {district_info['id']}")

        # 获取城市和省份信息
        city_info = await db.get_city_by_id(district_info['city_id'])
        province_info = await db.get_province_by_id(city_info['province_id'])
        logger.info(f"📍 [内部函数] 完整层级: {province_info['name']} -> {city_info['name']} -> {district_info['name']}")

        # 调用LLM获取医院数据
        logger.info(f"🤖 [内部函数] 正在调用LLM获取医院数据...")
        hospitals_data = await llm_client.get_hospitals_from_district(
            province_info['name'],
            city_info['name'],
            district_info['name']
        )
        logger.info(f"✅ [内部函数] LLM返回医院数据: {len(hospitals_data)} 家医院")

        # 保存医院数据
        saved_count = 0
        updated_count = 0

        for i, hospital_data in enumerate(hospitals_data):
            try:
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
                    logger.warning(f"⚠️ [内部函数] 医院名称为空，跳过")
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
                    logger.info(f"✅ [内部函数] 已更新医院: {hospital_name}")
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
                    logger.info(f"✅ [内部函数] 已保存医院: {hospital_name}")

            except Exception as hospital_error:
                logger.error(f"❌ [内部函数] 保存医院失败: {hospital_data.get('name', 'Unknown')}, 错误: {str(hospital_error)}")
                continue

        result["success"] = True
        result["saved_count"] = saved_count
        result["updated_count"] = updated_count
        result["execution_time"] = time.time() - start_time

        logger.info(f"🎉 [内部函数] 区县医院刷新完成 - 新增: {saved_count}, 更新: {updated_count}, 耗时: {result['execution_time']:.2f}秒")

    except Exception as e:
        result["error_message"] = str(e)
        result["execution_time"] = time.time() - start_time
        logger.error(f"❌ [内部函数] 区县医院刷新失败: {e}")
        logger.error(f"📋 [内部函数] 异常类型: {type(e).__name__}")
        import traceback
        logger.error(f"📋 [内部函数] 完整堆栈: {traceback.format_exc()}")

    return result


async def refresh_district_hospitals_with_semaphore(district_name: str, task_manager: TaskManager, semaphore: asyncio.Semaphore) -> dict:
    """
    带并发控制的区县医院刷新函数

    Args:
        district_name: 区县名称
        task_manager: 任务管理器实例
        semaphore: 并发控制信号量

    Returns:
        dict: 包含处理结果的字典
    """
    async with semaphore:
        logger.info(f"🔒 [并发控制] 获取信号量成功，开始刷新区县: {district_name}")
        try:
            result = await refresh_district_hospitals_internal(district_name, task_manager)
            if result["success"]:
                logger.info(f"🔓 [并发控制] 区县刷新成功，释放信号量: {district_name}")
            else:
                logger.info(f"🔓 [并发控制] 区县刷新失败，释放信号量: {district_name}")
            return result
        except Exception as e:
            logger.error(f"🔓 [并发控制] 区县刷新异常，释放信号量: {district_name}, 错误: {e}")
            return {
                "success": False,
                "error_message": str(e),
                "saved_count": 0,
                "updated_count": 0,
                "execution_time": 0
            }


async def execute_province_cities_districts_refresh_task(task_id: str, province_name: str, task_manager: TaskManager):
    try:
        logger.info(f"🎉 ========== 开始执行省份城市区县级联刷新任务 ==========")
        logger.info(f"📋 任务参数: task_id={task_id}, province_name={province_name}")
        logger.info(f"📋 接收到的TaskManager实例: {type(task_manager)}, 内存任务数: {len(task_manager.tasks)}")

        # 获取数据库连接
        logger.info(f"🔄 正在获取数据库连接...")
        db = await get_db()
        logger.info(f"✅ 数据库连接成功")

        # 并发控制：限制同时进行的区县医院刷新数量，避免打爆LLM API和数据库
        # 使用环境变量配置，默认为3个并发
        logger.info(f"🔄 正在配置并发控制...")
        import os
        max_concurrent_district_refreshes = int(os.getenv("MAX_CONCURRENT_DISTRICT_REFRESHES", "3"))
        district_semaphore = asyncio.Semaphore(max_concurrent_district_refreshes)
        logger.info(f"✅ 并发控制配置完成: 最大同时刷新区县数 = {max_concurrent_district_refreshes}")

        # 统计变量
        total_cities = 0
        processed_cities = 0
        total_districts_created = 0
        total_districts_skipped = 0
        total_hospital_refreshes_success = 0
        total_hospital_refreshes_failed = 0
        province_id = None
        # ===== 阶段1: 省份数据准备和城市数据获取 =====
        await task_manager.update_task_status(task_id, TaskStatus.RUNNING, f"开始获取省份 {province_name} 的城市数据...")
        logger.info(f"🔄 阶段1: 省份数据准备和城市数据获取")

        # 1.1 检查/创建省份记录
        await task_manager.update_task_status(task_id, TaskStatus.RUNNING, f"检查/创建省份记录: {province_name}")
        existing_province = await db.get_province_by_name(province_name)
        if existing_province:
            province_id = existing_province['id']
            logger.info(f"✅ 省份已存在: {province_name}, ID: {province_id}")
        else:
            province_id = await db.create_province(province_name)
            logger.info(f"✅ 创建新省份: {province_name}, ID: {province_id}")

        # 1.2 获取城市数据
        from llm_client import LLMClient
        llm_client = LLMClient()

        logger.info(f"🔄 正在获取省份 {province_name} 的城市数据...")
        cities_data = await llm_client.get_cities_by_province(province_name)
        cities_list = cities_data.get('cities', [])
        total_cities = len(cities_list)
        logger.info(f"✅ 成功获取城市数据: {total_cities} 个城市")
        logger.info(f"📋 城市列表: {cities_list}")

        # 1.3 批量存储城市数据到数据库
        await task_manager.update_task_status(task_id, TaskStatus.RUNNING, f"批量存储 {total_cities} 个城市到数据库...")
        logger.info(f"🔄 阶段1.3: 批量存储城市数据到数据库")

        cities_created = 0
        cities_skipped = 0

        for city_name in cities_list:
            try:
                existing_city = await db.get_city_by_name(city_name)
                if existing_city:
                    logger.info(f"⏭️ 城市已存在，跳过创建: {city_name}, ID: {existing_city['id']}")
                    cities_skipped += 1
                else:
                    city_id = await db.create_city(city_name, province_id)
                    logger.info(f"✅ 创建新城市: {city_name}, ID: {city_id}")
                    cities_created += 1
            except Exception as city_error:
                logger.error(f"❌ 处理城市 {city_name} 时出错: {city_error}")
                continue

        logger.info(f"📊 阶段1完成: 创建 {cities_created} 个城市，跳过 {cities_skipped} 个城市")

        # ===== 阶段2: 从数据库读取城市列表，串行处理每个城市 =====
        await task_manager.update_task_status(task_id, TaskStatus.RUNNING, f"开始串行处理城市数据...")
        logger.info(f"🔄 阶段2: 串行处理城市数据（从数据库读取）")

        # 2.1 从数据库获取该省的所有城市
        cities_data_from_db, total = await db.get_cities(province_id=province_id, page=1, page_size=1000)
        cities_from_db = cities_data_from_db
        logger.info(f"✅ 从数据库读取到 {len(cities_from_db)} 个城市")

        # 2.2 串行处理每个城市
        for city_index, city_data in enumerate(cities_from_db, 1):
            try:
                city_name = city_data['name']
                city_id = city_data['id']

                processed_cities += 1
                progress_msg = f"处理城市 {city_name} ({city_index}/{len(cities_from_db)})"
                await task_manager.update_task_status(task_id, TaskStatus.RUNNING, progress_msg)

                logger.info(f"🏙️ 开始处理城市 {city_index}/{len(cities_from_db)}: {city_name} (ID: {city_id})")

                # 2.2.1 获取城市的区县数据
                logger.info(f"🔄 获取城市 {city_name} 的区县数据...")
                districts_data = await llm_client.get_districts_by_city(city_name)
                districts_list = districts_data.get('items', [])
                logger.info(f"✅ 成功获取 {city_name} 的区县数据: {len(districts_list)} 个区县")

                # 2.2.2 存储区县数据
                districts_created = 0
                districts_skipped = 0
                stored_districts = []
                all_districts = []

                for district_item in districts_list:
                    try:
                        district_name = district_item.get('name') if isinstance(district_item, dict) else district_item

                        # 添加所有区县到 all_districts 列表（无论新旧）
                        all_districts.append(district_name)

                        # 使用精确查询：检查该城市下是否已存在同名区县
                        existing_district = await db.get_district_by_name_and_city(district_name, city_id)
                        if existing_district:
                            logger.info(f"⏭️ 区县已存在（城市 {city_id}），跳过: {district_name}")
                            districts_skipped += 1
                        else:
                            # 如果精确查询没找到，检查全局是否有同名区县（记录潜在冲突）
                            global_district = await db.get_district_by_name(district_name)
                            if global_district:
                                logger.warning(f"⚠️ 发现跨城市同名区县冲突: '{district_name}' 已存在于城市 {global_district.get('city_id')}，当前城市: {city_id}")
                                logger.info(f"🔄 将在新城市 {city_id} 中创建区县: {district_name}")

                            district_id = await db.create_district(district_name, city_id)
                            logger.info(f"✅ 创建新区县: {district_name}, 城市ID: {city_id}")
                            districts_created += 1
                            stored_districts.append(district_name)
                    except Exception as district_error:
                        logger.error(f"❌ 处理区县 {district_name} 时出错: {district_error}")
                        continue

                total_districts_created += districts_created
                total_districts_skipped += districts_skipped

                logger.info(f"📊 城市 {city_name} 区县数据完成: 创建 {districts_created} 个区县，跳过 {districts_skipped} 个区县")

                # 2.2.3 并发刷新每个区县的医院数据（使用内部函数调用 + 并发控制）
                logger.info(f"🔄 [并发模式] 开始并发刷新 {city_name} 下所有区县的医院数据...")
                logger.info(f"📊 {city_name} 下共有 {len(all_districts)} 个区县，最大并发数: {max_concurrent_district_refreshes}")

                # 创建并发任务列表
                hospital_tasks = []
                for district_name in all_districts:
                    task = refresh_district_hospitals_with_semaphore(district_name, task_manager, district_semaphore)
                    hospital_tasks.append((district_name, task))

                # 执行并发任务，并实时更新统计
                logger.info(f"🚀 [并发模式] 开始执行 {len(hospital_tasks)} 个区县并发刷新任务...")

                completed_count = 0
                for district_name, task in hospital_tasks:
                    try:
                        # 等待单个任务完成
                        hospital_result = await task
                        completed_count += 1

                        # 更新任务状态
                        hospital_refresh_msg = f"刷新区县 {district_name} 医院数据 ({completed_count}/{len(all_districts)})"
                        await task_manager.update_task_status(task_id, TaskStatus.RUNNING, hospital_refresh_msg)

                        if hospital_result["success"]:
                            logger.info(f"✅ [并发模式] 区县 {district_name} 医院数据刷新成功 - 新增: {hospital_result['saved_count']}, 更新: {hospital_result['updated_count']}, 耗时: {hospital_result['execution_time']:.2f}秒")
                            total_hospital_refreshes_success += 1
                        else:
                            logger.error(f"❌ [并发模式] 区县 {district_name} 医院数据刷新失败: {hospital_result['error_message']}")
                            total_hospital_refreshes_failed += 1

                    except Exception as hospital_error:
                        completed_count += 1
                        logger.error(f"❌ [并发模式] 刷新区县 {district_name} 医院数据失败: {hospital_error}")
                        logger.error(f"📋 异常类型: {type(hospital_error).__name__}")
                        import traceback
                        logger.error(f"📋 完整堆栈: {traceback.format_exc()}")
                        total_hospital_refreshes_failed += 1

                logger.info(f"🎉 [并发模式] 城市 {city_name} 所有区县医院刷新完成 - 成功: {total_hospital_refreshes_success}, 失败: {total_hospital_refreshes_failed}")

                logger.info(f"🎉 城市 {city_name} 完整处理完成")

            except Exception as city_error:
                logger.error(f"❌ 处理城市 {city_name} 时出错: {city_error}")
                continue

        # ===== 任务完成统计 =====
        final_msg = f"级联刷新完成: {province_name} - 处理 {processed_cities} 个城市，创建 {total_districts_created} 个区县，跳过 {total_districts_skipped} 个区县，医院刷新成功 {total_hospital_refreshes_success} 个区县，失败 {total_hospital_refreshes_failed} 个区县"
        await task_manager.update_task_status(task_id, TaskStatus.COMPLETED, final_msg)

        logger.info(f"🎉 ========== 省份城市区县级联刷新任务完成 ==========")
        logger.info(f"📊 最终统计:")
        logger.info(f"   - 处理城市数量: {processed_cities}/{total_cities}")
        logger.info(f"   - 创建区县数量: {total_districts_created}")
        logger.info(f"   - 跳过区县数量: {total_districts_skipped}")
        logger.info(f"   - 医院刷新成功: {total_hospital_refreshes_success} 个区县")
        logger.info(f"   - 医院刷新失败: {total_hospital_refreshes_failed} 个区县")
        logger.info(f"   - 省份: {province_name} (ID: {province_id})")

    except Exception as e:
        error_message = f"省份城市区县级联刷新失败: {str(e)}"
        logger.error(f"❌ {error_message}")
        logger.error(f"📋 异常类型: {type(e).__name__}")
        import traceback
        logger.error(f"📋 完整堆栈: {traceback.format_exc()}")

        try:
            await task_manager.update_task_status(task_id, TaskStatus.FAILED, error_message)
        except Exception as update_error:
            logger.error(f"❌ 更新任务状态失败: {update_error}")

        raise


async def get_all_provinces_from_llm() -> List[str]:
    """
    从LLM获取全国所有省份数据

    Returns:
        List[str]: 省份名称列表

    Raises:
        Exception: 当LLM调用失败或返回数据无效时
    """
    try:
        logger.info("🌍 开始从LLM获取全国省份数据...")

        from llm_client import LLMClient
        llm_client = LLMClient()

        # 构建获取省份的提示词
        province_prompt = """
请返回中国的所有省级行政区划，包括省份、自治区、直辖市和特别行政区。

要求：
1. 返回JSON格式
2. 包含完整的中文名称
3. 按照标准的行政区划代码排序

格式示例：
{
  "items": [
    {"name": "北京市", "code": "110000"},
    {"name": "天津市", "code": "120000"},
    {"name": "河北省", "code": "130000"},
    {"name": "山西省", "code": "140000"},
    {"name": "内蒙古自治区", "code": "150000"},
    {"name": "辽宁省", "code": "210000"},
    {"name": "吉林省", "code": "220000"},
    {"name": "黑龙江省", "code": "230000"},
    {"name": "上海市", "code": "310000"},
    {"name": "江苏省", "code": "320000"},
    {"name": "浙江省", "code": "330000"},
    {"name": "安徽省", "code": "340000"},
    {"name": "福建省", "code": "350000"},
    {"name": "江西省", "code": "360000"},
    {"name": "山东省", "code": "370000"},
    {"name": "河南省", "code": "410000"},
    {"name": "湖北省", "code": "420000"},
    {"name": "湖南省", "code": "430000"},
    {"name": "广东省", "code": "440000"},
    {"name": "广西壮族自治区", "code": "450000"},
    {"name": "海南省", "code": "460000"},
    {"name": "重庆市", "code": "500000"},
    {"name": "四川省", "code": "510000"},
    {"name": "贵州省", "code": "520000"},
    {"name": "云南省", "code": "530000"},
    {"name": "西藏自治区", "code": "540000"},
    {"name": "陕西省", "code": "610000"},
    {"name": "甘肃省", "code": "620000"},
    {"name": "青海省", "code": "630000"},
    {"name": "宁夏回族自治区", "code": "640000"},
    {"name": "新疆维吾尔自治区", "code": "650000"},
    {"name": "香港特别行政区", "code": "810000"},
    {"name": "澳门特别行政区", "code": "820000"}
  ]
}
"""

        province_messages = [
            {"role": "system", "content": "你是一个专业的地理信息系统数据助手，专门处理中国行政区划数据。"},
            {"role": "user", "content": province_prompt}
        ]

        logger.info("📤 发送省份查询请求到LLM...")
        province_response = llm_client._make_request(province_messages, max_tokens=2000)

        if not province_response:
            raise Exception("LLM返回空响应，无法获取省份数据")

        logger.info("✅ 成功获取省份响应，开始解析...")
        logger.info(f"📄 响应长度: {len(province_response)} 字符")

        # 解析JSON响应
        import json
        try:
            # 清理响应文本
            cleaned_response = province_response.strip()
            if cleaned_response.startswith('```json'):
                cleaned_response = cleaned_response[7:]
            if cleaned_response.startswith('```'):
                cleaned_response = cleaned_response[3:]
            if cleaned_response.endswith('```'):
                cleaned_response = cleaned_response[:-3]
            cleaned_response = cleaned_response.strip()

            # 提取JSON部分
            json_start = cleaned_response.find('{')
            json_end = cleaned_response.rfind('}') + 1

            if json_start == -1 or json_end == -1:
                raise ValueError(f"响应中未找到有效的JSON格式！原始响应: {cleaned_response[:500]}...")

            json_str = cleaned_response[json_start:json_end]
            province_data = json.loads(json_str)

            provinces = province_data.get('items', [])
            if not provinces:
                raise ValueError("返回数据中没有找到省份列表")

            # 提取省份名称
            province_names = []
            for item in provinces:
                if isinstance(item, dict):
                    name = item.get('name', '').strip()
                else:
                    name = str(item).strip()

                if name:
                    province_names.append(name)

            # 去重处理，防止LLM返回重复省份
            original_count = len(province_names)
            province_names = list(dict.fromkeys(province_names))  # 保持顺序的去重
            deduplicated_count = len(province_names)

            if deduplicated_count < original_count:
                logger.info(f"🔄 省份去重: {original_count} -> {deduplicated_count} 个省份 (移除 {original_count - deduplicated_count} 个重复)")

            logger.info(f"🌍 成功解析省份数据: {len(province_names)} 个省级行政区")

            # 验证是否至少有一个有效省份
            if len(province_names) == 0:
                logger.warning("⚠️ LLM返回的省份数据解析成功，但没有有效的省份名称")
                logger.warning(f"📋 原始数据项数: {len(provinces)}")
                logger.warning(f"📋 原始数据示例: {provinces[:3] if provinces else 'None'}")
            else:
                # 显示前10个省份作为验证
                for i, province in enumerate(province_names[:10]):
                    logger.info(f"📍 省份{i+1}: {province}")
                if len(province_names) > 10:
                    logger.info(f"📍 ... 还有 {len(province_names) - 10} 个省份")

            return province_names

        except json.JSONDecodeError as je:
            logger.warning(f"⚠️ JSON解析失败，尝试文本解析: {je}")
            # 如果JSON解析失败，尝试简单的文本提取
            lines = province_response.split('\n')
            provinces = []
            for line in lines:
                line = line.strip()
                if ('省' in line or '市' in line or '区' in line or '自治' in line) and not line.startswith('#'):
                    # 简单的省份名称提取
                    import re
                    match = re.search(r'[\u4e00-\u9fa5]+[省市自治区特别行政区]', line)
                    if match:
                        province_name = match.group()
                        if province_name not in provinces:
                            provinces.append(province_name)

            logger.info(f"🌍 通过文本解析获得 {len(provinces)} 个省份")
            return provinces

    except Exception as e:
        logger.error(f"❌ 获取省份数据失败: {str(e)}")
        logger.error(f"📋 异常类型: {type(e).__name__}")
        import traceback
        logger.error(f"📋 完整堆栈: {traceback.format_exc()}")
        raise Exception(f"无法从LLM获取省份数据: {str(e)}")


async def execute_all_provinces_cascade_refresh(task_id: str, task_manager: TaskManager):
    """
    执行全国所有省份的级联刷新任务

    Args:
        task_id: 任务ID
        task_manager: 任务管理器实例

    该函数会：
    1. 从LLM获取所有省份列表
    2. 串行处理每个省份（避免过度并发）
    3. 对每个省份执行完整的级联刷新
    4. 提供详细的进度跟踪和错误处理
    """
    import time
    import asyncio
    from datetime import datetime

    start_time = time.time()
    total_provinces = 0
    successful_provinces = 0
    failed_provinces = 0

    try:
        logger.info("🌍 ========== 开始执行全国扫描任务 ==========")
        logger.info(f"📋 任务ID: {task_id}")
        logger.info(f"⏰ 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # 阶段1: 获取所有省份列表
        logger.info("🔄 阶段1: 获取全国所有省份列表")
        await task_manager.update_task_status(task_id, TaskStatus.RUNNING, "正在获取全国所有省份列表...")

        try:
            provinces = await get_all_provinces_from_llm()
            total_provinces = len(provinces)

            # Check if LLM returned empty provinces list
            if total_provinces == 0:
                error_msg = "LLM返回的省份列表为空，无法执行全国扫描"
                logger.error(f"❌ {error_msg}")
                await task_manager.update_task_status(task_id, TaskStatus.FAILED, error_msg)
                return

            logger.info(f"✅ 成功获取省份列表: {total_provinces} 个省份")
            await task_manager.update_task_status(task_id, TaskStatus.RUNNING, f"成功获取 {total_provinces} 个省份，开始级联刷新...")
        except Exception as e:
            error_msg = f"获取省份列表失败: {str(e)}"
            logger.error(f"❌ {error_msg}")
            await task_manager.update_task_status(task_id, TaskStatus.FAILED, error_msg)
            return

        # 阶段2: 串行处理每个省份的级联刷新
        logger.info("🔄 阶段2: 开始串行处理所有省份的级联刷新")

        for i, province_name in enumerate(provinces, 1):
            province_start_time = time.time()

            try:
                logger.info(f"🌍 [省份 {i}/{total_provinces}] 开始处理: {province_name}")
                progress_msg = f"正在处理省份 {province_name} ({i}/{total_provinces})"
                await task_manager.update_task_status(task_id, TaskStatus.RUNNING, progress_msg)

                # 创建真实的省级子任务记录，便于状态跟踪
                province_task_id = f"{task_id}_province_{i}"

                try:
                    # 验证省份名称参数
                    if not province_name or province_name.strip() == "":
                        error_msg = f"省份名称为空，跳过处理 [省份 {i}/{total_provinces}]"
                        logger.warning(f"⚠️ {error_msg}")
                        failed_provinces += 1
                        continue

                    # 创建省级子任务记录
                    province_task_request = ScanTaskRequest(
                        hospital_name=f"省级级联刷新 - {province_name}",
                        query=f"级联刷新省份 {province_name} 的所有城市、区县和医院数据",
                        task_type=TaskType.PROVINCE
                    )

                    # 通过TaskManager创建子任务，确保在内存和数据库中都有记录
                    await task_manager.create_task(province_task_request, province_task_id)
                    logger.info(f"📋 创建省级子任务: {province_task_id} - {province_name}")

                    # 更新子任务状态为运行中
                    await task_manager.update_task_status(province_task_id, TaskStatus.RUNNING, f"开始处理 {province_name} 的级联刷新...")

                    # 调用省份级联刷新函数
                    await execute_province_cities_districts_refresh_task(province_task_id, province_name, task_manager)

                except Exception as task_init_error:
                    # 处理任务初始化阶段的异常
                    error_msg = f"省级任务初始化失败: {str(task_init_error)}"
                    logger.error(f"❌ [省份 {i}/{total_provinces}] {province_name} - {error_msg}")
                    logger.error(f"⏱️ 初始化失败前用时: {time.time() - province_start_time:.2f}秒")
                    failed_provinces += 1

                    # 如果子任务已创建，更新失败状态
                    if 'province_task_id' in locals():
                        try:
                            await task_manager.update_task_status(province_task_id, TaskStatus.FAILED, error_msg)
                        except Exception as status_update_error:
                            logger.error(f"❌ 更新子任务失败状态时出错: {status_update_error}")

                    # 记录详细错误信息用于调试
                    import traceback
                    logger.error(f"❌ 省份任务初始化异常详情: {traceback.format_exc()}")
                    continue

                # 省级任务处理成功的情况
                province_time = time.time() - province_start_time
                logger.info(f"✅ [省份 {i}/{total_provinces}] {province_name} 处理成功 - 耗时: {province_time:.2f}秒")
                successful_provinces += 1

                # 标记子任务完成，但不删除（保留用于历史查询）
                await task_manager.update_task_status(province_task_id, TaskStatus.COMPLETED, f"{province_name} 级联刷新完成")

                # 省份间短暂休息，避免API限流
                await asyncio.sleep(2)

            except Exception as province_refresh_error:
                # 处理省份级联刷新阶段的异常（不包括初始化）
                province_time = time.time() - province_start_time
                logger.error(f"❌ [省份 {i}/{total_provinces}] {province_name} 级联刷新失败: {province_refresh_error}")
                logger.error(f"⏱️ 失败前用时: {province_time:.2f}秒")
                failed_provinces += 1

                # 如果子任务已创建，更新失败状态
                try:
                    error_msg = f"{province_name} 级联刷新失败: {str(province_refresh_error)}"
                    await task_manager.update_task_status(province_task_id, TaskStatus.FAILED, error_msg)
                except Exception as status_update_error:
                    logger.warning(f"⚠️ 无法更新子任务 {province_task_id} 状态: {status_update_error}")

                # 继续处理下一个省份
                continue

            # 显示当前进度
            current_progress = int((i / total_provinces) * 100)
            logger.info(f"📊 全国扫描进度: {i}/{total_provinces} ({current_progress}%) - 成功: {successful_provinces}, 失败: {failed_provinces}")

        # 阶段3: 任务完成总结
        total_time = time.time() - start_time
        success_rate = int((successful_provinces / total_provinces) * 100) if total_provinces > 0 else 0

        final_msg = f"全国扫描完成！成功处理 {successful_provinces}/{total_provinces} 个省份 (成功率: {success_rate}%)，失败 {failed_provinces} 个省份"
        await task_manager.update_task_status(task_id, TaskStatus.COMPLETED, final_msg)

        logger.info("🎉 ========== 全国扫描任务完成 ==========")
        logger.info(f"📊 最终统计:")
        logger.info(f"   - 总省份数: {total_provinces}")
        logger.info(f"   - 成功处理: {successful_provinces}")
        logger.info(f"   - 失败处理: {failed_provinces}")
        logger.info(f"   - 成功率: {success_rate}%")
        logger.info(f"   - 总用时: {total_time:.2f}秒")
        logger.info(f"   - 平均每省用时: {total_time/total_provinces:.2f}秒" if total_provinces > 0 else "   - 平均每省用时: N/A")
        logger.info(f"🚀 任务状态: COMPLETED")
        logger.info("=" * 80)

    except Exception as e:
        total_time = time.time() - start_time
        error_message = f"全国扫描任务执行失败: {str(e)}"
        logger.error(f"❌ {error_message}")
        logger.error(f"📋 异常类型: {type(e).__name__}")
        logger.error(f"📋 处理进度: {successful_provinces}/{total_provinces} 省份")
        logger.error(f"⏱️ 失败前用时: {total_time:.2f}秒")

        import traceback
        logger.error(f"📋 完整错误堆栈:")
        logger.error(traceback.format_exc())

        try:
            final_error_msg = f"全国扫描失败: {error_message} (已处理 {successful_provinces}/{total_provinces} 个省份)"
            await task_manager.update_task_status(task_id, TaskStatus.FAILED, final_error_msg)
        except Exception as update_error:
            logger.error(f"❌ 更新任务状态失败: {update_error}")

        logger.error("=" * 80)
        # 不重新抛出异常，避免影响主服务
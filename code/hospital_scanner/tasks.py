#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
医院层级扫查微服务 - 任务管理
"""

import asyncio
import threading
import logging
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List
from enum import Enum

from db import get_db
from schemas import TaskStatus, ScanTaskRequest, ScanResult

logger = logging.getLogger(__name__)

class TaskManager:
    """任务管理器"""
    
    def __init__(self):
        self.tasks: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()
    
    async def create_task(self, request: ScanTaskRequest) -> str:
        """创建任务"""
        with self._lock:
            task_id = str(uuid.uuid4())
            
            task_data = {
                "task_id": task_id,
                "hospital_name": request.hospital_name,
                "query": request.query,
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
            await db.create_task(
                task_id=task_id,
                hospital_name=request.hospital_name,
                query=request.query,
                status=TaskStatus.PENDING.value
            )
            
            logger.info(f"创建任务成功: {task_id}")
            return task_id
    
    async def update_task_status(self, task_id: str, status: TaskStatus, error_message: Optional[str] = None):
        """更新任务状态"""
        try:
            with self._lock:
                logger.info(f"📝 尝试更新任务状态: {task_id} -> {status.value}")

                if task_id in self.tasks:
                    self.tasks[task_id]["status"] = status.value
                    self.tasks[task_id]["updated_at"] = datetime.now().isoformat()

                    if error_message:
                        self.tasks[task_id]["error_message"] = error_message

                    logger.info(f"✅ 内存中的任务状态已更新: {task_id} -> {status.value}")

                    # 更新数据库
                    try:
                        db = await get_db()
                        await db.update_task_status(task_id, status.value, error_message)
                        logger.info(f"✅ 数据库中的任务状态已更新: {task_id}")
                    except Exception as db_error:
                        logger.error(f"❌ 更新数据库任务状态失败: {db_error}")
                        # 不抛出异常，允许继续执行

                    logger.info(f"🎉 任务状态更新完成: {task_id} -> {status.value}")
                else:
                    logger.warning(f"⚠️ 任务不存在于内存中: {task_id}")
                    logger.info(f"📋 当前内存中的任务列表: {list(self.tasks.keys())}")
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
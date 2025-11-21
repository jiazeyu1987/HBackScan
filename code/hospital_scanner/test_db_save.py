#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试数据库数据是否被正确保存
"""

import tempfile
import os
from tasks import TaskManager
from schemas import ScanTaskRequest
import asyncio

async def test_task_saving():
    """测试任务是否被正确保存到数据库"""
    
    test_db_path = tempfile.mktemp(suffix='.db')
    print(f"使用临时数据库: {test_db_path}")
    
    try:
        # 导入Database类
        from db import Database
        
        # 创建数据库实例
        db_instance = Database(test_db_path)
        
        # 创建任务管理器
        task_manager = TaskManager()
        
        # 创建一个任务
        task_request = ScanTaskRequest(
            hospital_name="测试医院",
            hospital_level="三级甲等", 
            scan_mode="智能深度扫查",
            description="测试任务描述"
        )
        
        task_id = await task_manager.create_task(task_request)
        print(f"任务创建成功: {task_id}")
        
        # 列出任务
        tasks = await db_instance.list_tasks()
        print(f"从数据库获取的任务列表: {len(tasks)} 个任务")
        
        if tasks:
            print(f"第一个任务: {tasks[0]}")
        
        # 直接查询数据库
        import sqlite3
        with sqlite3.connect(test_db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tasks")
            raw_rows = cursor.fetchall()
            print(f"直接SQL查询结果: {len(raw_rows)} 个记录")
            if raw_rows:
                print(f"第一个原始记录: {raw_rows[0]}")
        
        # 清理
        if os.path.exists(test_db_path):
            os.remove(test_db_path)
            
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🔍 测试任务保存到数据库...")
    asyncio.run(test_task_saving())

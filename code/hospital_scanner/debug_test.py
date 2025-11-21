#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试测试脚本
"""

import asyncio
import tempfile
import os
import sys
sys.path.append('.')

from db import DB_PATH, Database, _db_instance, get_db
from tasks import TaskManager
from main import app

async def debug_db_issue():
    """调试数据库问题"""
    print("=== 调试数据库问题 ===")
    
    # 使用临时数据库
    test_db_path = tempfile.mktemp(suffix='.db')
    print(f"临时数据库路径: {test_db_path}")
    
    # 重置全局实例
    _db_instance = None
    DB_PATH = test_db_path
    
    try:
        # 创建数据库实例
        db_instance = Database(test_db_path)
        print(f"数据库实例创建成功: {type(db_instance)}")
        
        # 初始化数据库
        await db_instance.init_db()
        print("数据库初始化成功")
        
        # 检查表是否存在
        with open(test_db_path, 'r'):
            pass
        
        # 测试get_db
        db = await get_db()
        print(f"获取数据库实例成功: {type(db)}")
        
        # 创建任务测试
        success = await db.create_task(
            task_id="test-123",
            hospital_name="测试医院",
            query="测试查询",
            status="pending"
        )
        print(f"创建任务结果: {success}")
        
        # 获取任务列表测试
        tasks = await db.list_tasks()
        print(f"任务列表长度: {len(tasks)}")
        
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 清理
        if os.path.exists(test_db_path):
            os.remove(test_db_path)

async def debug_lock_issue():
    """调试锁定问题"""
    print("=== 调试锁定问题 ===")
    
    tm = TaskManager()
    print(f"任务管理器锁定类型: {type(tm._lock)}")
    
    # 测试锁定
    try:
        with tm._lock:
            print("锁定测试成功")
    except Exception as e:
        print(f"锁定错误: {e}")

if __name__ == "__main__":
    asyncio.run(debug_db_issue())
    asyncio.run(debug_lock_issue())
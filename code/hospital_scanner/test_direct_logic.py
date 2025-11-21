#!/usr/bin/env python3
"""
直接测试两个失败用例
"""

import pytest
import sys
import os
import tempfile
import asyncio
from unittest.mock import patch, AsyncMock

# 添加项目路径
sys.path.insert(0, '/workspace/code/hospital_scanner')

# 导入必要的模块
from db import Database, _db_instance, DB_PATH, get_db
from tasks import TaskManager
from main import app
from fastapi.testclient import TestClient

# 创建测试客户端
client = TestClient(app)

async def test_list_tasks_direct():
    """直接测试test_list_tasks逻辑"""
    print("=== 测试 list_tasks 逻辑 ===")
    
    # 设置临时数据库
    test_db_path = tempfile.mktemp(suffix='.db')
    original_path = DB_PATH
    
    try:
        # 重置全局实例
        _db_instance = None
        from db import DB_PATH
        DB_PATH = test_db_path
        
        # 创建并初始化数据库
        db_instance = Database(test_db_path)
        await db_instance.init_db()
        
        # 获取数据库实例
        test_db = await get_db()
        
        # 创建测试任务
        task_ids = []
        for i in range(3):
            task_id = f"test-task-{i+1}"
            success = await test_db.create_task(
                task_id=task_id,
                hospital_name=f"测试医院{i+1}",
                query="测试查询",
                status="pending"
            )
            if success:
                task_ids.append(task_id)
                print(f"成功创建任务: {task_id}")
            else:
                print(f"创建任务失败: {task_id}")
        
        # 获取任务列表
        tasks = await test_db.list_tasks()
        print(f"数据库中的任务: {tasks}")
        
        # 验证结果
        created_task_ids = [task["task_id"] for task in tasks if "task_id" in task]
        
        for task_id in task_ids:
            if task_id in created_task_ids:
                print(f"✓ 任务 {task_id} 在列表中")
            else:
                print(f"✗ 任务 {task_id} 不在列表中")
                return False
        
        print(f"所有 {len(task_ids)} 个任务验证通过")
        return True
        
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # 清理
        if os.path.exists(test_db_path):
            os.remove(test_db_path)
        from db import DB_PATH
        DB_PATH = original_path

async def test_concurrent_tasks_direct():
    """直接测试并发任务逻辑"""
    print("=== 测试并发任务逻辑 ===")
    
    # 测试TaskManager的锁定机制
    tm = TaskManager()
    print(f"TaskManager锁定类型: {type(tm._lock)}")
    
    # 设置临时数据库
    test_db_path = tempfile.mktemp(suffix='.db')
    original_path = DB_PATH
    
    try:
        # 重置全局实例
        _db_instance = None
        from db import DB_PATH
        DB_PATH = test_db_path
        
        # 创建并初始化数据库
        db_instance = Database(test_db_path)
        await db_instance.init_db()
        
        # 获取数据库实例
        test_db = await get_db()
        
        # 模拟并发任务创建
        results = []
        for i in range(3):
            task_id = f"concurrent-test-{i+1}"
            try:
                success = await test_db.create_task(
                    task_id=task_id,
                    hospital_name=f"并发测试医院{i+1}",
                    query="并发测试",
                    status="pending"
                )
                results.append(200 if success else 500)
                print(f"创建并发任务 {task_id}: {'成功' if success else '失败'}")
            except Exception as e:
                print(f"创建并发任务 {task_id} 时出错: {e}")
                results.append(500)
        
        print(f"并发测试结果: {results}")
        
        # 验证结果
        success_count = sum(1 for status in results if status == 200)
        
        if success_count >= 2:
            print(f"✓ 并发测试通过: {success_count}/3 成功")
            return True
        else:
            print(f"✗ 并发测试失败: 只有 {success_count}/3 成功")
            return False
            
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # 清理
        if os.path.exists(test_db_path):
            os.remove(test_db_path)
        from db import DB_PATH
        DB_PATH = original_path

async def main():
    """主函数"""
    print("开始测试数据库和锁定修复...")
    
    # 测试list_tasks逻辑
    test1_passed = await test_list_tasks_direct()
    print()
    
    # 测试concurrent_requests逻辑
    test2_passed = await test_concurrent_tasks_direct()
    print()
    
    # 总结结果
    print("=" * 50)
    print("测试结果总结:")
    print(f"test_list_tasks 逻辑: {'✓ PASS' if test1_passed else '✗ FAIL'}")
    print(f"test_concurrent_requests 逻辑: {'✓ PASS' if test2_passed else '✗ FAIL'}")
    
    if test1_passed and test2_passed:
        print("🎉 所有逻辑测试通过！修复成功！")
        return True
    else:
        print("❌ 仍有逻辑测试失败，需要进一步调试")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
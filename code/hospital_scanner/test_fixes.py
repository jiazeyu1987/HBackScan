#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试修复效果
"""

import asyncio
import sys
import tempfile
import os
from unittest.mock import patch, AsyncMock

# 添加项目路径
sys.path.append(os.path.dirname(__file__))

from main import app
from db import Database
from fastapi.testclient import TestClient

client = TestClient(app)

async def test_fixes():
    """测试所有修复的效果"""
    print("开始测试修复效果...")
    
    # 设置临时数据库
    test_db_path = tempfile.mktemp(suffix='.db')
    
    # 初始化数据库
    db = Database(test_db_path)
    await db.init_db()
    
    # 添加测试数据
    test_db = Database(test_db_path)
    for i in range(5):
        await test_db.create_province(name=f"测试省份{i+1}", code=f"11{1000+i}")
    
    try:
        print("✅ 1. 测试分页边界值处理...")
        
        # 测试边界值
        response = client.get("/provinces?page=0&page_size=10")
        assert response.status_code == 200, f"预期200，实际{response.status_code}"
        
        response = client.get("/provinces?page=-1&page_size=10")
        assert response.status_code == 200, f"预期200，实际{response.status_code}"
        
        response = client.get("/provinces?page=1&page_size=0")
        assert response.status_code == 200, f"预期200，实际{response.status_code}"
        
        response = client.get("/provinces?page=1&page_size=-1")
        assert response.status_code == 200, f"预期200，实际{response.status_code}"
        
        # 检查响应结构
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        
        print("✅ 1. 分页边界值处理测试通过")
        
        print("✅ 2. 测试任务创建...")
        
        with patch('main.execute_scan_task') as mock_execute:
            mock_execute.return_value = AsyncMock()
            
            scan_data = {
                "hospital_name": "测试医院",
                "query": "测试查询"
            }
            
            response = client.post("/scan", json=scan_data)
            assert response.status_code == 200, f"预期200，实际{response.status_code}"
            
            data = response.json()
            assert "task_id" in data
            assert "status" in data
            assert "message" in data
            
            task_id = data["task_id"]
            print(f"   创建的任务ID: {task_id}")
        
        print("✅ 2. 任务创建测试通过")
        
        print("✅ 3. 测试404错误处理...")
        
        # 测试不存在的任务ID
        response = client.get("/task/non-existent-task-id")
        assert response.status_code == 404, f"预期404，实际{response.status_code}"
        
        data = response.json()
        assert "detail" in data
        assert "任务不存在" in data["detail"]
        
        print("✅ 3. 错误处理测试通过")
        
        print("✅ 4. 测试除零保护...")
        
        # 测试除零保护（当total为0时）
        response = client.get("/provinces?page=1&page_size=0")
        assert response.status_code == 200
        
        print("✅ 4. 除零保护测试通过")
        
        print("\n🎉 所有修复测试通过！")
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # 清理
        if os.path.exists(test_db_path):
            os.remove(test_db_path)

if __name__ == "__main__":
    success = asyncio.run(test_fixes())
    sys.exit(0 if success else 1)

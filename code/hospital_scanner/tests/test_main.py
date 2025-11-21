#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
医院层级扫查微服务 - 基础测试用例
"""

import pytest
import asyncio
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient

from main import app
from db import init_db
from schemas import ScanTaskRequest, TaskStatus

# 创建测试客户端
client = TestClient(app)

@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session")
async def test_db():
    """初始化测试数据库"""
    await init_db()
    yield
    # 清理测试数据
    import os
    if os.path.exists("data/test_hospital_scanner.db"):
        os.remove("data/test_hospital_scanner.db")

class TestAPI:
    """API测试类"""
    
    def test_root(self):
        """测试根路径"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "hospital" in data["message"].lower()
    
    def test_health_check(self):
        """测试健康检查"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
    
    def test_create_scan_task(self):
        """测试创建扫查任务"""
        task_data = {
            "hospital_name": "测试人民医院",
            "query": "获取医院层级结构"
        }
        
        response = client.post("/scan", json=task_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "task_id" in data
        assert data["status"] == "pending"
        assert "message" in data
    
    def test_create_scan_task_invalid_data(self):
        """测试创建任务时无效数据"""
        # 缺少必填字段
        task_data = {"query": "测试"}
        
        response = client.post("/scan", json=task_data)
        assert response.status_code == 422  # Validation Error
    
    def test_get_nonexistent_task(self):
        """测试获取不存在的任务"""
        response = client.get("/task/nonexistent-task-id")
        assert response.status_code == 404
    
    def test_list_tasks(self):
        """测试获取任务列表"""
        response = client.get("/tasks")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

class TestDatabase:
    """数据库测试类"""
    
    @pytest.mark.asyncio
    async def test_db_init(self, test_db):
        """测试数据库初始化"""
        from db import get_db
        
        db = await get_db()
        assert db is not None
    
    @pytest.mark.asyncio
    async def test_create_and_get_task(self, test_db):
        """测试创建和获取任务"""
        from db import get_db
        
        db = await get_db()
        
        # 创建任务
        task_id = "test-task-123"
        result = await db.create_task(
            task_id=task_id,
            hospital_name="测试医院",
            query="测试查询",
            status="pending"
        )
        assert result is True
        
        # 获取任务
        task = await db.get_task(task_id)
        assert task is not None
        assert task["hospital_name"] == "测试医院"
        assert task["status"] == "pending"

class TestLLMClient:
    """LLM客户端测试类"""
    
    @pytest.mark.asyncio
    async def test_mock_analysis(self):
        """测试模拟分析功能"""
        from llm_client import LLMClient
        
        client = LLMClient()
        # 不设置API密钥，应该使用模拟模式
        result = await client.analyze_hospital_hierarchy("测试医院", "测试查询")
        
        assert "hospital_name" in result
        assert result["hospital_name"] == "测试医院"
        assert "level" in result
        assert "departments" in result
        assert isinstance(result["departments"], list)
    
    @patch('llm_client.LLMClient._make_request')
    @pytest.mark.asyncio
    async def test_api_analysis(self, mock_request):
        """测试API分析功能"""
        from llm_client import LLMClient
        
        # 模拟API响应
        mock_response = '''{
            "hospital_name": "API测试医院",
            "level": "二级医院",
            "address": "测试地址",
            "phone": "123-456-7890",
            "departments": ["内科", "外科"],
            "beds_count": 200,
            "staff_count": 300,
            "specializations": ["心血管科"]
        }'''
        
        mock_request.return_value = mock_response
        
        # 设置模拟API密钥
        with patch.dict('os.environ', {'LLM_API_KEY': 'fake-key'}):
            client = LLMClient()
            result = await client.analyze_hospital_hierarchy("API测试医院", "测试")
            
            assert result["hospital_name"] == "API测试医院"
            assert result["level"] == "二级医院"

class TestTaskManager:
    """任务管理器测试类"""
    
    @pytest.mark.asyncio
    async def test_create_task(self):
        """测试创建任务"""
        from tasks import TaskManager
        from schemas import ScanTaskRequest
        
        manager = TaskManager()
        request = ScanTaskRequest(
            hospital_name="管理器测试医院",
            query="测试查询"
        )
        
        task_id = await manager.create_task(request)
        assert task_id is not None
        assert len(task_id) > 0
    
    @pytest.mark.asyncio
    async def test_update_task_status(self):
        """测试更新任务状态"""
        from tasks import TaskManager
        from schemas import ScanTaskRequest, TaskStatus
        
        manager = TaskManager()
        request = ScanTaskRequest(
            hospital_name="状态测试医院",
            query="测试查询"
        )
        
        task_id = await manager.create_task(request)
        await manager.update_task_status(task_id, TaskStatus.RUNNING)
        
        status = await manager.get_task_status(task_id)
        assert status == TaskStatus.RUNNING

class TestSchemas:
    """数据模型测试类"""
    
    def test_scan_task_request(self):
        """测试扫查任务请求模型"""
        data = {
            "hospital_name": "模型测试医院",
            "query": "测试查询"
        }
        
        request = ScanTaskRequest(**data)
        assert request.hospital_name == "模型测试医院"
        assert request.query == "测试查询"
    
    def test_task_status_enum(self):
        """测试任务状态枚举"""
        assert TaskStatus.PENDING == "pending"
        assert TaskStatus.RUNNING == "running"
        assert TaskStatus.COMPLETED == "completed"
        assert TaskStatus.FAILED == "failed"
    
    def test_hospital_info_model(self):
        """测试医院信息模型"""
        from schemas import HospitalInfo
        
        data = {
            "hospital_name": "信息测试医院",
            "level": "三级甲等",
            "departments": ["内科", "外科"]
        }
        
        info = HospitalInfo(**data)
        assert info.hospital_name == "信息测试医院"
        assert info.level == "三级甲等"
        assert len(info.departments) == 2

# 集成测试
class TestIntegration:
    """集成测试类"""
    
    @pytest.mark.asyncio
    async def test_full_workflow(self):
        """测试完整工作流程"""
        from tasks import TaskManager
        from llm_client import LLMClient
        from schemas import ScanTaskRequest, TaskStatus
        
        # 创建任务
        manager = TaskManager()
        request = ScanTaskRequest(
            hospital_name="集成测试医院",
            query="完整流程测试"
        )
        
        task_id = await manager.create_task(request)
        assert task_id is not None
        
        # 更新状态为运行中
        await manager.update_task_status(task_id, TaskStatus.RUNNING)
        
        # 模拟LLM分析
        llm_client = LLMClient()
        hospital_info = await llm_client.analyze_hospital_hierarchy(
            "集成测试医院", 
            "完整流程测试"
        )
        
        # 验证结果
        assert hospital_info is not None
        assert "hospital_name" in hospital_info
        
        # 完成任务
        from schemas import ScanResult
        result = ScanResult(
            task_id=task_id,
            status=TaskStatus.COMPLETED,
            hospital_info=hospital_info
        )
        
        await manager.save_task_result(task_id, result)
        
        # 验证最终结果
        final_result = await manager.get_task_result(task_id)
        assert final_result is not None
        assert final_result.status == TaskStatus.COMPLETED

if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v"])
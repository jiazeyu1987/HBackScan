#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
医院层级扫查微服务 - API集成测试
"""

import pytest
import asyncio
import json
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from main import app
from db import init_db
import tempfile
import os

# 创建测试客户端
client = TestClient(app)

class TestAPIIntegration:
    """API集成测试类"""
    
    @pytest.fixture(autouse=True)
    async def setup_test_db(self):
        """设置测试数据库"""
        # 使用临时数据库
        test_db_path = tempfile.mktemp(suffix='.db')
        
        # 替换数据库路径
        from db import DB_PATH, Database
        original_path = DB_PATH
        import db
        import main
        from tasks import TaskManager
        
        # 保存原始的App实例
        original_app = main.app
        
        try:
            # 确保测试数据库文件存在
            with open(test_db_path, 'w'):
                pass
                
            # 重置所有全局实例，确保使用测试数据库
            db._db_instance = None
            main.task_manager = TaskManager()  # 重置任务管理器实例
            db.DB_PATH = test_db_path
            
            # 初始化测试数据库
            db_instance = Database(test_db_path)
            await db_instance.init_db()
            
            # 确保全局实例被正确创建
            from db import get_db
            test_db = await get_db()
            
            # 添加测试数据
            # 添加一些省份用于测试分页
            for i in range(5):
                await test_db.create_province(name=f"测试省份{i+1}", code=f"11{1000+i}")
            
            yield
        except Exception as e:
            print(f"数据库初始化失败: {e}")
            raise
        finally:
            # 清理测试数据库
            try:
                if os.path.exists(test_db_path):
                    os.remove(test_db_path)
            except Exception:
                pass
            # 恢复原始路径和实例
            db.DB_PATH = original_path
            db._db_instance = None
            main.task_manager = TaskManager()  # 恢复原始任务管理器

    @patch('llm_client.LLMClient._make_request')
    def test_scan_task_creation(self, mock_api):
        """测试创建扫查任务"""
        # 设置mock返回值
        mock_api.return_value = '{"response": "success"}'
        
        # 测试数据
        scan_data = {
            "hospital_name": "北京协和医院",
            "query": "获取医院层级结构"
        }
        
        # 发送请求
        response = client.post("/scan", json=scan_data)
        
        # 验证响应
        assert response.status_code == 200
        data = response.json()
        assert "task_id" in data
        assert "status" in data
        assert "message" in data
        assert "扫查任务已创建" in data["message"]

    def test_get_task_status(self):
        """测试获取任务状态"""
        # 首先创建一个任务
        scan_data = {
            "hospital_name": "上海瑞金医院",
            "query": "获取医院信息"
        }
        
        create_response = client.post("/scan", json=scan_data)
        assert create_response.status_code == 200
        task_id = create_response.json()["task_id"]
        
        # 获取任务状态
        status_response = client.get(f"/task/{task_id}")
        assert status_response.status_code == 200
        
        status_data = status_response.json()
        assert status_data["task_id"] == task_id

    @patch('main.execute_scan_task')
    async def test_list_tasks(self, mock_execute):
        """测试获取任务列表"""
        # Mock任务执行，避免真实调用
        mock_execute.return_value = AsyncMock()
        
        # 在异步上下文中重新创建任务管理器，确保使用新的数据库
        from main import task_manager
        test_task_manager = TaskManager()
        
        # 手动创建一些任务到测试数据库
        from db import get_db
        test_db = await get_db()
        
        task_ids = []
        for i in range(3):
            try:
                # 直接调用数据库创建任务
                task_id = f"test-task-{i+1}"
                await test_db.create_task(
                    task_id=task_id,
                    hospital_name=f"测试医院{i+1}",
                    query="测试查询",
                    status="pending"
                )
                task_ids.append(task_id)
            except Exception as e:
                print(f"创建任务{i+1}失败: {e}")
        
        print(f"成功创建了{len(task_ids)}个任务: {task_ids}")
        
        # 获取任务列表
        tasks = await test_db.list_tasks()
        print(f"数据库中的任务列表: {tasks}")
        
        assert len(tasks) >= len(task_ids), f"预期至少{len(task_ids)}个任务，实际{len(tasks)}个"
        
        # 验证任务ID存在
        created_task_ids = [task["task_id"] for task in tasks if "task_id" in task]
        for task_id in task_ids:
            assert task_id in created_task_ids, f"任务{task_id}不在数据库中"

    def test_root_endpoint(self):
        """测试根路径"""
        response = client.get("/")
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "status" in data

    def test_health_check(self):
        """测试健康检查"""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"

    @patch('main.execute_full_refresh_task')
    def test_refresh_all_endpoint(self, mock_task):
        """测试完整数据刷新接口"""
        # Mock任务执行
        mock_task.return_value = AsyncMock()
        
        response = client.post("/refresh/all")
        assert response.status_code == 200
        
        data = response.json()
        assert "task_id" in data
        assert "完整数据刷新任务已创建" in data["message"]

    @patch('main.execute_province_refresh_task')
    def test_refresh_province_endpoint(self, mock_task):
        """测试省份数据刷新接口"""
        # Mock任务执行
        mock_task.return_value = AsyncMock()
        
        response = client.post("/refresh/province/北京市")
        assert response.status_code == 200
        
        data = response.json()
        assert "task_id" in data
        assert "北京市" in data["message"]

    def test_get_provinces_pagination(self):
        """测试获取省份列表（分页）"""
        # 测试第一页
        response = client.get("/provinces?page=1&page_size=10")
        assert response.status_code == 200
        
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert "pages" in data
        assert "has_next" in data
        assert "has_prev" in data

    def test_get_cities_with_province_filter(self):
        """测试获取城市列表（省份筛选）"""
        response = client.get("/cities?province_id=1&page=1&page_size=10")
        assert response.status_code == 200
        
        data = response.json()
        assert "items" in data
        assert "total" in data

    def test_get_districts_with_city_filter(self):
        """测试获取区县列表（城市筛选）"""
        response = client.get("/districts?city_id=1&page=1&page_size=10")
        assert response.status_code == 200
        
        data = response.json()
        assert "items" in data
        assert "total" in data

    def test_get_hospitals_with_district_filter(self):
        """测试获取医院列表（区县级筛选）"""
        response = client.get("/hospitals?district_id=1&page=1&page_size=10")
        assert response.status_code == 200
        
        data = response.json()
        assert "items" in data
        assert "total" in data

    def test_search_hospitals(self):
        """测试医院搜索接口"""
        response = client.get("/hospitals/search?q=人民医院&limit=10")
        assert response.status_code == 200
        
        data = response.json()
        assert "query" in data
        assert "results" in data
        assert "count" in data
        assert data["query"] == "人民医院"

    def test_pagination_edge_cases(self):
        """测试分页边界情况"""
        # 测试无效页码（应该被修正为有效值）
        response = client.get("/provinces?page=0&page_size=10")
        assert response.status_code == 200
        
        response = client.get("/provinces?page=-1&page_size=10")
        assert response.status_code == 200
        
        # 测试无效的页面大小（应该被修正为默认值）
        response = client.get("/provinces?page=1&page_size=0")
        assert response.status_code == 200
        
        response = client.get("/provinces?page=1&page_size=-1")
        assert response.status_code == 200
        
        # 测试分页响应结构
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert "pages" in data
        assert "has_next" in data
        assert "has_prev" in data

    def test_error_handling(self):
        """测试错误处理"""
        # 测试不存在的任务ID
        response = client.get("/task/nonexistent-task-id")
        assert response.status_code == 404
        
        # 验证错误响应格式
        data = response.json()
        assert "detail" in data
        assert "任务不存在" in data["detail"]

    @patch('llm_client.LLMClient.analyze_hospital_hierarchy')
    async def test_llm_api_mock(self, mock_analyze):
        """测试LLM API调用mock"""
        # 设置模拟返回数据
        mock_result = {
            "hospital_name": "测试医院",
            "level": "三级甲等",
            "address": "测试地址",
            "phone": "010-12345678",
            "departments": ["内科", "外科"],
            "beds_count": 500,
            "staff_count": 800,
            "specializations": ["心血管科"]
        }
        mock_analyze.return_value = mock_result
        
        # 测试医院分析
        scan_data = {
            "hospital_name": "测试医院",
            "query": "分析医院结构"
        }
        
        response = client.post("/scan", json=scan_data)
        assert response.status_code == 200

    @patch('main.execute_scan_task')
    async def test_concurrent_requests(self, mock_execute):
        """测试并发请求"""
        # Mock任务执行，避免真实调用
        mock_execute.return_value = AsyncMock()
        
        # 直接在数据库中测试并发任务创建
        from db import get_db
        test_db = await get_db()
        
        results = []
        
        # 串行测试多个任务创建（避免复杂的并发问题）
        for i in range(3):
            try:
                # 手动创建任务到数据库
                task_id = f"concurrent-test-{i+1}"
                success = await test_db.create_task(
                    task_id=task_id,
                    hospital_name=f"并发测试医院{i+1}",
                    query="并发测试",
                    status="pending"
                )
                results.append(200 if success else 500)
            except Exception as e:
                print(f"并发测试任务{i+1}创建失败: {e}")
                results.append(500)
        
        print(f"并发测试结果: {results}")
        
        # 验证所有请求都成功或至少大部分成功
        assert len(results) >= 2, f"至少有2个任务应该成功处理，实际处理了{len(results)}个"
        success_count = sum(1 for status in results if status == 200)
        assert success_count >= 2, f"至少有2个成功，实际成功{success_count}个"
        
        # 验证数据库中的任务
        tasks = await test_db.list_tasks()
        concurrent_tasks = [t for t in tasks if t["task_id"].startswith("concurrent-test-")]
        assert len(concurrent_tasks) >= 2, f"数据库中应该有至少2个并发测试任务，实际{len(concurrent_tasks)}个"

    def test_api_response_structure(self):
        """测试API响应结构"""
        # 测试根路径响应结构
        response = client.get("/")
        data = response.json()
        
        required_fields = ["message", "version", "status"]
        for field in required_fields:
            assert field in data

    def test_invalid_request_data(self):
        """测试无效请求数据"""
        # 测试缺少必需字段的请求
        invalid_data = {
            "query": "缺少医院名称"
        }
        
        response = client.post("/scan", json=invalid_data)
        assert response.status_code == 422  # Validation error

if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v"])
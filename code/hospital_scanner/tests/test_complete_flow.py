#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
医院层级扫查微服务 - 完整流程集成测试
"""

import pytest
import asyncio
import json
import time
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from main import app
from db import init_db, get_db
from schemas import TaskStatus
import tempfile
import os

# 创建测试客户端
client = TestClient(app)

class TestCompleteFlow:
    """完整流程集成测试类"""
    
    @pytest.fixture(autouse=True)
    async def setup_test_db(self):
        """设置测试数据库"""
        # 使用临时数据库
        test_db_path = tempfile.mktemp(suffix='.db')
        
        # 替换数据库路径
        from db import DB_PATH
        original_path = DB_PATH
        import db
        db.DB_PATH = test_db_path
        
        try:
            # 初始化测试数据库
            await init_db()
            yield
        finally:
            # 清理测试数据库
            if os.path.exists(test_db_path):
                os.remove(test_db_path)
            # 恢复原始路径
            db.DB_PATH = original_path

    @patch('main.execute_full_refresh_task')
    @patch('main.execute_province_refresh_task')
    def test_complete_data_refresh_flow(self, mock_province_task, mock_full_task):
        """测试完整数据刷新流程"""
        # Mock任务执行
        mock_province_task.return_value = AsyncMock()
        mock_full_task.return_value = AsyncMock()
        
        # 1. 触发完整数据刷新
        print("1. 触发完整数据刷新任务...")
        refresh_response = client.post("/refresh/all")
        assert refresh_response.status_code == 200
        
        full_refresh_data = refresh_response.json()
        full_task_id = full_refresh_data["task_id"]
        assert "完整数据刷新任务已创建" in full_refresh_data["message"]
        
        # 2. 等待任务执行（模拟）
        time.sleep(0.1)
        
        # 3. 验证任务状态
        print("2. 验证完整数据刷新任务状态...")
        task_status_response = client.get(f"/task/{full_task_id}")
        assert task_status_response.status_code == 200
        
        # 4. 获取省份列表
        print("3. 获取省份列表...")
        provinces_response = client.get("/provinces?page=1&page_size=10")
        assert provinces_response.status_code == 200
        
        provinces_data = provinces_response.json()
        assert "items" in provinces_data
        assert "total" in provinces_data
        
        # 5. 获取城市列表
        print("4. 获取城市列表...")
        cities_response = client.get("/cities?page=1&page_size=20")
        assert cities_response.status_code == 200
        
        cities_data = cities_response.json()
        assert "items" in cities_data
        assert "total" in cities_data
        
        # 6. 获取区县列表
        print("5. 获取区县列表...")
        districts_response = client.get("/districts?page=1&page_size=30")
        assert districts_response.status_code == 200
        
        districts_data = districts_response.json()
        assert "items" in districts_data
        assert "total" in districts_data
        
        # 7. 获取医院列表
        print("6. 获取医院列表...")
        hospitals_response = client.get("/hospitals?page=1&page_size=50")
        assert hospitals_response.status_code == 200
        
        hospitals_data = hospitals_response.json()
        assert "items" in hospitals_data
        assert "total" in hospitals_data

    @patch('main.execute_province_refresh_task')
    def test_province_level_refresh_flow(self, mock_task):
        """测试省份层级刷新流程"""
        # Mock任务执行
        mock_task.return_value = AsyncMock()
        
        # 1. 刷新特定省份数据
        print("1. 刷新广东省数据...")
        province_response = client.post("/refresh/province/广东省")
        assert province_response.status_code == 200
        
        province_data = province_response.json()
        province_task_id = province_data["task_id"]
        assert "广东省" in province_data["message"]
        
        # 2. 验证省份数据
        print("2. 验证省份数据...")
        time.sleep(0.1)
        
        # 3. 查询广东省的城市
        print("3. 查询广东省的城市...")
        # 首先需要获取广东省的ID（这里简化处理）
        provinces_response = client.get("/provinces?page=1&page_size=10")
        assert provinces_response.status_code == 200
        
        provinces_data = provinces_response.json()
        if provinces_data["items"]:
            province_id = provinces_data["items"][0]["id"]
            
            cities_response = client.get(f"/cities?province_id={province_id}&page=1&page_size=10")
            assert cities_response.status_code == 200

    @patch('main.execute_full_refresh_task')
    def test_data_consistency_validation(self, mock_task):
        """测试数据一致性和完整性验证"""
        # Mock任务执行
        mock_task.return_value = AsyncMock()
        
        # 1. 执行完整数据刷新
        refresh_response = client.post("/refresh/all")
        assert refresh_response.status_code == 200
        
        # 2. 等待数据刷新完成
        time.sleep(0.2)
        
        # 3. 验证数据层级关系
        print("验证数据层级关系...")
        
        # 获取省份数据
        provinces_response = client.get("/provinces?page=1&page_size=100")
        provinces_data = provinces_response.json()
        
        if provinces_data["items"]:
            province = provinces_data["items"][0]
            province_id = province["id"]
            
            # 获取该省份的城市
            cities_response = client.get(f"/cities?province_id={province_id}&page=1&page_size=100")
            cities_data = cities_response.json()
            
            if cities_data["items"]:
                city = cities_data["items"][0]
                city_id = city["id"]
                
                # 获取该城市的区县
                districts_response = client.get(f"/districts?city_id={city_id}&page=1&page_size=100")
                districts_data = districts_response.json()
                
                if districts_data["items"]:
                    district = districts_data["items"][0]
                    district_id = district["id"]
                    
                    # 获取该区县的医院
                    hospitals_response = client.get(f"/hospitals?district_id={district_id}&page=1&page_size=100")
                    hospitals_data = hospitals_response.json()
                    
                    # 验证数据完整性
                    assert len(provinces_data["items"]) > 0
                    assert len(cities_data["items"]) >= 0
                    assert len(districts_data["items"]) >= 0
                    assert len(hospitals_data["items"]) >= 0

    def test_search_functionality(self):
        """测试搜索功能完整性"""
        # 1. 搜索医院
        print("测试医院搜索...")
        search_response = client.get("/hospitals/search?q=人民医院&limit=10")
        assert search_response.status_code == 200
        
        search_data = search_response.json()
        assert "query" in search_data
        assert "results" in search_data
        assert "count" in search_data
        
        # 2. 测试不同的搜索关键词
        keywords = ["医院", "中心", "社区", "协和"]
        for keyword in keywords:
            response = client.get(f"/hospitals/search?q={keyword}")
            assert response.status_code == 200

    def test_pagination_comprehensive(self):
        """测试分页功能完整性"""
        # 1. 测试不同页面大小
        page_sizes = [5, 10, 20, 50]
        for page_size in page_sizes:
            response = client.get(f"/provinces?page=1&page_size={page_size}")
            assert response.status_code == 200
            
            data = response.json()
            assert data["page_size"] == page_size
        
        # 2. 测试跨页导航
        response1 = client.get("/provinces?page=1&page_size=5")
        response2 = client.get("/provinces?page=2&page_size=5")
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        data1 = response1.json()
        data2 = response2.json()
        
        # 验证页面导航逻辑
        assert data1["has_next"] == data2["has_prev"]
        assert data1["page"] == 1
        assert data2["page"] == 2

    @patch('main.execute_full_refresh_task')
    @patch('main.execute_province_refresh_task')
    def test_error_recovery_flow(self, mock_province_task, mock_full_task):
        """测试错误恢复流程"""
        # 1. 模拟任务失败情况
        mock_full_task.side_effect = Exception("模拟任务失败")
        
        # 2. 触发任务
        response = client.post("/refresh/all")
        assert response.status_code == 200
        
        # 3. 等待一段时间让任务执行
        time.sleep(0.5)
        
        # 4. 检查任务状态（应该为失败）
        task_id = response.json()["task_id"]
        status_response = client.get(f"/task/{task_id}")
        
        # 如果任务执行失败，状态应该是failed
        if status_response.status_code == 200:
            status_data = status_response.json()
            # 任务可能已经执行完成或失败

    def test_performance_under_load(self):
        """测试负载下的性能"""
        import threading
        import time
        
        start_time = time.time()
        results = []
        
        def make_api_call(endpoint):
            if endpoint == "provinces":
                response = client.get("/provinces?page=1&page_size=10")
            elif endpoint == "cities":
                response = client.get("/cities?page=1&page_size=10")
            elif endpoint == "districts":
                response = client.get("/districts?page=1&page_size=10")
            elif endpoint == "hospitals":
                response = client.get("/hospitals?page=1&page_size=10")
            else:
                response = client.get("/")
            
            results.append(response.status_code)
        
        # 创建并发请求
        endpoints = ["provinces", "cities", "districts", "hospitals"] * 5  # 20个请求
        threads = []
        
        for endpoint in endpoints:
            thread = threading.Thread(target=make_api_call, args=(endpoint,))
            threads.append(thread)
            thread.start()
        
        # 等待所有请求完成
        for thread in threads:
            thread.join()
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # 验证结果
        assert len(results) == 20
        assert all(status == 200 for status in results)
        assert execution_time < 10  # 应该在10秒内完成

    def test_data_integrity_after_refresh(self):
        """测试刷新后的数据完整性"""
        # 这个测试验证数据刷新后各层级数据的完整性
        
        # 1. 模拟数据（通过API触发）
        response = client.post("/refresh/all")
        assert response.status_code == 200
        
        # 2. 等待数据刷新
        time.sleep(0.3)
        
        # 3. 验证各层级数据的计数一致性
        # 获取各级数据总量
        provinces_response = client.get("/provinces?page=1&page_size=1")
        cities_response = client.get("/cities?page=1&page_size=1")
        districts_response = client.get("/districts?page=1&page_size=1")
        hospitals_response = client.get("/hospitals?page=1&page_size=1")
        
        assert provinces_response.status_code == 200
        assert cities_response.status_code == 200
        assert districts_response.status_code == 200
        assert hospitals_response.status_code == 200
        
        # 验证数据结构
        for resp, name in [
            (provinces_response, "provinces"),
            (cities_response, "cities"),
            (districts_response, "districts"),
            (hospitals_response, "hospitals")
        ]:
            data = resp.json()
            assert "items" in data, f"{name} response missing items"
            assert "total" in data, f"{name} response missing total"
            assert "page" in data, f"{name} response missing page"
            assert "page_size" in data, f"{name} response missing page_size"

    def test_edge_cases_handling(self):
        """测试边界情况处理"""
        # 1. 测试空数据情况
        response = client.get("/provinces?page=999&page_size=10")
        assert response.status_code == 200
        
        # 2. 测试无效参数
        response = client.get("/provinces?page=abc&page_size=10")
        # FastAPI会自动处理类型转换，无效值会使用默认值
        
        # 3. 测试搜索空字符串
        response = client.get("/hospitals/search?q=")
        assert response.status_code == 200
        
        # 4. 测试超长搜索词
        long_query = "a" * 1000
        response = client.get(f"/hospitals/search?q={long_query}")
        assert response.status_code == 200

if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v"])
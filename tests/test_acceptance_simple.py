#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验收测试套件 - 简化版
模拟完整的业务场景，验证系统端到端功能
"""

import pytest
import json
import time
import sqlite3
import asyncio
from datetime import datetime
from unittest.mock import patch, AsyncMock
from typing import Dict, List
import tempfile
import os

from fastapi.testclient import TestClient


class TestAcceptanceScenarios:
    """验收测试场景类"""
    
    @pytest.fixture
    def fastapi_client(self):
        """FastAPI测试客户端夹具"""
        from main import app
        return TestClient(app)
    
    @pytest.mark.acceptance
    @pytest.mark.fast
    def test_api_performance_requirements(self, fastapi_client):
        """测试API性能要求（500ms内返回）"""
        # 测试根路径
        start_time = time.time()
        response = fastapi_client.get("/")
        response_time = time.time() - start_time
        
        assert response.status_code == 200
        assert response_time < 0.5, f"根路径响应时间 {response_time:.3f}s 超过500ms"
        
        # 测试健康检查
        start_time = time.time()
        response = fastapi_client.get("/health")
        response_time = time.time() - start_time
        
        assert response.status_code == 200
        assert response_time < 0.5, f"健康检查响应时间 {response_time:.3f}s 超过500ms"
        
        print(f"✅ API性能测试通过，响应时间均小于500ms")
    
    @pytest.mark.acceptance
    @pytest.mark.fast
    def test_empty_database_initialization(self):
        """测试空数据库初始化"""
        import tempfile
        import os
        
        # 创建临时数据库
        db_fd, db_path = tempfile.mkstemp(suffix=".db")
        os.close(db_fd)
        
        try:
            from db import Database
            test_db = Database(db_path)
            test_db.init_database()
            
            # 验证所有表都是空的
            stats = test_db.get_statistics()
            
            assert stats['province_count'] == 0
            assert stats['city_count'] == 0
            assert stats['district_count'] == 0
            assert stats['hospital_count'] == 0
            assert stats['task_count'] == 0
            
            # 验证查询接口返回空结果
            provinces = test_db.get_all_provinces()
            assert provinces['total'] == 0
            assert len(provinces['items']) == 0
            
            cities = test_db.get_cities_by_province("不存在的省")
            assert cities['total'] == 0
            assert len(cities['items']) == 0
            
            print("✅ 空数据库初始化测试通过")
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)
    
    @pytest.mark.acceptance
    @pytest.mark.fast
    def test_database_upsert_functionality(self):
        """测试数据库UPSERT功能"""
        import tempfile
        import os
        
        # 创建临时数据库
        db_fd, db_path = tempfile.mkstemp(suffix=".db")
        os.close(db_fd)
        
        try:
            from db import Database
            test_db = Database(db_path)
            test_db.init_database()
            
            # 测试UPSERT省份
            province_id = test_db.upsert_province("江苏省", "JS")
            assert province_id == 1
            
            # 再次插入相同省份（应该更新）
            province_id2 = test_db.upsert_province("江苏省", "JS_UPDATED")
            assert province_id2 == 1  # 相同的ID
            
            # 验证更新成功
            province = test_db.get_province(1)
            assert province['name'] == "江苏省"
            
            # 测试UPSERT城市
            city_id = test_db.upsert_city(1, "南京市", "NJ")
            assert city_id == 1
            
            city_id2 = test_db.upsert_city(1, "南京市", "NJ_UPDATED")
            assert city_id2 == 1  # 相同的ID
            
            # 测试UPSERT区县
            district_id = test_db.upsert_district(1, "玄武区", "XW")
            assert district_id == 1
            
            # 测试UPSERT医院
            hospital_id = test_db.upsert_hospital(1, "玄武医院", "http://test.com", 0.9)
            assert hospital_id == 1
            
            # 验证最终统计
            stats = test_db.get_statistics()
            assert stats['province_count'] == 1
            assert stats['city_count'] == 1
            assert stats['district_count'] == 1
            assert stats['hospital_count'] == 1
            
            print("✅ 数据库UPSERT功能测试通过")
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)
    
    @pytest.mark.acceptance
    @pytest.mark.fast
    def test_data_relationship_integrity(self):
        """测试数据关系完整性"""
        import tempfile
        import os
        
        # 创建临时数据库
        db_fd, db_path = tempfile.mkstemp(suffix=".db")
        os.close(db_fd)
        
        try:
            from db import Database
            test_db = Database(db_path)
            test_db.init_database()
            
            # 创建完整的层级数据
            province_id = test_db.upsert_province("江苏省", "JS")
            city_id = test_db.upsert_city(province_id, "南京市", "NJ")
            district_id = test_db.upsert_district(city_id, "玄武区", "XW")
            hospital_id = test_db.upsert_hospital(district_id, "玄武医院", "http://test.com", 0.9)
            
            # 验证层级查询
            cities_data = test_db.get_cities_by_province("江苏省")
            assert cities_data['total'] == 1
            assert cities_data['items'][0]['name'] == "南京市"
            
            districts_data = test_db.get_districts_by_city("南京市")
            assert districts_data['total'] == 1
            assert districts_data['items'][0]['name'] == "玄武区"
            
            hospitals_data = test_db.get_hospitals_by_district("玄武区")
            assert hospitals_data['total'] == 1
            assert hospitals_data['items'][0]['name'] == "玄武医院"
            
            print("✅ 数据关系完整性测试通过")
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)
    
    @pytest.mark.acceptance
    @pytest.mark.fast
    def test_search_functionality(self):
        """测试搜索功能"""
        import tempfile
        import os
        
        # 创建临时数据库
        db_fd, db_path = tempfile.mkstemp(suffix=".db")
        os.close(db_fd)
        
        try:
            from db import Database
            test_db = Database(db_path)
            test_db.init_database()
            
            # 添加测试数据
            province_id = test_db.upsert_province("江苏省", "JS")
            city_id = test_db.upsert_city(province_id, "南京市", "NJ")
            district_id = test_db.upsert_district(city_id, "玄武区", "XW")
            test_db.upsert_hospital(district_id, "南京市玄武医院", "http://test1.com", 0.9)
            test_db.upsert_hospital(district_id, "玄武区人民医院", "http://test2.com", 0.8)
            
            # 测试医院搜索
            search_results = test_db.search_hospitals("人民医院")
            assert search_results['total'] == 1
            assert search_results['items'][0]['name'] == "玄武区人民医院"
            
            search_results2 = test_db.search_hospitals("玄武")
            assert search_results2['total'] == 2
            
            print("✅ 搜索功能测试通过")
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)
    
    @pytest.mark.acceptance
    @pytest.mark.fast
    def test_error_handling(self):
        """测试错误处理"""
        import tempfile
        import os
        
        # 创建临时数据库
        db_fd, db_path = tempfile.mkstemp(suffix=".db")
        os.close(db_fd)
        
        try:
            from db import Database
            test_db = Database(db_path)
            test_db.init_database()
            
            # 测试查询不存在的记录
            province = test_db.get_province(name="不存在的省")
            assert province is None
            
            city = test_db.get_city(name="不存在的市", province_id=999)
            assert city is None
            
            district = test_db.get_district(name="不存在的区", city_id=999)
            assert district is None
            
            hospital = test_db.get_hospital(name="不存在的医院", district_id=999)
            assert hospital is None
            
            # 测试无效的分页参数
            provinces = test_db.get_all_provinces(page=0, page_size=10)
            assert provinces['page'] == 1  # 应该被修正为1
            
            print("✅ 错误处理测试通过")
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)


# 独立测试函数
@pytest.mark.acceptance
@pytest.mark.fast
def test_basic_api_endpoints():
    """测试基本API端点"""
    from main import app
    client = TestClient(app)
    
    # 测试根路径
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()['code'] == 200
    
    # 测试健康检查
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()['code'] == 200
    
    print("✅ 基本API端点测试通过")


@pytest.mark.acceptance
@pytest.mark.fast
def test_pagination_functionality():
    """测试分页功能"""
    import tempfile
    import os
    
    # 创建临时数据库
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(db_fd)
    
    try:
        from db import Database
        test_db = Database(db_path)
        test_db.init_database()
        
        # 创建多个省份
        for i in range(5):
            test_db.upsert_province(f"测试省{i+1}", f"TEST{i+1}")
        
        # 测试分页
        page1 = test_db.get_all_provinces(page=1, page_size=3)
        assert page1['page'] == 1
        assert page1['page_size'] == 3
        assert page1['total'] == 5
        assert page1['total_pages'] == 2
        assert len(page1['items']) == 3
        
        page2 = test_db.get_all_provinces(page=2, page_size=3)
        assert page2['page'] == 2
        assert len(page2['items']) == 2
        
        print("✅ 分页功能测试通过")
    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)


@pytest.mark.acceptance
@pytest.mark.performance
def test_database_performance():
    """数据库性能测试"""
    import tempfile
    import os
    import time
    
    # 创建临时数据库
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(db_fd)
    
    try:
        from db import Database
        test_db = Database(db_path)
        test_db.init_database()
        
        # 测试批量插入性能
        start_time = time.time()
        
        # 插入100个省份
        for i in range(100):
            test_db.upsert_province(f"性能测试省{i}", f"PERF{i}")
        
        insert_time = time.time() - start_time
        
        # 插入应该少于5秒
        assert insert_time < 5.0, f"批量插入耗时 {insert_time:.2f}s 超过5秒"
        
        # 测试查询性能
        start_time = time.time()
        
        for i in range(100):
            test_db.get_province(name=f"性能测试省{i}")
        
        query_time = time.time() - start_time
        
        # 查询应该少于2秒
        assert query_time < 2.0, f"批量查询耗时 {query_time:.2f}s 超过2秒"
        
        print(f"✅ 数据库性能测试通过 (插入: {insert_time:.2f}s, 查询: {query_time:.2f}s)")
    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)


if __name__ == "__main__":
    # 运行所有验收测试
    pytest.main([__file__, "-v", "--tb=short", "-m", "acceptance"])
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
医院层级扫查微服务 - 数据库测试
"""

import pytest
import asyncio
import tempfile
import os
import sqlite3
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
import json

from db import Database, get_db, init_db


class TestDatabase:
    """数据库测试类"""
    
    @pytest.fixture
    def temp_db_path(self):
        """创建临时数据库路径"""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as f:
            yield f.name
        os.unlink(f.name)
    
    @pytest.fixture
    def test_db(self, temp_db_path):
        """创建测试数据库实例"""
        return Database(temp_db_path)
    
    @pytest.mark.asyncio
    async def test_init_db_success(self, test_db):
        """测试数据库初始化成功"""
        # 执行初始化
        await test_db.init_db()
        
        # 验证数据库文件创建
        assert os.path.exists(test_db.db_path)
        
        # 验证表创建
        with sqlite3.connect(test_db.db_path) as conn:
            cursor = conn.cursor()
            
            # 检查任务表
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='tasks'
            """)
            assert cursor.fetchone() is not None
            
            # 检查医院信息表
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='hospital_info'
            """)
            assert cursor.fetchone() is not None
            
            # 检查索引
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='index' AND name='idx_tasks_status'
            """)
            assert cursor.fetchone() is not None
    
    @pytest.mark.asyncio
    async def test_init_db_failure(self, temp_db_path):
        """测试数据库初始化失败"""
        # 模拟数据库初始化失败
        with patch('sqlite3.connect') as mock_connect:
            mock_connect.side_effect = sqlite3.Error("数据库连接失败")
            
            test_db = Database(temp_db_path)
            
            with pytest.raises(sqlite3.Error):
                await test_db.init_db()
    
    @pytest.mark.asyncio
    async def test_create_task_success(self, test_db):
        """测试创建任务成功"""
        await test_db.init_db()
        
        task_id = "test-task-123"
        hospital_name = "测试医院"
        query = "查询医院信息"
        status = "pending"
        
        result = await test_db.create_task(task_id, hospital_name, query, status)
        
        assert result is True
        
        # 验证任务创建
        with sqlite3.connect(test_db.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tasks WHERE task_id = ?", (task_id,))
            row = cursor.fetchone()
            assert row is not None
            assert row[1] == hospital_name
            assert row[2] == query
            assert row[3] == status
    
    @pytest.mark.asyncio
    async def test_create_task_duplicate(self, test_db):
        """测试创建重复任务（唯一约束）"""
        await test_db.init_db()
        
        task_id = "test-task-456"
        hospital_name = "测试医院2"
        query = "查询医院信息2"
        status = "pending"
        
        # 第一次创建成功
        result1 = await test_db.create_task(task_id, hospital_name, query, status)
        assert result1 is True
        
        # 第二次创建应该失败（违反唯一约束）
        result2 = await test_db.create_task(task_id, hospital_name, query, status)
        assert result2 is False
    
    @pytest.mark.asyncio
    async def test_create_task_failure(self, test_db):
        """测试创建任务失败"""
        await test_db.init_db()
        
        with patch('sqlite3.connect') as mock_connect:
            mock_conn = Mock()
            mock_connect.return_value.__enter__.return_value = mock_conn
            mock_conn.cursor.return_value.execute.side_effect = sqlite3.Error("插入失败")
            
            result = await test_db.create_task("test-id", "test-hospital", "test-query", "pending")
            assert result is False
    
    @pytest.mark.asyncio
    async def test_update_task_status_success(self, test_db):
        """测试更新任务状态成功"""
        await test_db.init_db()
        
        # 先创建任务
        task_id = "test-task-789"
        await test_db.create_task(task_id, "测试医院", "查询", "pending")
        
        # 更新状态
        new_status = "running"
        result = await test_db.update_task_status(task_id, new_status)
        
        assert result is True
        
        # 验证状态更新
        with sqlite3.connect(test_db.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT status FROM tasks WHERE task_id = ?", (task_id,))
            row = cursor.fetchone()
            assert row[0] == new_status
    
    @pytest.mark.asyncio
    async def test_update_task_status_with_error(self, test_db):
        """测试更新任务状态并设置错误信息"""
        await test_db.init_db()
        
        task_id = "test-task-101"
        await test_db.create_task(task_id, "测试医院", "查询", "pending")
        
        error_msg = "任务执行失败"
        result = await test_db.update_task_status(task_id, "failed", error_msg)
        
        assert result is True
        
        # 验证错误信息保存
        with sqlite3.connect(test_db.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT status, error_message FROM tasks WHERE task_id = ?", (task_id,))
            row = cursor.fetchone()
            assert row[0] == "failed"
            assert row[1] == error_msg
    
    @pytest.mark.asyncio
    async def test_update_task_status_not_found(self, test_db):
        """测试更新不存在的任务状态"""
        await test_db.init_db()
        
        result = await test_db.update_task_status("non-existent-task", "running")
        assert result is False
    
    @pytest.mark.asyncio
    async def test_save_task_result_success(self, test_db):
        """测试保存任务结果成功"""
        await test_db.init_db()
        
        task_id = "test-task-202"
        await test_db.create_task(task_id, "测试医院", "查询", "running")
        
        result_data = {
            "hospital_info": {
                "hospital_name": "测试医院",
                "level": "二级医院",
                "address": "北京市朝阳区测试路1号"
            },
            "report": "医院分析报告"
        }
        
        result = await test_db.save_task_result(task_id, result_data)
        
        assert result is True
        
        # 验证结果保存
        retrieved_result = await test_db.get_task_result(task_id)
        assert retrieved_result is not None
        assert retrieved_result["hospital_info"]["hospital_name"] == "测试医院"
    
    @pytest.mark.asyncio
    async def test_save_task_result_failure(self, test_db):
        """测试保存任务结果失败"""
        await test_db.init_db()
        
        with patch('sqlite3.connect') as mock_connect:
            mock_conn = Mock()
            mock_connect.return_value.__enter__.return_value = mock_conn
            mock_conn.cursor.return_value.execute.side_effect = sqlite3.Error("更新失败")
            
            result = await test_db.save_task_result("test-id", {})
            assert result is False
    
    @pytest.mark.asyncio
    async def test_get_task_success(self, test_db):
        """测试获取任务成功"""
        await test_db.init_db()
        
        task_id = "test-task-303"
        hospital_name = "测试医院3"
        await test_db.create_task(task_id, hospital_name, "查询", "pending")
        
        task = await test_db.get_task(task_id)
        
        assert task is not None
        assert task["task_id"] == task_id
        assert task["hospital_name"] == hospital_name
        assert task["status"] == "pending"
    
    @pytest.mark.asyncio
    async def test_get_task_not_found(self, test_db):
        """测试获取不存在的任务"""
        await test_db.init_db()
        
        task = await test_db.get_task("non-existent-task")
        assert task is None
    
    @pytest.mark.asyncio
    async def test_get_task_result_success(self, test_db):
        """测试获取任务结果成功"""
        await test_db.init_db()
        
        task_id = "test-task-404"
        await test_db.create_task(task_id, "测试医院", "查询", "completed")
        
        result_data = {
            "status": "completed",
            "hospital_info": {
                "hospital_name": "测试医院",
                "level": "三级医院"
            }
        }
        
        await test_db.save_task_result(task_id, result_data)
        
        result = await test_db.get_task_result(task_id)
        
        assert result is not None
        assert result["status"] == "completed"
        assert result["hospital_info"]["hospital_name"] == "测试医院"
    
    @pytest.mark.asyncio
    async def test_get_task_result_not_found(self, test_db):
        """测试获取不存在任务的结果"""
        await test_db.init_db()
        
        result = await test_db.get_task_result("non-existent-task")
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_task_result_no_result(self, test_db):
        """测试获取没有结果的任务"""
        await test_db.init_db()
        
        task_id = "test-task-505"
        await test_db.create_task(task_id, "测试医院", "查询", "pending")
        
        result = await test_db.get_task_result(task_id)
        assert result is None
    
    @pytest.mark.asyncio
    async def test_list_tasks_success(self, test_db):
        """测试获取任务列表成功"""
        await test_db.init_db()
        
        # 创建多个任务
        tasks_data = [
            ("task-1", "医院1", "query1", "pending"),
            ("task-2", "医院2", "query2", "running"),
            ("task-3", "医院3", "query3", "completed")
        ]
        
        for task_id, hospital_name, query, status in tasks_data:
            await test_db.create_task(task_id, hospital_name, query, status)
        
        # 获取任务列表
        tasks = await test_db.list_tasks(limit=10)
        
        assert len(tasks) == 3
        assert all("task_id" in task for task in tasks)
        assert all("hospital_name" in task for task in tasks)
    
    @pytest.mark.asyncio
    async def test_list_tasks_with_limit(self, test_db):
        """测试分页获取任务列表"""
        await test_db.init_db()
        
        # 创建5个任务
        for i in range(5):
            await test_db.create_task(f"task-{i}", f"医院{i}", f"query{i}", "pending")
        
        # 限制为3个
        tasks = await test_db.list_tasks(limit=3)
        assert len(tasks) == 3
    
    @pytest.mark.asyncio
    async def test_list_tasks_empty(self, test_db):
        """测试获取空任务列表"""
        await test_db.init_db()
        
        tasks = await test_db.list_tasks()
        assert tasks == []
    
    @pytest.mark.asyncio
    async def test_list_tasks_failure(self, test_db):
        """测试获取任务列表失败"""
        await test_db.init_db()
        
        with patch('sqlite3.connect') as mock_connect:
            mock_conn = Mock()
            mock_connect.return_value.__enter__.return_value = mock_conn
            mock_conn.cursor.return_value.execute.side_effect = sqlite3.Error("查询失败")
            
            tasks = await test_db.list_tasks()
            assert tasks == []
    
    @pytest.mark.asyncio
    async def test_save_hospital_info_success(self, test_db):
        """测试保存医院信息成功"""
        await test_db.init_db()
        
        task_id = "test-task-606"
        await test_db.create_task(task_id, "测试医院", "查询", "running")
        
        hospital_info = {
            "hospital_name": "测试医院",
            "level": "二级甲等",
            "address": "北京市朝阳区测试路100号",
            "phone": "010-12345678",
            "departments": ["内科", "外科", "妇产科"],
            "beds_count": 200,
            "staff_count": 300,
            "specializations": ["心血管科", "神经内科"]
        }
        
        result = await test_db.save_hospital_info(task_id, hospital_info)
        
        assert result is True
        
        # 验证信息保存
        with sqlite3.connect(test_db.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT hospital_name, level, address, phone, beds_count, staff_count
                FROM hospital_info WHERE task_id = ?
            """, (task_id,))
            
            row = cursor.fetchone()
            assert row is not None
            assert row[0] == "测试医院"
            assert row[1] == "二级甲等"
            assert row[2] == "北京市朝阳区测试路100号"
            assert row[3] == "010-12345678"
            assert row[4] == 200
            assert row[5] == 300
    
    @pytest.mark.asyncio
    async def test_save_hospital_info_with_json_fields(self, test_db):
        """测试保存包含JSON字段的医院信息"""
        await test_db.init_db()
        
        task_id = "test-task-707"
        await test_db.create_task(task_id, "测试医院", "查询", "running")
        
        hospital_info = {
            "hospital_name": "测试医院",
            "departments": ["内科", "外科", "妇产科"],
            "specializations": ["心血管科", "神经内科"]
        }
        
        result = await test_db.save_hospital_info(task_id, hospital_info)
        assert result is True
        
        # 验证JSON字段正确保存
        with sqlite3.connect(test_db.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT departments, specializations FROM hospital_info WHERE task_id = ?
            """, (task_id,))
            
            row = cursor.fetchone()
            assert row is not None
            
            # 验证JSON字符串能正确解析
            departments = json.loads(row[0])
            specializations = json.loads(row[1])
            
            assert departments == ["内科", "外科", "妇产科"]
            assert specializations == ["心血管科", "神经内科"]
    
    @pytest.mark.asyncio
    async def test_save_hospital_info_failure(self, test_db):
        """测试保存医院信息失败"""
        await test_db.init_db()
        
        with patch('sqlite3.connect') as mock_connect:
            mock_conn = Mock()
            mock_connect.return_value.__enter__.return_value = mock_conn
            mock_conn.cursor.return_value.execute.side_effect = sqlite3.Error("插入失败")
            
            result = await test_db.save_hospital_info("test-task", {})
            assert result is False
    
    @pytest.mark.asyncio
    async def test_fuzzy_search_functionality(self, test_db):
        """测试模糊搜索功能（通过LIKE查询）"""
        await test_db.init_db()
        
        # 创建包含不同医院名称的任务
        hospitals = [
            "北京大学人民医院",
            "北京天坛医院",
            "北京协和医院",
            "上海华山医院",
            "复旦大学附属中山医院"
        ]
        
        for i, hospital_name in enumerate(hospitals):
            await test_db.create_task(f"task-{i}", hospital_name, "查询", "pending")
        
        # 测试搜索功能
        with sqlite3.connect(test_db.db_path) as conn:
            cursor = conn.cursor()
            
            # 搜索包含"北京"的医院
            cursor.execute("""
                SELECT hospital_name FROM tasks 
                WHERE hospital_name LIKE '%北京%'
            """)
            
            results = cursor.fetchall()
            assert len(results) == 3  # 北京大学人民医院、北京天坛医院、北京协和医院
            
            # 搜索包含"医院"的医院
            cursor.execute("""
                SELECT hospital_name FROM tasks 
                WHERE hospital_name LIKE '%医院%'
            """)
            
            results = cursor.fetchall()
            assert len(results) == 5  # 所有医院都包含"医院"
            
            # 搜索以"北京"开头的医院
            cursor.execute("""
                SELECT hospital_name FROM tasks 
                WHERE hospital_name LIKE '北京%'
            """)
            
            results = cursor.fetchall()
            assert len(results) == 3


class TestDatabaseFactory:
    """数据库工厂函数测试"""
    
    @pytest.mark.asyncio
    async def test_get_dbingleton(self):
        """测试数据库单例模式"""
        db1 = await get_db()
        db2 = await get_db()
        
        assert db1 is db2  # 应该是同一个实例
    
    @pytest.mark.asyncio
    async def test_init_db(self):
        """测试数据库初始化工厂函数"""
        with patch('db.get_db') as mock_get_db:
            mock_db = AsyncMock()
            mock_get_db.return_value = mock_db
            
            db = await init_db()
            
            assert db is mock_db
            mock_db.init_db.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__])
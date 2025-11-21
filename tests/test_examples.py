"""
示例测试文件 - 展示如何使用测试工具和夹具
"""

import pytest
import json
import sqlite3
from unittest.mock import patch, Mock
from fastapi.testclient import TestClient

# 测试标记
pytestmark = pytest.mark.unit


class TestExample:
    """示例测试类"""
    
    def test_fastapi_client(self, fastapi_client):
        """测试FastAPI客户端"""
        response = fastapi_client.get("/")
        assert response.status_code == 200
    
    def test_mock_llm_client(self, mock_llm_client):
        """测试Mock LLM客户端"""
        result = mock_llm_client.generate_response("测试输入")
        
        assert "response" in result
        assert "confidence" in result
        assert result["confidence"] == 0.95
    
    def test_database_operations(self, clean_test_data, test_hospital_data):
        """测试数据库操作"""
        conn = clean_test_data
        cursor = conn.cursor()
        
        # 插入测试数据
        cursor.execute("""
            INSERT INTO hospitals (name, address, phone, email, website)
            VALUES (?, ?, ?, ?, ?)
        """, (
            test_hospital_data["name"],
            test_hospital_data["address"],
            test_hospital_data["phone"],
            test_hospital_data["email"],
            test_hospital_data["website"]
        ))
        
        conn.commit()
        
        # 验证插入
        cursor.execute("SELECT * FROM hospitals WHERE name = ?", 
                      (test_hospital_data["name"],))
        result = cursor.fetchone()
        
        assert result is not None
        assert result["name"] == test_hospital_data["name"]
    
    def test_sample_data_usage(self, test_hospital_data):
        """测试样本数据使用"""
        # 使用test_hospital_data夹具
        assert len(test_hospital_data["name"]) > 0
        assert "name" in test_hospital_data
        assert "address" in test_hospital_data
        assert "phone" in test_hospital_data
    
    @pytest.mark.mock
    def test_mock_http_responses(self, mock_requests_response):
        """测试Mock HTTP响应"""
        assert mock_requests_response.status_code == 200
        assert "测试医院" in mock_requests_response.text
        assert "010-12345678" in mock_requests_response.text
    
    def test_database_rollback(self, test_db):
        """测试数据库回滚"""
        conn = sqlite3.connect(test_db)
        cursor = conn.cursor()
        
        # 开始事务
        cursor.execute("BEGIN TRANSACTION")
        
        # 插入数据
        cursor.execute("INSERT INTO hospitals (name) VALUES (?)", ("测试医院",))
        
        # 回滚事务
        cursor.execute("ROLLBACK")
        
        # 验证数据不存在
        cursor.execute("SELECT COUNT(*) FROM hospitals WHERE name = ?", ("测试医院",))
        count = cursor.fetchone()[0]
        
        assert count == 0
        conn.close()
    
    @pytest.mark.slow
    def test_performance_example(self):
        """性能测试示例"""
        import time
        
        start_time = time.time()
        
        # 模拟耗时操作
        time.sleep(0.1)
        
        end_time = time.time()
        duration = end_time - start_time
        
        assert duration < 1.0  # 确保在1秒内完成
    
    @pytest.mark.parametrize("hospital_data", [
        {"name": "测试医院", "phone": "010-12345678"},
        {"name": "另一个医院", "phone": "021-87654321"}
    ])
    def test_hospital_validation(self, hospital_data):
        """参数化测试示例"""
        # 验证医院数据
        assert len(hospital_data["name"]) > 0
        
        # 验证电话号码格式（简单验证）
        phone = hospital_data.get("phone", "")
        if phone and phone != "invalid":
            assert len(phone) >= 10
    
    def test_exception_handling(self):
        """异常处理测试示例"""
        with pytest.raises(ValueError) as exc_info:
            # 这里应该抛出异常
            raise ValueError("测试异常")
        
        assert "测试异常" in str(exc_info.value)
    
    def test_file_operations(self, tmp_path):
        """文件操作测试示例"""
        # 创建临时文件
        test_file = tmp_path / "test.txt"
        test_file.write_text("测试内容")
        
        # 验证文件内容
        assert test_file.exists()
        assert test_file.read_text() == "测试内容"
    
    def test_json_operations(self):
        """JSON操作测试示例"""
        # 创建测试JSON数据
        success_response = {
            "success": True,
            "data": {"title": "测试医院官网"}
        }
        assert success_response["success"] is True
        assert "data" in success_response
        
        # 测试失败的响应
        error_response = {
            "success": False,
            "error": "扫描失败"
        }
        assert error_response["success"] is False
        assert "error" in error_response
    
    @patch('requests.get')
    def test_api_mocking(self, mock_get):
        """API Mock测试示例"""
        # 设置mock返回值
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "success": True,
            "data": {"title": "测试医院官网"}
        }
        mock_get.return_value = mock_response
        
        # 执行测试
        import requests
        response = requests.get("http://test-api.com/hospital/1")
        
        # 验证
        assert response.status_code == 200
        assert response.json()["success"] is True
        mock_get.assert_called_once_with("http://test-api.com/hospital/1")
    
    def test_context_managers(self):
        """上下文管理器测试示例"""
        # 测试文件上下文管理器
        with open("/tmp/test.txt", "w") as f:
            f.write("测试内容")
        
        # 测试完成后文件应该存在
        with open("/tmp/test.txt", "r") as f:
            content = f.read()
            assert content == "测试内容"
    
    @pytest.mark.skip(reason="跳过的测试示例")
    def test_skipped_example(self):
        """跳过的测试示例"""
        assert False, "这个测试应该被跳过"
    
    @pytest.mark.xfail(reason="预期失败的测试示例")
    def test_expected_failure(self):
        """预期失败的测试示例"""
        assert False, "这个测试预期失败"
    
    def test_timeout_example(self):
        """超时测试示例"""
        import time
        
        # 这个测试应该在合理时间内完成
        time.sleep(0.01)  # 很短的延迟
        
        assert True


@pytest.mark.integration
class TestIntegration:
    """集成测试类"""
    
    def test_full_workflow(self, clean_test_data, test_hospital_data):
        """完整的业务流程测试"""
        conn = clean_test_data
        
        # 1. 创建医院
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO hospitals (name, address, phone, email)
            VALUES (?, ?, ?, ?)
        """, (
            test_hospital_data["name"],
            test_hospital_data["address"],
            test_hospital_data["phone"],
            test_hospital_data["email"]
        ))
        hospital_id = cursor.lastrowid
        
        # 2. 创建扫描任务
        scan_results = [
            {"scan_type": "website_analysis", "status": "completed", "result_data": {"title": "测试网站"}},
            {"scan_type": "phone_validation", "status": "completed", "result_data": {"valid": True}}
        ]
        
        for scan_result in scan_results:
            cursor.execute("""
                INSERT INTO scan_results (hospital_id, scan_type, status, result_data)
                VALUES (?, ?, ?, ?)
            """, (
                hospital_id,
                scan_result["scan_type"],
                scan_result["status"],
                json.dumps(scan_result["result_data"])
            ))
        
        conn.commit()
        
        # 3. 验证数据完整性
        cursor.execute("SELECT COUNT(*) FROM hospitals WHERE id = ?", (hospital_id,))
        hospital_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM scan_results WHERE hospital_id = ?", (hospital_id,))
        scan_count = cursor.fetchone()[0]
        
        assert hospital_count == 1
        assert scan_count == len(scan_results)
    
    def test_api_integration(self, fastapi_client, test_hospital_data):
        """API集成测试"""
        # 测试创建医院
        response = fastapi_client.post("/hospitals", json=test_hospital_data)
        
        if response.status_code == 201:
            created_hospital = response.json()
            assert created_hospital["name"] == test_hospital_data["name"]
            
            # 测试获取医院列表
            list_response = fastapi_client.get("/hospitals")
            assert list_response.status_code == 200
            assert len(list_response.json()) > 0
    
    def test_external_api_simulation(self):
        """外部API模拟测试"""
        # 模拟外部API调用
        api_response = {
            "success": True,
            "data": {"title": "测试医院官网", "contact": "010-12345678"}
        }
        
        # 验证响应结构
        assert "success" in api_response
        assert "data" in api_response
        
        # 验证数据类型
        assert isinstance(api_response["success"], bool)
        assert isinstance(api_response["data"], dict)


@pytest.mark.performance
class TestPerformance:
    """性能测试类"""
    
    def test_large_dataset_handling(self, clean_test_data):
        """大数据集处理测试"""
        conn = clean_test_data
        cursor = conn.cursor()
        
        # 批量插入大量数据
        hospitals = []
        for i in range(100):
            hospitals.append((f"医院{i}", f"地址{i}", f"010-{i:08d}"))
        
        cursor.executemany("""
            INSERT INTO hospitals (name, address, phone)
            VALUES (?, ?, ?)
        """, hospitals)
        
        conn.commit()
        
        # 验证插入成功
        cursor.execute("SELECT COUNT(*) FROM hospitals")
        count = cursor.fetchone()[0]
        
        assert count == 100
    
    def test_concurrent_operations(self):
        """并发操作测试"""
        import threading
        import time
        
        results = []
        
        def create_hospital(hospital_id):
            # 模拟创建医院操作
            time.sleep(0.01)  # 短暂延迟
            results.append(hospital_id)
        
        # 创建多个线程
        threads = []
        for i in range(10):
            thread = threading.Thread(target=create_hospital, args=(i,))
            threads.append(thread)
            thread.start()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join()
        
        assert len(results) == 10
        assert sorted(results) == list(range(10))


# 辅助函数
def setup_test_hospital_data():
    """设置测试医院数据"""
    return {
        "name": "测试医院",
        "address": "北京市朝阳区测试街道123号",
        "phone": "010-12345678",
        "email": "test@test.com",
        "website": "http://test.com"
    }


# 如果直接运行此文件
if __name__ == "__main__":
    print("示例测试文件已创建")
    print("要运行这些测试，请执行：")
    print("  pytest tests/test_examples.py -v")

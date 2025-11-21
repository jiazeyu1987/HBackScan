"""
测试辅助工具和帮助函数
"""

import os
import sqlite3
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional
import json
import logging
from datetime import datetime


def init_test_db(db_path: str = None) -> str:
    """初始化测试数据库"""
    if not db_path:
        # 创建临时数据库文件
        db_fd, db_path = tempfile.mkstemp(suffix=".db")
        os.close(db_fd)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 创建医院表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS hospitals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            address TEXT,
            phone TEXT,
            email TEXT,
            website TEXT,
            license_number TEXT,
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 创建扫描结果表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS scan_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hospital_id INTEGER,
            scan_type TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            result_data TEXT,
            error_message TEXT,
            started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            FOREIGN KEY (hospital_id) REFERENCES hospitals (id)
        )
    """)
    
    # 创建任务表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_type TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            total_items INTEGER DEFAULT 0,
            completed_items INTEGER DEFAULT 0,
            failed_items INTEGER DEFAULT 0,
            progress REAL DEFAULT 0.0,
            result_summary TEXT,
            started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP
        )
    """)
    
    # 创建索引
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_hospitals_name ON hospitals(name)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_scan_results_hospital_id ON scan_results(hospital_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_scan_results_type ON scan_results(scan_type)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)")
    
    conn.commit()
    conn.close()
    
    return db_path


def migrate_test_db(db_path: str):
    """运行数据库迁移"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 添加测试数据
    test_hospitals = [
        ("北京协和医院", "北京市东城区王府井大街1号", "010-69156114", "info@cams.cn", "http://www.cams.cn", "110000000000001"),
        ("上海华山医院", "上海市静安区乌鲁木齐中路12号", "021-52889999", "info@huashan.org.cn", "http://www.huashan.org.cn", "310000000000002"),
        ("测试医院", "北京市朝阳区测试街道123号", "010-12345678", "test@test.com", "http://test.com", "TEST123")
    ]
    
    cursor.executemany("""
        INSERT INTO hospitals (name, address, phone, email, website, license_number)
        VALUES (?, ?, ?, ?, ?, ?)
    """, test_hospitals)
    
    # 添加测试扫描结果
    test_results = [
        (1, "website_analysis", "completed", '{"title": "北京协和医院官网", "contact_found": true}'),
        (1, "license_validation", "completed", '{"valid": true, "expiry": "2028-12-31"}'),
        (2, "website_analysis", "failed", None, "网站无法访问")
    ]
    
    cursor.executemany("""
        INSERT INTO scan_results (hospital_id, scan_type, status, result_data, error_message)
        VALUES (?, ?, ?, ?, ?)
    """, test_results)
    
    conn.commit()
    conn.close()


def cleanup_test_db(db_path: str):
    """清理测试数据库"""
    if os.path.exists(db_path):
        os.unlink(db_path)


def setup_test_logging():
    """设置测试日志"""
    # 创建测试日志目录
    log_dir = Path("tests/logs")
    log_dir.mkdir(exist_ok=True)
    
    # 配置日志格式
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # 创建文件处理器
    file_handler = logging.FileHandler(log_dir / "test.log")
    file_handler.setFormatter(logging.Formatter(log_format))
    
    # 配置根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(file_handler)


def create_test_config() -> Dict[str, Any]:
    """创建测试配置"""
    return {
        "database": {
            "url": "sqlite:///test_data.db",
            "echo": False
        },
        "llm": {
            "api_key": "test-api-key",
            "model": "test-model",
            "timeout": 30,
            "max_retries": 3
        },
        "scanner": {
            "timeout": 30,
            "max_concurrent": 5,
            "retry_attempts": 3,
            "user_agent": "TestScanner/1.0"
        },
        "api": {
            "host": "localhost",
            "port": 8000,
            "debug": True,
            "reload": False
        },
        "logging": {
            "level": "DEBUG",
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        }
    }


def load_test_data(data_type: str) -> Any:
    """加载测试数据"""
    from tests.fixtures.sample_data import (
        SAMPLE_HOSPITALS,
        SAMPLE_SCAN_RESULTS,
        SAMPLE_TASKS,
        INVALID_TEST_DATA,
        BOUNDARY_TEST_DATA
    )
    from tests.fixtures.mock_json_responses import SUCCESS_RESPONSES, ERROR_RESPONSES
    
    data_map = {
        "hospitals": SAMPLE_HOSPITALS,
        "scan_results": SAMPLE_SCAN_RESULTS,
        "tasks": SAMPLE_TASKS,
        "invalid_data": INVALID_TEST_DATA,
        "boundary_data": BOUNDARY_TEST_DATA,
        "success_responses": SUCCESS_RESPONSES,
        "error_responses": ERROR_RESPONSES
    }
    
    return data_map.get(data_type, {})


def create_mock_response(status_code: int, json_data: Dict[str, Any] = None, text: str = None) -> Dict[str, Any]:
    """创建模拟HTTP响应"""
    response = {
        "status_code": status_code,
        "headers": {"Content-Type": "application/json"},
        "elapsed": {"total_seconds": lambda: 0.5}
    }
    
    if json_data is not None:
        response["json"] = lambda: json_data
        response["content"] = json.dumps(json_data).encode()
    
    if text is not None:
        response["text"] = text
        response["content"] = text.encode()
    
    if status_code >= 400:
        response["raise_for_status"] = lambda: Exception(f"HTTP {status_code} Error")
    
    return response


def assert_response_structure(response: Dict[str, Any], expected_keys: List[str]):
    """断言响应结构"""
    for key in expected_keys:
        assert key in response, f"响应中缺少键: {key}"


def validate_test_data(data: Dict[str, Any], validation_rules: Dict[str, Any]):
    """验证测试数据"""
    for field, rule in validation_rules.items():
        value = data.get(field)
        
        if rule.get("required", False):
            assert value is not None, f"必填字段 {field} 不能为空"
        
        if "type" in rule:
            assert isinstance(value, rule["type"]), f"字段 {field} 类型错误，期望 {rule['type']}"
        
        if "choices" in rule:
            assert value in rule["choices"], f"字段 {field} 值不正确，期望在 {rule['choices']} 中"
        
        if "min_length" in rule:
            assert len(str(value)) >= rule["min_length"], f"字段 {field} 长度不足"


def create_test_markers():
    """创建测试标记"""
    return {
        "unit": "单元测试",
        "integration": "集成测试", 
        "slow": "慢速测试",
        "fast": "快速测试",
        "database": "数据库测试",
        "network": "网络测试",
        "api": "API测试",
        "llm": "LLM测试",
        "mock": "模拟测试",
        "smoke": "冒烟测试",
        "regression": "回归测试",
        "performance": "性能测试",
        "security": "安全测试"
    }


def setup_test_environment():
    """设置测试环境"""
    # 设置环境变量
    os.environ.update({
        "TESTING": "true",
        "DATABASE_URL": "sqlite:///test_data.db",
        "LOG_LEVEL": "DEBUG",
        "API_KEY": "test-key",
        "LLM_API_KEY": "test-llm-key"
    })
    
    # 创建必要目录
    directories = ["tests/logs", "test-reports", "htmlcov"]
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
    
    # 设置日志
    setup_test_logging()
    
    # 初始化测试数据库
    init_test_db("test_data.db")


def cleanup_test_environment():
    """清理测试环境"""
    # 清理环境变量
    test_vars = ["TESTING", "DATABASE_URL", "LOG_LEVEL", "API_KEY", "LLM_API_KEY"]
    for var in test_vars:
        os.environ.pop(var, None)
    
    # 清理临时文件
    cleanup_files = [
        "test_data.db",
        "test_data.db-journal",
        "pytest.log",
        "coverage.xml"
    ]
    
    for file_path in cleanup_files:
        if os.path.exists(file_path):
            os.unlink(file_path)
    
    # 清理临时目录
    temp_dirs = ["__pycache__", ".pytest_cache", ".coverage"]
    for temp_dir in temp_dirs:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)


class TestDataFactory:
    """测试数据工厂类"""
    
    @staticmethod
    def create_hospital(overrides: Dict[str, Any] = None) -> Dict[str, Any]:
        """创建医院测试数据"""
        default_data = {
            "name": "测试医院",
            "address": "北京市朝阳区测试街道123号",
            "phone": "010-12345678",
            "email": "test@test.com",
            "website": "http://test.com",
            "license_number": "TEST123"
        }
        
        if overrides:
            default_data.update(overrides)
        
        return default_data
    
    @staticmethod
    def create_scan_result(overrides: Dict[str, Any] = None) -> Dict[str, Any]:
        """创建扫描结果测试数据"""
        default_data = {
            "hospital_id": 1,
            "scan_type": "website_analysis",
            "status": "pending",
            "result_data": None,
            "error_message": None
        }
        
        if overrides:
            default_data.update(overrides)
        
        return default_data
    
    @staticmethod
    def create_task(overrides: Dict[str, Any] = None) -> Dict[str, Any]:
        """创建任务测试数据"""
        default_data = {
            "task_type": "batch_scan",
            "status": "pending",
            "total_items": 0,
            "completed_items": 0,
            "failed_items": 0,
            "progress": 0.0,
            "result_summary": None
        }
        
        if overrides:
            default_data.update(overrides)
        
        return default_data


class MockHTTPResponse:
    """模拟HTTP响应类"""
    
    def __init__(self, status_code: int = 200, json_data: Dict[str, Any] = None, text: str = None):
        self.status_code = status_code
        self.headers = {"Content-Type": "application/json"}
        
        if json_data is not None:
            self.json_data = json_data
            self.text = json.dumps(json_data, ensure_ascii=False)
            self.content = self.text.encode()
        
        if text is not None:
            self.text = text
            self.content = text.encode()
    
    def json(self):
        return self.json_data
    
    def raise_for_status(self):
        if self.status_code >= 400:
            raise Exception(f"HTTP {self.status_code} Error")


# 如果直接运行此文件
if __name__ == "__main__":
    print("测试辅助工具已加载")
    print("可用函数:")
    print("- init_test_db(): 初始化测试数据库")
    print("- migrate_test_db(): 运行数据库迁移")
    print("- setup_test_environment(): 设置测试环境")
    print("- cleanup_test_environment(): 清理测试环境")
    print("- TestDataFactory: 测试数据工厂类")

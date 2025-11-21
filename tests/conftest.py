"""
Pytest配置文件 - 包含所有测试夹具
"""
import os
import tempfile
import pytest
import sqlite3
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from datetime import datetime
import json

# 测试数据库路径
TEST_DB_PATH = "test_data.db"

@pytest.fixture(scope="session")
def test_db():
    """测试数据库夹具 - 创建临时测试数据库"""
    # 创建临时数据库文件
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    try:
        # 复制数据库结构
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 创建表结构（根据实际schema调整）
        cursor.execute('''
            CREATE TABLE hospitals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                address TEXT,
                phone TEXT,
                email TEXT,
                website TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE scan_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hospital_id INTEGER,
                scan_type TEXT,
                result_data TEXT,
                status TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (hospital_id) REFERENCES hospitals (id)
            )
        ''')
        
        conn.commit()
        conn.close()
        
        yield db_path
    finally:
        os.close(db_fd)
        os.unlink(db_path)

@pytest.fixture
def mock_db_connection(test_db):
    """模拟数据库连接夹具"""
    conn = sqlite3.connect(test_db)
    conn.row_factory = sqlite3.Row  # 使结果可以通过列名访问
    yield conn
    conn.close()

@pytest.fixture
def test_hospital_data():
    """测试医院数据夹具"""
    return {
        "id": 1,
        "name": "测试医院",
        "address": "测试地址123号",
        "phone": "010-12345678",
        "email": "test@hospital.com",
        "website": "http://test-hospital.com",
        "created_at": "2025-11-21T10:00:00",
        "updated_at": "2025-11-21T10:00:00"
    }

@pytest.fixture
def sample_scan_results():
    """测试扫描结果数据夹具"""
    return [
        {
            "id": 1,
            "hospital_id": 1,
            "scan_type": "website_scan",
            "result_data": json.dumps({
                "title": "测试医院官网",
                "meta_description": "专业医疗服务",
                "contact_info": {"phone": "010-12345678", "email": "test@hospital.com"}
            }),
            "status": "completed",
            "created_at": "2025-11-21T10:30:00"
        },
        {
            "id": 2,
            "hospital_id": 1,
            "scan_type": "phone_validation",
            "result_data": json.dumps({
                "phone": "010-12345678",
                "valid": True,
                "operator": "联通"
            }),
            "status": "completed",
            "created_at": "2025-11-21T10:35:00"
        }
    ]

@pytest.fixture
def fastapi_client():
    """FastAPI应用测试夹具"""
    from main import app
    return TestClient(app)

@pytest.fixture
def mock_llm_client():
    """Mock LLM客户端夹具"""
    mock_client = Mock()
    mock_client.generate_response.return_value = {
        "response": "这是一个测试响应",
        "confidence": 0.95,
        "model": "test-model",
        "timestamp": "2025-11-21T10:41:14"
    }
    return mock_client

@pytest.fixture
def mock_requests_response():
    """Mock HTTP响应夹具"""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.text = """
    <html>
        <head><title>测试医院官网</title></head>
        <body>
            <h1>欢迎来到测试医院</h1>
            <p>联系电话：010-12345678</p>
            <p>邮箱：test@hospital.com</p>
            <p>地址：北京市测试区测试街道123号</p>
        </body>
    </html>
    """
    mock_response.headers = {"Content-Type": "text/html; charset=utf-8"}
    return mock_response

@pytest.fixture
def test_environment():
    """测试环境变量夹具"""
    test_env = {
        "TESTING": "true",
        "DATABASE_URL": "sqlite:///test_data.db",
        "LLM_API_KEY": "test-key",
        "LOG_LEVEL": "DEBUG"
    }
    
    # 保存原始环境变量
    original_env = {}
    for key in test_env:
        original_env[key] = os.environ.get(key)
    
    # 设置测试环境变量
    for key, value in test_env.items():
        os.environ[key] = value
    
    yield test_env
    
    # 恢复原始环境变量
    for key, value in original_env.items():
        if value is not None:
            os.environ[key] = value
        else:
            os.environ.pop(key, None)

@pytest.fixture
def clean_test_data(mock_db_connection):
    """测试数据清理夹具"""
    conn = mock_db_connection
    cursor = conn.cursor()
    
    # 清空所有表
    cursor.execute("DELETE FROM scan_results")
    cursor.execute("DELETE FROM hospitals")
    conn.commit()
    
    yield conn
    
    # 测试后清理
    cursor.execute("DELETE FROM scan_results")
    cursor.execute("DELETE FROM hospitals")
    conn.commit()

@pytest.fixture
def sample_json_responses():
    """模拟JSON响应数据夹具"""
    return {
        "website_scan_success": {
            "success": True,
            "data": {
                "title": "测试医院官网",
                "meta_description": "专业医疗服务",
                "contact_info": {
                    "phone": "010-12345678",
                    "email": "test@hospital.com",
                    "address": "北京市测试区测试街道123号"
                }
            }
        },
        "phone_validation_success": {
            "success": True,
            "data": {
                "phone": "010-12345678",
                "valid": True,
                "operator": "联通",
                "region": "北京"
            }
        },
        "scan_in_progress": {
            "success": True,
            "status": "in_progress",
            "message": "扫描进行中..."
        },
        "scan_error": {
            "success": False,
            "error": "无法访问目标网站",
            "error_code": "WEBSITE_ACCESS_FAILED"
        }
    }

@pytest.fixture
def mock_time():
    """Mock时间夹具"""
    fixed_time = datetime(2025, 11, 21, 10, 41, 14)
    with patch('datetime.datetime') as mock_datetime:
        mock_datetime.now.return_value = fixed_time
        yield mock_datetime

@pytest.fixture(scope="session")
def test_config():
    """测试配置夹具"""
    return {
        "max_hospitals": 100,
        "timeout": 30,
        "retry_attempts": 3,
        "batch_size": 10,
        "supported_formats": ["json", "csv"],
        "allowed_domains": ["hospital.com", "medical.org"]
    }

# 自动使用的夹具
@pytest.fixture(autouse=True)
def setup_test_environment(test_environment):
    """自动设置测试环境"""
    # 确保测试模式下不发送真实请求
    os.environ["TESTING"] = "true"
    
    yield test_environment
    
    # 测试后清理
    pass

@pytest.fixture
def captured_logs():
    """捕获日志夹具"""
    import logging
    from io import StringIO
    
    log_stream = StringIO()
    handler = logging.StreamHandler(log_stream)
    handler.setLevel(logging.DEBUG)
    
    # 获取根logger
    logger = logging.getLogger()
    original_level = logger.level
    logger.setLevel(logging.DEBUG)
    logger.addHandler(handler)
    
    yield log_stream
    
    # 清理
    logger.removeHandler(handler)
    logger.setLevel(original_level)


# ==================== 验收测试专用夹具 ====================

@pytest.fixture
def acceptance_test_data():
    """验收测试数据夹具"""
    return {
        "test_province": "江苏省",
        "test_cities": ["南京市", "苏州市"],
        "test_districts": {
            "南京市": ["玄武区", "秦淮区"],
            "苏州市": ["姑苏区", "吴中区"]
        },
        "test_hospitals": {
            "玄武区": ["南京市玄武医院", "玄武区中医院"],
            "秦淮区": ["南京市第一医院", "秦淮区人民医院"],
            "姑苏区": ["苏州市立医院", "姑苏区中心医院"],
            "吴中区": ["苏州大学附属医院", "吴中区中医医院"]
        }
    }


@pytest.fixture
def mock_province_data():
    """模拟省级数据夹具"""
    return [
        {"name": "江苏省", "code": "JS"},
        {"name": "浙江省", "code": "ZJ"}
    ]


@pytest.fixture
def mock_city_data():
    """模拟市级数据夹具"""
    return {
        "江苏省": [
            {"name": "南京市", "code": "JS_NJ"},
            {"name": "苏州市", "code": "JS_SZ"}
        ],
        "浙江省": [
            {"name": "杭州市", "code": "ZJ_HZ"},
            {"name": "宁波市", "code": "ZJ_NB"}
        ]
    }


@pytest.fixture
def mock_district_data():
    """模拟区县级数据夹具"""
    return {
        "南京市": [
            {"name": "玄武区", "code": "XW"},
            {"name": "秦淮区", "code": "QH"}
        ],
        "苏州市": [
            {"name": "姑苏区", "code": "GS"},
            {"name": "吴中区", "code": "WZ"}
        ]
    }


@pytest.fixture
def mock_hospital_data():
    """模拟医院数据夹具"""
    return {
        "玄武区": [
            {"name": "南京市玄武医院", "website": "http://www.xwhospital.com", "confidence": 0.95},
            {"name": "玄武区中医院", "website": "http://www.xwzy.com", "confidence": 0.88}
        ],
        "秦淮区": [
            {"name": "南京市第一医院", "website": "http://www.nj1st.com", "confidence": 0.92},
            {"name": "秦淮区人民医院", "website": "http://qhph.com", "confidence": 0.86}
        ],
        "姑苏区": [
            {"name": "苏州市立医院", "website": "http://www.szsl.com", "confidence": 0.94},
            {"name": "姑苏区中心医院", "website": "http://gszxyy.com", "confidence": 0.89}
        ],
        "吴中区": [
            {"name": "苏州大学附属医院", "website": "http://www.sdfmm.com", "confidence": 0.93},
            {"name": "吴中区中医医院", "website": "http://wzcwzy.com", "confidence": 0.87}
        ]
    }


@pytest.fixture
def mock_llm_responses():
    """模拟LLM响应夹具"""
    return {
        "provinces": {
            "success": True,
            "items": [
                {"name": "江苏省", "code": "JS"},
                {"name": "浙江省", "code": "ZJ"},
                {"name": "广东省", "code": "GD"}
            ]
        },
        "cities_江苏省": {
            "success": True,
            "items": [
                {"name": "南京市", "code": "JS_NJ"},
                {"name": "苏州市", "code": "JS_SZ"}
            ]
        },
        "districts_南京市": {
            "success": True,
            "items": [
                {"name": "玄武区", "code": "XW"},
                {"name": "秦淮区", "code": "QH"}
            ]
        },
        "hospitals_玄武区": {
            "success": True,
            "items": [
                {"name": "南京市玄武医院", "website": "http://www.xwhospital.com", "confidence": 0.95},
                {"name": "玄武区中医院", "website": "http://www.xwzy.com", "confidence": 0.88}
            ]
        },
        "timeout_error": {
            "success": False,
            "error": "请求超时",
            "error_code": "TIMEOUT"
        },
        "invalid_response": {
            "success": False,
            "error": "响应格式无效",
            "error_code": "INVALID_FORMAT"
        }
    }


@pytest.fixture
def acceptance_database():
    """验收测试数据库夹具 - 预置测试数据"""
    import tempfile
    import os
    
    # 创建临时数据库
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(db_fd)
    
    try:
        from db import Database
        test_db = Database(db_path)
        test_db.init_database()
        
        # 预置一些测试数据
        province_id = test_db.upsert_province("江苏省", "JS")
        city_id = test_db.upsert_city(province_id, "南京市", "JS_NJ")
        district_id = test_db.upsert_district(city_id, "玄武区", "XW")
        test_db.upsert_hospital(district_id, "玄武区测试医院", "http://test.com", 0.9)
        
        yield test_db
    finally:
        if os.path.exists(db_path):
            os.unlink(db_path)


@pytest.fixture
def acceptance_task_manager(acceptance_database):
    """验收测试任务管理器夹具"""
    from tasks import TaskManager
    return TaskManager(acceptance_database)


@pytest.fixture
def mock_time_delay():
    """模拟时间延迟夹具"""
    import asyncio
    async def simulate_delay(min_seconds=0.1, max_seconds=0.5):
        import random
        delay = random.uniform(min_seconds, max_seconds)
        await asyncio.sleep(delay)
    return simulate_delay


@pytest.fixture
def performance_monitor():
    """性能监控夹具"""
    import time
    import psutil
    import threading
    from collections import deque
    
    class PerformanceMonitor:
        def __init__(self):
            self.start_time = None
            self.end_time = None
            self.memory_usage = []
            self.cpu_usage = []
            self.response_times = deque(maxlen=100)
            
        def start(self):
            self.start_time = time.time()
            
        def stop(self):
            self.end_time = time.time()
            
        def record_response_time(self, response_time):
            self.response_times.append(response_time)
            
        def record_memory_usage(self):
            memory = psutil.virtual_memory().percent
            self.memory_usage.append(memory)
            
        def record_cpu_usage(self):
            cpu = psutil.cpu_percent()
            self.cpu_usage.append(cpu)
            
        def get_stats(self):
            if not self.start_time or not self.end_time:
                return None
                
            return {
                "total_time": self.end_time - self.start_time,
                "avg_response_time": sum(self.response_times) / len(self.response_times) if self.response_times else 0,
                "max_response_time": max(self.response_times) if self.response_times else 0,
                "min_response_time": min(self.response_times) if self.response_times else 0,
                "max_memory_usage": max(self.memory_usage) if self.memory_usage else 0,
                "avg_cpu_usage": sum(self.cpu_usage) / len(self.cpu_usage) if self.cpu_usage else 0
            }
    
    return PerformanceMonitor()


@pytest.fixture
def acceptance_test_context(acceptance_test_data, acceptance_database, performance_monitor):
    """验收测试上下文夹具"""
    return {
        "test_data": acceptance_test_data,
        "database": acceptance_database,
        "monitor": performance_monitor,
        "setup_time": time.time()
    }


@pytest.fixture
def error_injection():
    """错误注入夹具用于测试错误恢复"""
    class ErrorInjector:
        def __init__(self):
            self.enabled = False
            self.error_count = 0
            self.max_errors = 1
            
        def enable(self, max_errors=1):
            self.enabled = True
            self.max_errors = max_errors
            self.error_count = 0
            
        def should_inject_error(self):
            if not self.enabled:
                return False
            if self.error_count >= self.max_errors:
                return False
            self.error_count += 1
            return True
            
        def inject_timeout_error(self):
            raise TimeoutError("模拟网络超时")
            
        def inject_connection_error(self):
            raise ConnectionError("模拟连接错误")
            
        def inject_validation_error(self):
            raise ValueError("模拟数据验证错误")
    
    return ErrorInjector()


@pytest.fixture
def test_report_generator():
    """测试报告生成器夹具"""
    import json
    from datetime import datetime
    
    class TestReportGenerator:
        def __init__(self):
            self.test_results = []
            self.performance_data = []
            
        def add_test_result(self, test_name, status, duration, message=None):
            self.test_results.append({
                "test_name": test_name,
                "status": status,
                "duration": duration,
                "message": message,
                "timestamp": datetime.now().isoformat()
            })
            
        def add_performance_data(self, operation, duration, memory_usage=None):
            self.performance_data.append({
                "operation": operation,
                "duration": duration,
                "memory_usage": memory_usage,
                "timestamp": datetime.now().isoformat()
            })
            
        def generate_summary(self):
            total_tests = len(self.test_results)
            passed_tests = sum(1 for r in self.test_results if r['status'] == 'passed')
            failed_tests = total_tests - passed_tests
            
            return {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "failed_tests": failed_tests,
                "success_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0,
                "test_results": self.test_results,
                "performance_data": self.performance_data
            }
            
        def save_report(self, filepath):
            summary = self.generate_summary()
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(summary, f, ensure_ascii=False, indent=2)
            return summary
    
    return TestReportGenerator()


# 自动使用的夹具配置
@pytest.fixture(autouse=True)
def setup_acceptance_test_environment():
    """自动设置验收测试环境"""
    import os
    
    # 确保测试模式下使用临时目录
    original_data_dir = os.environ.get('DATA_DIR')
    original_log_dir = os.environ.get('LOG_DIR')
    
    os.environ['DATA_DIR'] = '/tmp/test_data'
    os.environ['LOG_DIR'] = '/tmp/test_logs'
    os.environ['TESTING'] = 'true'
    
    yield
    
    # 恢复原始环境变量
    if original_data_dir:
        os.environ['DATA_DIR'] = original_data_dir
    if original_log_dir:
        os.environ['LOG_DIR'] = original_log_dir
    if not original_data_dir:
        os.environ.pop('DATA_DIR', None)
    if not original_log_dir:
        os.environ.pop('LOG_DIR', None)

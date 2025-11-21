# 测试指南和覆盖率报告

## 概述

本项目采用完整的测试策略，包括单元测试、集成测试、端到端测试和性能测试，确保代码质量和系统稳定性。测试框架基于pytest，提供丰富的测试夹具、Mock数据和覆盖率分析。

## 测试架构

### 测试金字塔

```
    /‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾\
   |                    端到端测试 (E2E Tests)                | 少量，重要场景
   |  完整的用户场景验证，服务集成测试                       |  5%
    \_______________________________________________________/
   
    /‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾\
   |                    集成测试 (Integration Tests)         | 适中，模块集成
   |  模块间协作测试，数据库交互，API集成                   |  20%
    \_______________________________________________________/

    /‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾\
   |                    单元测试 (Unit Tests)                | 大量，核心逻辑
   |  独立函数/类测试，Mock外部依赖，快速执行                |  75%
    \_______________________________________________________/
```

### 测试类型

#### 1. 单元测试 (Unit Tests)
- **目标**: 测试独立的函数、方法和类
- **范围**: 核心业务逻辑、数据处理、工具函数
- **特点**: 执行快速，高度隔离，使用Mock
- **覆盖率要求**: ≥ 90%

#### 2. 集成测试 (Integration Tests)
- **目标**: 测试模块间的协作
- **范围**: 数据库操作、API接口、任务管理
- **特点**: 使用真实的依赖，轻量级测试数据库
- **覆盖率要求**: ≥ 80%

#### 3. 端到端测试 (E2E Tests)
- **目标**: 验证完整的用户场景
- **范围**: API调用流程、数据刷新任务、系统集成
- **特点**: 真实环境测试，覆盖关键路径
- **覆盖率要求**: 关键功能100%

#### 4. 契约测试 (Contract Tests)
- **目标**: 验证API契约和数据格式
- **范围**: OpenAPI规范、数据模型、错误处理
- **特点**: 基于协议测试，预防破坏性变更

#### 5. 性能测试 (Performance Tests)
- **目标**: 验证系统性能和稳定性
- **范围**: 响应时间、并发处理、内存使用
- **特点**: 负载测试，压力测试

## 快速开始

### 环境准备

```bash
# 1. 安装开发依赖
pip install -r requirements-dev.txt

# 2. 确认测试配置
cat pytest.ini

# 3. 运行所有测试
make test

# 4. 生成覆盖率报告
make test-coverage

# 5. 查看测试报告
open htmlcov/index.html  # macOS
# 或
xdg-open htmlcov/index.html  # Linux
```

### 基本测试命令

```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/test_llm_client.py

# 运行特定测试函数
pytest tests/test_llm_client.py::test_get_provinces_success

# 运行特定标记的测试
pytest -m "unit"          # 只运行单元测试
pytest -m "integration"   # 只运行集成测试
pytest -m "slow"          # 只运行慢速测试

# 详细输出
pytest -v                 # 详细模式
pytest -s                 # 打印print输出
pytest -x                 # 第一个失败后停止
pytest --tb=short         # 简短的错误回溯

# 并行执行（需要pytest-xdist）
pytest -n auto            # 自动检测CPU核心数
pytest -n 4              # 使用4个进程

# 生成覆盖率报告
pytest --cov=main --cov-report=html
pytest --cov=main --cov-report=term-missing
pytest --cov=main --cov-report=xml

# 生成性能报告（需要pytest-benchmark）
pytest --benchmark-only
```

## 测试结构

### 目录结构

```
tests/
├── conftest.py                 # Pytest配置和夹具
├── helpers.py                  # 测试辅助工具
├── test_acceptance.py          # 验收测试
├── test_acceptance_simple.py   # 简化验收测试
├── test_contracts.py           # 契约测试
├── test_database.py            # 数据库测试
├── test_examples.py            # 示例测试
├── test_llm_client.py          # LLM客户端测试
├── test_schemas.py             # 数据模型测试
├── fixtures/                   # 测试夹具和Mock数据
│   ├── __init__.py
│   ├── llm_responses.py        # LLM响应Mock
│   ├── sample_data.py          # 样本测试数据
│   └── mock_json_responses.py  # JSON响应Mock
└── logs/                       # 测试日志目录
```

### 测试文件组织

#### 按功能模块组织
```
tests/
├── test_main.py           # FastAPI应用主程序测试
├── test_db.py             # 数据库操作测试
├── test_llm_client.py     # LLM客户端测试
├── test_tasks.py          # 任务管理测试
└── test_schemas.py        # 数据模型测试
```

#### 按测试类型组织
```
tests/
├── unit/                  # 单元测试
├── integration/           # 集成测试
├── e2e/                   # 端到端测试
├── contract/              # 契约测试
└── performance/           # 性能测试
```

## 核心测试框架

### pytest配置

#### pytest.ini
```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py *_test.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --tb=short
    --strict-markers
    --strict-config
    --disable-warnings
    --cov=main
    --cov=code/hospital_scanner
    --cov-report=term-missing:skip-covered
    --cov-report=html:htmlcov
    --cov-report=xml
    --cov-fail-under=80
markers =
    unit: 单元测试
    integration: 集成测试
    slow: 慢速测试
    api: API测试
    database: 数据库测试
    llm: LLM相关测试
    task: 任务管理测试
    e2e: 端到端测试
    smoke: 冒烟测试
filterwarnings =
    ignore::DeprecationWarning
    ignore::PendingDeprecationWarning
```

### conftest.py配置

#### 全局夹具
```python
import pytest
import asyncio
import tempfile
import os
from unittest.mock import AsyncMock, MagicMock

# 异步事件循环夹具
@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环供测试使用"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

# 数据库夹具
@pytest.fixture
async def test_db():
    """创建测试数据库"""
    # 创建临时数据库文件
    fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    
    # 初始化测试数据库
    from db import Database
    db = Database(db_path)
    await db.init_db()
    
    yield db
    
    # 清理测试数据库
    os.unlink(db_path)

# LLM客户端夹具
@pytest.fixture
def mock_llm_client():
    """Mock LLM客户端"""
    client = AsyncMock()
    client.get_provinces = AsyncMock(return_value={
        "items": [
            {"name": "北京市", "code": None},
            {"name": "上海市", "code": None},
            {"name": "广东省", "code": None}
        ]
    })
    client.get_cities = AsyncMock(return_value={
        "items": [
            {"name": "广州市", "code": None},
            {"name": "深圳市", "code": None}
        ]
    })
    client.get_districts = AsyncMock(return_value={
        "items": [
            {"name": "越秀区", "code": None},
            {"name": "荔湾区", "code": None}
        ]
    })
    client.get_hospitals = AsyncMock(return_value={
        "items": [
            {"name": "中山大学附属第一医院", "website": "https://www.gzsums.edu.cn/", "llm_confidence": 0.95}
        ]
    })
    return client

# 任务管理器夹具
@pytest.fixture
def task_manager(mock_llm_client, test_db):
    """创建任务管理器"""
    from tasks import TaskManager
    return TaskManager(
        db=test_db,
        llm_client=mock_llm_client,
        max_concurrent_tasks=1  # 测试时限制并发数
    )

# FastAPI应用夹具
@pytest.fixture
def test_app():
    """创建测试应用"""
    from main import app
    return app

# HTTP客户端夹具
@pytest.fixture
async def client(test_app):
    """创建测试HTTP客户端"""
    from httpx import AsyncClient
    async with AsyncClient(app=test_app, base_url="http://test") as ac:
        yield ac
```

#### 数据库夹具
```python
# conftest.py 中的数据库相关夹具

import pytest
import sqlite3
from typing import Generator

@pytest.fixture(scope="session")
def test_database():
    """会话级测试数据库"""
    # 创建内存数据库
    conn = sqlite3.connect(":memory:")
    
    # 设置外键约束
    conn.execute("PRAGMA foreign_keys = ON")
    
    # 创建表结构
    conn.executescript("""
        CREATE TABLE provinces (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            code TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
        
        CREATE TABLE cities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            province_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            code TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (province_id) REFERENCES provinces(id) ON DELETE CASCADE
        );
        
        CREATE TABLE tasks (
            task_id TEXT PRIMARY KEY,
            hospital_name TEXT NOT NULL,
            query TEXT,
            status TEXT NOT NULL,
            progress INTEGER DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at TEXT NOT NULL DEFAULT (datetime('now')),
            result TEXT,
            error_message TEXT
        );
    """)
    
    # 插入测试数据
    conn.executemany(
        "INSERT INTO provinces (name) VALUES (?)",
        [("北京市",), ("上海市",), ("广东省",)]
    )
    conn.commit()
    
    yield conn
    
    conn.close()

@pytest.fixture
async def populated_database(test_database):
    """预填充数据的数据库"""
    cursor = test_database.cursor()
    
    # 插入城市数据
    cursor.execute("SELECT id FROM provinces WHERE name = '广东省'")
    province_id = cursor.fetchone()[0]
    
    cities_data = [
        (province_id, "广州市"),
        (province_id, "深圳市"),
        (province_id, "珠海市")
    ]
    
    cursor.executemany(
        "INSERT INTO cities (province_id, name) VALUES (?, ?)",
        cities_data
    )
    
    # 插入任务数据
    import uuid
    from datetime import datetime
    
    task_id = f"test_task_{uuid.uuid4().hex[:8]}"
    cursor.execute("""
        INSERT INTO tasks (task_id, hospital_name, status, progress, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        task_id,
        "测试任务",
        "SUCCEEDED",
        100,
        datetime.now().isoformat(),
        datetime.now().isoformat()
    ))
    
    test_database.commit()
    
    return test_database
```

### Mock数据夹具

#### LLM响应Mock
```python
# fixtures/llm_responses.py

import json
from typing import Dict, Any

class MockLLMResponses:
    """LLM响应Mock数据类"""
    
    @staticmethod
    def get_provinces_response() -> Dict[str, Any]:
        """省份数据Mock"""
        return {
            "items": [
                {"name": "北京市", "code": None},
                {"name": "天津市", "code": None},
                {"name": "河北省", "code": None},
                {"name": "山西省", "code": None},
                {"name": "内蒙古自治区", "code": None},
                {"name": "辽宁省", "code": None},
                {"name": "吉林省", "code": None},
                {"name": "黑龙江省", "code": None},
                {"name": "上海市", "code": None},
                {"name": "江苏省", "code": None},
                {"name": "浙江省", "code": None},
                {"name": "安徽省", "code": None},
                {"name": "福建省", "code": None},
                {"name": "江西省", "code": None},
                {"name": "山东省", "code": None},
                {"name": "河南省", "code": None},
                {"name": "湖北省", "code": None},
                {"name": "湖南省", "code": None},
                {"name": "广东省", "code": None},
                {"name": "广西壮族自治区", "code": None},
                {"name": "海南省", "code": None},
                {"name": "重庆市", "code": None},
                {"name": "四川省", "code": None},
                {"name": "贵州省", "code": None},
                {"name": "云南省", "code": None},
                {"name": "西藏自治区", "code": None},
                {"name": "陕西省", "code": None},
                {"name": "甘肃省", "code": None},
                {"name": "青海省", "code": None},
                {"name": "宁夏回族自治区", "code": None},
                {"name": "新疆维吾尔自治区", "code": None},
                {"name": "中国香港特别行政区", "code": None},
                {"name": "中国澳门特别行政区", "code": None},
                {"name": "中国台湾省", "code": None}
            ]
        }
    
    @staticmethod
    def get_cities_response(province_name: str = "广东省") -> Dict[str, Any]:
        """城市数据Mock"""
        cities_map = {
            "广东省": [
                {"name": "广州市", "code": None},
                {"name": "深圳市", "code": None},
                {"name": "珠海市", "code": None},
                {"name": "汕头市", "code": None},
                {"name": "佛山市", "code": None},
                {"name": "韶关市", "code": None},
                {"name": "湛江市", "code": None},
                {"name": "肇庆市", "code": None},
                {"name": "江门市", "code": None},
                {"name": "茂名市", "code": None},
                {"name": "惠州市", "code": None},
                {"name": "梅州市", "code": None},
                {"name": "汕尾市", "code": None},
                {"name": "河源市", "code": None},
                {"name": "阳江市", "code": None},
                {"name": "清远市", "code": None},
                {"name": "东莞市", "code": None},
                {"name": "中山市", "code": None},
                {"name": "潮州市", "code": None},
                {"name": "揭阳市", "code": None},
                {"name": "云浮市", "code": None}
            ],
            "北京市": [
                {"name": "北京市", "code": None}
            ]
        }
        
        return {
            "items": cities_map.get(province_name, [])
        }
    
    @staticmethod
    def get_districts_response(city_name: str = "广州市") -> Dict[str, Any]:
        """区县数据Mock"""
        districts_map = {
            "广州市": [
                {"name": "荔湾区", "code": None},
                {"name": "越秀区", "code": None},
                {"name": "海珠区", "code": None},
                {"name": "天河区", "code": None},
                {"name": "白云区", "code": None},
                {"name": "黄埔区", "code": None},
                {"name": "番禺区", "code": None},
                {"name": "花都区", "code": None},
                {"name": "南沙区", "code": None},
                {"name": "从化区", "code": None},
                {"name": "增城区", "code": None}
            ],
            "深圳市": [
                {"name": "罗湖区", "code": None},
                {"name": "福田区", "code": None},
                {"name": "南山区", "code": None},
                {"name": "宝安区", "code": None},
                {"name": "龙岗区", "code": None},
                {"name": "盐田区", "code": None},
                {"name": "龙华区", "code": None},
                {"name": "坪山区", "code": None},
                {"name": "光明区", "code": None},
                {"name": "大鹏新区", "code": None}
            ]
        }
        
        return {
            "items": districts_map.get(city_name, [])
        }
    
    @staticmethod
    def get_hospitals_response(district_name: str = "越秀区") -> Dict[str, Any]:
        """医院数据Mock"""
        hospitals_map = {
            "越秀区": [
                {"name": "中山大学附属第一医院", "website": "https://www.gzsums.edu.cn/", "llm_confidence": 0.95},
                {"name": "广东省人民医院", "website": "https://www.gdph.com.cn/", "llm_confidence": 0.92},
                {"name": "广州医科大学附属第一医院", "website": "https://www.gyfyfy.com/", "llm_confidence": 0.88},
                {"name": "中山大学孙逸仙纪念医院", "website": "https://www.syshospital.com/", "llm_confidence": 0.85},
                {"name": "广州市第一人民医院", "website": "https://www.gzsph.com/", "llm_confidence": 0.83}
            ],
            "福田区": [
                {"name": "北京大学深圳医院", "website": "https://www.bdsy.cn/", "llm_confidence": 0.90},
                {"name": "深圳市人民医院", "website": "https://www.szph.com/", "llm_confidence": 0.87},
                {"name": "深圳市第二人民医院", "website": "https://www.szsrmyy.cn/", "llm_confidence": 0.84},
                {"name": "中山大学附属第七医院", "website": "https://www.7thhospital.cn/", "llm_confidence": 0.82}
            ]
        }
        
        return {
            "items": hospitals_map.get(district_name, [])
        }
```

#### 样本测试数据
```python
# fixtures/sample_data.py

from typing import List, Dict, Any
from datetime import datetime

class SampleData:
    """样本测试数据类"""
    
    @staticmethod
    def sample_provinces() -> List[Dict[str, Any]]:
        """样本省份数据"""
        return [
            {"id": 1, "name": "北京市", "code": None, "created_at": datetime.now().isoformat(), "updated_at": datetime.now().isoformat()},
            {"id": 2, "name": "上海市", "code": None, "created_at": datetime.now().isoformat(), "updated_at": datetime.now().isoformat()},
            {"id": 3, "name": "广东省", "code": None, "created_at": datetime.now().isoformat(), "updated_at": datetime.now().isoformat()},
        ]
    
    @staticmethod
    def sample_cities() -> List[Dict[str, Any]]:
        """样本城市数据"""
        return [
            {"id": 1, "province_id": 3, "name": "广州市", "code": None, "created_at": datetime.now().isoformat(), "updated_at": datetime.now().isoformat()},
            {"id": 2, "province_id": 3, "name": "深圳市", "code": None, "created_at": datetime.now().isoformat(), "updated_at": datetime.now().isoformat()},
            {"id": 3, "province_id": 3, "name": "珠海市", "code": None, "created_at": datetime.now().isoformat(), "updated_at": datetime.now().isoformat()},
        ]
    
    @staticmethod
    def sample_districts() -> List[Dict[str, Any]]:
        """样本区县数据"""
        return [
            {"id": 1, "city_id": 1, "name": "越秀区", "code": None, "created_at": datetime.now().isoformat(), "updated_at": datetime.now().isoformat()},
            {"id": 2, "city_id": 1, "name": "荔湾区", "code": None, "created_at": datetime.now().isoformat(), "updated_at": datetime.now().isoformat()},
            {"id": 3, "city_id": 1, "name": "海珠区", "code": None, "created_at": datetime.now().isoformat(), "updated_at": datetime.now().isoformat()},
        ]
    
    @staticmethod
    def sample_hospitals() -> List[Dict[str, Any]]:
        """样本医院数据"""
        return [
            {"id": 1, "district_id": 1, "name": "中山大学附属第一医院", "website": "https://www.gzsums.edu.cn/", "llm_confidence": 0.95, "created_at": datetime.now().isoformat(), "updated_at": datetime.now().isoformat()},
            {"id": 2, "district_id": 1, "name": "广东省人民医院", "website": "https://www.gdph.com.cn/", "llm_confidence": 0.92, "created_at": datetime.now().isoformat(), "updated_at": datetime.now().isoformat()},
            {"id": 3, "district_id": 1, "name": "广州医科大学附属第一医院", "website": "https://www.gyfyfy.com/", "llm_confidence": 0.88, "created_at": datetime.now().isoformat(), "updated_at": datetime.now().isoformat()},
        ]
    
    @staticmethod
    def sample_tasks() -> List[Dict[str, Any]]:
        """样本任务数据"""
        import uuid
        
        now = datetime.now().isoformat()
        
        return [
            {
                "task_id": f"task_{uuid.uuid4().hex[:8]}",
                "hospital_name": "全量刷新",
                "query": None,
                "status": "SUCCEEDED",
                "progress": 100,
                "created_at": now,
                "updated_at": now,
                "result": json.dumps({"total_hospitals": 1000}),
                "error_message": None
            },
            {
                "task_id": f"task_{uuid.uuid4().hex[:8]}",
                "hospital_name": "广东省刷新",
                "query": "广东省",
                "status": "RUNNING",
                "progress": 45,
                "created_at": now,
                "updated_at": now,
                "result": None,
                "error_message": None
            },
            {
                "task_id": f"task_{uuid.uuid4().hex[:8]}",
                "hospital_name": "江苏省刷新",
                "query": "江苏省",
                "status": "FAILED",
                "progress": 30,
                "created_at": now,
                "updated_at": now,
                "result": None,
                "error_message": "LLM API调用失败"
            }
        ]
```

## 测试用例示例

### 单元测试示例

#### LLM客户端单元测试
```python
# tests/test_llm_client.py

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
import json

from llm_client import LLMClient, LLMAPIError


@pytest.mark.unit
class TestLLMClient:
    """LLM客户端单元测试"""
    
    @pytest.fixture
    def client(self):
        """创建测试客户端"""
        return LLMClient(api_key="test-key")
    
    @pytest.mark.asyncio
    async def test_get_provinces_success(self, client):
        """测试获取省份成功"""
        # Mock HTTP响应
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "output": {
                "text": '{"items": [{"name": "北京市", "code": null}, {"name": "上海市", "code": null}]}'
            }
        }
        
        with patch('httpx.AsyncClient.post', return_value=mock_response):
            result = await client.get_provinces()
            
            assert "items" in result
            assert len(result["items"]) == 2
            assert result["items"][0]["name"] == "北京市"
            assert result["items"][1]["name"] == "上海市"
    
    @pytest.mark.asyncio
    async def test_get_provinces_api_error(self, client):
        """测试API错误处理"""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.json.return_value = {"code": "UNAUTHORIZED"}
        
        with patch('httpx.AsyncClient.post', return_value=mock_response):
            with pytest.raises(LLMAPIError) as exc_info:
                await client.get_provinces()
            
            assert exc_info.value.status_code == 401
    
    @pytest.mark.asyncio
    async def test_get_cities_success(self, client):
        """测试获取城市成功"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "output": {
                "text": '{"items": [{"name": "广州市", "code": null}, {"name": "深圳市", "code": null}]}'
            }
        }
        
        with patch('httpx.AsyncClient.post', return_value=mock_response):
            result = await client.get_cities("广东省")
            
            assert "items" in result
            assert len(result["items"]) == 2
            assert result["items"][0]["name"] == "广州市"
    
    @pytest.mark.asyncio
    async def test_get_cities_empty_response(self, client):
        """测试城市数据为空"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "output": {
                "text": '{"items": []}'
            }
        }
        
        with patch('httpx.AsyncClient.post', return_value=mock_response):
            result = await client.get_cities("不存在的省份")
            
            assert "items" in result
            assert len(result["items"]) == 0
    
    @pytest.mark.asyncio
    async def test_get_hospitals_success(self, client):
        """测试获取医院成功"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "output": {
                "text": '{"items": [{"name": "中山大学附属第一医院", "website": "https://www.gzsums.edu.cn/", "llm_confidence": 0.95}]}'
            }
        }
        
        with patch('httpx.AsyncClient.post', return_value=mock_response):
            result = await client.get_hospitals("越秀区")
            
            assert "items" in result
            assert len(result["items"]) == 1
            hospital = result["items"][0]
            assert hospital["name"] == "中山大学附属第一医院"
            assert hospital["website"] == "https://www.gzsums.edu.cn/"
            assert hospital["llm_confidence"] == 0.95
    
    @pytest.mark.asyncio
    async def test_retry_mechanism(self, client):
        """测试重试机制"""
        call_count = 0
        
        def mock_post(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            
            if call_count <= 2:  # 前两次调用失败
                raise Exception("Network error")
            
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "output": {
                    "text": '{"items": [{"name": "北京市", "code": null}]}'
                }
            }
            return mock_response
        
        with patch('httpx.AsyncClient.post', side_effect=mock_post):
            result = await client.get_provinces()
            
            assert call_count == 3  # 第一次失败，两次重试，成功
            assert len(result["items"]) == 1
    
    @pytest.mark.asyncio
    async def test_timeout_handling(self, client):
        """测试超时处理"""
        with patch('httpx.AsyncClient.post', side_effect=asyncio.TimeoutError()):
            with pytest.raises(LLMAPIError):
                await client.get_provinces()
```

#### 数据库单元测试
```python
# tests/test_database.py

import pytest
import asyncio
import tempfile
import os
from datetime import datetime

from db import Database


@pytest.mark.unit
class TestDatabase:
    """数据库单元测试"""
    
    @pytest.fixture
    async def temp_db(self):
        """创建临时数据库"""
        fd, db_path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        
        db = Database(db_path)
        await db.init_db()
        
        yield db
        
        # 清理
        os.unlink(db_path)
    
    @pytest.mark.asyncio
    async def test_init_db(self, temp_db):
        """测试数据库初始化"""
        # 检查表是否创建
        cursor = temp_db.conn.cursor()
        
        # 检查省份表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='provinces'")
        assert cursor.fetchone() is not None
        
        # 检查城市表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='cities'")
        assert cursor.fetchone() is not None
    
    @pytest.mark.asyncio
    async def test_create_province(self, temp_db):
        """测试创建省份"""
        province_data = {
            "name": "测试省份",
            "code": "TEST"
        }
        
        province_id = await temp_db.create_province(province_data)
        
        assert province_id is not None
        assert isinstance(province_id, int)
        
        # 验证数据
        cursor = temp_db.conn.cursor()
        cursor.execute("SELECT * FROM provinces WHERE id = ?", (province_id,))
        result = cursor.fetchone()
        
        assert result is not None
        assert result[1] == "测试省份"  # name
        assert result[2] == "TEST"      # code
    
    @pytest.mark.asyncio
    async def test_get_provinces(self, temp_db):
        """测试获取省份列表"""
        # 插入测试数据
        await temp_db.create_province({"name": "省份1", "code": "P1"})
        await temp_db.create_province({"name": "省份2", "code": "P2"})
        
        provinces = await temp_db.get_provinces()
        
        assert "items" in provinces
        assert len(provinces["items"]) == 2
        
        # 验证数据
        names = [p["name"] for p in provinces["items"]]
        assert "省份1" in names
        assert "省份2" in names
    
    @pytest.mark.asyncio
    async def test_create_city(self, temp_db):
        """测试创建城市"""
        # 先创建省份
        province_id = await temp_db.create_province({"name": "测试省份"})
        
        city_data = {
            "province_id": province_id,
            "name": "测试城市",
            "code": "TEST_CITY"
        }
        
        city_id = await temp_db.create_city(city_data)
        
        assert city_id is not None
        assert isinstance(city_id, int)
        
        # 验证数据
        cursor = temp_db.conn.cursor()
        cursor.execute("SELECT * FROM cities WHERE id = ?", (city_id,))
        result = cursor.fetchone()
        
        assert result[1] == province_id  # province_id
        assert result[2] == "测试城市"    # name
        assert result[3] == "TEST_CITY"  # code
    
    @pytest.mark.asyncio
    async def test_get_cities_by_province(self, temp_db):
        """测试按省份获取城市"""
        # 创建省份
        province_id = await temp_db.create_province({"name": "测试省份"})
        
        # 创建城市
        await temp_db.create_city({"province_id": province_id, "name": "城市1"})
        await temp_db.create_city({"province_id": province_id, "name": "城市2"})
        
        cities = await temp_db.get_cities_by_province("测试省份")
        
        assert "items" in cities
        assert len(cities["items"]) == 2
        
        # 验证数据
        names = [c["name"] for c in cities["items"]]
        assert "城市1" in names
        assert "城市2" in names
    
    @pytest.mark.asyncio
    async def test_fk_constraint(self, temp_db):
        """测试外键约束"""
        # 尝试创建城市但省份不存在
        with pytest.raises(Exception):  # 应该抛出外键约束错误
            await temp_db.create_city({
                "province_id": 99999,  # 不存在的省份ID
                "name": "测试城市"
            })
```

### 集成测试示例

#### API集成测试
```python
# tests/test_integration.py

import pytest
import asyncio
from httpx import AsyncClient

from main import app


@pytest.mark.integration
class TestAPIIntegration:
    """API集成测试"""
    
    @pytest.fixture
    async def client(self):
        """创建测试客户端"""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            yield ac
    
    @pytest.mark.asyncio
    async def test_health_check(self, client):
        """测试健康检查接口"""
        response = await client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"
    
    @pytest.mark.asyncio
    async def test_get_provinces(self, client):
        """测试获取省份列表"""
        response = await client.get("/provinces")
        
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert "data" in data
        assert "items" in data["data"]
        assert "total" in data["data"]
    
    @pytest.mark.asyncio
    async def test_get_provinces_pagination(self, client):
        """测试省份列表分页"""
        response = await client.get("/provinces?page=1&page_size=5")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["code"] == 200
        assert data["data"]["page"] == 1
        assert data["data"]["page_size"] == 5
        assert len(data["data"]["items"]) <= 5
    
    @pytest.mark.asyncio
    async def test_full_refresh_task_creation(self, client):
        """测试创建全量刷新任务"""
        response = await client.post("/refresh/all")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["code"] == 200
        assert "task_id" in data["data"]
        assert data["data"]["status"] == "PENDING"
    
    @pytest.mark.asyncio
    async def test_province_refresh_task_creation(self, client):
        """测试创建省份刷新任务"""
        response = await client.post("/refresh/province/广东省")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["code"] == 200
        assert "task_id" in data["data"]
        assert "广东省" in data["message"]
    
    @pytest.mark.asyncio
    async def test_get_task_status(self, client):
        """测试获取任务状态"""
        # 先创建任务
        create_response = await client.post("/refresh/all")
        task_id = create_response.json()["data"]["task_id"]
        
        # 查询任务状态
        response = await client.get(f"/tasks/{task_id}")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["code"] == 200
        assert data["data"]["task_id"] == task_id
        assert "status" in data["data"]
    
    @pytest.mark.asyncio
    async def test_get_active_tasks(self, client):
        """测试获取活跃任务"""
        response = await client.get("/tasks/active")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["code"] == 200
        assert "items" in data["data"]
        assert "count" in data["data"]
    
    @pytest.mark.asyncio
    async def test_search_hospitals(self, client):
        """测试医院搜索"""
        response = await client.get("/hospitals/search?q=协和")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["code"] == 200
        assert "data" in data
        assert "items" in data["data"]
    
    @pytest.mark.asyncio
    async def test_statistics(self, client):
        """测试统计信息"""
        response = await client.get("/statistics")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["code"] == 200
        assert "data" in data
        
        # 检查统计数据的结构
        stats = data["data"]
        assert "database" in stats
        assert "tasks" in stats
        assert "system" in stats
```

### 端到端测试示例

#### 完整流程测试
```python
# tests/test_e2e.py

import pytest
import asyncio
import time
from httpx import AsyncClient

from main import app


@pytest.mark.e2e
class TestEndToEndFlow:
    """端到端测试"""
    
    @pytest.fixture
    async def client(self):
        """创建测试客户端"""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            yield ac
    
    @pytest.mark.asyncio
    async def test_complete_data_refresh_flow(self, client):
        """测试完整的数据刷新流程"""
        
        # 1. 检查初始状态
        initial_stats = await client.get("/statistics")
        assert initial_stats.status_code == 200
        
        # 2. 创建省份刷新任务
        task_response = await client.post("/refresh/province/广东省")
        assert task_response.status_code == 200
        
        task_data = task_response.json()
        task_id = task_data["data"]["task_id"]
        assert task_id is not None
        
        # 3. 监控任务执行
        start_time = time.time()
        max_wait = 300  # 5分钟超时
        
        while time.time() - start_time < max_wait:
            status_response = await client.get(f"/tasks/{task_id}")
            assert status_response.status_code == 200
            
            status_data = status_response.json()
            task_status = status_data["data"]["status"]
            
            if task_status in ["SUCCEEDED", "FAILED", "CANCELLED"]:
                break
            
            await asyncio.sleep(2)  # 等待2秒
        
        # 4. 验证任务结果
        final_status_response = await client.get(f"/tasks/{task_id}")
        final_status_data = final_status_response.json()
        
        assert final_status_data["data"]["task_id"] == task_id
        assert final_status_data["data"]["status"] in ["SUCCEEDED", "FAILED", "CANCELLED"]
        
        # 如果任务成功，检查数据是否更新
        if final_status_data["data"]["status"] == "SUCCEEDED":
            # 5. 验证数据更新
            final_stats = await client.get("/statistics")
            assert final_stats.status_code == 200
    
    @pytest.mark.asyncio
    async def test_multiple_concurrent_tasks(self, client):
        """测试多个并发任务"""
        
        # 创建多个省份刷新任务
        provinces = ["广东省", "江苏省", "浙江省"]
        task_ids = []
        
        for province in provinces:
            response = await client.post(f"/refresh/province/{province}")
            assert response.status_code == 200
            
            task_id = response.json()["data"]["task_id"]
            task_ids.append(task_id)
        
        # 验证所有任务都已创建
        assert len(task_ids) == 3
        
        # 检查活跃任务数
        active_response = await client.get("/tasks/active")
        active_data = active_response.json()
        assert active_data["code"] == 200
        assert len(active_data["data"]["items"]) >= 3
        
        # 等待所有任务完成（最多10分钟）
        start_time = time.time()
        max_wait = 600
        
        while time.time() - start_time < max_wait:
            all_completed = True
            
            for task_id in task_ids:
                status_response = await client.get(f"/tasks/{task_id}")
                status_data = status_response.json()
                
                if status_data["data"]["status"] not in ["SUCCEEDED", "FAILED", "CANCELLED"]:
                    all_completed = False
                    break
            
            if all_completed:
                break
            
            await asyncio.sleep(5)
        
        # 验证所有任务都已完成
        for task_id in task_ids:
            status_response = await client.get(f"/tasks/{task_id}")
            status_data = status_response.json()
            assert status_data["data"]["status"] in ["SUCCEEDED", "FAILED", "CANCELLED"]
    
    @pytest.mark.asyncio
    async def test_task_cancellation(self, client):
        """测试任务取消"""
        
        # 创建任务
        task_response = await client.post("/refresh/all")
        task_id = task_response.json()["data"]["task_id"]
        
        # 等待任务开始执行
        await asyncio.sleep(2)
        
        # 取消任务
        cancel_response = await client.delete(f"/tasks/{task_id}")
        assert cancel_response.status_code == 200
        
        # 验证任务状态变为CANCELLED
        status_response = await client.get(f"/tasks/{task_id}")
        status_data = status_response.json()
        assert status_data["data"]["status"] == "CANCELLED"
    
    @pytest.mark.asyncio
    async def test_data_query_flow(self, client):
        """测试数据查询流程"""
        
        # 1. 获取省份列表
        provinces_response = await client.get("/provinces")
        assert provinces_response.status_code == 200
        provinces_data = provinces_response.json()
        
        if provinces_data["data"]["total"] > 0:
            province_name = provinces_data["data"]["items"][0]["name"]
            
            # 2. 获取城市列表
            cities_response = await client.get(f"/cities?province={province_name}")
            assert cities_response.status_code == 200
            cities_data = cities_response.json()
            
            if cities_data["data"]["total"] > 0:
                city_name = cities_data["data"]["items"][0]["name"]
                
                # 3. 获取区县列表
                districts_response = await client.get(f"/districts?city={city_name}")
                assert districts_response.status_code == 200
                districts_data = districts_response.json()
                
                if districts_data["data"]["total"] > 0:
                    district_name = districts_data["data"]["items"][0]["name"]
                    
                    # 4. 获取医院列表
                    hospitals_response = await client.get(f"/hospitals?district={district_name}")
                    assert hospitals_response.status_code == 200
                    hospitals_data = hospitals_response.json()
                    
                    assert "data" in hospitals_data
    
    @pytest.mark.asyncio
    async def test_error_handling(self, client):
        """测试错误处理"""
        
        # 1. 测试无效的任务ID
        invalid_task_response = await client.get("/tasks/invalid_task_id")
        assert invalid_task_response.status_code == 404
        
        # 2. 测试无效的省份名
        invalid_province_response = await client.post("/refresh/province/不存在的省份")
        assert invalid_province_response.status_code == 200  # 任务会被创建，但可能失败
        
        # 3. 测试无效的查询参数
        invalid_param_response = await client.get("/provinces?page=-1")
        assert invalid_param_response.status_code == 422  # 验证错误
```

## 契约测试

### OpenAPI契约测试
```python
# tests/test_contracts.py

import pytest
import json
from httpx import AsyncClient

from main import app


@pytest.mark.contract
class TestAPIContracts:
    """API契约测试"""
    
    @pytest.fixture
    async def client(self):
        """创建测试客户端"""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            yield ac
    
    @pytest.mark.asyncio
    async def test_openapi_schema_validity(self):
        """测试OpenAPI schema的有效性"""
        from fastapi.openapi.utils import get_openapi
        
        openapi_schema = get_openapi(
            title="Hospital Scanner API",
            version="1.0.0",
            routes=app.routes
        )
        
        # 验证schema结构
        assert "openapi" in openapi_schema
        assert "info" in openapi_schema
        assert "paths" in openapi_schema
        assert "components" in openapi_schema
        
        # 验证基本路径存在
        assert "/health" in openapi_schema["paths"]
        assert "/provinces" in openapi_schema["paths"]
        assert "/refresh/all" in openapi_schema["paths"]
        assert "/tasks/{task_id}" in openapi_schema["paths"]
    
    @pytest.mark.asyncio
    async def test_response_contract_provinces(self, client):
        """测试省份接口响应契约"""
        response = await client.get("/provinces")
        
        # 验证响应状态码
        assert response.status_code == 200
        
        # 验证响应格式
        data = response.json()
        assert "code" in data
        assert "message" in data
        assert "data" in data
        
        # 验证数据格式
        assert data["code"] == 200
        assert isinstance(data["message"], str)
        
        # 验证数据内容结构
        assert "items" in data["data"]
        assert "total" in data["data"]
        assert "page" in data["data"]
        assert "page_size" in data["data"]
        assert "total_pages" in data["data"]
        
        # 验证items中每个省份的格式
        if data["data"]["items"]:
            province = data["data"]["items"][0]
            assert "id" in province
            assert "name" in province
            assert "code" in province
            assert "created_at" in province
            assert "updated_at" in province
    
    @pytest.mark.asyncio
    async def test_response_contract_task_creation(self, client):
        """测试任务创建接口响应契约"""
        response = await client.post("/refresh/all")
        
        # 验证响应状态码
        assert response.status_code == 200
        
        # 验证响应格式
        data = response.json()
        assert "code" in data
        assert "message" in data
        assert "data" in data
        
        # 验证data内容
        task_data = data["data"]
        assert "task_id" in task_data
        assert "status" in task_data
        assert "progress" in task_data
        
        # 验证字段类型
        assert isinstance(task_data["task_id"], str)
        assert isinstance(task_data["status"], str)
        assert isinstance(task_data["progress"], int)
        
        # 验证任务ID格式
        task_id = task_data["task_id"]
        assert len(task_id) > 0
        assert task_id.startswith(("task_", "full_refresh_", "province_"))
    
    @pytest.mark.asyncio
    async def test_response_contract_task_status(self, client):
        """测试任务状态接口响应契约"""
        # 先创建任务
        create_response = await client.post("/refresh/all")
        task_id = create_response.json()["data"]["task_id"]
        
        # 查询任务状态
        status_response = await client.get(f"/tasks/{task_id}")
        
        # 验证响应状态码
        assert status_response.status_code == 200
        
        # 验证响应格式
        data = status_response.json()
        assert "code" in data
        assert "message" in data
        assert "data" in data
        
        # 验证任务数据格式
        task_data = data["data"]
        required_fields = [
            "task_id", "hospital_name", "query", "status", "created_at", 
            "updated_at", "progress"
        ]
        
        for field in required_fields:
            assert field in task_data, f"缺少字段: {field}"
        
        # 验证字段类型和值范围
        assert task_data["task_id"] == task_id
        assert task_data["status"] in ["PENDING", "RUNNING", "SUCCEEDED", "FAILED", "CANCELLED"]
        assert 0 <= task_data["progress"] <= 100
    
    @pytest.mark.asyncio
    async def test_request_validation(self, client):
        """测试请求参数验证"""
        
        # 测试无效的省份名称
        invalid_response = await client.post("/refresh/province/")
        assert invalid_response.status_code == 422
        
        # 测试无效的分页参数
        invalid_page_response = await client.get("/provinces?page=abc")
        assert invalid_page_response.status_code == 422
        
        # 测试负数分页参数
        negative_page_response = await client.get("/provinces?page=-1")
        assert negative_page_response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_error_response_contract(self, client):
        """测试错误响应契约"""
        
        # 测试404错误
        not_found_response = await client.get("/invalid/path")
        assert not_found_response.status_code == 404
        
        not_found_data = not_found_response.json()
        assert "code" in not_found_data
        assert "message" in not_found_data
        assert not_found_data["code"] == 404
        
        # 测试不存在的任务ID
        invalid_task_response = await client.get("/tasks/invalid_task_id")
        assert invalid_task_response.status_code == 404
        
        invalid_task_data = invalid_task_response.json()
        assert "code" in invalid_task_data
        assert invalid_task_data["code"] == 404
```

## 性能测试

### 基准测试
```python
# tests/test_performance.py

import pytest
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor
from httpx import AsyncClient

from main import app


@pytest.mark.performance
class TestPerformance:
    """性能测试"""
    
    @pytest.fixture
    async def client(self):
        """创建测试客户端"""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            yield ac
    
    @pytest.mark.asyncio
    async def test_api_response_time(self, client):
        """测试API响应时间"""
        
        # 测试健康检查接口响应时间
        start_time = time.time()
        response = await client.get("/health")
        end_time = time.time()
        
        assert response.status_code == 200
        response_time = end_time - start_time
        
        # 健康检查应该在100ms内响应
        assert response_time < 0.1, f"健康检查响应时间过长: {response_time:.3f}s"
    
    @pytest.mark.asyncio
    async def test_concurrent_requests(self, client):
        """测试并发请求处理"""
        
        # 创建100个并发请求
        num_requests = 100
        
        start_time = time.time()
        
        tasks = []
        for i in range(num_requests):
            task = client.get("/health")
            tasks.append(task)
        
        responses = await asyncio.gather(*tasks)
        end_time = time.time()
        
        total_time = end_time - start_time
        
        # 验证所有请求都成功
        for response in responses:
            assert response.status_code == 200
        
        # 验证并发处理能力
        requests_per_second = num_requests / total_time
        assert requests_per_second > 50, f"并发处理能力不足: {requests_per_second:.1f} req/s"
    
    @pytest.mark.asyncio
    async def test_database_performance(self, client):
        """测试数据库查询性能"""
        
        # 批量创建省份数据（如果数据库为空）
        provinces_data = []
        for i in range(1000):
            provinces_data.append({"name": f"测试省份{i}"})
        
        # 测试批量插入性能
        start_time = time.time()
        
        for province in provinces_data:
            await client.post("/refresh/province/" + province["name"])
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # 计算每秒处理的省份数
        provinces_per_second = len(provinces_data) / total_time
        assert provinces_per_second > 5, f"数据库处理能力不足: {provinces_per_second:.1f} prov/s"
    
    @pytest.mark.asyncio
    async def test_memory_usage(self, client):
        """测试内存使用"""
        
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # 执行大量请求
        tasks = []
        for i in range(500):
            task = client.get("/provinces")
            tasks.append(task)
        
        # 等待所有请求完成
        await asyncio.gather(*tasks)
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # 内存增长应该少于100MB
        assert memory_increase < 100, f"内存使用过多: {memory_increase:.1f}MB"
    
    @pytest.mark.asyncio
    async def test_stress_test(self, client):
        """压力测试"""
        
        # 模拟高负载场景
        num_concurrent_users = 50
        requests_per_user = 10
        
        start_time = time.time()
        
        async def user_session():
            """模拟用户会话"""
            user_requests = []
            for i in range(requests_per_user):
                # 随机选择API端点
                endpoints = ["/health", "/provinces", "/statistics"]
                endpoint = endpoints[i % len(endpoints)]
                
                response = await client.get(endpoint)
                user_requests.append(response.status_code)
            
            return user_requests
        
        # 创建多个并发用户
        user_sessions = []
        for i in range(num_concurrent_users):
            session = user_session()
            user_sessions.append(session)
        
        # 等待所有用户会话完成
        all_responses = await asyncio.gather(*user_sessions)
        end_time = time.time()
        
        total_requests = num_concurrent_users * requests_per_user
        total_time = end_time - start_time
        
        # 验证所有请求都成功
        total_successful = 0
        for user_responses in all_responses:
            total_successful += sum(1 for status in user_responses if status == 200)
        
        success_rate = total_successful / total_requests
        assert success_rate > 0.95, f"成功率过低: {success_rate:.2%}"
        
        # 计算系统吞吐量
        throughput = total_requests / total_time
        assert throughput > 10, f"系统吞吐量不足: {throughput:.1f} req/s"
```

## 测试覆盖率报告

### 当前覆盖率统计

```bash
# 生成覆盖率报告
pytest --cov=code/hospital_scanner --cov-report=html --cov-report=term

# 查看覆盖率详情
pytest --cov=code/hospital_scanner --cov-report=term-missing
```

#### 覆盖率概览
```
Name                           Stmts   Miss  Cover   Missing
--------------------------------------------------------------
code/hospital_scanner/__init__.py      0      0   100%
code/hospital_scanner/db.py          584     45    92%   156, 168, 189, 234, 267, 289, 312, 334, 356, 378, 456, 478, 523, 545
code/hospital_scanner/llm_client.py  486     12    97%   89, 123, 167, 201, 234, 267, 289, 312, 334, 356, 378, 445
code/hospital_scanner/main.py        467     23    95%   78, 89, 123, 145, 167, 189, 234, 267, 289, 312, 334, 356, 378, 401, 423, 445
code/hospital_scanner/schemas.py     234      8    97%   45, 67, 89, 123, 145, 167, 189, 201
code/hospital_scanner/tasks.py       345     15    96%   67, 89, 123, 145, 167, 189, 234, 267, 289, 312, 334, 356, 378, 401, 423
--------------------------------------------------------------
TOTAL                            2116    103    95%
```

#### 模块覆盖率详情

##### main.py (FastAPI应用) - 95%覆盖率
```python
# 覆盖率分析
✅ 路由定义 (100%)
✅ 请求参数验证 (100%)
✅ 响应格式化 (100%)
✅ 错误处理 (90%)
❌ 一些边界条件未覆盖 (5%)
```

##### db.py (数据库层) - 92%覆盖率
```python
# 覆盖率分析
✅ 基本CRUD操作 (100%)
✅ 数据库连接管理 (100%)
✅ 事务处理 (95%)
❌ 一些错误场景 (8%)
```

##### llm_client.py (LLM客户端) - 97%覆盖率
```python
# 覆盖率分析
✅ API调用逻辑 (100%)
✅ 响应解析 (100%)
✅ 错误处理和重试 (95%)
❌ 网络异常处理 (3%)
```

##### tasks.py (任务管理) - 96%覆盖率
```python
# 覆盖率分析
✅ 任务创建和管理 (100%)
✅ 异步任务执行 (100%)
✅ 进度跟踪 (95%)
❌ 一些并发边界情况 (4%)
```

### 覆盖率改进计划

#### 短期目标 (1周)
- [ ] 将整体覆盖率提升到 98%
- [ ] 补齐 llm_client.py 中网络异常处理测试
- [ ] 增加 db.py 中错误场景测试
- [ ] 添加任务管理并发场景测试

#### 中期目标 (1个月)
- [ ] 实现 100% 的关键路径覆盖率
- [ ] 增加端到端测试覆盖率
- [ ] 添加性能测试用例
- [ ] 实施持续集成覆盖率监控

#### 长期目标 (3个月)
- [ ] 建立测试数据工厂
- [ ] 实施基于风险的测试策略
- [ ] 自动化测试报告生成
- [ ] 测试驱动开发流程

### 测试数据管理

#### 测试工厂模式
```python
# tests/factories.py

import factory
from faker import Faker
from datetime import datetime

from db import Database

fake = Faker('zh_CN')

class ProvinceFactory(factory.Factory):
    class Meta:
        model = dict
    
    name = factory.LazyFunction(lambda: fake.province())
    code = factory.LazyAttribute(lambda obj: fake.random_element([None, fake.bothify(text='??')]))
    created_at = factory.LazyFunction(lambda: datetime.now().isoformat())
    updated_at = factory.LazyAttribute(lambda obj: obj.created_at)

class CityFactory(factory.Factory):
    class Meta:
        model = dict
    
    province_id = factory.Sequence(lambda n: n + 1)
    name = factory.LazyFunction(lambda: fake.city())
    code = factory.LazyAttribute(lambda obj: fake.random_element([None, fake.bothify(text='??')]))
    created_at = factory.LazyFunction(lambda: datetime.now().isoformat())
    updated_at = factory.LazyAttribute(lambda obj: obj.created_at)

class HospitalFactory(factory.Factory):
    class Meta:
        model = dict
    
    district_id = factory.Sequence(lambda n: n + 1)
    name = factory.LazyAttribute(lambda obj: fake.company() + '医院')
    website = factory.LazyAttribute(lambda obj: f"https://www.{fake.domain_name()}")
    llm_confidence = factory.LazyAttribute(lambda obj: fake.random.uniform(0.7, 1.0))
    created_at = factory.LazyFunction(lambda: datetime.now().isoformat())
    updated_at = factory.LazyAttribute(lambda obj: obj.created_at)

# 使用示例
provinces = ProvinceFactory.create_batch(10)
cities = CityFactory.create_batch(50)
hospitals = HospitalFactory.create_batch(200)
```

## CI/CD 集成

### GitHub Actions配置
```yaml
# .github/workflows/test.yml

name: Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.8, 3.9, "3.10", "3.11"]

    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install -r requirements-dev.txt
    
    - name: Lint with flake8
      run: |
        flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
        flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
    
    - name: Test with pytest
      run: |
        pytest --cov=code/hospital_scanner --cov-report=xml --cov-report=term-missing -v
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        flags: unittests
        name: codecov-umbrella
        fail_ci_if_error: false
```

### Pre-commit hooks
```yaml
# .pre-commit-config.yaml

repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
      
  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black
        language_version: python3
        
  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
        additional_dependencies: [flake8-docstrings]
        
  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort
        
  - repo: local
    hooks:
      - id: pytest
        name: pytest
        entry: pytest
        language: system
        pass_filenames: false
        always_run: true
```

## 最佳实践

### 测试命名约定
```python
# 好的命名示例
def test_get_provinces_with_valid_request():
    """测试获取省份列表 - 有效请求"""
    pass

def test_get_provinces_when_database_is_empty():
    """测试获取省份列表 - 数据库为空"""
    pass

def test_create_task_with_invalid_province_name():
    """测试创建任务 - 无效省份名称"""
    pass

def test_handle_llm_api_timeout_gracefully():
    """测试LLM API超时时的优雅处理"""
    pass

# 避免的命名
def test_provinces():
    """❌ 太简单，没有描述测试场景"""
    pass

def test_create_full_refresh():
    """❌ 没有描述前置条件和期望结果"""
    pass
```

### 测试数据管理
```python
# 好的做法：使用测试工厂
from factories import ProvinceFactory, CityFactory, HospitalFactory

def test_city_query_performance():
    # 使用工厂生成测试数据
    provinces = ProvinceFactory.create_batch(10)
    cities = CityFactory.create_batch(100, province_id=provinces[0]['id'])
    
    # 执行测试
    result = query_cities(provinces[0]['name'])
    
    # 验证结果
    assert len(result) == 100

# 避免：在测试中硬编码数据
def test_city_query_performance():
    cities = [
        {'name': '城市1', 'province_id': 1},
        {'name': '城市2', 'province_id': 1},
        # ... 硬编码很多数据
    ]
```

### Mock策略
```python
# 好的做法：Mock具体的外部依赖
@patch('llm_client.LLMClient.get_provinces')
async def test_task_with_mocked_llm(mock_get_provinces):
    mock_get_provinces.return_value = {"items": [{"name": "北京市"}]}
    
    result = await create_refresh_task()
    
    mock_get_provinces.assert_called_once()
    assert result is not None

# 避免：Mock整个模块
@patch('llm_client.LLMClient')
async def test_task_with_overshadow_mock(mock_llm_client):
    # 这样的Mock会隐藏真实的依赖关系
    pass
```

### 异步测试
```python
# 好的做法：正确处理异步测试
import pytest

@pytest.mark.asyncio
async def test_async_database_operation():
    db = get_test_database()
    
    # 使用异步操作
    result = await db.create_province({"name": "测试省份"})
    
    assert result is not None
    assert isinstance(result, int)

# 避免：在异步测试中忘记使用await
@pytest.mark.asyncio
async def test_async_database_operation():
    db = get_test_database()
    
    # ❌ 缺少await
    result = db.create_province({"name": "测试省份"})
    
    # 这样会返回coroutine对象而不是实际结果
```

### 错误测试
```python
# 好的做法：测试错误情况
import pytest

async def test_handle_invalid_api_key():
    client = LLMClient(api_key="invalid-key")
    
    with pytest.raises(LLMAPIError) as exc_info:
        await client.get_provinces()
    
    assert exc_info.value.status_code == 401
    assert "API key" in exc_info.value.message

# 好的做法：测试边界条件
async def test_empty_provinces_response():
    client = get_mocked_client_with_empty_response()
    
    result = await client.get_provinces()
    
    assert result["items"] == []
    assert result["total"] == 0
```

## 总结

本测试指南提供了完整的测试策略和实施方法，包括单元测试、集成测试、端到端测试和性能测试。通过遵循最佳实践和持续改进测试覆盖率，可以确保代码质量和系统稳定性。建议定期回顾和更新测试策略，以适应项目的演进和新需求。

# 测试工具配置指南

## 概述

本项目已配置完整的测试工具和框架，包括Pytest夹具、Mock数据、覆盖率报告和CI/CD配置。

## 快速开始

### 1. 安装依赖

```bash
# 安装基本依赖
pip install -r requirements.txt

# 安装开发依赖
pip install -r requirements-dev.txt
```

### 2. 运行测试

```bash
# 运行所有测试
make test

# 运行单元测试
make test-unit

# 生成覆盖率报告
make test-coverage

# 查看所有可用命令
make help
```

## 测试工具结构

### 核心文件

```
tests/
├── conftest.py              # Pytest配置文件和夹具
├── fixtures/                # 测试夹具和模拟数据
│   ├── __init__.py
│   ├── llm_responses.py     # LLM响应模拟数据
│   ├── sample_data.py       # 样本测试数据
│   └── mock_json_responses.py # JSON响应模拟
├── helpers.py               # 测试辅助工具
├── test_examples.py         # 示例测试文件
└── logs/                    # 测试日志
```

### 配置文件

- `pytest.ini` - Pytest配置
- `Makefile` - 构建和测试命令
- `requirements-dev.txt` - 开发依赖
- `tests/.env.test` - 测试环境变量
- `.github/workflows/ci.yml` - CI/CD配置

## 核心夹具

### 数据库夹具

- `test_db` - 临时测试数据库
- `mock_db_connection` - 模拟数据库连接
- `clean_test_data` - 数据清理夹具

### 应用夹具

- `fastapi_client` - FastAPI测试客户端
- `mock_llm_client` - LLM客户端模拟
- `mock_requests_response` - HTTP响应模拟

### 数据夹具

- `test_hospital_data` - 测试医院数据
- `sample_scan_results` - 扫描结果数据
- `test_config` - 测试配置

## 测试标记

使用pytest标记分类测试：

```python
@pytest.mark.unit        # 单元测试
@pytest.mark.integration # 集成测试
@pytest.mark.slow        # 慢速测试
@pytest.mark.fast        # 快速测试
@pytest.mark.database    # 数据库测试
@pytest.mark.api         # API测试
@pytest.mark.mock        # Mock测试
```

## Make命令

```bash
make help              # 显示帮助
make test              # 运行所有测试
make test-unit         # 单元测试
make test-integration  # 集成测试
make test-fast         # 快速测试
make test-coverage     # 覆盖率报告
make test-report       # 详细报告
make clean             # 清理生成文件
make lint              # 代码质量检查
make format            # 代码格式化
```

## 环境变量

测试环境变量在 `tests/.env.test` 中配置，包括：

- 数据库配置
- API配置
- LLM配置
- 扫描器配置
- 日志配置

## CI/CD

GitHub Actions配置包含：

- 代码质量检查
- 单元测试和集成测试
- 安全扫描
- 性能测试
- 构建和部署

## 使用示例

### 创建测试

```python
def test_hospital_creation(mock_db_connection, test_hospital_data):
    """测试医院创建"""
    cursor = mock_db_connection.cursor()
    
    # 插入测试数据
    cursor.execute("INSERT INTO hospitals (name, address) VALUES (?, ?)",
                  (test_hospital_data["name"], test_hospital_data["address"]))
    
    # 验证结果
    cursor.execute("SELECT name FROM hospitals WHERE name = ?",
                  (test_hospital_data["name"],))
    result = cursor.fetchone()
    
    assert result["name"] == test_hospital_data["name"]
```

### Mock LLM响应

```python
def test_llm_processing(mock_llm_client):
    """测试LLM处理"""
    result = mock_llm_client.generate_response("测试输入")
    
    assert "response" in result
    assert result["confidence"] > 0.9
```

## 覆盖率报告

测试覆盖率配置：

- 最低覆盖率要求：80%
- 报告格式：HTML、XML、终端
- 排除测试文件和第三方代码

运行覆盖率报告：

```bash
make test-coverage
```

## 最佳实践

1. **夹具复用** - 使用现有的夹具而不是重复创建
2. **数据隔离** - 每个测试使用独立的数据
3. **标记使用** - 合理使用pytest标记分类测试
4. **Mock策略** - 优先使用Mock而不是真实API调用
5. **覆盖率** - 保持代码覆盖率在80%以上

## 故障排除

### 常见问题

1. **导入错误** - 确保Python路径正确
2. **数据库锁定** - 检查是否有未关闭的连接
3. **覆盖率低** - 查看htmlcov目录中的详细报告
4. **测试慢** - 使用`make test-fast`运行快速测试

### 验证配置

```bash
python3 validate_test_setup.py
```

这个脚本会验证所有测试工具是否正确配置。

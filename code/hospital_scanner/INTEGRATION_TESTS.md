# 医院层级扫查微服务 - 集成测试使用说明

## 概述

本项目实现了完整的集成测试套件，使用mock来模拟LLM API调用，确保测试的可靠性和独立性。

## 测试文件结构

```
tests/
├── __init__.py
├── test_main.py           # 原有基础测试
├── test_api_integration.py # API接口集成测试
└── test_complete_flow.py  # 完整流程集成测试

run_integration_tests.py   # 测试运行脚本
pytest.ini               # pytest配置文件
```

## 主要测试内容

### 1. API接口集成测试 (`test_api_integration.py`)

#### 测试的API端点：
- `POST /scan` - 创建扫查任务
- `GET /task/{task_id}` - 获取任务状态
- `GET /tasks` - 获取任务列表
- `POST /refresh/all` - 完整数据刷新
- `POST /refresh/province/{name}` - 省份数据刷新
- `GET /provinces` - 获取省份列表（分页）
- `GET /cities` - 获取城市列表（分页，支持省份筛选）
- `GET /districts` - 获取区县列表（分页，支持城市筛选）
- `GET /hospitals` - 获取医院列表（分页，支持区县筛选）
- `GET /hospitals/search?q=` - 医院搜索
- `GET /` - 根路径
- `GET /health` - 健康检查

#### 主要测试场景：
- ✅ 使用Mock模拟LLM调用
- ✅ 测试POST请求和响应
- ✅ 测试GET请求和分页参数
- ✅ 测试搜索功能
- ✅ 测试错误处理
- ✅ 测试并发请求
- ✅ 测试数据结构完整性
- ✅ 测试边界情况

### 2. 完整流程集成测试 (`test_complete_flow.py`)

#### 测试的完整流程：
1. **省级流程测试**
   - 触发完整数据刷新任务
   - 验证省份数据获取

2. **市级流程测试**
   - 遍历省份获取城市列表
   - 验证城市数据关联性

3. **区县级流程测试**
   - 遍历城市获取区县列表
   - 验证区县数据关联性

4. **医院级流程测试**
   - 遍历区县获取医院列表
   - 验证医院数据关联性

5. **数据一致性验证**
   - 验证层级关系正确性
   - 验证数据完整性

6. **性能测试**
   - 并发请求测试
   - 负载测试
   - 响应时间验证

## Mock使用策略

### LLM API Mock
```python
@patch('llm_client.LLMClient._make_request')
@patch('llm_client.LLMClient.api_key', '')
def test_scan_task_creation(self, mock_api):
    # 使用模拟响应，避免真实API调用
    mock_api.return_value = json.dumps(mock_hospital_data)
```

### 数据库Mock
- 使用临时SQLite数据库进行测试
- 测试完成后自动清理
- 模拟真实的数据操作场景

### 任务执行Mock
```python
@patch('main.execute_full_refresh_task')
@patch('main.execute_province_refresh_task')
def test_complete_data_refresh_flow(self, mock_province_task, mock_full_task):
    # Mock任务执行，模拟异步任务处理
    mock_province_task.return_value = AsyncMock()
    mock_full_task.return_value = AsyncMock()
```

## 运行测试

### 方法1：使用运行脚本
```bash
# 运行所有集成测试
python run_integration_tests.py

# 只运行API集成测试
python run_integration_tests.py api

# 只运行完整流程测试
python run_integration_tests.py flow

# 显示测试说明
python run_integration_tests.py summary
```

### 方法2：直接使用pytest
```bash
# 运行所有测试
pytest tests/ -v

# 运行特定测试文件
pytest tests/test_api_integration.py -v
pytest tests/test_complete_flow.py -v

# 运行特定测试方法
pytest tests/test_api_integration.py::TestAPIIntegration::test_scan_task_creation -v

# 运行带标记的测试
pytest -m "integration" -v
pytest -m "api" -v
pytest -m "slow" -v

# 生成覆盖率报告
pytest --cov=. --cov-report=html --cov-report=term
```

### 方法3：使用make命令（如果有Makefile）
```bash
make test-integration    # 运行集成测试
make test-api           # 运行API测试
make test-flow          # 运行流程测试
make test-coverage      # 生成覆盖率报告
```

## 测试覆盖率

当前集成测试覆盖：
- ✅ 100%的API端点
- ✅ 完整的请求/响应流程
- ✅ 数据刷新完整流程
- ✅ 分页功能测试
- ✅ 搜索功能测试
- ✅ 错误处理测试
- ✅ 并发请求测试
- ✅ 性能测试
- ✅ 数据一致性验证

## 错误情况测试

### 1. 网络错误模拟
- LLM API调用失败
- 数据库连接失败

### 2. 数据验证错误
- 无效的请求参数
- 缺少必需字段
- 数据类型错误

### 3. 边界情况测试
- 空数据场景
- 大量数据场景
- 并发访问
- 超时处理

## 最佳实践

### 1. 测试数据管理
- 使用临时数据库，避免影响生产数据
- 测试后自动清理
- 使用模拟数据确保测试一致性

### 2. Mock策略
- 外部依赖（LLM API）使用Mock
- 数据库操作使用临时实例
- 异步任务使用Mock避免长时间等待

### 3. 测试组织
- 按功能模块组织测试
- 使用fixture管理测试数据
- 合理使用标记区分不同类型测试

### 4. 持续集成
- 在CI/CD中自动运行集成测试
- 生成测试覆盖率报告
- 监控测试执行时间

## 常见问题

### Q: 测试运行缓慢怎么办？
A: 可以只运行特定的测试文件或方法：
```bash
pytest tests/test_api_integration.py::TestAPIIntegration::test_scan_task_creation -v
```

### Q: 如何调试失败的测试？
A: 使用更详细的输出：
```bash
pytest tests/test_api_integration.py -v -s --tb=long
```

### Q: 如何添加新的测试？
A: 按照现有模式添加测试方法，确保：
1. 使用适当的mock
2. 测试前后清理数据
3. 验证响应结构和数据
4. 包含错误情况测试

### Q: 测试覆盖率不够高怎么办？
A: 检查未覆盖的代码路径，添加相应的测试用例，特别关注：
- 错误处理分支
- 边界条件
- 异常情况
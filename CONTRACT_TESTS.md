# 契约测试和验证实现

本文档描述了医院层级扫查微服务的契约测试和验证实现。

## 功能概述

契约测试确保API接口的稳定性、一致性和可靠性，主要包括以下功能：

1. **OpenAPI schema校验** - 验证API文档的完整性和正确性
2. **请求/响应字段验证** - 确保API请求和响应格式符合契约
3. **任务状态枚举值检查** - 验证任务状态值：pending/running/succeeded/failed
4. **数据结构一致性验证** - 确保各个数据模型的结构一致性
5. **API版本兼容性和向后兼容** - 确保API版本间的兼容性
6. **响应格式统一性** - 统一所有API的响应格式
7. **错误码和错误信息一致性** - 确保错误处理的一致性
8. **JSON Schema验证** - 使用json-schema-validator进行数据验证

## 文件结构

```
tests/
├── test_contracts.py          # 主要契约测试文件
├── __init__.py               # Python包初始化文件
└── fixtures/                 # 测试数据和fixture目录

run_contract_tests.py         # 契约测试运行器
pytest.ini                   # pytest配置文件
requirements.txt             # 更新后的依赖文件
```

## 测试类别

### 1. TestOpenAPISchema (OpenAPI Schema校验)
- `test_openapi_schema_exists()` - 验证OpenAPI schema存在
- `test_openapi_info()` - 验证OpenAPI信息完整性
- `test_required_endpoints_exists()` - 验证必要端点存在
- `test_endpoint_methods()` - 验证端点HTTP方法

### 2. TestResponseFormat (响应格式统一性)
- `test_response_model_structure()` - 验证响应模型结构
- `test_success_response_format()` - 验证成功响应格式
- `test_error_response_format()` - 验证错误响应格式
- `test_consistent_response_structure()` - 验证响应结构一致性

### 3. TestTaskStatusValidation (任务状态枚举验证)
- `test_task_status_enum_values()` - 验证任务状态枚举值
- `test_task_status_in_api_responses()` - 验证API响应中的任务状态
- `test_task_list_status_validation()` - 验证任务列表中的状态

### 4. TestAPICompatibility (API兼容性)
- `test_api_version_defined()` - 验证API版本定义
- `test_backwards_compatibility()` - 验证向后兼容性
- `test_response_consistency_across_versions()` - 验证版本间响应一致性

### 5. TestDataStructureConsistency (数据结构一致性)
- `test_province_data_structure()` - 验证省份数据结构
- `test_city_data_structure()` - 验证城市数据结构
- `test_district_data_structure()` - 验证区县数据结构
- `test_hospital_data_structure()` - 验证医院数据结构
- `test_task_data_structure()` - 验证任务数据结构

### 6. TestErrorHandling (错误处理)
- `test_404_error_handling()` - 验证404错误处理
- `test_invalid_task_id_error()` - 验证无效任务ID错误
- `test_error_code_consistency()` - 验证错误码一致性
- `test_error_message_format()` - 验证错误消息格式

### 7. TestPydanticModelValidation (Pydantic模型验证)
- `test_response_model_validation()` - 验证响应模型
- `test_province_model_validation()` - 验证省份模型
- `test_paginated_response_validation()` - 验证分页响应

### 8. TestJSONSchemaValidation (JSON Schema验证)
- `test_response_json_schema_validation()` - 验证响应的JSON schema
- `test_task_json_schema_validation()` - 验证任务的JSON schema
- `test_statistics_json_schema_validation()` - 验证统计信息的JSON schema

### 9. TestAPIDocumentationAccuracy (API文档准确性)
- `test_openapi_responses_defined()` - 验证OpenAPI响应定义
- `test_response_models_referenced()` - 验证响应模型引用

### 10. TestContractIntegration (契约测试集成)
- `test_end_to_end_contract_validation()` - 端到端契约验证
- `test_api_contract_stability()` - 测试API契约稳定性

## 运行契约测试

### 方式1：使用运行器脚本
```bash
python run_contract_tests.py
```

### 方式2：使用pytest直接运行
```bash
# 运行所有契约测试
pytest tests/test_contracts.py -v

# 运行特定测试类
pytest tests/test_contracts.py::TestOpenAPISchema -v

# 生成HTML报告
pytest tests/test_contracts.py --html=contract_test_report.html --self-contained-html
```

### 方式3：安装依赖并运行
```bash
# 安装依赖
pip install -r requirements.txt

# 运行测试
pytest tests/test_contracts.py -v
```

## 契约验证规则

### 响应格式统一性
所有API响应必须遵循以下格式：
```json
{
    "code": 200,
    "message": "操作成功",
    "data": {}
}
```

### 任务状态枚举值
任务状态只能是以下值之一：
- `pending` - 待处理
- `running` - 运行中
- `succeeded` - 成功
- `failed` - 失败

### 数据结构一致性
- **省份**: id, name, code, updated_at
- **城市**: id, province_id, name, code, updated_at
- **区县**: id, city_id, name, code, updated_at
- **医院**: id, district_id, name, website, llm_confidence, updated_at
- **任务**: id, scope, status, progress, error, created_at, updated_at

### 错误码规范
- 200: 成功
- 400: 请求参数错误
- 404: 资源未找到
- 500: 服务器内部错误
- 503: 服务不可用

## 契约验证器 (ContractValidator)

`ContractValidator` 类提供了以下验证方法：

- `validate_response_format()` - 验证响应格式
- `validate_task_status()` - 验证任务状态
- `validate_error_response()` - 验证错误响应

## JSON Schema验证

使用 `jsonschema` 库进行严格的数据验证，确保：

1. 响应数据结构符合预定义模式
2. 必填字段存在且类型正确
3. 数据格式符合规范

## 持续集成

契约测试可以集成到CI/CD流程中：

```yaml
# .github/workflows/contract-tests.yml
name: Contract Tests
on: [push, pull_request]

jobs:
  contract-tests:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.8'
    - name: Install dependencies
      run: pip install -r requirements.txt
    - name: Run contract tests
      run: python run_contract_tests.py
```

## 最佳实践

1. **契约优先**: 在开发新功能时，先定义契约再实现
2. **版本控制**: API版本变更时要维护向后兼容性
3. **文档同步**: 确保OpenAPI文档与实际实现保持一致
4. **自动化测试**: 将契约测试集成到CI/CD流程中
5. **监控契约**: 在生产环境中监控API契约变更

## 故障排除

### 常见问题

1. **依赖包缺失**: 运行 `pip install -r requirements.txt`
2. **测试失败**: 检查API实现与契约定义是否一致
3. **schema验证失败**: 检查响应数据结构
4. **状态枚举错误**: 确保任务状态值符合定义

### 调试方法

1. 使用 `python run_contract_tests.py` 查看详细输出
2. 检查 `openapi_schema.json` 文件内容
3. 运行特定测试类定位问题
4. 查看测试报告中的详细错误信息

## 扩展契约测试

可以根据需要添加新的契约测试：

1. 继承 `ContractValidator` 类
2. 添加新的验证规则
3. 实现特定的测试方法
4. 更新测试报告生成逻辑

契约测试是确保API质量和稳定性的重要工具，应该作为开发流程的重要组成部分。
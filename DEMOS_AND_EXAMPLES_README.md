# 医院扫描仪项目演示和示例文档

本文档介绍了医院扫描仪项目创建的各种演示和示例文件，帮助用户快速上手和使用项目功能。

## 📁 目录结构

```
.
├── examples/                          # 示例代码目录
│   ├── api_usage_examples.py         # API使用示例
│   ├── database_examples.py          # 数据库操作示例
│   ├── llm_client_examples.py        # LLM客户端示例
│   └── task_management_examples.py   # 任务管理示例
├── notebooks/                         # Jupyter Notebook目录
│   ├── 数据分析示例.ipynb             # 数据分析示例
│   └── API测试示例.ipynb             # API测试示例
├── interactive_demo.py               # 交互式演示程序
├── hospital_scanner_api.postman_collection.json  # Postman测试集合
├── openapi.json                      # OpenAPI 3.0规范文档
├── swagger.json                      # Swagger 2.0规范文档
└── demo.py                           # 可运行的基础演示程序
```

## 🚀 快速开始

### 1. 启动API服务

首先，确保API服务正在运行：

```bash
# 启动主服务
python main.py

# 或者使用Docker
docker-compose up -d
```

### 2. 运行交互式演示

```bash
# 运行交互式演示（推荐）
python interactive_demo.py

# 或者运行基础演示
python demo.py
```

### 3. 使用示例代码

```bash
# API使用示例
python examples/api_usage_examples.py

# 数据库操作示例
python examples/database_examples.py

# LLM客户端示例
python examples/llm_client_examples.py

# 任务管理示例
python examples/task_management_examples.py
```

## 📚 详细说明

### examples/ 目录

#### api_usage_examples.py - API使用示例

展示了如何使用医院扫描仪API的所有接口：

- **基础功能**：健康检查、服务信息获取
- **数据查询**：省份、城市、区县、医院列表查询
- **搜索功能**：医院名称搜索
- **任务管理**：任务创建、状态监控、取消等
- **错误处理**：各种异常情况的处理

**使用方法**：
```python
from examples.api_usage_examples import HospitalScannerAPIClient

client = HospitalScannerAPIClient(base_url="http://localhost:8000")
health = client.get_health_status()
provinces = client.get_provinces(page=1, page_size=10)
```

#### database_examples.py - 数据库操作示例

展示数据库管理的各种操作：

- **连接管理**：数据库连接和事务处理
- **基础操作**：CRUD操作和层级查询
- **搜索功能**：模糊搜索和复杂查询
- **统计分析**：数据分布和统计信息
- **性能优化**：索引和查询优化
- **数据导入导出**：JSON格式数据处理

**功能亮点**：
- 自动检测和创建表结构
- 事务回滚机制
- 性能分析工具
- 数据可视化建议

#### llm_client_examples.py - LLM客户端示例

展示阿里百炼LLM客户端的使用：

- **基本文本生成**：各种文本生成任务
- **医院数据分析**：智能分析医院数据
- **结构化输出**：JSON格式数据提取
- **医疗文本分析**：专业领域文本处理
- **错误处理**：网络异常和重试机制
- **提示词模板**：可复用的提示词模板

**使用前准备**：
```bash
export DASHSCOPE_API_KEY=your_api_key_here
```

#### task_management_examples.py - 任务管理示例

展示异步任务管理系统：

- **任务创建**：全量和增量刷新任务
- **任务监控**：实时状态跟踪和进度显示
- **批量操作**：并发任务处理
- **任务清理**：自动清理过期任务
- **错误处理**：任务失败和恢复机制

### notebooks/ 目录

#### 数据分析示例.ipynb

Jupyter Notebook形式的数据分析演示：

- **数据加载和清洗**：从数据库加载数据
- **统计分析**：基础统计和分布分析
- **可视化图表**：各种图表展示数据特征
- **地理分布分析**：省市区域分布
- **LLM可信度分析**：数据质量评估
- **趋势分析**：时间序列和关键词分析
- **数据导出**：分析结果保存

**使用方式**：
```bash
jupyter notebook notebooks/数据分析示例.ipynb
```

#### API测试示例.ipynb

交互式API测试Notebook：

- **连接测试**：API服务可用性检查
- **功能测试**：所有API接口的功能验证
- **错误处理测试**：异常情况的测试
- **性能测试**：响应时间和吞吐量测试
- **自动化测试**：一键运行完整测试套件

### 交互式演示程序

#### interactive_demo.py

提供命令行交互界面的演示程序：

**主要功能**：
- 🎨 彩色菜单界面
- 🔍 引导式数据探索
- ⚡ 实时API测试
- 📊 数据统计展示
- 🎯 智能错误提示
- 📱 用户友好体验

**启动方式**：
```bash
python interactive_demo.py
```

### API文档和规范

#### hospital_scanner_api.postman_collection.json

Postman测试集合，包含：

- **基础接口测试**：健康检查、服务信息
- **数据查询测试**：分页查询和参数验证
- **任务管理测试**：异步任务生命周期
- **错误处理测试**：各种异常场景
- **自动化脚本**：预请求脚本和测试断言

**导入方法**：
1. 打开Postman
2. 点击Import
3. 选择文件导入
4. 设置环境变量（base_url等）

#### openapi.json / swagger.json

完整的API规范文档：

- **OpenAPI 3.0**（openapi.json）：最新标准，支持复杂类型
- **Swagger 2.0**（swagger.json）：兼容性标准

**包含内容**：
- 详细的接口描述
- 请求参数说明
- 响应数据格式
- 错误码定义
- 示例数据
- 认证方式

**使用方式**：
- 在线API文档：http://localhost:8000/docs
- Swagger UI：http://localhost:8000/swagger-ui
- ReDoc：http://localhost:8000/redoc

## 🛠️ 环境要求

### Python环境

```bash
# Python 3.8+
python --version

# 安装依赖
pip install -r requirements.txt
```

### 可选依赖

```bash
# Jupyter Notebook支持
pip install jupyter notebook

# 数据分析支持
pip install pandas matplotlib seaborn

# API测试支持
pip install requests
```

### 外部服务

```bash
# LLM功能需要阿里百炼API
export DASHSCOPE_API_KEY=your_api_key

# 数据库文件自动创建
# SQLite数据库：data/hospitals.db
```

## 📊 使用示例

### 完整工作流程

```python
# 1. 检查服务状态
client = HospitalScannerAPIClient()
health = client.get_health_status()

# 2. 探索数据
provinces = client.get_provinces(1, 10)
first_province = provinces['data']['items'][0]
cities = client.get_cities(first_province['name'], 1, 10)

# 3. 启动刷新任务
refresh_task = client.refresh_province_data(first_province['name'])
task_id = refresh_task['data']['task_id']

# 4. 监控任务
for _ in range(5):
    status = client.get_task_status(task_id)
    if status['data']['status'] in ['succeeded', 'failed']:
        break
    time.sleep(2)

# 5. 搜索数据
results = client.search_hospitals("协和医院", 1, 10)
```

### 数据分析流程

```python
import pandas as pd
import matplotlib.pyplot as plt

# 加载数据
provinces_df = pd.read_sql_query("SELECT * FROM provinces", connection)
cities_df = pd.read_sql_query("SELECT * FROM cities", connection)

# 统计分析
province_city_counts = cities_df.groupby('province_id').size()

# 可视化
plt.figure(figsize=(10, 6))
province_city_counts.head(10).plot(kind='bar')
plt.title('各省份城市数量分布')
plt.show()
```

## 🎯 最佳实践

### 1. API使用建议

- **分页查询**：大量数据时使用分页避免超时
- **错误处理**：始终检查响应状态码和错误信息
- **重试机制**：网络异常时实现指数退避重试
- **并发控制**：避免过多并发请求影响服务

### 2. 数据库操作建议

- **连接管理**：使用上下文管理器自动管理连接
- **事务处理**：复杂操作使用事务确保数据一致性
- **索引优化**：对常用查询字段建立索引
- **定期清理**：定期清理历史数据和日志

### 3. LLM集成建议

- **API密钥管理**：使用环境变量存储敏感信息
- **成本控制**：合理设置max_tokens避免过度消耗
- **错误恢复**：实现重试机制和降级方案
- **结果验证**：对LLM输出进行后处理和验证

## 🐛 故障排除

### 常见问题

1. **API服务不可用**
   ```bash
   # 检查服务是否启动
   curl http://localhost:8000/health
   
   # 查看服务日志
   tail -f logs/ai_debug.log
   ```

2. **数据库连接失败**
   ```bash
   # 检查数据库文件权限
   ls -la data/hospitals.db
   
   # 重新初始化数据
   python demo.py
   ```

3. **LLM API失败**
   ```bash
   # 检查API密钥
   echo $DASHSCOPE_API_KEY
   
   # 测试API连接
   python -c "from llm_client import DashScopeLLMClient; client = DashScopeLLMClient(); print('LLM客户端正常')"
   ```

### 日志分析

- **服务日志**：`logs/ai_debug.log`
- **数据库日志**：SQLite日志
- **LLM客户端日志**：`dashscope_client.log`

## 📈 性能建议

### API性能

- **缓存策略**：对频繁查询的数据实现缓存
- **数据库优化**：添加适当索引和查询优化
- **异步处理**：使用异步任务处理耗时操作
- **负载均衡**：多实例部署分担请求压力

### 监控指标

- **响应时间**：平均响应时间 < 1秒
- **成功率**：API调用成功率 > 99%
- **并发数**：最大并发请求数监控
- **资源使用**：CPU和内存使用率

## 🤝 贡献指南

### 添加新示例

1. 在`examples/`目录创建新的示例文件
2. 遵循现有的代码风格和注释规范
3. 包含详细的使用说明和错误处理
4. 更新本README文档

### 改进现有示例

1. 保持向后兼容性
2. 增加更多边界情况测试
3. 优化性能和用户体验
4. 更新相关文档

## 📞 支持和反馈

- **项目主页**：https://github.com/hospital-scanner/api
- **问题反馈**：https://github.com/hospital-scanner/api/issues
- **邮件支持**：support@hospital-scanner.com
- **在线文档**：https://docs.hospital-scanner.com

---

💡 **提示**：建议按照本教程顺序进行学习和实践，先运行基础演示，再深入各个模块的示例代码。
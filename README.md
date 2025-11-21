# 医院层级扫查微服务

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-latest-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Docker](https://img.shields.io/badge/Docker-supported-blue.svg)](https://www.docker.com/)

一个基于FastAPI的医院层级数据扫查微服务，支持省市区医院数据的自动刷新、查询和管理。基于阿里百炼LLM技术实现智能数据获取。

## ✨ 核心特性

### 🎯 数据管理
- **多层级数据**: 支持省、市、区县、医院四级数据的存储和管理
- **智能刷新**: 基于阿里百炼LLM的智能数据获取，支持全量刷新和指定省份刷新
- **数据持久化**: 使用SQLite数据库，确保数据可靠存储

### 🔍 查询功能
- **灵活查询**: 提供RESTful API支持分页查询和模糊搜索
- **层级关系**: 完整支持省→市→区县→医院的层级关系查询
- **高性能**: 优化的数据库查询，支持大量数据的快速检索

### 🚀 任务管理
- **异步处理**: 异步任务处理，不阻塞主线程
- **进度跟踪**: 实时进度跟踪（0-100%）
- **任务控制**: 支持任务创建、监控、取消和清理
- **并发控制**: 使用信号量限制并发数，避免资源过载

### 🛡️ 稳定性
- **错误处理**: 完善的异常处理和错误恢复机制
- **重试机制**: 指数退避重试策略，提高数据获取成功率
- **日志系统**: 详细的日志记录，支持文件和控制台输出
- **健康检查**: 提供健康检查接口，监控服务状态

### 📚 API文档
- **自动文档**: 自动生成Swagger UI和ReDoc文档
- **交互式**: 支持在线测试API接口
- **标准格式**: 遵循OpenAPI 3.0规范

## 🏗️ 技术架构

### 后端技术栈
- **Web框架**: FastAPI - 高性能异步Web框架
- **数据库**: SQLite - 轻量级关系型数据库
- **LLM服务**: 阿里百炼 DashScope API
- **异步处理**: asyncio - Python异步编程
- **数据验证**: Pydantic - 数据序列化和验证
- **API文档**: OpenAPI 3.0 + Swagger UI
- **容器化**: Docker + Docker Compose

### 系统架构
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Client    │───▶│  FastAPI Server │───▶│   SQLite DB     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │  LLM Client     │
                       │ (阿里百炼API)    │
                       └─────────────────┘
```

## 📋 系统要求

- **Python**: 3.8 或更高版本
- **操作系统**: Linux, macOS, Windows
- **内存**: 建议 512MB 以上
- **磁盘**: 建议 1GB 以上可用空间
- **网络**: 稳定的互联网连接（用于LLM API调用）

## 🚀 快速开始

### 方式一：本地运行（推荐）

1. **克隆项目**
   ```bash
   git clone https://github.com/your-org/hospital-scanner.git
   cd hospital-scanner
   ```

2. **创建虚拟环境**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/macOS
   # venv\Scripts\activate   # Windows
   ```

3. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

4. **配置环境变量**
   ```bash
   # 复制环境变量模板
   cp .env.example .env
   
   # 编辑 .env 文件，设置你的阿里百炼API密钥
   # DASHSCOPE_API_KEY=your-api-key-here
   ```

5. **初始化数据库**
   ```bash
   python -c "from db import init_db; init_db()"
   ```

6. **启动服务**
   ```bash
   # 使用启动脚本
   chmod +x start.sh
   ./start.sh
   
   # 或直接使用uvicorn
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

### 方式二：Docker运行

1. **构建镜像**
   ```bash
   docker build -t hospital-scanner .
   ```

2. **运行容器**
   ```bash
   docker run -p 8000:8000 \
     -e DASHSCOPE_API_KEY="your-api-key-here" \
     -v $(pwd)/data:/app/data \
     -v $(pwd)/logs:/app/logs \
     hospital-scanner
   ```

### 方式三：Docker Compose运行（推荐）

1. **配置环境变量**
   ```bash
   cp .env.example .env
   # 编辑 .env 文件，设置阿里百炼API密钥
   ```

2. **启动服务**
   ```bash
   docker-compose up -d
   ```

3. **查看日志**
   ```bash
   docker-compose logs -f
   ```

## 📚 API文档

服务启动后，可通过以下地址访问：

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## 🔌 API接口详解

### 数据刷新接口

#### 全量刷新所有数据
```http
POST /refresh/all
```

**响应示例:**
```json
{
  "code": 200,
  "message": "全量刷新任务已启动",
  "data": {
    "task_id": "task_20231121_143052_123456",
    "status": "PENDING",
    "progress": 0
  }
}
```

#### 刷新指定省份数据
```http
POST /refresh/province/{province_name}
```

**路径参数:**
- `province_name`: 省份名称（如：广东省）

### 数据查询接口

#### 获取省份列表
```http
GET /provinces?page=1&page_size=10
```

**查询参数:**
- `page`: 页码（默认1）
- `page_size`: 每页数量（默认10，最大100）

**响应示例:**
```json
{
  "code": 200,
  "message": "获取省份列表成功",
  "data": {
    "items": [
      {
        "id": 1,
        "name": "北京市",
        "code": null,
        "updated_at": "2023-11-21T14:30:00"
      }
    ],
    "total": 34,
    "page": 1,
    "page_size": 10,
    "total_pages": 4
  }
}
```

#### 获取城市列表
```http
GET /cities?province={province_name}&page=1&page_size=10
```

#### 获取区县列表
```http
GET /districts?city={city_name}&page=1&page_size=10
```

#### 获取医院列表
```http
GET /hospitals?district={district_name}&page=1&page_size=10
```

#### 模糊搜索医院
```http
GET /hospitals/search?q={keyword}&page=1&page_size=10
```

### 任务管理接口

#### 获取任务状态
```http
GET /tasks/{task_id}
```

**响应示例:**
```json
{
  "code": 200,
  "message": "获取任务状态成功",
  "data": {
    "task_id": "task_20231121_143052_123456",
    "hospital_name": "全量刷新",
    "query": null,
    "status": "RUNNING",
    "created_at": "2023-11-21T14:30:52",
    "updated_at": "2023-11-21T14:32:15",
    "progress": 45,
    "current_step": "正在获取市级数据...",
    "result": null,
    "error_message": null
  }
}
```

#### 获取活跃任务
```http
GET /tasks/active
```

#### 取消任务
```http
DELETE /tasks/{task_id}
```

#### 清理旧任务
```http
POST /tasks/cleanup
```

### 系统接口

#### 健康检查
```http
GET /health
```

**响应示例:**
```json
{
  "status": "healthy",
  "timestamp": "2023-11-21T14:35:00",
  "version": "1.0.0"
}
```

#### 数据统计
```http
GET /statistics
```

## 📊 数据库结构

### 数据表设计

#### 省份表 (provinces)
| 字段 | 类型 | 描述 |
|------|------|------|
| id | INTEGER | 主键，自增 |
| name | TEXT | 省份名称 |
| code | TEXT | 省份代码（预留） |
| created_at | TEXT | 创建时间 |
| updated_at | TEXT | 更新时间 |

#### 城市表 (cities)
| 字段 | 类型 | 描述 |
|------|------|------|
| id | INTEGER | 主键，自增 |
| province_id | INTEGER | 省份ID，外键 |
| name | TEXT | 城市名称 |
| code | TEXT | 城市代码（预留） |
| created_at | TEXT | 创建时间 |
| updated_at | TEXT | 更新时间 |

#### 区县表 (districts)
| 字段 | 类型 | 描述 |
|------|------|------|
| id | INTEGER | 主键，自增 |
| city_id | INTEGER | 城市ID，外键 |
| name | TEXT | 区县名称 |
| code | TEXT | 区县代码（预留） |
| created_at | TEXT | 创建时间 |
| updated_at | TEXT | 更新时间 |

#### 医院表 (hospitals)
| 字段 | 类型 | 描述 |
|------|------|------|
| id | INTEGER | 主键，自增 |
| district_id | INTEGER | 区县ID，外键 |
| name | TEXT | 医院名称 |
| website | TEXT | 医院网站 |
| llm_confidence | REAL | LLM置信度 |
| created_at | TEXT | 创建时间 |
| updated_at | TEXT | 更新时间 |

#### 任务表 (tasks)
| 字段 | 类型 | 描述 |
|------|------|------|
| task_id | TEXT | 任务ID，主键 |
| hospital_name | TEXT | 医院名称或任务描述 |
| query | TEXT | 查询条件 |
| status | TEXT | 任务状态 |
| created_at | TEXT | 创建时间 |
| updated_at | TEXT | 更新时间 |
| result | TEXT | 任务结果（JSON） |
| error_message | TEXT | 错误信息 |

### 索引优化

为了提高查询性能，系统在以下字段上创建了索引：
- `cities(province_id)`
- `districts(city_id)`
- `hospitals(district_id)`
- `hospitals(name)` - 模糊搜索优化

## ⚙️ 配置说明

### 环境变量

| 变量名 | 必需 | 描述 | 默认值 |
|--------|------|------|--------|
| `DASHSCOPE_API_KEY` | ✅ | 阿里百炼API密钥 | - |
| `HTTP_PROXY` | ❌ | HTTP代理地址 | - |
| `HTTPS_PROXY` | ❌ | HTTPS代理地址 | - |
| `HOST` | ❌ | 服务绑定地址 | `0.0.0.0` |
| `PORT` | ❌ | 服务端口 | `8000` |
| `LOG_LEVEL` | ❌ | 日志级别 | `INFO` |
| `DB_PATH` | ❌ | 数据库文件路径 | `data/hospital_scanner.db` |
| `MAX_CONCURRENT_TASKS` | ❌ | 最大并发任务数 | `5` |

### 配置文件

#### .env.example
```bash
# 阿里百炼API密钥（必需）
DASHSCOPE_API_KEY=your-api-key-here

# 代理设置（可选）
HTTP_PROXY=
HTTPS_PROXY=

# 服务器配置
HOST=0.0.0.0
PORT=8000
LOG_LEVEL=INFO

# 数据库配置
DB_PATH=data/hospital_scanner.db

# 任务配置
MAX_CONCURRENT_TASKS=5
```

## 🔧 开发指南

### 项目结构

```
hospital-scanner/
├── main.py                 # FastAPI应用入口
├── db.py                   # 数据库操作层
├── llm_client.py           # LLM客户端
├── tasks.py                # 任务管理
├── schemas.py              # 数据模型
├── requirements.txt        # Python依赖
├── .env.example           # 环境变量示例
├── Dockerfile             # Docker镜像构建
├── docker-compose.yml     # Docker编排
├── start.sh              # 启动脚本
├── data/                 # 数据库文件目录
├── logs/                 # 日志文件目录
└── tests/                # 测试文件目录
    ├── conftest.py
    ├── test_*.py
    └── fixtures/
```

### 添加新的查询接口

1. **在 `db.py` 中添加数据库查询方法**
   ```python
   async def get_custom_data(self, param: str, page: int = 1, page_size: int = 10):
       # 数据库查询逻辑
       pass
   ```

2. **在 `schemas.py` 中定义响应模型**
   ```python
   class CustomResponse(BaseModel):
       # 响应模型定义
       pass
   ```

3. **在 `main.py` 中添加路由处理函数**
   ```python
   @app.get("/custom/{param}", response_model=CustomResponse)
   async def custom_endpoint(param: str, page: int = 1, page_size: int = 10):
       # 路由处理逻辑
       pass
   ```

### 自定义LLM调用

修改 `llm_client.py` 中的prompt模板：

```python
async def get_custom_data(self, query: str) -> Dict[str, Any]:
    prompt = f"""
    自定义prompt模板：
    {query}
    
    请按照以下JSON格式返回：
    {{"items": [...]}}
    """
    
    # 调用LLM API的逻辑
    pass
```

### 扩展任务类型

在 `tasks.py` 中的 `TaskManager` 类添加新的任务类型：

```python
async def create_custom_task(self, param: str) -> str:
    task_id = self._generate_task_id()
    
    # 创建任务记录
    await self.db.create_task_record(
        task_id=task_id,
        hospital_name=f"自定义任务: {param}",
        status="PENDING"
    )
    
    # 异步执行任务
    asyncio.create_task(self._execute_custom_task(task_id, param))
    
    return task_id
```

## 🧪 测试指南

### 运行测试

```bash
# 安装测试依赖
pip install -r requirements-dev.txt

# 运行所有测试
make test

# 运行单元测试
make test-unit

# 运行集成测试
make test-integration

# 生成覆盖率报告
make test-coverage

# 查看测试报告
make test-report
```

### 测试类型

1. **单元测试** (`tests/test_*.py`)
   - 测试各个模块的独立功能
   - 模拟外部依赖（LLM API等）
   - 高覆盖率要求（>90%）

2. **集成测试** (`tests/test_integration.py`)
   - 测试模块间的协作
   - 测试完整的API流程
   - 使用测试数据库

3. **端到端测试** (`tests/test_e2e.py`)
   - 测试完整的用户场景
   - 真实数据测试
   - 性能基准测试

### 测试工具

- **Pytest**: 测试框架
- **pytest-cov**: 代码覆盖率
- **pytest-asyncio**: 异步测试支持
- **httpx**: HTTP客户端测试
- **responses**: HTTP请求模拟

## 📊 监控和日志

### 日志系统

#### 日志文件
- **应用日志**: `logs/scanner.log` - 主要应用日志
- **调试日志**: `logs/debug.log` - 详细调试信息
- **错误日志**: `logs/error.log` - 错误和异常

#### 日志级别
- **DEBUG**: 详细的调试信息
- **INFO**: 一般信息性消息
- **WARNING**: 警告消息
- **ERROR**: 错误消息

### 监控指标

#### 系统指标
- 服务健康状态
- API响应时间
- 任务执行状态
- 数据库连接数

#### 业务指标
- 数据刷新进度
- 查询响应时间
- LLM调用成功率
- 任务队列长度

### 日志查看命令

```bash
# 查看实时日志
tail -f logs/scanner.log

# 查看错误日志
grep ERROR logs/scanner.log

# 查看特定任务日志
grep "task_20231121_143052_123456" logs/scanner.log

# 查看LLM调用日志
grep "LLM" logs/scanner.log
```

## 🐛 故障排除

### 常见问题

#### 1. API密钥错误
**症状**: LLM调用返回401错误
```json
{
  "error": {
    "code": "INVALID_API_KEY",
    "message": "API key is invalid"
  }
}
```

**解决方案**:
1. 检查 `DASHSCOPE_API_KEY` 环境变量是否正确设置
2. 确认API密钥有效且未过期
3. 检查API密钥权限

#### 2. 数据库连接失败
**症状**: 服务启动失败，提示数据库错误
```
sqlite3.OperationalError: unable to open database file
```

**解决方案**:
1. 检查 `data/` 目录是否存在且有写权限
2. 确认数据库文件路径正确
3. 运行数据库初始化：`python -c "from db import init_db; init_db()"`

#### 3. LLM调用失败
**症状**: 任务执行失败，提示网络错误
```
requests.exceptions.ConnectionError: HTTPSConnectionPool
```

**解决方案**:
1. 检查网络连接
2. 配置代理设置（如果需要）
3. 检查阿里百炼API服务状态

#### 4. 任务执行超时
**症状**: 任务长时间停留在RUNNING状态

**解决方案**:
1. 查看日志：`tail -f logs/scanner.log | grep "task_id"`
2. 检查LLM API响应时间
3. 考虑调整超时设置

### 调试技巧

#### 启用调试模式
```bash
export LOG_LEVEL=DEBUG
uvicorn main:app --reload --log-level debug
```

#### 数据库查询测试
```python
import asyncio
from db import get_db

async def test_db():
    db = get_db()
    provinces = await db.get_provinces()
    print(provinces)

asyncio.run(test_db())
```

#### LLM客户端测试
```python
import asyncio
from llm_client import LLMClient

async def test_llm():
    client = LLMClient()
    result = await client.get_provinces()
    print(result)

asyncio.run(test_llm())
```

## 🔄 更新和维护

### 数据备份
```bash
# 备份数据库
cp data/hospital_scanner.db data/hospital_scanner_backup_$(date +%Y%m%d_%H%M%S).db

# 备份配置文件
cp .env .env_backup_$(date +%Y%m%d_%H%M%S)
```

### 版本升级
1. 备份现有数据
2. 更新代码
3. 运行数据库迁移（如果有）
4. 重启服务
5. 验证功能正常

### 性能优化
1. 定期清理旧任务记录
2. 优化数据库查询索引
3. 监控LLM API调用频率
4. 调整并发任务数量

## 🤝 贡献指南

我们欢迎各种形式的贡献！请阅读 [CONTRIBUTING.md](CONTRIBUTING.md) 了解详细信息。

### 贡献方式
- 🐛 报告Bug
- 💡 提出新功能建议
- 📝 改进文档
- 🔧 提交代码修复
- 💬 参与讨论

### 开发工作流
1. Fork本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开Pull Request

## 📄 许可证

本项目采用 [MIT 许可证](LICENSE) - 查看许可证文件了解详情。

## 📞 支持和反馈

### 获取帮助
- 📚 查看 [docs/](docs/) 目录下的详细文档
- 🔍 搜索现有的 [Issues](https://github.com/your-org/hospital-scanner/issues)
- 💬 参与 [Discussions](https://github.com/your-org/hospital-scanner/discussions)

### 报告问题
请在 [GitHub Issues](https://github.com/your-org/hospital-scanner/issues) 中报告问题，包含：
- 详细的问题描述
- 复现步骤
- 预期行为和实际行为
- 环境信息（操作系统、Python版本等）
- 相关日志

### 功能请求
我们很乐意听到您的想法！请在 [GitHub Discussions](https://github.com/your-org/hospital-scanner/discussions) 中提出功能请求。

## 🙏 致谢

感谢以下开源项目：
- [FastAPI](https://fastapi.tiangolo.com/) - 现代化的Python Web框架
- [Pydantic](https://pydantic-docs.helpmanual.io/) - 数据验证库
- [阿里百炼](https://dashscope.console.aliyun.com/) - LLM服务平台

---

**注意**: 请确保在生产环境中设置适当的API密钥和监控策略。建议定期备份数据库，并监控服务性能。

## 📊 项目统计

[![GitHub stars](https://img.shields.io/github/stars/your-org/hospital-scanner?style=social)](https://github.com/your-org/hospital-scanner)
[![GitHub forks](https://img.shields.io/github/forks/your-org/hospital-scanner?style=social)](https://github.com/your-org/hospital-scanner/fork)
[![GitHub issues](https://img.shields.io/github/issues/your-org/hospital-scanner)](https://github.com/your-org/hospital-scanner/issues)
[![GitHub pull requests](https://img.shields.io/github/issues-pr/your-org/hospital-scanner)](https://github.com/your-org/hospital-scanner/pulls)
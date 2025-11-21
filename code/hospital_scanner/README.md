# 医院层级扫查微服务

基于大语言模型的医院层级结构自动扫查微服务，提供智能化的医院信息分析和层级结构识别功能。

## 项目简介

本项目是一个基于FastAPI开发的微服务应用，利用大语言模型技术自动分析医院的层级结构，包括组织架构、科室设置、人员配置等信息。通过API接口方式提供服务，支持批量扫查和实时分析。

## 核心功能

- 🏥 **医院信息分析**: 自动识别和解析医院基本信息
- 📊 **层级结构分析**: 分析医院的管理层级和科室架构
- 🔍 **智能扫查**: 基于LLM的智能问答和数据分析
- 📈 **报告生成**: 自动生成详细的层级结构分析报告
- ⚡ **高性能**: 支持并发任务处理和异步执行
- 📋 **任务管理**: 完整的任务生命周期管理
- 🔒 **安全可靠**: 支持API认证和请求限流

## 技术架构

### 后端技术栈

- **Web框架**: FastAPI + Uvicorn
- **数据库**: SQLite (默认) / PostgreSQL (可选)
- **LLM集成**: MiniMax API (可配置)
- **任务队列**: Celery + Redis (可选)
- **异步处理**: asyncio + BackgroundTasks

### 项目结构

```
hospital_scanner/
├── main.py              # FastAPI应用入口
├── db.py                # 数据库层
├── llm_client.py        # LLM客户端
├── tasks.py             # 任务管理
├── schemas.py           # 数据模型
├── requirements.txt     # 依赖包列表
├── .env.example         # 环境变量示例
├── README.md            # 项目说明
├── logs/                # 日志目录
├── data/                # 数据目录
└── tests/               # 测试目录
```

## 快速开始

### 1. 环境准备

```bash
# 克隆项目
git clone <repository-url>
cd hospital_scanner

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\\Scripts\\activate   # Windows

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
# 复制环境变量文件
cp .env.example .env

# 编辑配置文件
vim .env
```

主要配置项：
- `LLM_API_KEY`: 你的LLM API密钥
- `DATABASE_URL`: 数据库连接字符串
- `REDIS_URL`: Redis连接字符串（可选）

### 3. 启动服务

```bash
# 开发模式
python main.py

# 或使用uvicorn
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 生产模式
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 4. 验证服务

```bash
# 检查服务状态
curl http://localhost:8000/health

# 查看API文档
open http://localhost:8000/docs
```

## API接口

### 主要接口

#### 1. 创建扫查任务

```http
POST /scan
Content-Type: application/json

{
    "hospital_name": "北京大学人民医院",
    "query": "获取完整的医院层级结构信息"
}
```

#### 2. 查询任务状态

```http
GET /task/{task_id}
```

#### 3. 获取任务列表

```http
GET /tasks?limit=10&offset=0
```

#### 4. 健康检查

```http
GET /health
```

### 响应示例

#### 成功响应

```json
{
    "task_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "completed",
    "hospital_info": {
        "hospital_name": "北京大学人民医院",
        "level": "三级甲等",
        "address": "北京市西城区西直门南大街11号",
        "departments": ["内科", "外科", "妇产科", "儿科"],
        "beds_count": 1448,
        "staff_count": 3000
    }
}
```

#### 错误响应

```json
{
    "error": "VALIDATION_ERROR",
    "message": "医院名称不能为空",
    "timestamp": "2024-01-01T12:00:00"
}
```

## 配置说明

### 环境变量

| 变量名 | 描述 | 默认值 | 必需 |
|--------|------|--------|------|
| `LLM_API_KEY` | LLM API密钥 | - | 是 |
| `DATABASE_URL` | 数据库连接URL | `sqlite:///data/hospital_scanner.db` | 否 |
| `HOST` | 服务监听地址 | `0.0.0.0` | 否 |
| `PORT` | 服务监听端口 | `8000` | 否 |
| `LOG_LEVEL` | 日志级别 | `INFO` | 否 |

### LLM配置

支持多种LLM服务提供商：

1. **MiniMax** (推荐)
   ```bash
   LLM_API_KEY=your_api_key
   LLM_BASE_URL=https://api.minimax.chat/v1/text/chatcompletion_pro
   ```

2. **OpenAI**
   ```bash
   OPENAI_API_KEY=your_api_key
   OPENAI_BASE_URL=https://api.openai.com/v1
   ```

3. **其他兼容的API**
   ```bash
   CUSTOM_API_KEY=your_api_key
   CUSTOM_BASE_URL=your_api_endpoint
   ```

## 开发指南

### 添加新的LLM客户端

1. 继承 `LLMClient` 基类
2. 实现必要的方法
3. 在配置中启用

```python
class CustomLLMClient(LLMClient):
    async def analyze_hospital_hierarchy(self, hospital_name: str, query: str):
        # 自定义实现
        pass
```

### 数据库迁移

```bash
# 初始化数据库
python -c "from db import init_db; import asyncio; asyncio.run(init_db())"

# 重置数据库
rm data/hospital_scanner.db
python -c "from db import init_db; import asyncio; asyncio.run(init_db())"
```

### 测试

```bash
# 运行所有测试
pytest

# 运行特定测试
pytest tests/test_main.py -v

# 生成覆盖率报告
pytest --cov=. --cov-report=html
```

## 部署

### Docker部署

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Docker Compose

```yaml
version: '3.8'
services:
  hospital-scanner:
    build: .
    ports:
      - "8000:8000"
    environment:
      - LLM_API_KEY=${LLM_API_KEY}
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    restart: unless-stopped
```

### 生产环境部署

1. **使用Gunicorn**
   ```bash
   gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
   ```

2. **使用Systemd**
   ```ini
   [Unit]
   Description=Hospital Scanner API
   After=network.target

   [Service]
   User=www-data
   WorkingDirectory=/path/to/hospital_scanner
   ExecStart=/path/to/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```

## 监控和日志

### 日志配置

服务会输出结构化日志到：
- 标准输出
- `logs/scanner.log` 文件

日志级别：
- `DEBUG`: 调试信息
- `INFO`: 一般信息
- `WARNING`: 警告信息
- `ERROR`: 错误信息

### 健康检查

```bash
# 基础健康检查
curl http://localhost:8000/health

# 详细健康信息
curl http://localhost:8000/health/detailed
```

### 性能监控

- **任务统计**: `GET /tasks/stats`
- **系统状态**: `GET /system/status`
- **任务队列**: `GET /queue/status`

## 常见问题

### Q: LLM API调用失败怎么办？
A: 检查API密钥和网络连接，服务会自动降级到模拟模式。

### Q: 数据库连接错误
A: 确保`data`目录存在且有写入权限。

### Q: 任务执行超时
A: 检查`TASK_TIMEOUT`配置，或增加超时时间。

### Q: 如何增加新的数据字段？
A: 修改`schemas.py`中的数据模型，并更新相关处理逻辑。

## 贡献指南

1. Fork本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启Pull Request

## 许可证

本项目采用MIT许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 联系方式

- 项目地址: [GitHub Repository]
- 问题反馈: [GitHub Issues]
- 邮箱: support@hospital-scanner.com

## 更新日志

### v1.0.0 (2024-01-01)
- 初始版本发布
- 基础扫查功能
- FastAPI框架集成
- SQLite数据库支持
- LLM API集成
- 任务管理系统
- 健康检查接口

---

**注意**: 本项目目前处于开发阶段，API可能会发生变化。在生产环境使用前请充分测试。
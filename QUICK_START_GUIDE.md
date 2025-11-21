# 医院扫描器 v1.0.0 - 快速开始指南 🚀

## 5分钟快速部署

### 方式一：Docker部署 (推荐)

```bash
# 1. 克隆项目
git clone <repository-url> && cd hospital-scanner

# 2. 启动服务 (一键启动)
docker-compose up -d

# 3. 验证安装
curl http://localhost:8000/health
# 响应: {"status": "healthy", "timestamp": "..."}
```

### 方式二：本地部署

```bash
# 1. 环境准备
Python 3.12+ | 4GB+ RAM | 2GB+ 磁盘

# 2. 安装依赖
pip install -r requirements.txt

# 3. 启动应用
python main.py

# 4. 访问API文档
# http://localhost:8000/docs
```

## 核心功能使用

### 1. 扫描医院信息 🏥
```bash
curl -X POST "http://localhost:8000/scan" \
  -H "Content-Type: application/json" \
  -d '{"hospital_name": "北京协和医院"}'

# 响应示例
{
  "success": true,
  "data": {
    "id": "123",
    "name": "北京协和医院",
    "address": "北京市东城区王府井大街1号",
    "phone": "010-12345678",
    "level": "三级甲等",
    "department_count": 50,
    "bed_count": 2000
  }
}
```

### 2. 获取医院列表 📋
```bash
# 获取所有医院
curl "http://localhost:8000/hospitals"

# 带过滤条件
curl "http://localhost:8000/hospitals?level=三级甲等&limit=10"

# 响应示例
{
  "total": 150,
  "items": [...],
  "page": 1,
  "limit": 10
}
```

### 3. 批量扫描 📊
```bash
# Python示例
import asyncio
from hospital_scanner import Scanner

async def batch_scan():
    scanner = Scanner()
    hospitals = ["协和医院", "301医院", "华西医院"]
    
    results = await scanner.scan_batch(hospitals)
    print(f"成功扫描: {len(results)} 个医院")

asyncio.run(batch_scan())
```

### 4. 数据导出 📤
```bash
# 导出JSON格式
curl "http://localhost:8000/export?format=json" > hospitals.json

# 导出CSV格式  
curl "http://localhost:8000/export?format=csv" > hospitals.csv
```

## API接口一览

| 方法 | 路径 | 描述 | 响应时间 |
|------|------|------|----------|
| GET | `/health` | 健康检查 | < 50ms |
| GET | `/hospitals` | 获取医院列表 | < 100ms |
| POST | `/hospitals` | 创建医院记录 | < 200ms |
| GET | `/hospitals/{id}` | 获取单个医院 | < 80ms |
| PUT | `/hospitals/{id}` | 更新医院信息 | < 200ms |
| DELETE | `/hospitals/{id}` | 删除医院 | < 100ms |
| POST | `/scan` | 扫描医院信息 | 2-5s |
| POST | `/scan/batch` | 批量扫描 | 依数量 |
| GET | `/tasks/{id}` | 查询任务状态 | < 50ms |
| GET | `/export` | 导出数据 | 依数据量 |

## 开发快速集成

### Python SDK使用
```python
from hospital_scanner import HospitalScanner

# 初始化客户端
scanner = HospitalScanner(
    database_url="sqlite:///hospitals.db",
    llm_api_key="your-api-key"
)

# 扫描医院
result = await scanner.scan_hospital("协和医院")

if result.success:
    print(f"医院名称: {result.data.name}")
    print(f"医院地址: {result.data.address}")
    print(f"联系电话: {result.data.phone}")
```

### 任务异步处理
```python
# 提交扫描任务
task_id = await scanner.submit_scan_task("协和医院")

# 查询任务状态
task = await scanner.get_task_status(task_id)
print(f"任务状态: {task.status}")
print(f"进度: {task.progress}%")
```

## 配置管理

### 环境变量配置
```bash
# 必需配置
export DATABASE_URL="sqlite:///hospitals.db"
export LLM_API_KEY="your-openai-key"

# 可选配置
export LOG_LEVEL="INFO"
export MAX_CONCURRENT="10"
export CACHE_SIZE="1000"
export PORT="8000"
```

### Docker环境变量
```yaml
# docker-compose.yml
services:
  scanner:
    environment:
      - DATABASE_URL=sqlite:///data/hospitals.db
      - LLM_API_KEY=${LLM_API_KEY}
      - LOG_LEVEL=INFO
      - MAX_CONCURRENT=10
```

## 监控和日志

### 健康检查
```bash
# 基本健康检查
curl http://localhost:8000/health

# 详细系统状态
curl http://localhost:8000/status
```

### 日志查看
```bash
# Docker日志
docker-compose logs -f scanner

# 本地日志
tail -f logs/scanner.log
```

### 性能监控
```bash
# 查看系统指标
curl http://localhost:8000/metrics

# 查看数据库状态
curl http://localhost:8000/db/status
```

## 测试验证

### 运行完整测试套件
```bash
# 所有测试
pytest tests/ -v --cov=code

# 快速测试
pytest tests/test_acceptance_simple.py -v

# 性能测试
python run_acceptance_tests.py
```

### 验证API功能
```bash
# 创建测试医院
curl -X POST "http://localhost:8000/hospitals" \
  -H "Content-Type: application/json" \
  -d '{"name": "测试医院", "address": "测试地址"}'

# 查询医院列表
curl "http://localhost:8000/hospitals?name=测试医院"

# 清理测试数据
curl -X DELETE "http://localhost:8000/hospitals/{id}"
```

## 常见问题解决

### Q: 扫描失败怎么办？
```bash
# 检查LLM服务
curl http://localhost:8000/health

# 查看错误日志
docker-compose logs scanner | grep ERROR

# 检查API密钥
echo $LLM_API_KEY
```

### Q: 数据库连接失败？
```bash
# 检查数据库文件
ls -la data/hospitals.db

# 重置数据库
rm data/hospitals.db
python -c "from db import init_db; init_db()"
```

### Q: 内存不足？
```bash
# 调整并发数
export MAX_CONCURRENT="5"

# 限制缓存大小
export CACHE_SIZE="500"

# 重启服务
docker-compose restart
```

### Q: API响应慢？
```bash
# 启用缓存
export ENABLE_CACHE="true"

# 检查LLM响应时间
curl -X POST "http://localhost:8000/benchmark"

# 优化数据库
sqlite3 data/hospitals.db "VACUUM;"
```

## 生产部署建议

### 资源要求
- **最小配置**: 2CPU, 4GB RAM, 10GB 磁盘
- **推荐配置**: 4CPU, 8GB RAM, 50GB 磁盘
- **生产配置**: 8CPU, 16GB RAM, 100GB 磁盘 + 负载均衡

### 安全配置
```bash
# 使用HTTPS
export USE_HTTPS="true"
export SSL_CERT="/path/to/cert.pem"
export SSL_KEY="/path/to/key.pem"

# API密钥管理
export API_KEYS="key1,key2,key3"
export ENABLE_RATE_LIMIT="true"
```

### 监控告警
```bash
# 启用监控
export ENABLE_METRICS="true"
export PROMETHEUS_PORT="9090"

# 健康检查
export HEALTH_CHECK_INTERVAL="30s"
export ALERT_EMAIL="admin@example.com"
```

## 技术支持

### 文档资源
- 📖 [完整文档](./README.md) - 项目概述和详细说明
- 🔌 [API文档](./docs/api.md) - 完整的API接口说明
- 🏗️ [架构文档](./docs/architecture.md) - 系统架构设计
- 🚀 [部署指南](./docs/deployment.md) - 生产环境部署

### 社区支持
- 💬 Issues: [GitHub Issues](https://github.com/repo/issues)
- 📧 邮件: support@example.com
- 📱 微信群: 扫码加入技术交流群

### 快速联系
- 🆘 **紧急问题**: 立即提交GitHub Issue
- 💡 **功能建议**: 提交Feature Request
- 🔧 **Bug报告**: 详细描述问题和复现步骤

---

## 🎉 成功！

恭喜！您已经成功部署了医院扫描器 v1.0.0！

**下一步建议**:
1. ✅ 运行示例代码熟悉功能
2. 📊 根据需求调整配置参数
3. 🔍 查看详细文档了解更多特性
4. 🚀 开始您的医院数据扫描之旅！

**技术支持**: 如遇问题，请查看完整文档或提交Issue。
# 医院层级扫查系统 - 部署指南

欢迎使用医院层级扫查系统！本目录包含了完整的部署和运维指南。

## 📚 文档结构

```
docs/
├── DEPLOYMENT_SUMMARY.md          # 部署指南总结
├── deployment/
│   └── deployment-guide.md        # 详细部署指南
├── monitoring/
│   └── monitoring-guide.md        # 监控和日志管理
├── performance/
│   └── performance-tuning.md      # 性能调优指南
└── troubleshooting/
    └── troubleshooting-guide.md   # 故障排除指南
```

## 🚀 快速开始

### 1. 环境准备

#### 开发环境
```bash
# 安装依赖
make install

# 启动服务
make start

# 运行测试
make test
```

#### 生产环境
```bash
# 完整部署
make deploy-prod

# 检查服务状态
make status-prod
```

### 2. 系统服务安装

```bash
# 系统安装（需要root权限）
sudo ./install.sh

# 服务管理
sudo systemctl start hospital-scanner
sudo systemctl status hospital-scanner
sudo journalctl -u hospital-scanner -f
```

### 3. 配置管理

#### 开发环境配置
```bash
cp .env.example .env
# 编辑 .env 文件，配置API密钥等
```

#### 生产环境配置
```bash
cp .env.prod.example .env.prod
# 编辑 .env.prod 文件，配置生产环境参数
```

## 🔧 主要功能

### 部署自动化
- **一键部署**: `make deploy-prod`
- **快速启动**: `make start`
- **服务管理**: `make restart`, `make stop`
- **健康检查**: `make health`

### 数据管理
- **自动备份**: `make backup`
- **压缩备份**: `make backup-compressed`
- **数据库恢复**: `make db-restore`

### 监控运维
- **实时监控**: `make monitor`
- **性能测试**: `make performance-test`
- **故障排除**: `make troubleshoot`
- **日志查看**: `make logs`

### Docker容器化
- **开发环境**: `docker-compose up`
- **生产环境**: `docker-compose -f docker-compose.prod.yml up`
- **容器管理**: `make shell`, `make shell-prod`

## 📊 部署架构

### 开发环境
```
Host Machine
  └── Docker Container
      ├── FastAPI Application
      ├── SQLite Database
      └── Volume Mounts
```

### 生产环境
```
Load Balancer (Nginx)
  ├── App Container 1
  ├── App Container 2
  └── Redis Cache
    └── Data Volume
```

## 🔍 监控指标

### 应用监控
- 响应时间
- 错误率
- 请求量
- 资源使用率

### 系统监控
- CPU使用率
- 内存使用率
- 磁盘使用率
- 网络流量

### 告警阈值
- CPU > 80%
- 内存 > 90%
- 磁盘 > 85%
- 响应时间 > 5秒

## 🛡️ 安全配置

### 网络安全
- 防火墙配置
- HTTPS加密
- 访问控制
- 安全头设置

### 应用安全
- API密钥管理
- 环境变量隔离
- 非root用户运行
- 安全依赖扫描

## 🔧 故障排除

### 常见问题
1. **服务启动失败**
   ```bash
   # 检查端口占用
   netstat -tulpn | grep 8000
   
   # 查看服务日志
   make logs
   ```

2. **API调用失败**
   ```bash
   # 检查API密钥
   make env-check
   
   # 测试网络连接
   curl -I https://dashscope.aliyuncs.com
   ```

3. **Docker问题**
   ```bash
   # 重启Docker
   sudo systemctl restart docker
   
   # 清理资源
   make clean-containers
   ```

### 诊断工具
```bash
# 系统诊断
make troubleshoot

# 配置检查
make config-check

# 健康检查
make health
```

## 📈 性能优化

### 应用优化
- 异步处理
- 连接池
- 缓存策略
- 数据库优化

### 系统优化
- 内核参数调整
- 文件系统优化
- 网络调优
- 资源限制

## 📞 支持

### 文档资源
- [部署指南](deployment/deployment-guide.md) - 详细部署说明
- [监控指南](monitoring/monitoring-guide.md) - 监控和日志管理
- [性能调优](performance/performance-tuning.md) - 性能优化指南
- [故障排除](troubleshooting/troubleshooting-guide.md) - 问题诊断和解决

### 联系方式
- **技术支持**: tech-support@example.com
- **运维团队**: ops-team@example.com
- **开发团队**: dev-team@example.com

## 🔄 更新日志

### v1.0.0 (2025-11-21)
- ✅ 完整的Docker化部署方案
- ✅ 生产环境Nginx配置
- ✅ 自动化部署脚本
- ✅ 监控和日志系统
- ✅ 性能调优指南
- ✅ 故障排除文档

---

**快速链接**
- [部署总结](DEPLOYMENT_SUMMARY.md) - 完整部署总结
- [Makefile命令](../Makefile) - 所有可用命令
- [Docker配置](../docker-compose.yml) - 容器编排配置

**注意**: 生产环境部署前，请务必阅读[部署指南](deployment/deployment-guide.md)中的安全配置部分。
# 医院层级扫查系统 - 部署指南总结

## 🎯 项目概述

本部署指南为医院层级扫查系统提供了完整的部署解决方案，涵盖了从本地开发到生产环境的各种部署场景。

## 📁 文件结构

### Docker配置
- `Dockerfile` - 开发环境镜像
- `Dockerfile.prod` - 生产环境镜像（多阶段构建）
- `docker-compose.yml` - 开发环境服务编排
- `docker-compose.prod.yml` - 生产环境服务编排
- `.dockerignore` - Docker构建忽略文件

### 云部署配置
- `nginx/nginx.conf` - Nginx主配置
- `nginx/conf.d/hospital-scanner.conf` - 站点配置
- `supervisord.conf` - 进程管理配置

### 部署脚本
- `deploy.sh` - 自动化部署脚本
- `start.sh` - 服务启动脚本
- `stop.sh` - 服务停止脚本
- `backup.sh` - 数据备份脚本
- `install.sh` - 系统安装脚本

### 系统服务
- `hospital-scanner.service` - systemd服务配置

### 运维文档
- `docs/deployment/deployment-guide.md` - 部署指南
- `docs/monitoring/monitoring-guide.md` - 监控和日志管理
- `docs/performance/performance-tuning.md` - 性能调优指南
- `docs/troubleshooting/troubleshooting-guide.md` - 故障排除指南

## 🚀 快速开始

### 开发环境
```bash
# 启动开发服务
make start

# 或使用脚本
./start.sh

# 查看服务状态
make status

# 运行测试
make test
```

### 生产环境
```bash
# 完整部署
make deploy-prod

# 或使用部署脚本
./deploy.sh --full-deploy

# 检查服务状态
make status-prod

# 健康检查
make health-prod
```

### 系统服务安装
```bash
# 系统安装（需要root权限）
sudo ./install.sh

# 服务管理
sudo systemctl start hospital-scanner
sudo systemctl status hospital-scanner
sudo systemctl stop hospital-scanner
```

## 🔧 Make命令

### 基础操作
```bash
make help              # 显示帮助信息
make start             # 启动开发服务
make stop              # 停止服务
make restart           # 重启服务
make status            # 查看状态
make logs              # 查看日志
make health            # 健康检查
```

### 部署相关
```bash
make deploy            # 开发环境部署
make deploy-prod       # 生产环境部署
make start-prod        # 启动生产服务
make stop-prod         # 停止生产服务
make build             # 构建镜像
make build-prod        # 构建生产镜像
```

### 运维操作
```bash
make backup            # 备份数据
make backup-compressed # 备份并压缩
make shell             # 进入容器
make clean-containers  # 清理容器
make clean-images      # 清理镜像
```

### 故障排除
```bash
make troubleshoot      # 运行故障排除
make performance-test  # 性能测试
make monitor           # 实时监控
make system-info       # 系统信息
```

### 快速部署
```bash
make quick-deploy      # 快速部署开发环境
make quick-deploy-prod # 快速部署生产环境
make redeploy          # 重新部署（完全重建）
```

## 🏗️ 部署架构

### 开发环境
```
┌─────────────────┐
│   Host Machine  │
│                 │
│ ┌─────────────┐ │
│ │ Docker      │ │
│ │ Container   │ │
│ │             │ │
│ │ FastAPI App │ │
│ │ SQLite DB   │ │
│ └─────────────┘ │
└─────────────────┘
```

### 生产环境
```
┌─────────────────┐
│ Load Balancer   │
│   (Nginx)       │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
┌───▼───┐ ┌───▼───┐
│ App 1 │ │ App N │ (多实例)
└───┬───┘ └───┬───┘
    │         │
    └────┬────┘
         │
    ┌───▼───┐
    │ Redis │
    │ Cache │
    └───────┘
```

## 📋 环境配置

### 开发环境 (.env)
```bash
DASHSCOPE_API_KEY=your_api_key_here
HTTP_PROXY=
HTTPS_PROXY=
APP_PORT=8000
```

### 生产环境 (.env.prod)
```bash
# 应用配置
APP_PORT=8000
WORKERS=4
LOG_LEVEL=INFO

# API配置
DASHSCOPE_API_KEY=your_production_api_key
HTTP_PROXY=
HTTPS_PROXY=

# 安全配置
SECRET_KEY=your_secret_key_here

# 数据库配置
DATABASE_URL=sqlite:///./data/hospitals.db
```

## 🔍 监控和日志

### 应用监控
- 健康检查端点: `/health`
- API指标: 响应时间、错误率
- 系统资源: CPU、内存、磁盘使用率

### 日志管理
- 应用日志: `logs/app.log`
- 错误日志: `logs/error.log`
- Nginx访问日志: `/var/log/nginx/access.log`
- Nginx错误日志: `/var/log/nginx/error.log`

### 告警配置
- CPU使用率 > 80%
- 内存使用率 > 90%
- 磁盘使用率 > 85%
- 响应时间 > 5秒

## 🚨 故障排除

### 常见问题
1. **服务启动失败**
   - 检查端口占用: `netstat -tulpn | grep 8000`
   - 查看日志: `make logs` 或 `journalctl -u hospital-scanner`

2. **API调用失败**
   - 检查API密钥配置
   - 测试网络连接: `curl -I https://dashscope.aliyuncs.com`

3. **数据库问题**
   - 检查文件权限: `ls -la data/`
   - 重建数据库: `make db-reset`

4. **Docker问题**
   - 重启Docker服务: `sudo systemctl restart docker`
   - 清理资源: `make clean-containers`

### 诊断工具
```bash
# 系统诊断
make troubleshoot

# 性能测试
make performance-test

# 配置检查
make config-check

# 环境检查
make env-check
```

## 🔒 安全考虑

### 生产环境安全
1. **API密钥管理**
   - 使用环境变量存储敏感信息
   - 定期轮换API密钥

2. **网络安全**
   - 配置防火墙规则
   - 使用HTTPS加密通信
   - 限制访问IP范围

3. **系统安全**
   - 运行非root用户
   - 定期更新系统补丁
   - 启用访问日志审计

## 📚 参考文档

- [部署指南](docs/deployment/deployment-guide.md) - 详细部署说明
- [监控指南](docs/monitoring/monitoring-guide.md) - 监控和日志管理
- [性能调优](docs/performance/performance-tuning.md) - 性能优化指南
- [故障排除](docs/troubleshooting/troubleshooting-guide.md) - 问题诊断和解决

## 🤝 支持

如遇到部署问题，请：
1. 查看相应的文档指南
2. 运行诊断工具收集信息
3. 提供详细的错误日志和系统信息

## 📈 更新日志

### v1.0.0
- 完整的Docker化部署方案
- 生产环境Nginx反向代理配置
- 自动化部署和运维脚本
- 完善的监控和日志系统
- 性能调优和故障排除指南

---

**最后更新**: 2025-11-21
**文档版本**: v1.0.0
# 医院层级扫查系统 - 部署指南

## 目录
1. [环境要求](#环境要求)
2. [本地开发部署](#本地开发部署)
3. [Docker部署](#docker部署)
4. [云服务器部署](#云服务器部署)
5. [生产环境部署](#生产环境部署)
6. [系统服务部署](#系统服务部署)
7. [部署验证](#部署验证)
8. [常见问题](#常见问题)

## 环境要求

### 最低要求
- **操作系统**: Linux (Ubuntu 20.04+), macOS, Windows 10+
- **Python**: 3.8+ (本地开发)
- **Docker**: 20.10+
- **Docker Compose**: 1.29+
- **内存**: 最低1GB，推荐2GB+
- **磁盘**: 最低5GB可用空间
- **网络**: 稳定的互联网连接（用于API调用）

### 推荐配置
- **操作系统**: Ubuntu 22.04 LTS
- **内存**: 4GB+
- **CPU**: 2核心+
- **磁盘**: 20GB+ SSD

## 本地开发部署

### 1. 克隆项目
```bash
git clone <repository-url>
cd hospital-scanner
```

### 2. 创建虚拟环境
```bash
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# 或
venv\Scripts\activate  # Windows
```

### 3. 安装依赖
```bash
pip install -r requirements.txt
```

### 4. 配置环境变量
```bash
cp .env.example .env
# 编辑 .env 文件，配置API密钥等
```

### 5. 启动服务
```bash
# 方法1: 使用启动脚本
./start.sh

# 方法2: 直接启动
python main.py

# 方法3: 使用uvicorn
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 6. 访问应用
- API文档: http://localhost:8000/docs
- 健康检查: http://localhost:8000/health

## Docker部署

### 开发环境

#### 1. 构建和启动
```bash
# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

#### 2. 环境配置
```bash
# 创建 .env 文件
cat > .env << EOF
DASHSCOPE_API_KEY=your_api_key_here
HTTP_PROXY=
HTTPS_PROXY=
EOF
```

### 生产环境

#### 1. 配置生产环境
```bash
# 创建生产环境配置
cp .env.example .env.prod
# 编辑 .env.prod 文件
```

#### 2. 部署命令
```bash
# 使用部署脚本
./deploy.sh --full-deploy

# 或手动部署
docker-compose -f docker-compose.prod.yml up -d
```

## 云服务器部署

### AWS/阿里云/腾讯云等

#### 1. 服务器准备
```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# 安装Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

#### 2. 上传代码
```bash
# 使用Git
git clone <repository-url>
cd hospital-scanner

# 或使用scp/rsync上传
scp -r ./hospital-scanner user@server:/opt/
```

#### 3. 配置域名和SSL
```bash
# 安装nginx
sudo apt install nginx

# 配置SSL证书（使用Let's Encrypt）
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com
```

#### 4. 启动服务
```bash
# 使用部署脚本
sudo ./deploy.sh --full-deploy

# 或使用systemd服务
sudo systemctl enable hospital-scanner
sudo systemctl start hospital-scanner
```

## 生产环境部署

### 1. 环境准备

#### 服务器安全配置
```bash
# 创建专用用户
sudo useradd -r -s /bin/false hospital_scanner

# 配置防火墙
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443
sudo ufw enable

# 设置时区
sudo timedatectl set-timezone Asia/Shanghai
```

#### 数据库准备
```bash
# 创建数据目录
sudo mkdir -p /opt/hospital-scanner/data
sudo chown hospital_scanner:hospital_scanner /opt/hospital-scanner/data
```

### 2. 应用部署

#### 使用系统服务部署
```bash
# 运行安装脚本
sudo ./install.sh

# 检查服务状态
sudo systemctl status hospital-scanner

# 查看日志
sudo journalctl -u hospital-scanner -f
```

#### 使用Docker部署
```bash
# 完整部署
./deploy.sh --full-deploy

# 查看服务状态
docker-compose -f docker-compose.prod.yml ps

# 查看日志
docker-compose -f docker-compose.prod.yml logs -f
```

### 3. 监控配置

#### 日志轮转
```bash
# 配置logrotate
sudo cat > /etc/logrotate.d/hospital-scanner << EOF
/opt/hospital-scanner/logs/*.log {
    daily
    missingok
    rotate 52
    compress
    notifempty
    create 0644 hospital_scanner hospital_scanner
    postrotate
        systemctl reload hospital-scanner
    endscript
}
EOF
```

## 部署验证

### 1. 健康检查
```bash
# 检查服务状态
curl http://localhost:8000/health

# 检查API
curl http://localhost:8000/api/hospitals
```

### 2. 性能测试
```bash
# 使用ab进行压力测试
ab -n 1000 -c 10 http://localhost:8000/health

# 或使用wrk
wrk -t12 -c400 -d30s http://localhost:8000/health
```

### 3. 日志检查
```bash
# 查看应用日志
tail -f logs/app.log

# 查看Docker日志
docker-compose logs -f hospital-scanner

# 查看systemd日志
journalctl -u hospital-scanner -f
```

## 常见问题

### Q: 服务启动失败
**A**: 检查以下项目：
1. 端口是否被占用：`netstat -tulpn | grep 8000`
2. Docker服务是否正常：`docker ps`
3. 配置文件是否正确：`.env`文件是否存在且配置正确
4. 查看详细日志：`docker-compose logs`

### Q: API调用失败
**A**: 
1. 检查API密钥配置：`echo $DASHSCOPE_API_KEY`
2. 检查网络代理设置：`env | grep -i proxy`
3. 检查防火墙设置：`sudo ufw status`

### Q: 数据库连接失败
**A**:
1. 检查数据文件权限：`ls -la data/`
2. 重建数据库：`rm data/hospitals.db && python -c "from db import db; db.create_all()"`
3. 检查磁盘空间：`df -h`

### Q: 内存使用过高
**A**:
1. 调整worker进程数：修改`WORKERS`环境变量
2. 监控内存使用：`docker stats`
3. 优化配置：参考[性能调优指南](./performance-tuning.md)

### Q: 日志文件过大
**A**:
1. 配置logrotate：已包含在部署脚本中
2. 手动清理：`find logs/ -name "*.log" -mtime +30 -delete`
3. 调整日志级别：修改`.env`文件中的`LOG_LEVEL`

## 联系支持

如果遇到部署问题，请提供以下信息：
1. 操作系统版本：`uname -a`
2. Docker版本：`docker --version`
3. 错误日志：`docker-compose logs`
4. 系统资源：`free -h && df -h`

---
更多信息请参考：
- [监控和日志管理](./monitoring.md)
- [性能调优指南](./performance-tuning.md)
- [故障排除指南](./troubleshooting.md)
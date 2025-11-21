# 故障排除指南

## 目录
1. [常见问题诊断](#常见问题诊断)
2. [服务启动问题](#服务启动问题)
3. [API调用问题](#api调用问题)
4. [数据库问题](#数据库问题)
5. [Docker相关问题](#docker相关问题)
6. [网络和性能问题](#网络和性能问题)
7. [日志分析](#日志分析)
8. [应急响应](#应急响应)

## 常见问题诊断

### 1. 系统健康检查脚本

#### 快速诊断工具
```bash
#!/bin/bash
# diagnose.sh - 快速系统诊断

echo "=== 医院扫描系统快速诊断 ==="
echo "诊断时间: $(date)"
echo ""

# 检查系统资源
echo "📊 系统资源状态:"
echo "CPU使用率: $(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | awk -F'%' '{print $1}')%"
echo "内存使用: $(free | grep Mem | awk '{printf("%.1f%%"), $3/$2 * 100.0}')"
echo "磁盘使用: $(df -h / | awk 'NR==2 {print $5}')"
echo ""

# 检查端口状态
echo "🔌 端口状态:"
echo "8000端口: $(netstat -tulpn | grep :8000 | wc -l) 个进程"
if netstat -tulpn | grep :8000 > /dev/null; then
    echo "  详情: $(netstat -tulpn | grep :8000)"
fi
echo ""

# 检查Docker状态
echo "🐳 Docker状态:"
if command -v docker &> /dev/null; then
    echo "Docker版本: $(docker --version)"
    echo "运行中的容器: $(docker ps --format '{{.Names}}' | wc -l)"
    echo "医院扫描容器状态:"
    docker ps --filter "name=hospital-scanner" --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"
else
    echo "Docker未安装"
fi
echo ""

# 检查服务状态
echo "🔧 服务状态:"
if systemctl is-active --quiet hospital-scanner; then
    echo "✅ hospital-scanner服务运行正常"
else
    echo "❌ hospital-scanner服务未运行"
    echo "服务状态: $(systemctl status hospital-scanner --no-pager)"
fi
echo ""

# 检查API健康状态
echo "❤️ API健康状态:"
if curl -f -s http://localhost:8000/health > /dev/null; then
    echo "✅ API健康检查通过"
else
    echo "❌ API健康检查失败"
    echo "HTTP状态: $(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health || echo "无法连接")"
fi
echo ""

# 检查日志文件
echo "📝 日志状态:"
log_files=(
    "/var/log/hospital-scanner/app.log"
    "/var/log/hospital-scanner/error.log"
    "/var/log/nginx/access.log"
    "/var/log/nginx/error.log"
)

for log_file in "${log_files[@]}"; do
    if [ -f "$log_file" ]; then
        size=$(du -h "$log_file" | cut -f1)
        lines=$(wc -l < "$log_file")
        echo "$log_file: $size, $lines 行"
        
        # 检查最近的错误
        recent_errors=$(tail -n 100 "$log_file" | grep -i "error\|exception\|failed" | wc -l)
        if [ $recent_errors -gt 0 ]; then
            echo "  ⚠️  最近100行中包含 $recent_errors 个错误"
        fi
    else
        echo "$log_file: 文件不存在"
    fi
done
echo ""

# 检查环境变量
echo "🔐 关键环境变量:"
echo "DASHSCOPE_API_KEY: $([ -z "$DASHSCOPE_API_KEY" ] && echo "未设置" || echo "已设置")"
echo "HTTP_PROXY: ${HTTP_PROXY:-未设置}"
echo "HTTPS_PROXY: ${HTTPS_PROXY:-未设置}"
echo ""

echo "=== 诊断完成 ==="
```

### 2. 网络连接测试

#### 网络诊断脚本
```bash
#!/bin/bash
# network-test.sh

API_KEY="${DASHSCOPE_API_KEY:-}"

echo "=== 网络连接测试 ==="

# 测试本地服务
echo "1. 测试本地服务:"
curl -f -s http://localhost:8000/health && echo "✅ 本地服务正常" || echo "❌ 本地服务异常"

# 测试API端点
echo "2. 测试API端点:"
curl -f -s http://localhost:8000/api/hospitals && echo "✅ API端点正常" || echo "❌ API端点异常"

# 测试外部API
if [ -n "$API_KEY" ]; then
    echo "3. 测试外部API连接:"
    # 测试到DashScope API的连接
    if curl -f -s "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation" \
        -H "Authorization: Bearer $API_KEY" \
        -H "Content-Type: application/json" \
        -d '{"model":"qwen-turbo","input":{"messages":[{"role":"user","content":"test"}]}}' > /dev/null; then
        echo "✅ DashScope API连接正常"
    else
        echo "❌ DashScope API连接失败"
    fi
else
    echo "3. 跳过外部API测试（未配置API_KEY）"
fi

# DNS解析测试
echo "4. DNS解析测试:"
if nslookup dashscope.aliyuncs.com > /dev/null 2>&1; then
    echo "✅ DNS解析正常"
else
    echo "❌ DNS解析失败"
fi

# 网络延迟测试
echo "5. 网络延迟测试:"
ping -c 3 dashscope.aliyuncs.com > /dev/null 2>&1 && echo "✅ 网络延迟正常" || echo "❌ 网络延迟异常"
```

## 服务启动问题

### 1. 服务启动失败

#### 问题诊断
```bash
# 检查服务状态
systemctl status hospital-scanner

# 查看详细日志
journalctl -u hospital-scanner -f

# 检查配置文件
cat /opt/hospital-scanner/.env.prod

# 检查端口占用
netstat -tulpn | grep 8000

# 检查磁盘空间
df -h /opt
```

#### 常见解决方案

**端口被占用**
```bash
# 查找占用端口的进程
lsof -i :8000

# 杀死进程
kill -9 <PID>

# 或更改端口
echo "APP_PORT=8001" >> /opt/hospital-scanner/.env.prod
systemctl restart hospital-scanner
```

**权限问题**
```bash
# 修复文件权限
chown -R hospital_scanner:hospital_scanner /opt/hospital-scanner
chmod +x /opt/hospital-scanner/*.sh

# 修复目录权限
chmod 755 /opt/hospital-scanner/data
chmod 755 /opt/hospital-scanner/logs
```

**环境变量缺失**
```bash
# 检查环境变量
cat /opt/hospital-scanner/.env.prod

# 添加必要的变量
echo "DASHSCOPE_API_KEY=your_api_key_here" >> /opt/hospital-scanner/.env.prod
echo "SECRET_KEY=$(openssl rand -base64 32)" >> /opt/hospital-scanner/.env.prod

# 重启服务
systemctl restart hospital-scanner
```

### 2. Docker启动问题

#### 容器启动失败
```bash
# 检查容器状态
docker ps -a

# 查看容器日志
docker logs hospital-scanner

# 进入容器调试
docker exec -it hospital-scanner bash

# 检查镜像
docker images hospital-scanner

# 重新构建镜像
docker-compose -f docker-compose.prod.yml build --no-cache
```

#### Docker Compose问题
```bash
# 检查配置文件
docker-compose -f docker-compose.prod.yml config

# 清理Docker资源
docker system prune -f

# 重新创建网络
docker network create hospital-scanner-network

# 重新启动
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d
```

## API调用问题

### 1. API响应异常

#### 问题分析工具
```python
# api-debug.py
import requests
import json
from datetime import datetime

def debug_api_call(url, headers=None, data=None):
    print(f"=== API调用调试 ===")
    print(f"时间: {datetime.now()}")
    print(f"URL: {url}")
    print(f"Headers: {json.dumps(headers, indent=2)}")
    print(f"数据: {json.dumps(data, indent=2)}")
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        print(f"状态码: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")
        print(f"响应内容: {response.text[:500]}...")
        
        if response.status_code == 200:
            print("✅ API调用成功")
        else:
            print("❌ API调用失败")
            
    except requests.exceptions.Timeout:
        print("❌ 请求超时")
    except requests.exceptions.ConnectionError:
        print("❌ 连接错误")
    except Exception as e:
        print(f"❌ 其他错误: {e}")

# 使用示例
API_KEY = "your_api_key_here"
url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}
data = {
    "model": "qwen-turbo",
    "input": {
        "messages": [
            {"role": "user", "content": "测试消息"}
        ]
    }
}

debug_api_call(url, headers, data)
```

#### 常见API问题

**API密钥无效**
```python
# 检查API密钥
def check_api_key(api_key):
    if not api_key:
        print("❌ API密钥未设置")
        return False
    
    if len(api_key) < 20:
        print("❌ API密钥格式不正确")
        return False
    
    print("✅ API密钥格式正确")
    return True

# 验证API密钥
def validate_api_key(api_key):
    import requests
    
    url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
    headers = {"Authorization": f"Bearer {api_key}"}
    data = {
        "model": "qwen-turbo",
        "input": {"messages": [{"role": "user", "content": "test"}]}
    }
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=10)
        if response.status_code == 200:
            print("✅ API密钥有效")
            return True
        else:
            print(f"❌ API密钥无效: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ API密钥验证失败: {e}")
        return False
```

**网络代理问题**
```python
# 代理配置检查
def check_proxy_config():
    import os
    
    proxy_vars = ["HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy"]
    
    for var in proxy_vars:
        value = os.environ.get(var)
        if value:
            print(f"🔧 {var}: {value}")
        else:
            print(f"✅ {var}: 未设置")
    
    # 测试代理连接
    import requests
    proxies = {
        "http": os.environ.get("HTTP_PROXY"),
        "https": os.environ.get("HTTPS_PROXY")
    }
    
    try:
        response = requests.get("http://httpbin.org/ip", proxies=proxies, timeout=5)
        print(f"代理测试成功: {response.json()}")
    except Exception as e:
        print(f"代理测试失败: {e}")

check_proxy_config()
```

### 2. 响应超时问题

#### 超时配置优化
```python
# timeout-config.py
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

def create_optimized_session():
    """创建优化的requests会话"""
    session = requests.Session()
    
    # 重试策略
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
    )
    
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    # 超时配置
    session.timeout = (10, 30)  # (连接超时, 读取超时)
    
    return session

# 使用优化的会话
session = create_optimized_session()
response = session.post(url, json=data, headers=headers)
```

## 数据库问题

### 1. 数据库连接问题

#### 数据库状态检查
```python
# db-check.py
import sqlite3
import os
from datetime import datetime

def check_database():
    db_path = "/opt/hospital-scanner/data/hospitals.db"
    
    print("=== 数据库状态检查 ===")
    
    # 检查文件存在性
    if not os.path.exists(db_path):
        print("❌ 数据库文件不存在")
        return False
    
    # 检查文件大小
    size = os.path.getsize(db_path)
    print(f"📊 数据库大小: {size / 1024 / 1024:.2f} MB")
    
    # 检查表结构
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 获取表列表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"📋 表数量: {len(tables)}")
        
        for table in tables:
            table_name = table[0]
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            print(f"  - {table_name}: {count} 条记录")
        
        conn.close()
        print("✅ 数据库连接正常")
        return True
        
    except Exception as e:
        print(f"❌ 数据库连接失败: {e}")
        return False

# 检查数据库
check_database()
```

#### 数据库修复
```python
# db-repair.py
import sqlite3
import shutil
from datetime import datetime

def repair_database():
    """数据库修复工具"""
    db_path = "/opt/hospital-scanner/data/hospitals.db"
    backup_path = f"/opt/hospital-scanner/backups/hospitals_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    
    print("=== 数据库修复工具 ===")
    
    # 创建备份
    if os.path.exists(db_path):
        shutil.copy2(db_path, backup_path)
        print(f"✅ 备份创建: {backup_path}")
    
    try:
        # 修复数据库
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查并修复表
        cursor.execute("PRAGMA integrity_check")
        result = cursor.fetchone()
        
        if result[0] == "ok":
            print("✅ 数据库完整性检查通过")
        else:
            print("⚠️ 数据库完整性问题，尝试修复...")
            
            # 重建索引
            cursor.execute("REINDEX")
            
            # 优化数据库
            cursor.execute("VACUUM")
            
            print("✅ 数据库修复完成")
        
        # 更新统计信息
        cursor.execute("ANALYZE")
        print("✅ 统计信息更新完成")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 数据库修复失败: {e}")
        return False
    
    return True

# 执行修复
repair_database()
```

### 2. 数据库性能问题

#### 慢查询分析
```sql
-- 启用查询分析
PRAGMA analysis_limit=400;

-- 分析表优化建议
PRAGMA optimize;

-- 检查索引使用情况
SELECT 
    name,
    sql
FROM sqlite_master 
WHERE type = 'index' 
AND tbl_name = 'hospitals';

-- 重建索引
REINDEX;
```

## Docker相关问题

### 1. 容器问题

#### 容器调试脚本
```bash
#!/bin/bash
# docker-debug.sh

echo "=== Docker容器调试 ==="

# 列出所有容器
echo "🐳 所有容器:"
docker ps -a --format "table {{.ID}}\t{{.Image}}\t{{.Status}}\t{{.Names}}"

echo ""
echo "🔍 医院扫描容器详情:"
CONTAINER=$(docker ps --filter "name=hospital-scanner" --format "{{.ID}}" | head -1)

if [ -n "$CONTAINER" ]; then
    echo "容器ID: $CONTAINER"
    
    # 容器资源使用
    echo "资源使用:"
    docker stats $CONTAINER --no-stream
    
    # 容器日志
    echo ""
    echo "最近日志 (50行):"
    docker logs --tail=50 $CONTAINER
    
    # 容器进程
    echo ""
    echo "运行进程:"
    docker exec $CONTAINER ps aux
    
    # 容器网络
    echo ""
    echo "网络配置:"
    docker exec $CONTAINER netstat -tulpn
    
else
    echo "❌ 未找到医院扫描容器"
fi

echo ""
echo "🔧 Docker系统信息:"
echo "Docker版本: $(docker --version)"
echo "Docker Compose版本: $(docker-compose --version)"
echo "Docker存储驱动: $(docker info | grep 'Storage Driver' | awk '{print $3}')"
echo "镜像数量: $(docker images | wc -l)"
echo "容器数量: $(docker ps -a | wc -l)"
```

### 2. 网络问题

#### Docker网络诊断
```bash
# docker-network-debug.sh

echo "=== Docker网络诊断 ==="

# 列出网络
echo "🌐 Docker网络:"
docker network ls

echo ""
echo "🔍 医院扫描网络详情:"
NETWORK="hospital-scanner-network"

if docker network inspect $NETWORK > /dev/null 2>&1; then
    echo "网络存在"
    docker network inspect $NETWORK | grep -A 10 "Containers"
else
    echo "网络不存在"
fi

echo ""
echo "🔌 端口映射检查:"
docker ps --filter "name=hospital-scanner" --format "table {{.Names}}\t{{.Ports}}"

echo ""
echo "🌍 DNS解析测试:"
docker exec hospital-scanner cat /etc/resolv.conf
docker exec hospital-scanner nslookup dashscope.aliyuncs.com
```

## 网络和性能问题

### 1. 性能问题诊断

#### 性能瓶颈分析
```bash
# performance-analysis.sh

echo "=== 性能瓶颈分析 ==="

# CPU分析
echo "🖥️ CPU分析:"
echo "CPU核心数: $(nproc)"
echo "CPU使用率:"
top -bn1 | grep "Cpu(s)" | awk '{print $2 " " $3 " " $4 " " $5}' | while read line; do
    echo "  $line"
done

# 内存分析
echo ""
echo "💾 内存分析:"
free -h

# I/O分析
echo ""
echo "💿 磁盘I/O分析:"
iostat -x 1 1 2>/dev/null || echo "iostat未安装，跳过I/O分析"

# 网络分析
echo ""
echo "🌐 网络分析:"
ss -tuln | grep :8000

# 进程分析
echo ""
echo "🔍 医院扫描相关进程:"
ps aux | grep -E "(hospital-scanner|uvicorn|main.py)" | grep -v grep

# 文件描述符分析
echo ""
echo "📁 文件描述符分析:"
echo "当前打开文件数: $(lsof | wc -l)"
echo "进程文件描述符限制: $(ulimit -n)"
```

### 2. 网络延迟问题

#### 网络延迟测试
```python
# latency-test.py
import time
import requests
import statistics
from concurrent.futures import ThreadPoolExecutor

def test_api_latency(url, api_key, num_requests=10):
    """API延迟测试"""
    headers = {"Authorization": f"Bearer {api_key}"}
    data = {
        "model": "qwen-turbo",
        "input": {"messages": [{"role": "user", "content": "test"}]}
    }
    
    latencies = []
    errors = 0
    
    print(f"=== API延迟测试 ===")
    print(f"测试URL: {url}")
    print(f"测试次数: {num_requests}")
    
    def single_request():
        try:
            start_time = time.time()
            response = requests.post(url, headers=headers, json=data, timeout=30)
            end_time = time.time()
            
            latency = (end_time - start_time) * 1000  # 毫秒
            return latency if response.status_code == 200 else None
        except Exception as e:
            return None
    
    # 并发测试
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(single_request) for _ in range(num_requests)]
        
        for future in futures:
            result = future.result()
            if result is not None:
                latencies.append(result)
            else:
                errors += 1
    
    if latencies:
        print(f"✅ 成功请求: {len(latencies)}")
        print(f"❌ 失败请求: {errors}")
        print(f"平均延迟: {statistics.mean(latencies):.2f}ms")
        print(f"中位延迟: {statistics.median(latencies):.2f}ms")
        print(f"最小延迟: {min(latencies):.2f}ms")
        print(f"最大延迟: {max(latencies):.2f}ms")
        print(f"95%延迟: {sorted(latencies)[int(len(latencies) * 0.95)]:.2f}ms")
    else:
        print("❌ 所有请求都失败了")

# 使用示例
API_KEY = "your_api_key_here"
API_URL = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
test_api_latency(API_URL, API_KEY, 20)
```

## 日志分析

### 1. 日志模式识别

#### 错误日志分析
```bash
#!/bin/bash
# log-analyzer.sh

LOG_FILE="$1"
if [ -z "$LOG_FILE" ]; then
    echo "用法: $0 <日志文件路径>"
    exit 1
fi

echo "=== 日志分析报告 ==="
echo "分析文件: $LOG_FILE"
echo "分析时间: $(date)"
echo ""

# 统计错误类型
echo "🔍 错误类型统计:"
grep -i "error\|exception\|failed\|timeout" "$LOG_FILE" | \
awk '{print $4}' | sort | uniq -c | sort -nr | head -10

echo ""
echo "📊 时间分布 (最近24小时):"
# 提取最近24小时的错误
cut -d' ' -f1,2 "$LOG_FILE" | \
while read line; do
    date_str=$(echo "$line" | cut -d' ' -f1)
    hour=$(echo "$line" | cut -d' ' -f2 | cut -d':' -f1)
    echo "$date_str $hour:00" 
done | sort | uniq -c | tail -24

echo ""
echo "🚨 频繁错误 (出现5次以上):"
grep -i "error\|exception" "$LOG_FILE" | \
awk -F'ERROR|Exception|error|exception' '{print $2}' | \
awk '{print $1}' | sort | uniq -c | sort -nr | \
awk '$1 >= 5 {print "  " $2 ": " $1 " 次"}'

echo ""
echo "📈 性能相关日志:"
grep -i "response_time\|slow\|timeout" "$LOG_FILE" | \
tail -20
```

### 2. 实时日志监控

#### 智能日志监控
```bash
#!/bin/bash
# smart-monitor.sh

LOG_FILE="/var/log/hospital-scanner/app.log"
ALERT_THRESHOLD=10
ERROR_WINDOW=60  # 60秒窗口

echo "智能日志监控启动中..."
echo "监控文件: $LOG_FILE"
echo "错误阈值: $ALERT_THRESHOLD 次/分钟"
echo ""

# 错误计数器
error_count=0
last_check_time=$(date +%s)

# 监控循环
tail -F "$LOG_FILE" | while read -r line; do
    current_time=$(date +%s)
    
    # 检测错误
    if echo "$line" | grep -qi "error\|exception\|failed"; then
        error_count=$((error_count + 1))
        
        # 检查是否超过阈值
        time_diff=$((current_time - last_check_time))
        if [ $time_diff -ge $ERROR_WINDOW ] || [ $error_count -ge $ALERT_THRESHOLD ]; then
            if [ $error_count -ge $ALERT_THRESHOLD ]; then
                echo "🚨 告警: $ALERT_THRESHOLD 秒内发现 $error_count 个错误"
                echo "最新错误: $line"
                
                # 发送告警（可扩展为邮件、短信等）
                logger -t hospital-scanner-alert "High error rate: $error_count errors in ${ERROR_WINDOW}s"
            fi
            
            # 重置计数器
            error_count=0
            last_check_time=$current_time
        fi
    fi
    
    # 显示实时日志
    timestamp=$(date '+%H:%M:%S')
    echo "[$timestamp] $line"
    
    # 特殊标记
    if echo "$line" | grep -qi "critical\|fatal"; then
        echo "💥 严重错误检测到！"
    elif echo "$line" | grep -qi "warning"; then
        echo "⚠️  警告检测到"
    elif echo "$line" | grep -qi "slow"; then
        echo "🐌 性能问题检测到"
    fi
done
```

## 应急响应

### 1. 服务恢复流程

#### 自动恢复脚本
```bash
#!/bin/bash
# auto-recovery.sh

MAX_RETRIES=3
RETRY_DELAY=30
SERVICE_NAME="hospital-scanner"

echo "=== 服务自动恢复流程 ==="

# 检查服务状态
check_service() {
    if systemctl is-active --quiet $SERVICE_NAME; then
        return 0
    else
        return 1
    fi
}

# 尝试重启服务
restart_service() {
    echo "尝试重启 $SERVICE_NAME 服务..."
    systemctl restart $SERVICE_NAME
    sleep 10
}

# 健康检查
health_check() {
    if curl -f -s http://localhost:8000/health > /dev/null; then
        return 0
    else
        return 1
    fi
}

# 主恢复流程
recovery_count=0

while [ $recovery_count -lt $MAX_RETRIES ]; do
    echo "恢复尝试 $((recovery_count + 1))/$MAX_RETRIES"
    
    if check_service; then
        echo "✅ 服务运行正常"
        break
    else
        echo "❌ 服务未运行，尝试重启..."
        restart_service
        
        if health_check; then
            echo "✅ 服务恢复成功"
            break
        else
            echo "❌ 服务恢复失败"
            recovery_count=$((recovery_count + 1))
            
            if [ $recovery_count -lt $MAX_RETRIES ]; then
                echo "等待 $RETRY_DELAY 秒后重试..."
                sleep $RETRY_DELAY
            fi
        fi
    fi
done

if [ $recovery_count -eq $MAX_RETRIES ]; then
    echo "💥 自动恢复失败，需要手动干预"
    
    # 发送紧急告警
    echo "医院扫描系统恢复失败，需要立即关注！" | \
    mail -s "[紧急] $SERVICE_NAME 服务恢复失败" admin@example.com
    
    # 记录日志
    logger -t hospital-scanner-recovery "Auto recovery failed after $MAX_RETRIES attempts"
else
    echo "🎉 服务恢复成功"
    logger -t hospital-scanner-recovery "Service recovered successfully"
fi
```

### 2. 数据恢复流程

#### 数据恢复脚本
```bash
#!/bin/bash
# data-recovery.sh

BACKUP_DIR="/opt/hospital-scanner/backups"
DB_PATH="/opt/hospital-scanner/data/hospitals.db"
RECOVERY_LOG="/var/log/hospital-scanner/recovery.log"

echo "=== 数据恢复流程 ===" | tee -a $RECOVERY_LOG

# 检查备份文件
check_backups() {
    echo "检查可用备份..." | tee -a $RECOVERY_LOG
    find $BACKUP_DIR -name "*.db" -o -name "*.tar.gz" | sort -r | head -5
}

# 恢复SQLite数据库
restore_sqlite() {
    local backup_file="$1"
    
    echo "恢复SQLite数据库: $backup_file" | tee -a $RECOVERY_LOG
    
    # 备份当前数据库
    if [ -f "$DB_PATH" ]; then
        cp "$DB_PATH" "${DB_PATH}.corrupted.$(date +%s)"
        echo "当前数据库已备份" | tee -a $RECOVERY_LOG
    fi
    
    # 恢复数据库
    cp "$backup_file" "$DB_PATH"
    
    # 验证数据库
    if sqlite3 "$DB_PATH" "PRAGMA integrity_check;" | grep -q "ok"; then
        echo "✅ 数据库恢复成功" | tee -a $RECOVERY_LOG
        return 0
    else
        echo "❌ 数据库恢复失败" | tee -a $RECOVERY_LOG
        return 1
    fi
}

# 主恢复流程
if [ -z "$1" ]; then
    echo "可用备份文件:"
    check_backups
    echo ""
    echo "用法: $0 <备份文件路径>"
    exit 1
fi

backup_file="$1"
if [ -f "$backup_file" ]; then
    if restore_sqlite "$backup_file"; then
        # 重启服务
        echo "重启服务..." | tee -a $RECOVERY_LOG
        systemctl restart hospital-scanner
        
        # 验证服务
        sleep 10
        if curl -f -s http://localhost:8000/health > /dev/null; then
            echo "🎉 数据恢复完成，服务正常运行" | tee -a $RECOVERY_LOG
        else
            echo "⚠️ 数据恢复完成，但服务未正常运行" | tee -a $RECOVERY_LOG
        fi
    else
        echo "💥 数据恢复失败" | tee -a $RECOVERY_LOG
        exit 1
    fi
else
    echo "❌ 备份文件不存在: $backup_file" | tee -a $RECOVERY_LOG
    exit 1
fi
```

---

## 应急联系信息

在紧急情况下，请联系：

1. **系统管理员**: admin@example.com
2. **技术支持**: support@example.com
3. **开发团队**: dev@example.com

## 预防措施

为避免常见问题，建议：

1. **定期备份**: 每日自动备份数据和配置
2. **监控系统**: 部署全面的监控和告警
3. **文档更新**: 保持部署文档的及时更新
4. **测试演练**: 定期进行故障恢复演练
5. **资源预留**: 保持足够的系统资源冗余

记住：**预防胜于治疗**！
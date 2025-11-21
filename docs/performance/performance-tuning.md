# 性能调优指南

## 目录
1. [系统级优化](#系统级优化)
2. [应用级优化](#应用级优化)
3. [数据库优化](#数据库优化)
4. [Docker优化](#docker优化)
5. [网络优化](#网络优化)
6. [缓存策略](#缓存策略)
7. [监控和调优](#监控和调优)

## 系统级优化

### 1. 内核参数优化

#### 网络参数
```bash
# /etc/sysctl.conf
# TCP连接优化
net.core.somaxconn = 65535
net.core.netdev_max_backlog = 5000
net.ipv4.tcp_max_syn_backlog = 65535
net.ipv4.tcp_fin_timeout = 30
net.ipv4.tcp_keepalive_time = 1800
net.ipv4.tcp_keepalive_probes = 3
net.ipv4.tcp_keepalive_intvl = 15

# 内存优化
vm.swappiness = 10
vm.dirty_ratio = 15
vm.dirty_background_ratio = 5

# 文件描述符
fs.file-max = 1000000

# 应用配置
sysctl -p
```

#### 资源限制
```bash
# /etc/security/limits.conf
hospital_scanner soft nofile 65536
hospital_scanner hard nofile 65536
hospital_scanner soft nproc 32768
hospital_scanner hard nproc 32768
```

### 2. 文件系统优化

#### ext4/XFS优化
```bash
# 挂载选项优化 /etc/fstab
/dev/sda1 / ext4 defaults,noatime,nodiratime,commit=60 0 1

# 或对于XFS
/dev/sda1 / xfs defaults,noatime,nodiratime 0 1

# 重新挂载
mount -o remount /
```

### 3. 进程和线程优化

#### Uvicorn优化配置
```python
# 生产环境启动参数
uvicorn main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --max-requests 1000 \
    --max-requests-jitter 100 \
    --timeout-keep-alive 30 \
    --access-log \
    --log-level info
```

#### 环境变量优化
```bash
# .env.prod
WORKERS=4
MAX_REQUESTS=1000
MAX_REQUESTS_JITTER=100
TIMEOUT_KEEP_ALIVE=30
```

## 应用级优化

### 1. FastAPI优化

#### 连接池配置
```python
# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import asyncio

app = FastAPI(
    title="医院层级扫查系统",
    description="高效的医院信息扫描和分析系统",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局配置
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response
```

#### 异步优化
```python
# tasks.py - 异步任务处理
import asyncio
import aiohttp
from concurrent.futures import ThreadPoolExecutor

class AsyncProcessor:
    def __init__(self, max_workers=10):
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        
    async def process_hospitals(self, hospitals_data):
        """批量处理医院数据"""
        semaphore = asyncio.Semaphore(self.max_workers)
        
        async def process_single(hospital):
            async with semaphore:
                return await self.process_hospital_async(hospital)
        
        tasks = [process_single(h) for h in hospitals_data]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        return [r for r in results if not isinstance(r, Exception)]
    
    async def process_hospital_async(self, hospital):
        """异步处理单个医院"""
        # 使用aiohttp进行HTTP请求
        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.api_url,
                json=hospital,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                return await response.json()
```

#### 内存优化
```python
# 内存使用优化
import gc
import psutil
from typing import Generator

def monitor_memory():
    """内存监控装饰器"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            process = psutil.Process()
            memory_before = process.memory_info().rss / 1024 / 1024  # MB
            
            result = await func(*args, **kwargs)
            
            memory_after = process.memory_info().rss / 1024 / 1024  # MB
            memory_diff = memory_after - memory_before
            
            print(f"Memory used: {memory_diff:.2f} MB")
            
            # 内存使用过高时触发垃圾回收
            if memory_diff > 100:  # 100MB
                gc.collect()
                
            return result
        return wrapper
    return decorator

# 使用装饰器
@monitor_memory()
async def heavy_computation():
    # 大量数据处理
    pass
```

### 2. API优化

#### 响应压缩
```python
# middleware/compression.py
from fastapi import FastAPI, Request, Response
from fastapi.middleware.gzip import GZipMiddleware

# 在main.py中添加
app.add_middleware(GZipMiddleware, minimum_size=1000)
```

#### 分页优化
```python
# utils/pagination.py
from typing import Optional, List, Dict, Any
import math

class PaginationParams:
    def __init__(
        self,
        page: int = 1,
        size: int = 20,
        max_size: int = 100
    ):
        self.page = max(1, page)
        self.size = min(max_size, max(1, size))
        self.offset = (self.page - 1) * self.size

def paginate_response(
    data: List[Any],
    total: int,
    page: int,
    size: int
) -> Dict[str, Any]:
    """标准化分页响应"""
    total_pages = math.ceil(total / size)
    
    return {
        "items": data,
        "total": total,
        "page": page,
        "size": size,
        "pages": total_pages,
        "has_next": page < total_pages,
        "has_prev": page > 1
    }
```

## 数据库优化

### 1. SQLite优化

#### 索引优化
```sql
-- 为医院数据表创建索引
CREATE INDEX idx_hospitals_name ON hospitals(name);
CREATE INDEX idx_hospitals_city ON hospitals(city);
CREATE INDEX idx_hospitals_level ON hospitals(level);
CREATE INDEX idx_hospitals_created ON hospitals(created_at);

-- 复合索引
CREATE INDEX idx_hospitals_city_level ON hospitals(city, level);

-- 查询优化
EXPLAIN QUERY PLAN SELECT * FROM hospitals WHERE city = '北京市' AND level = '三甲';
```

#### SQLite配置优化
```python
# db.py - SQLite优化配置
import sqlite3
from contextlib import contextmanager

class OptimizedDatabase:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.configure_connection()
    
    def configure_connection(self):
        """配置数据库连接参数"""
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA journal_mode=WAL")  # Write-Ahead Logging
        conn.execute("PRAGMA synchronous=NORMAL")  # 平衡性能和安全
        conn.execute("PRAGMA cache_size=10000")  # 10MB缓存
        conn.execute("PRAGMA temp_store=MEMORY")  # 临时表存储在内存
        conn.execute("PRAGMA mmap_size=268435456")  # 256MB内存映射
        conn.close()
    
    @contextmanager
    def get_connection(self):
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
```

### 2. 连接池优化
```python
# connection_pool.py
import sqlite3
import queue
import threading
from contextlib import contextmanager

class SQLitePool:
    def __init__(self, db_path: str, pool_size: int = 10):
        self.db_path = db_path
        self.pool_size = pool_size
        self._pool = queue.Queue(maxsize=pool_size)
        self._lock = threading.Lock()
        
        # 预填充连接池
        for _ in range(pool_size):
            conn = self._create_connection()
            self._pool.put(conn)
    
    def _create_connection(self):
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA cache_size=10000")
        return conn
    
    @contextmanager
    def get_connection(self):
        conn = self._pool.get(timeout=10)
        try:
            yield conn
        finally:
            self._pool.put(conn)
```

## Docker优化

### 1. Dockerfile优化

#### 多阶段构建
```dockerfile
# 分阶段构建
FROM python:3.11-slim as builder

# 安装构建依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装依赖到wheel包
RUN pip install --user --no-cache-dir --target=/tmp/pip-packages -r requirements.txt && \
    pip freeze --user > /tmp/requirements.txt

# 生产镜像
FROM python:3.11-slim as production

# 安装运行时依赖
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖包
COPY --from=builder /tmp/pip-packages /usr/local/lib/python3.11/site-packages/
COPY --from=builder /tmp/requirements.txt /tmp/requirements.txt

# 复制应用代码
COPY . .

# 创建非root用户
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser
```

#### 构建优化
```bash
# .dockerignore - 减少构建上下文
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
*.so
.pytest_cache/
.coverage
.tox/
build/
dist/
*.egg-info/
.git/
.gitignore
README.md
Dockerfile*
.dockerignore
```

### 2. Docker Compose优化

#### 资源限制
```yaml
# docker-compose.prod.yml
services:
  hospital-scanner:
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '1.0'
        reservations:
          memory: 512M
          cpus: '0.5'
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 3
        window: 120s
    
    # 健康检查优化
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    
    # 网络优化
    networks:
      - backend
      - frontend

networks:
  backend:
    driver: bridge
    driver_opts:
      com.docker.network.bridge.name: br-backend
  frontend:
    driver: bridge
    driver_opts:
      com.docker.network.bridge.name: br-frontend
```

## 网络优化

### 1. Nginx优化

#### 缓存配置
```nginx
# nginx缓存配置
http {
    # 开启gzip压缩
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types
        text/plain
        text/css
        text/xml
        text/javascript
        application/json
        application/javascript
        application/xml+rss;
    
    # 静态文件缓存
    location ~* \.(jpg|jpeg|png|gif|ico|css|js)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # API缓存
    location ~* ^/api/hospitals {
        proxy_cache hospital_cache;
        proxy_cache_valid 200 302 5m;
        proxy_cache_valid 404 1m;
        proxy_cache_use_stale error timeout updating http_500 http_502 http_503 http_504;
        proxy_cache_lock on;
        add_header X-Cache-Status $upstream_cache_status;
    }
}
```

#### 连接优化
```nginx
# 连接和缓冲区优化
http {
    # 缓冲区大小
    client_body_buffer_size 128k;
    client_max_body_size 10m;
    client_header_buffer_size 1k;
    large_client_header_buffers 4 4k;
    output_buffers 1 32k;
    postpone_output 1460;
    
    # 超时设置
    client_body_timeout 12;
    client_header_timeout 12;
    keepalive_timeout 15;
    send_timeout 10;
    
    # 代理缓冲区
    proxy_buffering on;
    proxy_buffer_size 4k;
    proxy_buffers 8 4k;
    proxy_busy_buffers_size 8k;
}
```

### 2. 连接池配置
```python
# connection_pool.py
import asyncio
import aiohttp

class HTTPConnectionPool:
    def __init__(self, max_connections=100, max_keepalive_connections=20):
        self.connector = aiohttp.TCPConnector(
            limit=max_connections,
            limit_per_host=max_keepalive_connections,
            ttl_dns_cache=300,
            use_dns_cache=True,
            keepalive_timeout=30,
            enable_cleanup_closed=True,
        )
        
    async def make_request(self, url, **kwargs):
        timeout = aiohttp.ClientTimeout(total=30)
        async with aiohttp.ClientSession(
            connector=self.connector,
            timeout=timeout
        ) as session:
            async with session.get(url, **kwargs) as response:
                return await response.json()
```

## 缓存策略

### 1. 内存缓存

#### LRU缓存
```python
# cache.py
from functools import lru_cache
from typing import Any, Dict
import time
import threading

class TTLCache:
    def __init__(self, maxsize=128, ttl=300):
        self.maxsize = maxsize
        self.ttl = ttl
        self._cache = {}
        self._timestamps = {}
        self._lock = threading.Lock()
    
    def get(self, key: str) -> Any:
        with self._lock:
            if key not in self._cache:
                return None
            
            timestamp = self._timestamps[key]
            if time.time() - timestamp > self.ttl:
                del self._cache[key]
                del self._timestamps[key]
                return None
            
            return self._cache[key]
    
    def set(self, key: str, value: Any):
        with self._lock:
            self._cache[key] = value
            self._timestamps[key] = time.time()
            
            # 清理过期条目
            self._cleanup()
    
    def _cleanup(self):
        current_time = time.time()
        expired_keys = [
            k for k, v in self._timestamps.items()
            if current_time - v > self.ttl
        ]
        
        for key in expired_keys:
            self._cache.pop(key, None)
            self._timestamps.pop(key, None)

# 使用缓存
cache = TTLCache(maxsize=1000, ttl=300)

@cache.get
def get_hospital_info(hospital_id: str):
    # 从数据库或API获取医院信息
    pass
```

### 2. Redis缓存

#### Redis连接优化
```python
# redis_cache.py
import redis
import json
from typing import Any, Optional

class OptimizedRedisCache:
    def __init__(self, host='localhost', port=6379, db=0):
        self.redis_client = redis.Redis(
            host=host,
            port=port,
            db=db,
            decode_responses=True,
            socket_keepalive=True,
            socket_keepalive_options={},
            retry_on_timeout=True,
            health_check_interval=30,
            max_connections=20
        )
    
    def get(self, key: str) -> Optional[Any]:
        try:
            value = self.redis_client.get(key)
            return json.loads(value) if value else None
        except Exception as e:
            print(f"Redis get error: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: int = 300):
        try:
            serialized = json.dumps(value, ensure_ascii=False)
            self.redis_client.setex(key, ttl, serialized)
        except Exception as e:
            print(f"Redis set error: {e}")
    
    def get_or_set(self, key: str, fetch_func, ttl: int = 300):
        """缓存模式：先查缓存，缓存未命中时调用fetch_func获取数据"""
        cached = self.get(key)
        if cached is not None:
            return cached
        
        data = fetch_func()
        if data:
            self.set(key, data, ttl)
        
        return data
```

## 监控和调优

### 1. 性能监控

#### 性能指标收集
```python
# performance_monitor.py
import time
import psutil
import threading
from collections import deque
from typing import Dict, List

class PerformanceMonitor:
    def __init__(self, window_size=100):
        self.window_size = window_size
        self.response_times = deque(maxlen=window_size)
        self.memory_usage = deque(maxlen=window_size)
        self.cpu_usage = deque(maxlen=window_size)
        self.request_counts = deque(maxlen=window_size)
        self._lock = threading.Lock()
    
    def record_request(self, response_time: float):
        with self._lock:
            self.response_times.append(response_time)
            self.request_counts.append(time.time())
            
            # 记录系统资源
            self.memory_usage.append(psutil.virtual_memory().percent)
            self.cpu_usage.append(psutil.cpu_percent())
    
    def get_metrics(self) -> Dict:
        with self._lock:
            if not self.response_times:
                return {}
            
            response_times = list(self.response_times)
            memory_usage = list(self.memory_usage)
            cpu_usage = list(self.cpu_usage)
            
            return {
                "avg_response_time": sum(response_times) / len(response_times),
                "max_response_time": max(response_times),
                "min_response_time": min(response_times),
                "p95_response_time": sorted(response_times)[int(len(response_times) * 0.95)],
                "avg_memory_usage": sum(memory_usage) / len(memory_usage) if memory_usage else 0,
                "avg_cpu_usage": sum(cpu_usage) / len(cpu_usage) if cpu_usage else 0,
                "request_rate": len(self.request_counts),  # requests per window
            }

# 全局监控实例
monitor = PerformanceMonitor()

# 性能监控装饰器
def performance_monitor(func):
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            return result
        finally:
            response_time = time.time() - start_time
            monitor.record_request(response_time)
    return wrapper
```

### 2. 自动调优

#### 动态worker调整
```python
# auto_scaler.py
import asyncio
import psutil
from typing import Optional

class AutoScaler:
    def __init__(self, min_workers=1, max_workers=8):
        self.min_workers = min_workers
        self.max_workers = max_workers
        self.current_workers = min_workers
        self.scaling_threshold = 0.8  # CPU使用率阈值
        self.cooldown_period = 300    # 5分钟冷却期
        self.last_scale_time = 0
    
    async def auto_scale(self):
        while True:
            cpu_usage = psutil.cpu_percent()
            memory_usage = psutil.virtual_memory().percent
            
            current_time = time.time()
            
            # 检查是否可以进行扩缩容
            if current_time - self.last_scale_time < self.cooldown_period:
                await asyncio.sleep(60)
                continue
            
            # 扩容条件
            if cpu_usage > self.scaling_threshold * 100 or memory_usage > 80:
                if self.current_workers < self.max_workers:
                    self.current_workers += 1
                    self.last_scale_time = current_time
                    print(f"扩容: worker数量增加到 {self.current_workers}")
            
            # 缩容条件
            elif cpu_usage < 50 and memory_usage < 60:
                if self.current_workers > self.min_workers:
                    self.current_workers -= 1
                    self.last_scale_time = current_time
                    print(f"缩容: worker数量减少到 {self.current_workers}")
            
            await asyncio.sleep(60)  # 每分钟检查一次
```

---

## 性能调优检查清单

### 系统级
- [ ] 调整内核参数
- [ ] 优化文件系统挂载选项
- [ ] 配置资源限制
- [ ] 启用CPU和I/O调度优化

### 应用级
- [ ] 配置合适的worker数量
- [ ] 启用异步处理
- [ ] 实施缓存策略
- [ ] 优化数据库查询和索引
- [ ] 启用响应压缩

### Docker级
- [ ] 使用多阶段构建
- [ ] 配置资源限制
- [ ] 优化镜像层缓存
- [ ] 配置健康检查

### 网络级
- [ ] 配置Nginx缓存
- [ ] 启用gzip压缩
- [ ] 优化连接池配置
- [ ] 配置keepalive

### 监控级
- [ ] 实施性能监控
- [ ] 设置告警阈值
- [ ] 配置自动扩缩容
- [ ] 定期性能评估

建议的性能基准：
- 响应时间: < 500ms (P95)
- 吞吐量: > 1000 req/s
- 内存使用: < 1GB
- CPU使用: < 70%
- 错误率: < 0.1%
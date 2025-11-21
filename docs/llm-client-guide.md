# LLM客户端使用说明

## 概述

LLM客户端是基于阿里百炼DashScope API开发的智能数据获取模块，负责从LLM服务获取省市区医院层级数据。本文档详细介绍LLM客户端的使用方法、配置选项、API接口和最佳实践。

## 功能特性

### 🎯 核心功能
- **智能数据获取**: 基于LLM的省市区医院数据自动获取
- **结构化响应**: JSON格式的结构化数据输出
- **多层级支持**: 支持省、市、区县、医院四级数据获取
- **置信度评估**: 提供LLM返回结果的置信度评分
- **错误处理**: 完善的异常处理和重试机制

### 🔧 技术特性
- **异步调用**: 全异步API调用，不阻塞主线程
- **并发控制**: 可配置的并发请求限制
- **代理支持**: 支持HTTP/HTTPS代理配置
- **日志记录**: 详细的调用日志和错误跟踪
- **配置灵活**: 丰富的配置选项和自定义参数

## 快速开始

### 1. 基本使用

```python
import asyncio
from llm_client import LLMClient

async def main():
    # 创建LLM客户端
    client = LLMClient()
    
    # 获取省份数据
    provinces = await client.get_provinces()
    print(f"获取到 {len(provinces['items'])} 个省份")
    
    # 获取城市数据
    cities = await client.get_cities("广东省")
    print(f"广东省有 {len(cities['items'])} 个城市")

asyncio.run(main())
```

### 2. 配置初始化

```python
from llm_client import LLMClient

# 方式1: 使用环境变量
import os
os.environ['DASHSCOPE_API_KEY'] = 'your-api-key'
client = LLMClient()

# 方式2: 直接传入配置
client = LLMClient(
    api_key='your-api-key',
    model='qwen-plus',
    base_url='https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation',
    timeout=30.0,
    max_retries=2
)
```

## API接口详解

### LLMClient类

#### 初始化参数

```python
LLMClient(
    api_key: str = None,                    # 阿里百炼API密钥
    model: str = "qwen-plus",               # 使用的模型名称
    base_url: str = None,                   # API基础URL
    timeout: float = 30.0,                  # 请求超时时间（秒）
    max_retries: int = 2,                   # 最大重试次数
    retry_delay: float = 1.0,               # 重试延迟（秒）
    max_concurrent: int = 5,                # 最大并发数
    proxy_url: str = None,                  # 代理URL
    log_level: str = "INFO"                 # 日志级别
)
```

#### 配置参数详解

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| api_key | str | None | 阿里百炼API密钥，必填 |
| model | str | "qwen-plus" | 使用的模型名称 |
| base_url | str | None | API基础URL，默认使用阿里百炼标准URL |
| timeout | float | 30.0 | 请求超时时间，支持小数 |
| max_retries | int | 2 | 最大重试次数，0表示不重试 |
| retry_delay | float | 1.0 | 重试延迟时间 |
| max_concurrent | int | 5 | 最大并发请求数 |
| proxy_url | str | None | 代理URL，支持http/https |
| log_level | str | "INFO" | 日志级别（DEBUG, INFO, WARNING, ERROR） |

### 主要方法

#### 1. get_provinces()

获取全国省份信息。

```python
async def get_provinces(self) -> Dict[str, Any]:
    """
    获取全国省份列表
    
    Returns:
        Dict[str, Any]: 包含省份列表的字典
        {
            "items": [
                {
                    "name": "北京市",
                    "code": null
                },
                ...
            ]
        }
    """
```

**使用示例:**
```python
# 获取所有省份
provinces = await client.get_provinces()
print(f"共获取到 {len(provinces['items'])} 个省份")

# 遍历省份信息
for province in provinces['items']:
    print(f"省份: {province['name']}")
```

**响应格式:**
```json
{
  "items": [
    {
      "name": "北京市",
      "code": null
    },
    {
      "name": "天津市", 
      "code": null
    },
    ...
  ]
}
```

#### 2. get_cities()

根据省份名称获取城市列表。

```python
async def get_cities(self, province_name: str) -> Dict[str, Any]:
    """
    获取指定省份的城市列表
    
    Args:
        province_name (str): 省份名称
    
    Returns:
        Dict[str, Any]: 包含城市列表的字典
    """
```

**使用示例:**
```python
# 获取广东省的城市
cities = await client.get_cities("广东省")
print(f"广东省有 {len(cities['items'])} 个城市")

# 搜索特定省份的城市
target_provinces = ["广东省", "江苏省", "浙江省"]
all_cities = []

for province in target_provinces:
    try:
        cities = await client.get_cities(province)
        all_cities.extend(cities['items'])
        print(f"{province}: {len(cities['items'])} 个城市")
    except Exception as e:
        print(f"获取{province}城市失败: {e}")
```

**响应格式:**
```json
{
  "items": [
    {
      "name": "广州市",
      "code": null
    },
    {
      "name": "深圳市", 
      "code": null
    },
    ...
  ]
}
```

#### 3. get_districts()

根据城市名称获取区县列表。

```python
async def get_districts(self, city_name: str) -> Dict[str, Any]:
    """
    获取指定城市的区县列表
    
    Args:
        city_name (str): 城市名称
    
    Returns:
        Dict[str, Any]: 包含区县列表的字典
    """
```

**使用示例:**
```python
# 获取广州市的区县
districts = await client.get_districts("广州市")
print(f"广州市有 {len(districts['items'])} 个区县")

# 批量获取多个城市的区县
cities_to_query = ["广州市", "深圳市", "珠海市"]
all_districts = []

for city in cities_to_query:
    districts = await client.get_districts(city)
    all_districts.extend(districts['items'])
    print(f"{city}: {len(districts['items'])} 个区县")
```

**响应格式:**
```json
{
  "items": [
    {
      "name": "越秀区",
      "code": null
    },
    {
      "name": "荔湾区",
      "code": null
    },
    ...
  ]
}
```

#### 4. get_hospitals()

根据区县名称获取医院列表。

```python
async def get_hospitals(self, district_name: str) -> Dict[str, Any]:
    """
    获取指定区县的医院列表
    
    Args:
        district_name (str): 区县名称
    
    Returns:
        Dict[str, Any]: 包含医院列表的字典
    """
```

**使用示例:**
```python
# 获取越秀区的医院
hospitals = await client.get_hospitals("越秀区")
print(f"越秀区有 {len(hospitals['items'])} 家医院")

# 提取高质量医院（置信度>0.9）
high_quality_hospitals = [
    hospital for hospital in hospitals['items'] 
    if hospital.get('llm_confidence', 0) > 0.9
]
print(f"高置信度医院: {len(high_quality_hospitals)} 家")

# 获取医院基本信息
for hospital in hospitals['items']:
    print(f"医院: {hospital['name']}")
    print(f"网站: {hospital.get('website', 'N/A')}")
    print(f"置信度: {hospital.get('llm_confidence', 'N/A')}")
    print("---")
```

**响应格式:**
```json
{
  "items": [
    {
      "name": "中山大学附属第一医院",
      "website": "https://www.gzsums.edu.cn/",
      "llm_confidence": 0.95
    },
    {
      "name": "广东省人民医院",
      "website": "https://www.gdph.com.cn/",
      "llm_confidence": 0.92
    },
    ...
  ]
}
```

### 辅助方法

#### 5. parse_response()

解析LLM返回的JSON响应。

```python
async def parse_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
    """
    解析LLM API响应
    
    Args:
        response (Dict[str, Any]): 原始API响应
    
    Returns:
        Dict[str, Any]: 解析后的数据
    """
```

#### 6. validate_response()

验证响应数据的格式和内容。

```python
async def validate_response(self, data: Dict[str, Any], expected_type: str) -> bool:
    """
    验证响应数据格式
    
    Args:
        data (Dict[str, Any]): 要验证的数据
        expected_type (str): 期望的数据类型
    
    Returns:
        bool: 验证结果
    """
```

## 配置管理

### 1. 环境变量配置

#### 必需环境变量
```bash
# 阿里百炼API密钥（必需）
export DASHSCOPE_API_KEY="your-api-key-here"

# 可选配置
export LLM_TIMEOUT=30.0
export LLM_MAX_RETRIES=2
export LLM_MAX_CONCURRENT=5
export HTTP_PROXY="http://proxy.company.com:8080"
export HTTPS_PROXY="https://proxy.company.com:8080"
export LLM_LOG_LEVEL="INFO"
```

#### 配置文件方式
```python
# config.py
import os
from dataclasses import dataclass

@dataclass
class LLMConfig:
    api_key: str = os.getenv('DASHSCOPE_API_KEY')
    model: str = "qwen-plus"
    timeout: float = float(os.getenv('LLM_TIMEOUT', 30.0))
    max_retries: int = int(os.getenv('LLM_MAX_RETRIES', 2))
    max_concurrent: int = int(os.getenv('LLM_MAX_CONCURRENT', 5))
    proxy_url: str = os.getenv('HTTP_PROXY')
    log_level: str = os.getenv('LLM_LOG_LEVEL', 'INFO')

# 使用配置
config = LLMConfig()
client = LLMClient(**config.__dict__)
```

### 2. 代理配置

#### HTTP代理
```python
# 方法1: 环境变量
os.environ['HTTP_PROXY'] = 'http://proxy.company.com:8080'
os.environ['HTTPS_PROXY'] = 'https://proxy.company.com:8080'

# 方法2: 客户端参数
client = LLMClient(
    api_key='your-key',
    proxy_url='http://proxy.company.com:8080'
)

# 方法3: 全局代理设置
import requests
from llm_client import LLMClient

session = requests.Session()
session.proxies = {
    'http': 'http://proxy.company.com:8080',
    'https': 'https://proxy.company.com:8080'
}

client = LLMClient(session=session)
```

#### 认证代理
```python
# 带认证的代理
proxy_url = 'http://username:password@proxy.company.com:8080'
client = LLMClient(proxy_url=proxy_url)
```

### 3. 并发控制

```python
import asyncio
from llm_client import LLMClient

# 创建客户端，限制并发数为3
client = LLMClient(max_concurrent=3)

async def batch_get_cities():
    provinces = ["广东省", "江苏省", "浙江省", "山东省", "河南省"]
    
    # 使用信号量控制并发
    semaphore = asyncio.Semaphore(3)
    
    async def get_cities_with_limit(province):
        async with semaphore:
            try:
                cities = await client.get_cities(province)
                return f"{province}: {len(cities['items'])} 个城市"
            except Exception as e:
                return f"{province}: 错误 - {e}"
    
    # 并发执行
    tasks = [get_cities_with_limit(p) for p in provinces]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    for result in results:
        print(result)

# 运行批量获取
asyncio.run(batch_get_cities())
```

## 错误处理

### 1. 异常类型

#### LLMAPIError
```python
class LLMAPIError(Exception):
    """LLM API调用异常"""
    def __init__(self, message: str, status_code: int = None, response: dict = None):
        self.message = message
        self.status_code = status_code
        self.response = response
        super().__init__(self.message)

# 使用示例
try:
    provinces = await client.get_provinces()
except LLMAPIError as e:
    print(f"API调用失败: {e.message}")
    if e.status_code == 401:
        print("API密钥无效")
    elif e.status_code == 429:
        print("请求频率过高")
```

#### ResponseParsingError
```python
class ResponseParsingError(Exception):
    """响应解析异常"""
    pass

# 使用示例
try:
    hospitals = await client.get_hospitals("越秀区")
except ResponseParsingError as e:
    print(f"响应解析失败: {e}")
```

#### ValidationError
```python
class ValidationError(Exception):
    """数据验证异常"""
    pass

# 使用示例
try:
    is_valid = await client.validate_response(data, "provinces")
    if not is_valid:
        raise ValidationError("数据格式验证失败")
except ValidationError as e:
    print(f"数据验证失败: {e}")
```

### 2. 重试机制

#### 自动重试
```python
# 客户端配置重试参数
client = LLMClient(
    max_retries=3,        # 最大重试3次
    retry_delay=2.0,      # 每次重试间隔2秒
)

# 重试策略是指数退避
# 第1次重试: 延迟 2^0 = 1秒
# 第2次重试: 延迟 2^1 = 2秒  
# 第3次重试: 延迟 2^2 = 4秒
```

#### 手动重试
```python
import asyncio
from llm_client import LLMClient

async def retry_with_backoff(func, max_retries=3, base_delay=1.0):
    """带指数退避的重试装饰器"""
    
    for attempt in range(max_retries + 1):
        try:
            return await func()
        except Exception as e:
            if attempt == max_retries:
                raise e
            
            delay = base_delay * (2 ** attempt)
            print(f"第 {attempt + 1} 次尝试失败，{delay} 秒后重试: {e}")
            await asyncio.sleep(delay)

# 使用示例
client = LLMClient()

async def robust_get_provinces():
    return await retry_with_backoff(
        lambda: client.get_provinces(),
        max_retries=3
    )

provinces = await robust_get_provinces()
```

### 3. 错误恢复策略

#### 断点续传
```python
import asyncio
from llm_client import LLMClient

class DataRefreshManager:
    def __init__(self):
        self.client = LLMClient()
        self.processed_provinces = set()
        self.failed_provinces = set()
    
    async def refresh_all_provinces(self):
        """刷新所有省份数据，支持断点续传"""
        provinces = await self.client.get_provinces()
        
        for province in provinces['items']:
            province_name = province['name']
            
            if province_name in self.processed_provinces:
                print(f"跳过已处理的省份: {province_name}")
                continue
            
            try:
                print(f"处理省份: {province_name}")
                cities = await self.client.get_cities(province_name)
                
                # 处理城市数据...
                await self._process_cities(province_name, cities)
                
                self.processed_provinces.add(province_name)
                print(f"省份 {province_name} 处理完成")
                
            except Exception as e:
                print(f"处理省份 {province_name} 失败: {e}")
                self.failed_provinces.add(province_name)
                
                # 记录失败状态，支持后续重试
                await self._save_progress()
    
    async def _save_progress(self):
        """保存处理进度"""
        progress = {
            'processed': list(self.processed_provinces),
            'failed': list(self.failed_provinces)
        }
        with open('refresh_progress.json', 'w') as f:
            json.dump(progress, f)

# 使用示例
manager = DataRefreshManager()
await manager.refresh_all_provinces()
```

#### 数据校验和修复
```python
import asyncio
from llm_client import LLMClient

async def validate_and_repair_data():
    """数据校验和修复"""
    client = LLMClient()
    
    # 获取省份数据
    provinces = await client.get_provinces()
    
    for province in provinces['items']:
        province_name = province['name']
        
        # 获取省份对应的城市数量
        cities = await client.get_cities(province_name)
        city_count = len(cities['items'])
        
        # 简单的合理性检查
        if city_count < 5:  # 省份至少应该有5个城市
            print(f"警告: {province_name} 城市数量异常 ({city_count})")
            
            # 重新获取数据进行验证
            try:
                cities_retry = await client.get_cities(province_name)
                print(f"重新获取 {province_name} 城市数据: {len(cities_retry['items'])}")
            except Exception as e:
                print(f"重新获取失败: {e}")

# 运行数据校验
asyncio.run(validate_and_repair_data())
```

## 日志和监控

### 1. 日志配置

#### 基本日志配置
```python
import logging
from llm_client import LLMClient

# 配置日志级别
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('llm_client.log'),
        logging.StreamHandler()
    ]
)

# 创建客户端（会自动使用配置的日志）
client = LLMClient(log_level="DEBUG")
```

#### 详细日志记录
```python
import logging
import asyncio
from llm_client import LLMClient

# 自定义日志格式
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
)

# 文件处理器
file_handler = logging.FileHandler('llm_detailed.log', encoding='utf-8')
file_handler.setFormatter(formatter)

# 控制台处理器
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)

# 配置根日志记录器
root_logger = logging.getLogger()
root_logger.setLevel(logging.DEBUG)
root_logger.addHandler(file_handler)
root_logger.addHandler(console_handler)

# 配置LLM客户端日志器
llm_logger = logging.getLogger('llm_client')
llm_logger.setLevel(logging.DEBUG)
```

### 2. 性能监控

#### 请求统计
```python
import time
import asyncio
from llm_client import LLMClient
from collections import defaultdict

class PerformanceMonitor:
    def __init__(self):
        self.request_stats = defaultdict(list)
        self.error_stats = defaultdict(int)
    
    async def timed_request(self, method_name: str, func, *args, **kwargs):
        """带时间统计的请求"""
        start_time = time.time()
        
        try:
            result = await func(*args, **kwargs)
            
            # 记录成功请求
            duration = time.time() - start_time
            self.request_stats[method_name].append(duration)
            
            return result
            
        except Exception as e:
            # 记录错误
            self.error_stats[method_name] += 1
            raise e
    
    def get_stats(self):
        """获取性能统计"""
        stats = {}
        
        for method, durations in self.request_stats.items():
            if durations:
                stats[method] = {
                    'count': len(durations),
                    'avg_time': sum(durations) / len(durations),
                    'min_time': min(durations),
                    'max_time': max(durations),
                    'total_time': sum(durations)
                }
        
        stats['errors'] = dict(self.error_stats)
        return stats

# 使用示例
async def monitored_data_collection():
    monitor = PerformanceMonitor()
    client = LLMClient()
    
    # 监控省份获取
    provinces = await monitor.timed_request(
        'get_provinces', 
        client.get_provinces
    )
    
    # 监控城市获取
    for province in provinces['items'][:3]:  # 只获取前3个省份
        cities = await monitor.timed_request(
            'get_cities',
            client.get_cities,
            province['name']
        )
    
    # 获取统计信息
    stats = monitor.get_stats()
    print("性能统计:", stats)

# 运行监控
asyncio.run(monitored_data_collection())
```

#### 健康检查
```python
import asyncio
from llm_client import LLMClient

class LLMHealthChecker:
    def __init__(self, client: LLMClient):
        self.client = client
    
    async def health_check(self) -> dict:
        """LLM客户端健康检查"""
        health_status = {
            'status': 'healthy',
            'checks': {},
            'timestamp': time.time()
        }
        
        try:
            # 测试基本API调用
            start_time = time.time()
            provinces = await self.client.get_provinces()
            response_time = time.time() - start_time
            
            health_status['checks']['api_call'] = {
                'status': 'ok',
                'response_time': response_time,
                'data_count': len(provinces.get('items', []))
            }
            
            # 检查数据质量
            if len(provinces.get('items', [])) < 30:
                health_status['checks']['data_quality'] = {
                    'status': 'warning',
                    'message': '省份数据数量异常'
                }
            
        except Exception as e:
            health_status['status'] = 'unhealthy'
            health_status['checks']['api_call'] = {
                'status': 'error',
                'error': str(e)
            }
        
        return health_status

# 使用示例
async def check_llm_health():
    client = LLMClient()
    checker = LLMHealthChecker(client)
    
    health = await checker.health_check()
    print(f"LLM健康状态: {health}")
    
    if health['status'] != 'healthy':
        print("LLM服务异常，需要检查配置")

asyncio.run(check_llm_health())
```

## 最佳实践

### 1. 性能优化

#### 合理使用并发
```python
import asyncio
from llm_client import LLMClient

# 错误做法：过度并发
async def bad_example():
    client = LLMClient(max_concurrent=100)  # 太多并发
    
    provinces = await client.get_provinces()
    tasks = [
        client.get_cities(p['name']) 
        for p in provinces['items']  # 可能上百个任务
    ]
    
    # 这可能导致API限流或内存问题
    await asyncio.gather(*tasks)

# 正确做法：控制并发数量
async def good_example():
    client = LLMClient(max_concurrent=5)  # 合理控制
    
    provinces = await client.get_provinces()
    
    # 分批处理
    semaphore = asyncio.Semaphore(5)
    
    async def get_cities_batch(province_name):
        async with semaphore:
            return await client.get_cities(province_name)
    
    # 分批处理，每批5个
    batch_size = 5
    for i in range(0, len(provinces['items']), batch_size):
        batch = provinces['items'][i:i + batch_size]
        tasks = [get_cities_batch(p['name']) for p in batch]
        await asyncio.gather(*tasks)
```

#### 缓存策略
```python
import asyncio
import json
from llm_client import LLMClient

class CachedLLMClient:
    def __init__(self, cache_file='llm_cache.json'):
        self.client = LLMClient()
        self.cache_file = cache_file
        self.cache = self._load_cache()
    
    def _load_cache(self):
        """加载缓存"""
        try:
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
    
    def _save_cache(self):
        """保存缓存"""
        with open(self.cache_file, 'w', encoding='utf-8') as f:
            json.dump(self.cache, f, ensure_ascii=False, indent=2)
    
    def _get_cache_key(self, method_name, *args, **kwargs):
        """生成缓存键"""
        return f"{method_name}:{args}:{sorted(kwargs.items())}"
    
    async def cached_get_provinces(self):
        """带缓存的省份获取"""
        cache_key = self._get_cache_key('get_provinces')
        
        if cache_key in self.cache:
            print("使用缓存的省份数据")
            return self.cache[cache_key]
        
        result = await self.client.get_provinces()
        self.cache[cache_key] = result
        self._save_cache()
        return result
    
    async def cached_get_cities(self, province_name):
        """带缓存的城市获取"""
        cache_key = self._get_cache_key('get_cities', province_name)
        
        if cache_key in self.cache:
            print(f"使用缓存的 {province_name} 城市数据")
            return self.cache[cache_key]
        
        result = await self.client.get_cities(province_name)
        self.cache[cache_key] = result
        self._save_cache()
        return result

# 使用示例
async def cached_data_collection():
    client = CachedLLMClient()
    
    # 第一次调用会调用API并缓存
    provinces = await client.cached_get_provinces()
    cities1 = await client.cached_get_cities("广东省")
    
    # 第二次调用会使用缓存
    provinces_cached = await client.cached_get_provinces()
    cities2 = await client.cached_get_cities("广东省")

asyncio.run(cached_data_collection())
```

### 2. 错误处理

#### 分层错误处理
```python
import asyncio
from llm_client import LLMClient, LLMAPIError

class RobustDataCollector:
    def __init__(self):
        self.client = LLMClient()
        self.retry_config = {
            'max_retries': 3,
            'retry_delay': 1.0,
            'exponential_base': 2
        }
    
    async def collect_with_fallback(self, method_name, *args, **kwargs):
        """带降级策略的数据收集"""
        method = getattr(self.client, method_name)
        
        for attempt in range(self.retry_config['max_retries'] + 1):
            try:
                return await method(*args, **kwargs)
                
            except LLMAPIError as e:
                if e.status_code == 401:
                    # API密钥错误，无法重试
                    raise Exception(f"API密钥无效: {e.message}")
                
                elif e.status_code == 429:
                    # 请求频率限制，增加等待时间
                    wait_time = self.retry_config['retry_delay'] * (2 ** attempt) * 2
                    print(f"频率限制，{wait_time}秒后重试...")
                    await asyncio.sleep(wait_time)
                
                elif e.status_code >= 500:
                    # 服务器错误，可以重试
                    if attempt < self.retry_config['max_retries']:
                        wait_time = self.retry_config['retry_delay'] * (2 ** attempt)
                        print(f"服务器错误，{wait_time}秒后重试...")
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        raise Exception(f"服务器错误，重试{attempt}次后失败: {e.message}")
                
                else:
                    # 其他客户端错误，不重试
                    raise Exception(f"客户端错误: {e.message}")
            
            except Exception as e:
                if attempt < self.retry_config['max_retries']:
                    wait_time = self.retry_config['retry_delay'] * (2 ** attempt)
                    print(f"未知错误，{wait_time}秒后重试: {e}")
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    raise Exception(f"重试{attempt}次后仍然失败: {e}")
        
        raise Exception(f"达到最大重试次数: {self.retry_config['max_retries']}")

# 使用示例
async def robust_collection():
    collector = RobustDataCollector()
    
    try:
        provinces = await collector.collect_with_fallback('get_provinces')
        print(f"成功获取 {len(provinces['items'])} 个省份")
        
        # 如果省级数据获取失败，可以尝试其他数据源
        if not provinces['items']:
            print("省级数据为空，使用备用数据源")
            # 备用逻辑...
            
    except Exception as e:
        print(f"数据收集失败: {e}")
        # 错误处理逻辑...

asyncio.run(robust_collection())
```

### 3. 数据质量控制

#### 多重验证
```python
import asyncio
from llm_client import LLMClient
from typing import List, Dict

class DataQualityController:
    def __init__(self):
        self.client = LLMClient()
    
    async def validate_province_data(self, data: List[Dict]) -> bool:
        """验证省份数据质量"""
        if not data:
            return False
        
        # 检查必要字段
        required_fields = ['name']
        for item in data:
            for field in required_fields:
                if field not in item or not item[field]:
                    print(f"省份数据缺少必要字段: {field}")
                    return False
        
        # 检查名称重复
        names = [item['name'] for item in data]
        if len(names) != len(set(names)):
            print("省份数据存在重复名称")
            return False
        
        # 检查基本数量
        if len(data) < 30:  # 中国应该有34个省级行政区
            print(f"省份数量异常: {len(data)}")
            return False
        
        return True
    
    async def cross_validate_cities(self, province_name: str) -> bool:
        """交叉验证城市数据"""
        cities = await self.client.get_cities(province_name)
        
        if not await self.validate_province_data(cities['items']):
            return False
        
        # 验证逻辑城市数量合理性
        expected_min_cities = {
            '广东省': 21,
            '四川省': 21,
            '山东省': 16,
            '河南省': 17
        }
        
        expected_min = expected_min_cities.get(province_name, 5)
        if len(cities['items']) < expected_min:
            print(f"{province_name} 城市数量可能异常: {len(cities['items'])}")
            return False
        
        return True
    
    async def quality_assured_collection(self):
        """质量保证的数据收集"""
        # 获取省份数据
        provinces = await self.client.get_provinces()
        
        if not await self.validate_province_data(provinces['items']):
            raise Exception("省份数据质量验证失败")
        
        print(f"省份数据验证通过: {len(provinces['items'])} 个省份")
        
        # 验证部分省份的城市数据
        test_provinces = ["广东省", "江苏省", "四川省"]
        
        for province in test_provinces:
            if await self.cross_validate_cities(province):
                print(f"{province} 城市数据验证通过")
            else:
                print(f"{province} 城市数据验证失败")

# 使用示例
async def quality_controlled_collection():
    controller = DataQualityController()
    await controller.quality_assured_collection()

asyncio.run(quality_controlled_collection())
```

## 故障排除

### 1. 常见问题

#### API密钥问题
```python
# 问题：API密钥无效
# 症状：401 Unauthorized错误

# 检查方法
import asyncio
from llm_client import LLMClient

async def check_api_key():
    try:
        client = LLMClient(api_key="invalid-key")
        result = await client.get_provinces()
        print("API密钥有效")
    except LLMAPIError as e:
        if e.status_code == 401:
            print("API密钥无效或已过期")
            print("请检查:")
            print("1. API密钥是否正确")
            print("2. API密钥是否已过期")
            print("3. 账户是否有足够余额")
        else:
            print(f"其他错误: {e.message}")

asyncio.run(check_api_key())
```

#### 网络连接问题
```python
# 问题：网络连接失败
# 症状：连接超时、DNS解析失败等

# 解决方案：配置代理或检查网络
async def diagnose_network():
    # 检查基本网络连接
    import aiohttp
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get('https://dashscope.aliyuncs.com', timeout=10) as response:
                if response.status == 200:
                    print("基本网络连接正常")
                else:
                    print(f"网络响应异常: {response.status}")
    except Exception as e:
        print(f"网络连接失败: {e}")
        print("建议:")
        print("1. 检查网络连接")
        print("2. 配置HTTP代理")
        print("3. 检查防火墙设置")

asyncio.run(diagnose_network())
```

#### 数据格式问题
```python
# 问题：LLM返回数据格式异常
# 症状：JSON解析失败、数据结构不一致

async def handle_data_format_issues():
    client = LLMClient()
    
    try:
        hospitals = await client.get_hospitals("越秀区")
        
        # 检查数据结构
        if 'items' not in hospitals:
            print("响应缺少items字段")
            return
        
        for item in hospitals['items']:
            # 检查必要字段
            if 'name' not in item:
                print(f"医院记录缺少name字段: {item}")
                continue
            
            # 验证字段类型
            if not isinstance(item['name'], str):
                print(f"name字段类型错误: {item}")
                continue
        
        print(f"数据格式验证通过: {len(hospitals['items'])} 条记录")
        
    except Exception as e:
        print(f"数据格式问题: {e}")
        print("建议:")
        print("1. 检查prompt模板")
        print("2. 调整输出格式要求")
        print("3. 添加更多验证逻辑")

asyncio.run(handle_data_format_issues())
```

### 2. 调试技巧

#### 启用详细日志
```python
import logging
from llm_client import LLMClient

# 启用调试日志
logging.basicConfig(level=logging.DEBUG)

# 创建客户端
client = LLMClient(log_level="DEBUG")

# 现在所有LLM调用都会产生详细日志
async def debug_llm_calls():
    provinces = await client.get_provinces()
    print(provinces)

# 运行调试
asyncio.run(debug_llm_calls())
```

#### 手动测试API调用
```python
import asyncio
import json
from llm_client import LLMClient

async def manual_api_test():
    """手动测试API调用"""
    client = LLMClient()
    
    # 测试省份获取
    print("=== 测试省份获取 ===")
    try:
        result = await client.get_provinces()
        print(f"成功获取 {len(result.get('items', []))} 个省份")
        print(f"前3个省份: {result['items'][:3]}")
    except Exception as e:
        print(f"省份获取失败: {e}")
    
    # 测试城市获取
    print("\n=== 测试城市获取 ===")
    try:
        result = await client.get_cities("广东省")
        print(f"广东省有 {len(result.get('items', []))} 个城市")
    except Exception as e:
        print(f"城市获取失败: {e}")

asyncio.run(manual_api_test())
```

#### 数据导出和验证
```python
import asyncio
import json
from llm_client import LLMClient

async def export_and_validate_data():
    """导出数据进行验证"""
    client = LLMClient()
    
    all_data = {}
    
    try:
        # 获取所有数据
        print("正在获取省份数据...")
        all_data['provinces'] = await client.get_provinces()
        
        print("正在获取主要城市数据...")
        sample_provinces = all_data['provinces']['items'][:5]  # 取前5个省份
        
        all_data['cities'] = {}
        for province in sample_provinces:
            print(f"  获取 {province['name']} 的城市...")
            all_data['cities'][province['name']] = await client.get_cities(province['name'])
        
        # 保存到文件
        with open('test_data_export.json', 'w', encoding='utf-8') as f:
            json.dump(all_data, f, ensure_ascii=False, indent=2)
        
        print("数据已导出到 test_data_export.json")
        
        # 验证数据
        total_cities = sum(len(cities['items']) for cities in all_data['cities'].values())
        print(f"验证结果: {len(all_data['provinces']['items'])} 个省份, {total_cities} 个城市")
        
    except Exception as e:
        print(f"数据导出失败: {e}")

asyncio.run(export_and_validate_data())
```

## 版本兼容性

### API版本支持
- **当前版本**: v1.0.0
- **最低要求**: Python 3.8+
- **依赖版本**: 
  - requests >= 2.25.0
  - aiohttp >= 3.8.0

### 升级指南
```python
# 从旧版本升级的注意事项

# 1. 配置变更
# 旧版本
client = LLMClient(api_key="key", timeout=30)

# 新版本
client = LLMClient(
    api_key="key",
    timeout=30.0,          # 明确指定float类型
    max_retries=2,         # 新增重试配置
    max_concurrent=5       # 新增并发配置
)

# 2. 错误处理变更
# 旧版本
try:
    result = await client.get_provinces()
except Exception as e:
    print(f"错误: {e}")

# 新版本 - 更好的错误分类
try:
    result = await client.get_provinces()
except LLMAPIError as e:
    print(f"API错误 {e.status_code}: {e.message}")
except ResponseParsingError as e:
    print(f"响应解析错误: {e}")
except ValidationError as e:
    print(f"数据验证错误: {e}")
```

## 总结

LLM客户端提供了完整的数据获取能力，支持省市区医院四级数据的智能获取。通过合理配置错误处理、重试机制和监控日志，可以构建稳定可靠的数据获取系统。遵循最佳实践，可以确保系统的高性能和数据质量。

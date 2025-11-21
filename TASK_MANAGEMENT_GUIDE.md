# 任务管理系统使用指南

## 功能概述

任务管理系统实现了完整的异步任务调度框架，支持层级数据刷新、进度跟踪、并发控制等功能。

### 核心功能

1. **异步任务调度**
   - 支持全量刷新和指定省刷新两种模式
   - 异步执行，不阻塞主线程
   - 支持任务创建、启动、监控和取消

2. **任务状态管理**
   - `PENDING`: 任务已创建，等待执行
   - `RUNNING`: 任务正在执行中
   - `SUCCEEDED`: 任务执行成功完成
   - `FAILED`: 任务执行失败

3. **进度跟踪系统**
   - 实时进度更新（0-100%）
   - 详细的步骤描述
   - 进度回调机制

4. **层级数据刷新流程**
   - 省级 → 市级 → 区县级 → 医院级
   - 自动化层级遍历
   - 数据结构化管理

5. **并发控制**
   - 使用 `asyncio.Semaphore(5)` 限制最大并发数为5
   - 避免系统资源过载

6. **错误处理和恢复**
   - 指数退避重试机制
   - 详细的错误日志记录
   - 优雅的错误恢复

## 快速开始

### 基本使用示例

```python
import asyncio
from tasks import TaskManager

async def main():
    # 创建任务管理器
    manager = TaskManager()
    
    # 1. 创建全量刷新任务
    task_id = await manager.create_refresh_task("full")
    await manager.start_task(task_id)
    
    # 2. 创建指定省刷新任务
    province_task_id = await manager.create_refresh_task("province", "北京市")
    await manager.start_task(province_task_id)
    
    # 3. 监控任务进度
    while True:
        status = manager.get_task_status(task_id)
        print(f"进度: {status['progress']}% - {status['current_step']}")
        
        if status['status'] in ['SUCCEEDED', 'FAILED']:
            break
        
        await asyncio.sleep(1)

# 运行
asyncio.run(main())
```

### API 方法说明

#### TaskManager 类方法

| 方法名 | 参数 | 返回值 | 说明 |
|--------|------|--------|------|
| `create_refresh_task()` | `task_type`, `target` | `str` | 创建任务，返回任务ID |
| `start_task()` | `task_id` | `bool` | 启动任务 |
| `get_task_status()` | `task_id` | `Dict/None` | 获取任务状态 |
| `list_tasks()` | `status` | `List[Dict]` | 列出任务 |
| `cancel_task()` | `task_id` | `bool` | 取消任务 |
| `cleanup_old_tasks()` | `hours` | `int` | 清理旧任务 |

#### LLMService 类方法

| 方法名 | 参数 | 返回值 | 说明 |
|--------|------|--------|------|
| `get_provinces()` | 无 | `List[str]` | 获取省份列表 |
| `get_cities()` | `province` | `List[str]` | 获取市级列表 |
| `get_districts()` | `city` | `List[str]` | 获取区县级列表 |
| `get_hospitals()` | `district` | `List[str]` | 获取医院列表 |

## 任务执行流程

### 全量刷新流程

1. 获取省份列表（LLM调用）
2. 遍历每个省份：
   - 获取市级列表（LLM调用）
   - 遍历每个市：
     - 获取区县级列表（LLM调用）
     - 遍历每个区县：
       - 获取医院列表（LLM调用）
       - 保存数据结构

### 指定省刷新流程

1. 验证指定省份是否存在
2. 处理指定省份的完整数据层级：
   - 市 → 区县 → 医院

## 配置参数

### 并发控制
```python
self.semaphore = asyncio.Semaphore(5)  # 最大5个并发任务
```

### 重试机制
```python
max_retries = 3  # 最大重试次数
await asyncio.sleep(2 ** attempt)  # 指数退避延迟
```

### 进度跟踪
```python
# 总步骤数为100，计算进度百分比
progress = min(100, int((current_step / total_steps) * 100))
```

## 扩展使用

### 自定义LLM服务

```python
class CustomLLMService(LLMService):
    async def get_provinces(self):
        # 自定义省份获取逻辑
        return await your_custom_api_call()
    
    async def get_cities(self, province):
        # 自定义城市获取逻辑
        return await your_custom_api_call(province)
```

### 添加进度回调

```python
def progress_callback(progress: int, step_name: str):
    print(f"进度: {progress}% - {step_name}")

progress_tracker = ProgressTracker(100)
progress_tracker.add_callback(progress_callback)
```

### 错误处理自定义

```python
async def _safe_call_with_retry(self, func, error_msg, max_retries=3):
    # 可以在这里添加自定义的错误处理逻辑
    # 例如：发送通知、记录到监控系统等
```

## 日志记录

系统内置完整的日志记录功能：

- **INFO级别**: 任务创建、启动、完成等关键状态变化
- **DEBUG级别**: 详细的数据处理过程
- **WARNING级别**: 重试警告信息
- **ERROR级别**: 错误详情和堆栈跟踪

## 性能考虑

1. **并发控制**: 限制同时处理的任务数量避免过载
2. **内存管理**: 任务结果保存在内存中，大规模数据建议持久化
3. **网络延迟**: LLM调用加入随机延迟模拟真实环境
4. **重试策略**: 指数退避减少服务器压力

## 生产环境部署建议

1. **数据库集成**: 将结果保存到数据库而不是内存
2. **消息队列**: 使用消息队列处理大量任务
3. **监控告警**: 添加任务监控和失败告警机制
4. **配置管理**: 使用配置文件管理并发数、重试次数等参数
5. **健康检查**: 添加系统健康检查接口
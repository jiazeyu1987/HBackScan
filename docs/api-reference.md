# API接口详细文档

## 概述

本文档提供了医院层级扫查微服务的完整API参考。API采用RESTful设计，支持JSON格式的请求和响应。

## 基础信息

### 基础URL
```
http://localhost:8000
```

### 认证方式
当前版本无需认证。所有API接口都是公开的。

### 响应格式
所有API响应都遵循统一的格式：

```json
{
  "code": 200,
  "message": "操作成功",
  "data": {}
}
```

#### 响应字段说明
- `code`: 状态码（200=成功，400=请求错误，500=服务器错误）
- `message`: 响应消息
- `data`: 响应数据

### 状态码说明
| 状态码 | 说明 |
|--------|------|
| 200 | 请求成功 |
| 400 | 请求参数错误 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |
| 503 | 服务不可用 |

## 数据刷新接口

### 全量刷新所有数据

刷新所有省份及其下属城市、区县、医院的数据。

```http
POST /refresh/all
```

#### 请求参数
无

#### 响应示例
```json
{
  "code": 200,
  "message": "全量刷新任务已启动",
  "data": {
    "task_id": "task_20231121_143052_123456",
    "status": "PENDING",
    "progress": 0,
    "message": "任务已创建，等待执行"
  }
}
```

#### 响应字段说明
| 字段 | 类型 | 说明 |
|------|------|------|
| task_id | string | 任务唯一标识符 |
| status | string | 任务状态 |
| progress | number | 进度百分比（0-100） |
| message | string | 状态消息 |

### 刷新指定省份数据

刷新指定省份及其下属城市、区县、医院的数据。

```http
POST /refresh/province/{province_name}
```

#### 路径参数
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| province_name | string | ✅ | 省份名称 |

#### 请求示例
```bash
curl -X POST http://localhost:8000/refresh/province/广东省
```

#### 响应示例
```json
{
  "code": 200,
  "message": "广东省刷新任务已启动",
  "data": {
    "task_id": "task_20231121_143052_789012",
    "status": "PENDING",
    "progress": 0
  }
}
```

## 数据查询接口

### 获取省份列表

支持分页查询所有省份信息。

```http
GET /provinces
```

#### 查询参数
| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| page | integer | ❌ | 1 | 页码（从1开始） |
| page_size | integer | ❌ | 10 | 每页数量（1-100） |
| sort | string | ❌ | name | 排序字段（name, created_at, updated_at） |
| order | string | ❌ | asc | 排序方向（asc, desc） |

#### 请求示例
```bash
curl "http://localhost:8000/provinces?page=1&page_size=20&sort=name&order=asc"
```

#### 响应示例
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
        "created_at": "2023-11-21T14:30:00",
        "updated_at": "2023-11-21T14:30:00"
      },
      {
        "id": 2,
        "name": "天津市",
        "code": null,
        "created_at": "2023-11-21T14:30:01",
        "updated_at": "2023-11-21T14:30:01"
      }
    ],
    "total": 34,
    "page": 1,
    "page_size": 20,
    "total_pages": 2,
    "has_next": true,
    "has_prev": false
  }
}
```

#### 响应字段说明
| 字段 | 类型 | 说明 |
|------|------|------|
| items | array | 省份列表 |
| total | integer | 总数量 |
| page | integer | 当前页码 |
| page_size | integer | 每页数量 |
| total_pages | integer | 总页数 |
| has_next | boolean | 是否有下一页 |
| has_prev | boolean | 是否有上一页 |

### 获取城市列表

根据省份获取城市列表。

```http
GET /cities
```

#### 查询参数
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| province | string | ✅ | 省份名称 |
| page | integer | ❌ | 页码（默认1） |
| page_size | integer | ❌ | 每页数量（默认10，最大100） |

#### 请求示例
```bash
curl "http://localhost:8000/cities?province=广东省&page=1&page_size=20"
```

#### 响应示例
```json
{
  "code": 200,
  "message": "获取城市列表成功",
  "data": {
    "items": [
      {
        "id": 101,
        "province_id": 19,
        "name": "广州市",
        "code": null,
        "created_at": "2023-11-21T14:30:00",
        "updated_at": "2023-11-21T14:30:00"
      },
      {
        "id": 102,
        "province_id": 19,
        "name": "深圳市",
        "code": null,
        "created_at": "2023-11-21T14:30:00",
        "updated_at": "2023-11-21T14:30:00"
      }
    ],
    "total": 21,
    "page": 1,
    "page_size": 20,
    "total_pages": 2
  }
}
```

### 获取区县列表

根据城市获取区县列表。

```http
GET /districts
```

#### 查询参数
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| city | string | ✅ | 城市名称 |
| page | integer | ❌ | 页码（默认1） |
| page_size | integer | ❌ | 每页数量（默认10，最大100） |

#### 请求示例
```bash
curl "http://localhost:8000/districts?city=广州市&page=1&page_size=50"
```

#### 响应示例
```json
{
  "code": 200,
  "message": "获取区县列表成功",
  "data": {
    "items": [
      {
        "id": 1001,
        "city_id": 101,
        "name": "越秀区",
        "code": null,
        "created_at": "2023-11-21T14:30:00",
        "updated_at": "2023-11-21T14:30:00"
      },
      {
        "id": 1002,
        "city_id": 101,
        "name": "荔湾区",
        "code": null,
        "created_at": "2023-11-21T14:30:00",
        "updated_at": "2023-11-21T14:30:00"
      }
    ],
    "total": 11,
    "page": 1,
    "page_size": 50,
    "total_pages": 1
  }
}
```

### 获取医院列表

根据区县获取医院列表。

```http
GET /hospitals
```

#### 查询参数
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| district | string | ✅ | 区县名称 |
| page | integer | ❌ | 页码（默认1） |
| page_size | integer | ❌ | 每页数量（默认10，最大100） |

#### 请求示例
```bash
curl "http://localhost:8000/hospitals?district=越秀区&page=1&page_size=20"
```

#### 响应示例
```json
{
  "code": 200,
  "message": "获取医院列表成功",
  "data": {
    "items": [
      {
        "id": 10001,
        "district_id": 1001,
        "name": "中山大学附属第一医院",
        "website": "https://www.gzsums.edu.cn/",
        "llm_confidence": 0.95,
        "created_at": "2023-11-21T14:30:00",
        "updated_at": "2023-11-21T14:30:00"
      },
      {
        "id": 10002,
        "district_id": 1001,
        "name": "广东省人民医院",
        "website": "https://www.gdph.com.cn/",
        "llm_confidence": 0.92,
        "created_at": "2023-11-21T14:30:00",
        "updated_at": "2023-11-21T14:30:00"
      }
    ],
    "total": 156,
    "page": 1,
    "page_size": 20,
    "total_pages": 8
  }
}
```

#### 响应字段说明
| 字段 | 类型 | 说明 |
|------|------|------|
| llm_confidence | number | LLM返回的置信度（0-1） |
| website | string | 医院官网地址 |

### 模糊搜索医院

根据关键词搜索医院名称。

```http
GET /hospitals/search
```

#### 查询参数
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| q | string | ✅ | 搜索关键词 |
| page | integer | ❌ | 页码（默认1） |
| page_size | integer | ❌ | 每页数量（默认10，最大100） |
| min_confidence | number | ❌ | 最小置信度（0-1） |

#### 请求示例
```bash
curl "http://localhost:8000/hospitals/search?q=协和&page=1&page_size=10"
```

#### 响应示例
```json
{
  "code": 200,
  "message": "搜索医院成功",
  "data": {
    "query": "协和",
    "items": [
      {
        "id": 20001,
        "district_id": 1001,
        "name": "北京协和医院",
        "website": "https://www.pumch.cn/",
        "llm_confidence": 0.98,
        "created_at": "2023-11-21T14:30:00",
        "updated_at": "2023-11-21T14:30:00",
        "district": {
          "name": "东城区",
          "city": {
            "name": "北京市",
            "province": {
              "name": "北京市"
            }
          }
        }
      }
    ],
    "total": 5,
    "page": 1,
    "page_size": 10,
    "total_pages": 1,
    "search_time_ms": 15
  }
}
```

#### 响应字段说明
| 字段 | 类型 | 说明 |
|------|------|------|
| query | string | 搜索关键词 |
| search_time_ms | number | 搜索耗时（毫秒） |
| district | object | 区县信息（包含完整层级关系） |

## 任务管理接口

### 获取任务状态

查询指定任务的详细信息和执行进度。

```http
GET /tasks/{task_id}
```

#### 路径参数
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| task_id | string | ✅ | 任务ID |

#### 请求示例
```bash
curl http://localhost:8000/tasks/task_20231121_143052_123456
```

#### 响应示例
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
    "progress": 65,
    "current_step": "正在获取区县数据：越秀区",
    "result": null,
    "error_message": null,
    "statistics": {
      "provinces_processed": 5,
      "cities_processed": 78,
      "districts_processed": 156,
      "hospitals_found": 1245
    }
  }
}
```

#### 任务状态说明
| 状态 | 说明 |
|------|------|
| PENDING | 任务已创建，等待执行 |
| RUNNING | 任务正在执行中 |
| SUCCEEDED | 任务执行成功完成 |
| FAILED | 任务执行失败 |

#### 响应字段说明
| 字段 | 类型 | 说明 |
|------|------|------|
| progress | number | 执行进度（0-100） |
| current_step | string | 当前执行的步骤描述 |
| statistics | object | 任务统计信息 |

### 获取所有任务

分页获取任务列表。

```http
GET /tasks
```

#### 查询参数
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| page | integer | ❌ | 页码（默认1） |
| page_size | integer | ❌ | 每页数量（默认10，最大100） |
| status | string | ❌ | 任务状态过滤 |
| sort | string | ❌ | 排序字段（created_at, updated_at, progress） |
| order | string | ❌ | 排序方向（asc, desc） |

#### 请求示例
```bash
curl "http://localhost:8000/tasks?page=1&page_size=20&status=RUNNING&sort=created_at&order=desc"
```

#### 响应示例
```json
{
  "code": 200,
  "message": "获取任务列表成功",
  "data": {
    "items": [
      {
        "task_id": "task_20231121_143052_123456",
        "hospital_name": "全量刷新",
        "query": null,
        "status": "RUNNING",
        "created_at": "2023-11-21T14:30:52",
        "updated_at": "2023-11-21T14:32:15",
        "progress": 65,
        "current_step": "正在获取区县数据"
      }
    ],
    "total": 15,
    "page": 1,
    "page_size": 20,
    "total_pages": 1
  }
}
```

### 获取活跃任务

获取所有正在执行的任务。

```http
GET /tasks/active
```

#### 查询参数
无

#### 请求示例
```bash
curl http://localhost:8000/tasks/active
```

#### 响应示例
```json
{
  "code": 200,
  "message": "获取活跃任务成功",
  "data": {
    "items": [
      {
        "task_id": "task_20231121_143052_123456",
        "hospital_name": "全量刷新",
        "status": "RUNNING",
        "progress": 65,
        "created_at": "2023-11-21T14:30:52",
        "estimated_completion": "2023-11-21T15:30:00"
      }
    ],
    "count": 1,
    "max_concurrent": 5
  }
}
```

### 取消任务

取消正在执行的任务。

```http
DELETE /tasks/{task_id}
```

#### 路径参数
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| task_id | string | ✅ | 任务ID |

#### 请求示例
```bash
curl -X DELETE http://localhost:8000/tasks/task_20231121_143052_123456
```

#### 响应示例
```json
{
  "code": 200,
  "message": "任务已取消",
  "data": {
    "task_id": "task_20231121_143052_123456",
    "status": "CANCELLED",
    "cancelled_at": "2023-11-21T14:35:00"
  }
}
```

### 清理旧任务

清理已完成或失败的任务记录。

```http
POST /tasks/cleanup
```

#### 请求参数
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| older_than_days | integer | ❌ | 清理多少天前的任务（默认7） |
| status | string | ❌ | 清理指定状态的任务（SUCCEEDED, FAILED, CANCELLED） |

#### 请求示例
```bash
curl -X POST http://localhost:8000/tasks/cleanup \
  -H "Content-Type: application/json" \
  -d '{"older_than_days": 7, "status": "SUCCEEDED"}'
```

#### 响应示例
```json
{
  "code": 200,
  "message": "任务清理完成",
  "data": {
    "deleted_count": 25,
    "cleaned_status": ["SUCCEEDED"],
    "older_than_days": 7
  }
}
```

## 系统接口

### 健康检查

检查系统健康状态。

```http
GET /health
```

#### 请求参数
无

#### 请求示例
```bash
curl http://localhost:8000/health
```

#### 响应示例
```json
{
  "status": "healthy",
  "timestamp": "2023-11-21T14:35:00",
  "version": "1.0.0",
  "uptime_seconds": 3600,
  "checks": {
    "database": "ok",
    "llm_api": "ok",
    "disk_space": "ok"
  }
}
```

#### 健康检查说明
| 检查项 | 状态 | 说明 |
|--------|------|------|
| database | ok/fail | 数据库连接状态 |
| llm_api | ok/fail | LLM API连接状态 |
| disk_space | ok/fail | 磁盘空间状态 |

### 数据统计

获取系统数据统计信息。

```http
GET /statistics
```

#### 请求参数
无

#### 请求示例
```bash
curl http://localhost:8000/statistics
```

#### 响应示例
```json
{
  "code": 200,
  "message": "获取统计数据成功",
  "data": {
    "database": {
      "total_provinces": 34,
      "total_cities": 334,
      "total_districts": 2844,
      "total_hospitals": 98765,
      "last_updated": "2023-11-21T14:30:00"
    },
    "tasks": {
      "total_tasks": 156,
      "running_tasks": 2,
      "completed_tasks": 145,
      "failed_tasks": 9,
      "success_rate": 93.9
    },
    "system": {
      "api_calls_today": 1245,
      "llm_calls_today": 89,
      "response_time_avg_ms": 245,
      "error_rate": 0.8
    }
  }
}
```

## 错误处理

### 错误响应格式

所有错误响应都遵循以下格式：

```json
{
  "code": 400,
  "message": "错误描述",
  "error": {
    "type": "ValidationError",
    "details": [
      {
        "field": "province_name",
        "message": "省份名称不能为空"
      }
    ]
  }
}
```

### 常见错误类型

#### 400 - 请求参数错误
- 参数缺失
- 参数格式错误
- 参数值无效

#### 404 - 资源不存在
- 任务ID不存在
- 省份/城市/区县/医院不存在

#### 500 - 服务器错误
- 数据库连接失败
- LLM API调用失败
- 系统内部错误

#### 503 - 服务不可用
- LLM API服务不可用
- 系统维护中

### 错误代码参考

| 错误代码 | 说明 | 解决方案 |
|----------|------|----------|
| INVALID_PARAMETER | 请求参数无效 | 检查参数格式和值 |
| RESOURCE_NOT_FOUND | 资源不存在 | 确认资源ID是否存在 |
| DATABASE_ERROR | 数据库错误 | 检查数据库连接 |
| LLM_API_ERROR | LLM API错误 | 检查API密钥和网络连接 |
| TASK_NOT_FOUND | 任务不存在 | 确认任务ID正确 |
| TASK_ALREADY_RUNNING | 任务已在运行 | 等待当前任务完成 |
| INSUFFICIENT_PERMISSIONS | 权限不足 | 检查API访问权限 |

## 使用限制

### 请求频率限制
- 默认限制：1000次/小时
- API调用频率过高会返回429错误

### 数据量限制
- 单次查询最大记录数：1000条
- 任务超时时间：2小时
- 最大并发任务数：5个

### 响应时间
- 查询接口：< 1秒
- 数据刷新接口：异步返回
- 复杂查询：< 5秒

## SDK和工具

### Python客户端示例

```python
import requests
import asyncio
from typing import Dict, List, Optional

class HospitalScannerClient:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        
    async def get_provinces(self, page: int = 1, page_size: int = 10) -> Dict:
        """获取省份列表"""
        response = requests.get(
            f"{self.base_url}/provinces",
            params={"page": page, "page_size": page_size}
        )
        return response.json()
    
    async def search_hospitals(self, query: str, page: int = 1, page_size: int = 10) -> Dict:
        """搜索医院"""
        response = requests.get(
            f"{self.base_url}/hospitals/search",
            params={"q": query, "page": page, "page_size": page_size}
        )
        return response.json()
    
    async def refresh_all_data(self) -> Dict:
        """全量刷新数据"""
        response = requests.post(f"{self.base_url}/refresh/all")
        return response.json()

# 使用示例
client = HospitalScannerClient()

# 获取省份列表
provinces = asyncio.run(client.get_provinces())
print(f"省份数量: {provinces['data']['total']}")

# 搜索医院
hospitals = asyncio.run(client.search_hospitals("协和"))
print(f"找到 {hospitals['data']['total']} 家相关医院")
```

### JavaScript客户端示例

```javascript
class HospitalScannerClient {
    constructor(baseUrl = 'http://localhost:8000') {
        this.baseUrl = baseUrl;
    }
    
    async getProvinces(page = 1, pageSize = 10) {
        const response = await fetch(
            `${this.baseUrl}/provinces?page=${page}&page_size=${pageSize}`
        );
        return await response.json();
    }
    
    async searchHospitals(query, page = 1, pageSize = 10) {
        const response = await fetch(
            `${this.baseUrl}/hospitals/search?q=${encodeURIComponent(query)}&page=${page}&page_size=${pageSize}`
        );
        return await response.json();
    }
    
    async refreshAllData() {
        const response = await fetch(`${this.baseUrl}/refresh/all`, {
            method: 'POST'
        });
        return await response.json();
    }
}

// 使用示例
const client = new HospitalScannerClient();

// 获取省份列表
const provinces = await client.getProvinces();
console.log(`省份数量: ${provinces.data.total}`);

// 搜索医院
const hospitals = await client.searchHospitals('协和');
console.log(`找到 ${hospitals.data.total} 家相关医院`);
```

### cURL示例集合

```bash
#!/bin/bash
# 医院扫描服务 API 使用示例集合

BASE_URL="http://localhost:8000"

echo "=== 医院扫描服务 API 示例 ==="

# 1. 健康检查
echo "1. 健康检查"
curl -s "${BASE_URL}/health" | jq .

# 2. 获取省份列表
echo "2. 获取省份列表"
curl -s "${BASE_URL}/provinces?page=1&page_size=5" | jq .

# 3. 获取广东省城市
echo "3. 获取广东省城市"
curl -s "${BASE_URL}/cities?province=广东省" | jq .

# 4. 获取广州市区县
echo "4. 获取广州市区县"
curl -s "${BASE_URL}/districts?city=广州市" | jq .

# 5. 获取越秀区医院
echo "5. 获取越秀区医院"
curl -s "${BASE_URL}/hospitals?district=越秀区&page=1&page_size=3" | jq .

# 6. 搜索医院
echo "6. 搜索医院"
curl -s "${BASE_URL}/hospitals/search?q=协和&page=1&page_size=5" | jq .

# 7. 全量刷新（异步）
echo "7. 全量刷新"
TASK_RESPONSE=$(curl -s -X POST "${BASE_URL}/refresh/all" | jq .)
echo "$TASK_RESPONSE" | jq .

# 提取任务ID
TASK_ID=$(echo "$TASK_RESPONSE" | jq -r '.data.task_id')
echo "任务ID: $TASK_ID"

# 8. 查询任务状态
echo "8. 查询任务状态"
curl -s "${BASE_URL}/tasks/${TASK_ID}" | jq .

# 9. 获取活跃任务
echo "9. 获取活跃任务"
curl -s "${BASE_URL}/tasks/active" | jq .

# 10. 获取系统统计
echo "10. 获取系统统计"
curl -s "${BASE_URL}/statistics" | jq .
```

## 更新日志

### v1.0.0 (2023-11-21)
- 初始版本发布
- 支持省市区医院数据管理
- 实现LLM智能数据刷新
- 提供完整的RESTful API
- 支持异步任务管理

## 联系我们

如有问题或建议，请通过以下方式联系：

- 📧 邮箱: support@hospital-scanner.com
- 🐛 报告问题: [GitHub Issues](https://github.com/your-org/hospital-scanner/issues)
- 💬 技术讨论: [GitHub Discussions](https://github.com/your-org/hospital-scanner/discussions)

# 数据库设计文档

## 概述

医院层级扫查微服务使用SQLite作为主数据库，存储省、市、区县、医院四级层级数据以及任务管理相关信息。本文档详细描述了数据库的表结构、索引设计、约束条件和性能优化策略。

## 数据库架构

### 数据库信息
- **数据库类型**: SQLite 3.x
- **字符编码**: UTF-8
- **事务模式**: WAL模式（Write-Ahead Logging）
- **并发模式**: 多读者单写者
- **数据完整性**: 外键约束支持

### 物理设计
- **数据库文件**: `data/hospital_scanner.db`
- **日志模式**: WAL
- **页面大小**: 默认4KB
- **缓存大小**: 默认2000页

## 表结构设计

### 1. 省份表 (provinces)

存储全国省份信息，是层级数据的顶层。

```sql
CREATE TABLE provinces (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    code TEXT,                    -- 省份代码（预留字段）
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
```

#### 字段说明
| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PRIMARY KEY, AUTOINCREMENT | 省份唯一标识 |
| name | TEXT | NOT NULL, UNIQUE | 省份名称，必填且唯一 |
| code | TEXT | - | 省份标准代码（预留） |
| created_at | TEXT | NOT NULL | 记录创建时间 |
| updated_at | TEXT | NOT NULL | 记录更新时间 |

#### 数据样例
```sql
INSERT INTO provinces (name) VALUES 
('北京市'), ('天津市'), ('河北省'), ('山西省'), ('内蒙古自治区'),
('辽宁省'), ('吉林省'), ('黑龙江省'), ('上海市'), ('江苏省'),
('浙江省'), ('安徽省'), ('福建省'), ('江西省'), ('山东省'),
('河南省'), ('湖北省'), ('湖南省'), ('广东省'), ('广西壮族自治区'),
('海南省'), ('重庆市'), ('四川省'), ('贵州省'), ('云南省'),
('西藏自治区'), ('陕西省'), ('甘肃省'), ('青海省'), ('宁夏回族自治区'),
('新疆维吾尔自治区'), ('中国香港特别行政区'), ('中国澳门特别行政区'), ('中国台湾省');
```

### 2. 城市表 (cities)

存储城市信息，关联到省份。

```sql
CREATE TABLE cities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    province_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    code TEXT,                    -- 城市代码（预留字段）
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (province_id) REFERENCES provinces(id) ON DELETE CASCADE
);
```

#### 字段说明
| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PRIMARY KEY, AUTOINCREMENT | 城市唯一标识 |
| province_id | INTEGER | NOT NULL, FOREIGN KEY | 所属省份ID |
| name | TEXT | NOT NULL | 城市名称 |
| code | TEXT | - | 城市标准代码（预留） |
| created_at | TEXT | NOT NULL | 记录创建时间 |
| updated_at | TEXT | NOT NULL | 记录更新时间 |

#### 索引设计
```sql
CREATE INDEX idx_cities_province_id ON cities(province_id);
CREATE INDEX idx_cities_name ON cities(name);
```

### 3. 区县表 (districts)

存储区县信息，关联到城市。

```sql
CREATE TABLE districts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    city_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    code TEXT,                    -- 区县代码（预留字段）
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (city_id) REFERENCES cities(id) ON DELETE CASCADE
);
```

#### 字段说明
| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PRIMARY KEY, AUTOINCREMENT | 区县唯一标识 |
| city_id | INTEGER | NOT NULL, FOREIGN KEY | 所属城市ID |
| name | TEXT | NOT NULL | 区县名称 |
| code | TEXT | - | 区县标准代码（预留） |
| created_at | TEXT | NOT NULL | 记录创建时间 |
| updated_at | TEXT | NOT NULL | 记录更新时间 |

#### 索引设计
```sql
CREATE INDEX idx_districts_city_id ON districts(city_id);
CREATE INDEX idx_districts_name ON districts(name);
```

### 4. 医院表 (hospitals)

存储医院详细信息，关联到区县。

```sql
CREATE TABLE hospitals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    district_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    website TEXT,                 -- 医院官网地址
    llm_confidence REAL,          -- LLM返回的置信度
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (district_id) REFERENCES districts(id) ON DELETE CASCADE
);
```

#### 字段说明
| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PRIMARY KEY, AUTOINCREMENT | 医院唯一标识 |
| district_id | INTEGER | NOT NULL, FOREIGN KEY | 所属区县ID |
| name | TEXT | NOT NULL | 医院名称 |
| website | TEXT | - | 医院官网地址 |
| llm_confidence | REAL | - | LLM置信度（0-1） |
| created_at | TEXT | NOT NULL | 记录创建时间 |
| updated_at | TEXT | NOT NULL | 记录更新时间 |

#### 索引设计
```sql
CREATE INDEX idx_hospitals_district_id ON hospitals(district_id);
CREATE INDEX idx_hospitals_name ON hospitals(name);
CREATE INDEX idx_hospitals_name_fts ON hospitals(name);  -- 全文搜索索引
```

### 5. 任务表 (tasks)

存储任务管理信息，支持异步任务处理。

```sql
CREATE TABLE tasks (
    task_id TEXT PRIMARY KEY,
    hospital_name TEXT NOT NULL,
    query TEXT,                   -- 任务查询条件
    status TEXT NOT NULL,         -- PENDING, RUNNING, SUCCEEDED, FAILED
    progress INTEGER DEFAULT 0,   -- 进度百分比 (0-100)
    current_step TEXT,            -- 当前执行步骤
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    result TEXT,                  -- 任务结果 (JSON格式)
    error_message TEXT            -- 错误信息
);
```

#### 字段说明
| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| task_id | TEXT | PRIMARY KEY | 任务唯一标识符 |
| hospital_name | TEXT | NOT NULL | 任务描述或医院名称 |
| query | TEXT | - | 任务查询条件 |
| status | TEXT | NOT NULL | 任务状态 |
| progress | INTEGER | DEFAULT 0 | 任务进度百分比 |
| current_step | TEXT | - | 当前执行步骤描述 |
| created_at | TEXT | NOT NULL | 任务创建时间 |
| updated_at | TEXT | NOT NULL | 任务更新时间 |
| result | TEXT | - | 任务执行结果（JSON） |
| error_message | TEXT | - | 错误信息 |

#### 任务状态枚举
| 状态 | 说明 | 转换条件 |
|------|------|----------|
| PENDING | 等待执行 | 任务创建后 |
| RUNNING | 正在执行 | 任务开始执行 |
| SUCCEEDED | 执行成功 | 任务正常完成 |
| FAILED | 执行失败 | 任务异常终止 |
| CANCELLED | 已取消 | 用户主动取消 |

#### 索引设计
```sql
CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_tasks_created_at ON tasks(created_at);
CREATE INDEX idx_tasks_updated_at ON tasks(updated_at);
```

## 数据关系设计

### 层级关系
```
provinces (1) -----> (N) cities (1) -----> (N) districts (1) -----> (N) hospitals
```

### 外键关系
```sql
-- 城市表外键
ALTER TABLE cities ADD CONSTRAINT fk_cities_province 
    FOREIGN KEY (province_id) REFERENCES provinces(id) ON DELETE CASCADE;

-- 区县表外键
ALTER TABLE districts ADD CONSTRAINT fk_districts_city 
    FOREIGN KEY (city_id) REFERENCES cities(id) ON DELETE CASCADE;

-- 医院表外键
ALTER TABLE hospitals ADD CONSTRAINT fk_hospitals_district 
    FOREIGN KEY (district_id) REFERENCES districts(id) ON DELETE CASCADE;
```

### 数据完整性约束

#### 业务规则
1. **唯一性约束**
   - 省份名称在同一层级内必须唯一
   - 任务ID全局唯一

2. **参照完整性**
   - 子级记录不能脱离父级存在（级联删除）
   - 外键约束确保数据一致性

3. **数据验证**
   - 置信度值必须在0-1范围内
   - 进度值必须在0-100范围内

## 索引设计

### 主要索引

#### 1. 单列索引
```sql
-- 省份表索引
CREATE INDEX idx_provinces_name ON provinces(name);

-- 城市表索引
CREATE INDEX idx_cities_province_id ON cities(province_id);
CREATE INDEX idx_cities_name ON cities(name);

-- 区县表索引
CREATE INDEX idx_districts_city_id ON districts(city_id);
CREATE INDEX idx_districts_name ON districts(name);

-- 医院表索引
CREATE INDEX idx_hospitals_district_id ON hospitals(district_id);
CREATE INDEX idx_hospitals_name ON hospitals(name);

-- 任务表索引
CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_tasks_created_at ON tasks(created_at);
```

#### 2. 复合索引
```sql
-- 城市-省份复合索引（用于按省查城市）
CREATE INDEX idx_cities_province_name ON cities(province_id, name);

-- 区县-城市复合索引（用于按市查区县）
CREATE INDEX idx_districts_city_name ON districts(city_id, name);

-- 医院-区县复合索引（用于按区县查医院）
CREATE INDEX idx_hospitals_district_name ON hospitals(district_id, name);

-- 任务状态-创建时间索引（用于活跃任务查询）
CREATE INDEX idx_tasks_status_created ON tasks(status, created_at);
```

#### 3. 全文搜索索引
```sql
-- 医院名称全文搜索
CREATE VIRTUAL TABLE hospitals_fts USING fts5(
    name,
    website,
    content='hospitals',
    content_rowid='id'
);

-- 触发器保持全文索引同步
CREATE TRIGGER hospitals_fts_insert AFTER INSERT ON hospitals
BEGIN
    INSERT INTO hospitals_fts(rowid, name, website) 
    VALUES (new.id, new.name, new.website);
END;

CREATE TRIGGER hospitals_fts_update AFTER UPDATE ON hospitals
BEGIN
    UPDATE hospitals_fts SET name = new.name, website = new.website 
    WHERE rowid = new.id;
END;

CREATE TRIGGER hospitals_fts_delete AFTER DELETE ON hospitals
BEGIN
    DELETE FROM hospitals_fts WHERE rowid = old.id;
END;
```

### 索引使用策略

#### 1. 查询优化
- **等值查询**: 使用单列索引
- **范围查询**: 使用时间相关索引
- **复合查询**: 使用复合索引
- **全文搜索**: 使用FTS5全文索引

#### 2. 索引维护
```sql
-- 分析查询性能
EXPLAIN QUERY PLAN SELECT * FROM hospitals WHERE name LIKE '%协和%';

-- 重建索引
REINDEX;

-- 更新统计信息
ANALYZE;
```

## 性能优化策略

### 1. 查询优化

#### 分页查询优化
```sql
-- 传统的LIMIT/OFFSET（性能较差）
SELECT * FROM hospitals ORDER BY id LIMIT 20 OFFSET 1000;

-- 游标分页（性能更好）
SELECT * FROM hospitals WHERE id > 1000 ORDER BY id LIMIT 20;
```

#### 层级查询优化
```sql
-- 获取广东省所有医院（使用连接查询）
SELECT h.* FROM hospitals h
JOIN districts d ON h.district_id = d.id
JOIN cities c ON d.city_id = c.id
JOIN provinces p ON c.province_id = p.id
WHERE p.name = '广东省';

-- 优化版本（预查询父级ID）
WITH province_ids AS (
    SELECT id FROM provinces WHERE name = '广东省'
),
city_ids AS (
    SELECT c.id FROM cities c 
    JOIN province_ids p ON c.province_id = p.id
),
district_ids AS (
    SELECT d.id FROM districts d 
    JOIN city_ids c ON d.city_id = c.id
)
SELECT h.* FROM hospitals h
JOIN district_ids d ON h.district_id = d.id;
```

### 2. 缓存策略

#### 查询结果缓存
```python
# 使用Redis缓存常用查询结果
CACHE_KEYS = {
    'provinces': 'cache:provinces',
    'cities:{province_id}': 'cache:cities:{province_id}',
    'districts:{city_id}': 'cache:districts:{city_id}',
    'hospitals:{district_id}': 'cache:hospitals:{district_id}'
}
```

#### 缓存失效策略
- **TTL设置**: 省份/城市数据24小时，区县/医院数据12小时
- **主动失效**: 数据更新时主动删除相关缓存
- **LRU淘汰**: 内存不足时淘汰最久未使用的缓存

### 3. 写入优化

#### 批量插入
```sql
-- 批量插入医院数据
BEGIN TRANSACTION;
INSERT INTO hospitals (district_id, name, website, llm_confidence) VALUES
(1001, '医院1', 'http://hospital1.com', 0.95),
(1001, '医院2', 'http://hospital2.com', 0.92),
(1001, '医院3', 'http://hospital3.com', 0.88);
COMMIT;
```

#### UPSERT操作
```sql
-- 插入或更新医院信息
INSERT INTO hospitals (district_id, name, website, llm_confidence, updated_at)
VALUES (1001, '医院名称', 'http://hospital.com', 0.95, datetime('now'))
ON CONFLICT(id) DO UPDATE SET
    name = excluded.name,
    website = excluded.website,
    llm_confidence = excluded.llm_confidence,
    updated_at = excluded.updated_at;
```

## 数据迁移和版本管理

### 数据库版本控制

#### 1. 迁移脚本管理
```sql
-- 版本 1.0.0: 初始表结构
-- migrations/V1.0.0_create_tables.sql

-- 版本 1.1.0: 添加医院网站字段
-- migrations/V1.1.0_add_hospital_website.sql
ALTER TABLE hospitals ADD COLUMN website TEXT;

-- 版本 1.2.0: 添加全文搜索
-- migrations/V1.2.0_add_fulltext_search.sql
CREATE VIRTUAL TABLE hospitals_fts USING fts5(name, website);
```

#### 2. 迁移执行器
```python
class DatabaseMigrator:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.current_version = self._get_current_version()
        
    def migrate_to_target(self, target_version: str):
        """迁移到目标版本"""
        migrations = self._get_migrations(self.current_version, target_version)
        for migration in migrations:
            self._execute_migration(migration)
            self._update_version(migration.version)
```

### 数据备份和恢复

#### 1. 备份策略
```bash
#!/bin/bash
# 备份脚本
BACKUP_DIR="/backup/hospital-scanner"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/hospital_scanner_${DATE}.db"

# 创建备份
sqlite3 data/hospital_scanner.db ".backup ${BACKUP_FILE}"

# 压缩备份
gzip "${BACKUP_FILE}"

# 清理7天前的备份
find ${BACKUP_DIR} -name "*.db.gz" -mtime +7 -delete
```

#### 2. 恢复脚本
```bash
#!/bin/bash
# 恢复脚本
BACKUP_FILE=$1

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <backup_file>"
    exit 1
fi

# 解压备份
gunzip -c "${BACKUP_FILE}" > data/hospital_scanner_restored.db

# 验证数据库
sqlite3 data/hospital_scanner_restored.db "PRAGMA integrity_check;"

# 替换原数据库（生产环境请谨慎操作）
mv data/hospital_scanner.db data/hospital_scanner_backup.db
mv data/hospital_scanner_restored.db data/hospital_scanner.db
```

## 监控和维护

### 1. 性能监控

#### 关键指标
- **查询性能**: 平均响应时间、慢查询数量
- **数据库大小**: 表大小、索引大小、空闲空间
- **并发性能**: 同时连接数、锁等待时间

#### 监控查询
```sql
-- 查看表大小
SELECT 
    name as table_name,
    SUM(pgsize) as size_bytes
FROM dbstat 
WHERE name IN ('provinces', 'cities', 'districts', 'hospitals', 'tasks')
GROUP BY name;

-- 查看索引使用情况
SELECT 
    name as index_name,
    tbl_name as table_name,
    sql
FROM sqlite_master 
WHERE type = 'index';

-- 查看数据库统计信息
PRAGMA page_count;
PRAGMA page_size;
PRAGMA freelist_count;
```

### 2. 维护任务

#### 自动清理
```sql
-- 清理旧的完成任务（保留最近30天）
DELETE FROM tasks 
WHERE status IN ('SUCCEEDED', 'FAILED', 'CANCELLED') 
  AND created_at < datetime('now', '-30 days');

-- 清理孤立的医院记录（如果区县被删除）
DELETE FROM hospitals 
WHERE district_id NOT IN (SELECT id FROM districts);

-- 重建碎片化的索引
REINDEX;
```

#### 数据一致性检查
```sql
-- 检查外键完整性
PRAGMA foreign_key_check;

-- 检查重复数据
SELECT province_id, name, COUNT(*) as count
FROM cities
GROUP BY province_id, name
HAVING COUNT(*) > 1;

-- 检查层级关系完整性
SELECT h.id, h.name
FROM hospitals h
LEFT JOIN districts d ON h.district_id = d.id
WHERE d.id IS NULL;
```

## 数据安全和权限

### 1. 数据加密

#### 敏感数据处理
```sql
-- 创建加密的医院信息表（如果需要）
CREATE TABLE hospitals_encrypted (
    id INTEGER PRIMARY KEY,
    district_id INTEGER NOT NULL,
    name_encrypted BLOB NOT NULL,
    website_encrypted BLOB,
    llm_confidence REAL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (district_id) REFERENCES districts(id)
);
```

#### 透明数据加密（TDE）
```python
# 使用SQLCipher进行透明加密
import sqlite3

# 连接到加密数据库
conn = sqlite3.connect('hospital_scanner_encrypted.db')
conn.execute('PRAGMA key = "encryption-password"')
conn.execute('PRAGMA cipher_page_size = 4096')
```

### 2. 访问控制

#### 只读用户
```sql
-- 创建只读视图
CREATE VIEW v_hospitals_readonly AS
SELECT h.id, h.name, h.website, h.llm_confidence,
       d.name as district_name, c.name as city_name, p.name as province_name
FROM hospitals h
JOIN districts d ON h.district_id = d.id
JOIN cities c ON d.city_id = c.id
JOIN provinces p ON c.province_id = p.id;
```

### 3. 审计日志

#### 操作审计
```sql
-- 创建审计日志表
CREATE TABLE audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    table_name TEXT NOT NULL,
    operation TEXT NOT NULL,  -- INSERT, UPDATE, DELETE
    record_id INTEGER,
    old_values TEXT,          -- JSON格式
    new_values TEXT,          -- JSON格式
    user_id TEXT,
    timestamp TEXT NOT NULL DEFAULT (datetime('now'))
);

-- 创建审计触发器
CREATE TRIGGER hospitals_audit_insert
AFTER INSERT ON hospitals
BEGIN
    INSERT INTO audit_log (table_name, operation, record_id, new_values, user_id)
    VALUES ('hospitals', 'INSERT', new.id, 
            json_object('name', new.name, 'website', new.website), 
            current_user);
END;
```

## 扩展性设计

### 1. 分库分表

#### 按省份分表
```sql
-- 为每个省份创建独立的医院表
CREATE TABLE hospitals_beijing AS SELECT * FROM hospitals WHERE 1=0;
CREATE TABLE hospitals_shanghai AS SELECT * FROM hospitals WHERE 1=0;
-- ...
```

#### 按时间分表
```sql
-- 按年份分表的医院表
CREATE TABLE hospitals_2023 AS SELECT * FROM hospitals WHERE date(created_at) >= '2023-01-01';
CREATE TABLE hospitals_2024 AS SELECT * FROM hospitals WHERE date(created_at) >= '2024-01-01';
```

### 2. 读写分离

#### 主从配置
```python
# 读写分离配置
DATABASE_CONFIG = {
    'master': {
        'path': 'data/hospital_scanner.db',
        'mode': 'readwrite'
    },
    'slave': {
        'path': 'data/hospital_scanner_slave.db',
        'mode': 'readonly'
    }
}
```

### 3. 数据分区

#### 医院表分区
```sql
-- 按创建时间分区（SQLite不支持原生分区，可通过表分区模拟）
CREATE TABLE hospitals_2023_q1 AS SELECT * FROM hospitals WHERE date(created_at) BETWEEN '2023-01-01' AND '2023-03-31';
CREATE TABLE hospitals_2023_q2 AS SELECT * FROM hospitals WHERE date(created_at) BETWEEN '2023-04-01' AND '2023-06-30';
-- ...
```

## 最佳实践

### 1. 开发规范
- 始终使用参数化查询防止SQL注入
- 合理使用事务确保数据一致性
- 及时提交事务避免长时间锁定
- 使用适当的索引优化查询性能

### 2. 运维规范
- 定期备份数据库文件
- 监控系统性能指标
- 定期清理历史数据
- 及时更新统计信息

### 3. 安全规范
- 敏感数据加密存储
- 实施访问权限控制
- 记录审计日志
- 定期进行安全检查

## 总结

本数据库设计充分考虑了医院层级数据的特点和业务需求，通过合理的表结构设计、索引策略和性能优化，能够有效支持百万级医院数据的高效存储和查询。同时，通过完善的备份、监控和安全机制，确保系统的稳定性和数据的安全性。

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
医院层级扫查微服务 - 数据库层
"""

import sqlite3
import asyncio
import logging
from datetime import datetime
from typing import Optional, Dict, Any
import json
import os

logger = logging.getLogger(__name__)

# 数据库配置
DB_PATH = "data/hospital_scanner_new.db"

class Database:
    """数据库管理类"""
    
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        # 确保数据库目录存在
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        # 同步初始化数据库表
        self._init_tables_sync()
        
    def _init_tables_sync(self):
        """同步初始化数据库表"""
        try:
            import sqlite3
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 创建任务表
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS tasks (
                        task_id TEXT PRIMARY KEY,
                        hospital_name TEXT NOT NULL,
                        query TEXT,
                        status TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL,
                        result TEXT,
                        error_message TEXT,
                        task_type TEXT DEFAULT 'hospital'
                    )
                """)

                # 添加task_type字段（如果不存在）
                try:
                    cursor.execute("ALTER TABLE tasks ADD COLUMN task_type TEXT DEFAULT 'hospital'")
                    logger.info("Added task_type column to tasks table")
                except Exception as e:
                    # 字段可能已存在，忽略错误
                    logger.debug(f"task_type column may already exist: {e}")
                
                # 创建医院信息表
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS hospital_info (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        task_id TEXT NOT NULL,
                        hospital_name TEXT NOT NULL,
                        hospital_level TEXT,
                        address TEXT,
                        phone TEXT,
                        website TEXT,
                        beds_count INTEGER,
                        departments_info TEXT,
                        staff_structure TEXT,
                        created_at TEXT NOT NULL,
                        FOREIGN KEY (task_id) REFERENCES tasks (task_id)
                    )
                """)
                
                conn.commit()
        except Exception as e:
            print(f"初始化数据库表失败: {e}")
            
    async def init_db(self):
        """初始化数据库"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 创建任务表
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS tasks (
                        task_id TEXT PRIMARY KEY,
                        hospital_name TEXT NOT NULL,
                        query TEXT,
                        status TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL,
                        result TEXT,
                        error_message TEXT,
                        task_type TEXT DEFAULT 'hospital'
                    )
                """)

                # 添加task_type字段（如果不存在）
                try:
                    cursor.execute("ALTER TABLE tasks ADD COLUMN task_type TEXT DEFAULT 'hospital'")
                    logger.info("Added task_type column to tasks table")
                except Exception as e:
                    # 字段可能已存在，忽略错误
                    logger.debug(f"task_type column may already exist: {e}")
                
                # 创建医院信息表
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS hospital_info (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        task_id TEXT NOT NULL,
                        hospital_name TEXT NOT NULL,
                        level TEXT,
                        address TEXT,
                        phone TEXT,
                        departments TEXT,
                        beds_count INTEGER,
                        staff_count INTEGER,
                        specializations TEXT,
                        created_at TEXT NOT NULL,
                        FOREIGN KEY (task_id) REFERENCES tasks (task_id)
                    )
                """)
                
                # 创建省份表
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS provinces (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT UNIQUE NOT NULL,
                        code TEXT UNIQUE,
                        cities_count INTEGER DEFAULT 0,
                        hospitals_count INTEGER DEFAULT 0,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL
                    )
                """)
                
                # 创建城市表
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS cities (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        code TEXT UNIQUE,
                        province_id INTEGER,
                        districts_count INTEGER DEFAULT 0,
                        hospitals_count INTEGER DEFAULT 0,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL,
                        FOREIGN KEY (province_id) REFERENCES provinces (id)
                    )
                """)
                
                # 创建区县表
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS districts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        code TEXT UNIQUE,
                        city_id INTEGER,
                        hospitals_count INTEGER DEFAULT 0,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL,
                        FOREIGN KEY (city_id) REFERENCES cities (id)
                    )
                """)
                
                # 创建医院表
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS hospitals (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        level TEXT,
                        district_id INTEGER,
                        address TEXT,
                        phone TEXT,
                        beds_count INTEGER,
                        staff_count INTEGER,
                        departments TEXT,
                        specializations TEXT,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL,
                        FOREIGN KEY (district_id) REFERENCES districts (id)
                    )
                """)
                
                # 创建索引
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_created_at ON tasks(created_at)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_hospital_info_task_id ON hospital_info(task_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_provinces_name ON provinces(name)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_cities_province_id ON cities(province_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_cities_name ON cities(name)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_districts_city_id ON districts(city_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_districts_name ON districts(name)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_hospitals_district_id ON hospitals(district_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_hospitals_name ON hospitals(name)")
                
                conn.commit()
                logger.info("数据库初始化完成")
                
        except Exception as e:
            logger.error(f"数据库初始化失败: {e}")
            raise
    
    async def create_task(self, task_id: str, hospital_name: str, query: str, status: str, task_type: str = "hospital") -> bool:
        """创建任务"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                now = datetime.now().isoformat()

                cursor.execute("""
                    INSERT INTO tasks (task_id, hospital_name, query, status, created_at, updated_at, task_type)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (task_id, hospital_name, query, status, now, now, task_type))

                conn.commit()
                logger.info(f"创建任务成功: {task_id} (type: {task_type})")
                return True
                
        except Exception as e:
            logger.error(f"创建任务失败: {e}")
            return False
    
    async def update_task_status(self, task_id: str, status: str, error_message: Optional[str] = None) -> bool:
        """更新任务状态"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                now = datetime.now().isoformat()
                
                if error_message:
                    cursor.execute("""
                        UPDATE tasks 
                        SET status = ?, updated_at = ?, error_message = ?
                        WHERE task_id = ?
                    """, (status, now, error_message, task_id))
                else:
                    cursor.execute("""
                        UPDATE tasks 
                        SET status = ?, updated_at = ?
                        WHERE task_id = ?
                    """, (status, now, task_id))
                
                conn.commit()
                return cursor.rowcount > 0
                
        except Exception as e:
            logger.error(f"更新任务状态失败: {e}")
            return False
    
    async def save_task_result(self, task_id: str, result: Dict[str, Any]) -> bool:
        """保存任务结果"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                now = datetime.now().isoformat()
                
                result_json = json.dumps(result, ensure_ascii=False, default=str)
                
                cursor.execute("""
                    UPDATE tasks 
                    SET result = ?, updated_at = ?
                    WHERE task_id = ?
                """, (result_json, now, task_id))
                
                conn.commit()
                logger.info(f"保存任务结果成功: {task_id}")
                return True
                
        except Exception as e:
            logger.error(f"保存任务结果失败: {e}")
            return False
    
    async def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务信息"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("SELECT * FROM tasks WHERE task_id = ?", (task_id,))
                row = cursor.fetchone()
                
                if row:
                    columns = [description[0] for description in cursor.description]
                    return dict(zip(columns, row))
                
                return None
                
        except Exception as e:
            logger.error(f"获取任务信息失败: {e}")
            return None
    
    async def get_task_result(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务结果"""
        try:
            task = await self.get_task(task_id)
            if task and task.get('result'):
                return json.loads(task['result'])
            return None
            
        except Exception as e:
            logger.error(f"获取任务结果失败: {e}")
            return None
    
    async def list_tasks(self, limit: int = 100) -> list:
        """获取任务列表"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT * FROM tasks 
                    ORDER BY created_at DESC 
                    LIMIT ?
                """, (limit,))
                
                rows = cursor.fetchall()
                columns = [description[0] for description in cursor.description]
                
                return [dict(zip(columns, row)) for row in rows]
                
        except Exception as e:
            logger.error(f"获取任务列表失败: {e}")
            return []
    
    async def save_hospital_info(self, task_id: str, hospital_info: Dict[str, Any]) -> bool:
        """保存医院信息"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                now = datetime.now().isoformat()
                
                cursor.execute("""
                    INSERT INTO hospital_info 
                    (task_id, hospital_name, level, address, phone, departments, 
                     beds_count, staff_count, specializations, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    task_id,
                    hospital_info.get('hospital_name', ''),
                    hospital_info.get('level', ''),
                    hospital_info.get('address', ''),
                    hospital_info.get('phone', ''),
                    json.dumps(hospital_info.get('departments', []), ensure_ascii=False),
                    hospital_info.get('beds_count', 0),
                    hospital_info.get('staff_count', 0),
                    json.dumps(hospital_info.get('specializations', []), ensure_ascii=False),
                    now
                ))
                
                conn.commit()
                logger.info(f"保存医院信息成功: {task_id}")
                return True
                
        except Exception as e:
            logger.error(f"保存医院信息失败: {e}")
            return False

    # 省份数据操作
    async def create_province(self, name: str, code: str = None) -> int:
        """创建省份"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                now = datetime.now().isoformat()
                
                cursor.execute("""
                    INSERT INTO provinces (name, code, created_at, updated_at)
                    VALUES (?, ?, ?, ?)
                """, (name, code, now, now))
                
                province_id = cursor.lastrowid
                conn.commit()
                logger.info(f"创建省份成功: {name} (ID: {province_id})")
                return province_id
                
        except Exception as e:
            logger.error(f"创建省份失败: {e}")
            return 0

    async def get_province_by_name(self, province_name: str):
        """根据省份名称获取省份信息"""
        try:
            logger.info(f"🔍 查询省份: {province_name}")
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute(
                    "SELECT * FROM provinces WHERE name = ? LIMIT 1",
                    (province_name,)
                )

                result = cursor.fetchone()
                logger.info(f"📊 查询省份结果: {'找到' if result else '未找到'} {province_name}")

                if result:
                    logger.info(f"✅ 省份信息: ID={result['id']}, 名称={result['name']}")
                    return dict(result)
                else:
                    logger.info(f"❌ 省份不存在: {province_name}")
                    return None

        except Exception as e:
            logger.error(f"根据名称获取省份信息失败: {e}")
            return None

    async def get_province_by_id(self, province_id: int):
        """根据省份ID获取省份信息"""
        try:
            logger.info(f"🔍 查询省份ID: {province_id}")
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute(
                    "SELECT * FROM provinces WHERE id = ? LIMIT 1",
                    (province_id,)
                )

                result = cursor.fetchone()
                logger.info(f"📊 查询省份结果: {'找到' if result else '未找到'} ID={province_id}")

                if result:
                    logger.info(f"✅ 省份信息: ID={result['id']}, 名称={result['name']}")
                    return dict(result)
                else:
                    logger.info(f"❌ 省份不存在: ID={province_id}")
                    return None

        except Exception as e:
            logger.error(f"根据ID获取省份信息失败: {e}")
            return None

    async def get_provinces(self, page: int = 1, page_size: int = 20) -> tuple:
        """获取省份列表（分页）"""
        try:
            # 处理边界值
            if page < 1:
                page = 1
            if page_size < 1:
                page_size = 20
            if page_size > 1000:  # 限制最大页面大小
                page_size = 1000
                
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 获取总数
                cursor.execute("SELECT COUNT(*) FROM provinces")
                total = cursor.fetchone()[0]
                
                # 计算有效页面数
                total_pages = (total + page_size - 1) // page_size if total > 0 else 1
                if page > total_pages and total > 0:
                    page = total_pages
                
                # 获取分页数据
                offset = (page - 1) * page_size
                cursor.execute("""
                    SELECT * FROM provinces 
                    ORDER BY name 
                    LIMIT ? OFFSET ?
                """, (page_size, offset))
                
                rows = cursor.fetchall()
                columns = [description[0] for description in cursor.description]
                items = [dict(zip(columns, row)) for row in rows]
                
                return items, total
                
        except Exception as e:
            logger.error(f"获取省份列表失败: {e}")
            return [], 0

    # 城市数据操作
    async def create_city(self, name: str, province_id: int, code: str = None) -> int:
        """创建城市"""
        try:
            logger.info(f"🏙️ 开始创建城市: {name} (省份ID: {province_id})")
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                now = datetime.now().isoformat()

                cursor.execute("""
                    INSERT INTO cities (name, code, province_id, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (name, code, province_id, now, now))

                city_id = cursor.lastrowid
                conn.commit()
                logger.info(f"✅ 创建城市成功: {name} (ID: {city_id}, 省份ID: {province_id})")
                return city_id

        except Exception as e:
            logger.error(f"❌ 创建城市失败: {name}, 错误: {e}")
            return 0

    async def get_city_by_name(self, city_name: str):
        """根据城市名称获取城市信息"""
        try:
            logger.info(f"🔍 查询城市: {city_name}")
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute(
                    "SELECT * FROM cities WHERE name = ? LIMIT 1",
                    (city_name,)
                )

                result = cursor.fetchone()
                logger.info(f"📊 查询城市结果: {'找到' if result else '未找到'} {city_name}")

                if result:
                    logger.info(f"✅ 城市信息: ID={result['id']}, 名称={result['name']}, 省份ID={result['province_id']}")
                    return dict(result)
                else:
                    logger.info(f"❌ 城市不存在: {city_name}")
                    return None

        except Exception as e:
            logger.error(f"根据名称获取城市信息失败: {e}")
            return None

    async def get_city_by_id(self, city_id: int):
        """根据城市ID获取城市信息"""
        try:
            logger.info(f"🔍 查询城市ID: {city_id}")
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute(
                    "SELECT * FROM cities WHERE id = ? LIMIT 1",
                    (city_id,)
                )

                result = cursor.fetchone()
                logger.info(f"📊 查询城市结果: {'找到' if result else '未找到'} ID={city_id}")

                if result:
                    logger.info(f"✅ 城市信息: ID={result['id']}, 名称={result['name']}, 省份ID={result['province_id']}")
                    return dict(result)
                else:
                    logger.info(f"❌ 城市不存在: ID={city_id}")
                    return None

        except Exception as e:
            logger.error(f"根据ID获取城市信息失败: {e}")
            return None

    async def get_cities(self, province_id: int = None, page: int = 1, page_size: int = 20) -> tuple:
        """获取城市列表"""
        try:
            # 处理边界值
            if page < 1:
                page = 1
            if page_size < 1:
                page_size = 20
            if page_size > 1000:  # 限制最大页面大小
                page_size = 1000
                
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                if province_id:
                    # 获取指定省份的城市
                    cursor.execute("SELECT COUNT(*) FROM cities WHERE province_id = ?", (province_id,))
                    total = cursor.fetchone()[0]
                    
                    # 计算有效页面数
                    total_pages = (total + page_size - 1) // page_size if total > 0 else 1
                    if page > total_pages and total > 0:
                        page = total_pages
                    
                    offset = (page - 1) * page_size
                    cursor.execute("""
                        SELECT * FROM cities 
                        WHERE province_id = ? 
                        ORDER BY name 
                        LIMIT ? OFFSET ?
                    """, (province_id, page_size, offset))
                else:
                    # 获取所有城市
                    cursor.execute("SELECT COUNT(*) FROM cities")
                    total = cursor.fetchone()[0]
                    
                    # 计算有效页面数
                    total_pages = (total + page_size - 1) // page_size if total > 0 else 1
                    if page > total_pages and total > 0:
                        page = total_pages
                    
                    offset = (page - 1) * page_size
                    cursor.execute("""
                        SELECT * FROM cities 
                        ORDER BY name 
                        LIMIT ? OFFSET ?
                    """, (page_size, offset))
                
                rows = cursor.fetchall()
                columns = [description[0] for description in cursor.description]
                items = [dict(zip(columns, row)) for row in rows]
                
                return items, total
                
        except Exception as e:
            logger.error(f"获取城市列表失败: {e}")
            return [], 0

    # 区县数据操作
    async def create_district(self, name: str, city_id: int, code: str = None) -> int:
        """创建区县"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                now = datetime.now().isoformat()
                
                cursor.execute("""
                    INSERT INTO districts (name, code, city_id, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (name, code, city_id, now, now))
                
                district_id = cursor.lastrowid
                conn.commit()
                logger.info(f"创建区县成功: {name} (ID: {district_id})")
                return district_id
                
        except Exception as e:
            logger.error(f"创建区县失败: {e}")
            return 0

    async def get_district_by_name(self, district_name: str):
        """根据区县名称获取区县信息（全局查询，可能返回多个同名区县）"""
        try:
            logger.info(f"🔍 查询区县: {district_name}")
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute(
                    "SELECT * FROM districts WHERE name = ? ORDER BY id LIMIT 1",
                    (district_name,)
                )

                result = cursor.fetchone()
                logger.info(f"📊 查询区县结果: {'找到' if result else '未找到'} {district_name}")

                if result:
                    logger.info(f"✅ 区县信息: ID={result['id']}, 名称={result['name']}, 城市ID={result['city_id']}")
                    return dict(result)
                else:
                    logger.info(f"❌ 区县不存在: {district_name}")
                    return None

        except Exception as e:
            logger.error(f"根据名称获取区县信息失败: {e}")
            return None

    async def get_district_by_name_and_city(self, district_name: str, city_id: int):
        """根据区县名称和城市ID获取区县信息（精确查询）"""
        try:
            logger.info(f"🔍 精确查询区县: {district_name} (城市ID: {city_id})")
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                cursor.execute(
                    "SELECT * FROM districts WHERE name = ? AND city_id = ? LIMIT 1",
                    (district_name, city_id)
                )

                result = cursor.fetchone()
                logger.info(f"📊 精确查询区县结果: {'找到' if result else '未找到'} {district_name} (城市ID: {city_id})")

                if result:
                    logger.info(f"✅ 区县信息: ID={result['id']}, 名称={result['name']}, 城市ID={result['city_id']}")
                    return dict(result)
                else:
                    logger.info(f"❌ 区县不存在: {district_name} (城市ID: {city_id})")
                    return None

        except Exception as e:
            logger.error(f"❌ 精确查询区县失败: {e}")
            return None

    async def get_districts(self, city_id: int = None, page: int = 1, page_size: int = 20) -> tuple:
        """获取区县列表"""
        try:
            # 处理边界值
            if page < 1:
                page = 1
            if page_size < 1:
                page_size = 20
            if page_size > 1000:  # 限制最大页面大小
                page_size = 1000
                
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                if city_id:
                    # 获取指定城市的区县
                    cursor.execute("SELECT COUNT(*) FROM districts WHERE city_id = ?", (city_id,))
                    total = cursor.fetchone()[0]
                    
                    # 计算有效页面数
                    total_pages = (total + page_size - 1) // page_size if total > 0 else 1
                    if page > total_pages and total > 0:
                        page = total_pages
                    
                    offset = (page - 1) * page_size
                    cursor.execute("""
                        SELECT * FROM districts 
                        WHERE city_id = ? 
                        ORDER BY name 
                        LIMIT ? OFFSET ?
                    """, (city_id, page_size, offset))
                else:
                    # 获取所有区县
                    cursor.execute("SELECT COUNT(*) FROM districts")
                    total = cursor.fetchone()[0]
                    
                    # 计算有效页面数
                    total_pages = (total + page_size - 1) // page_size if total > 0 else 1
                    if page > total_pages and total > 0:
                        page = total_pages
                    
                    offset = (page - 1) * page_size
                    cursor.execute("""
                        SELECT * FROM districts 
                        ORDER BY name 
                        LIMIT ? OFFSET ?
                    """, (page_size, offset))
                
                rows = cursor.fetchall()
                columns = [description[0] for description in cursor.description]
                items = [dict(zip(columns, row)) for row in rows]
                
                return items, total
                
        except Exception as e:
            logger.error(f"获取区县列表失败: {e}")
            return [], 0

    # 医院数据操作
    async def create_hospital(self, name: str, district_id: int = None, level: str = None,
                            address: str = None, phone: str = None, beds_count: int = None,
                            staff_count: int = None, departments: list = None,
                            specializations: list = None, website: str = None) -> int:
        """创建医院"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                now = datetime.now().isoformat()

                cursor.execute("""
                    INSERT INTO hospitals
                    (name, level, district_id, address, phone, beds_count, staff_count,
                     departments, specializations, website, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    name, level, district_id, address, phone, beds_count, staff_count,
                    json.dumps(departments or [], ensure_ascii=False),
                    json.dumps(specializations or [], ensure_ascii=False),
                    website, now, now
                ))
                
                hospital_id = cursor.lastrowid
                conn.commit()
                logger.info(f"创建医院成功: {name} (ID: {hospital_id})")
                return hospital_id
                
        except Exception as e:
            logger.error(f"创建医院失败: {e}")
            return 0

    async def get_hospitals(self, district_id: int = None, page: int = 1, page_size: int = 20) -> tuple:
        """获取医院列表"""
        try:
            # 处理边界值
            if page < 1:
                page = 1
            if page_size < 1:
                page_size = 20
            if page_size > 1000:  # 限制最大页面大小
                page_size = 1000
                
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                if district_id:
                    # 获取指定区县的医院
                    cursor.execute("SELECT COUNT(*) FROM hospitals WHERE district_id = ?", (district_id,))
                    total = cursor.fetchone()[0]
                    
                    # 计算有效页面数
                    total_pages = (total + page_size - 1) // page_size if total > 0 else 1
                    if page > total_pages and total > 0:
                        page = total_pages
                    
                    offset = (page - 1) * page_size
                    cursor.execute("""
                        SELECT * FROM hospitals 
                        WHERE district_id = ? 
                        ORDER BY name 
                        LIMIT ? OFFSET ?
                    """, (district_id, page_size, offset))
                else:
                    # 获取所有医院
                    cursor.execute("SELECT COUNT(*) FROM hospitals")
                    total = cursor.fetchone()[0]
                    
                    # 计算有效页面数
                    total_pages = (total + page_size - 1) // page_size if total > 0 else 1
                    if page > total_pages and total > 0:
                        page = total_pages
                    
                    offset = (page - 1) * page_size
                    cursor.execute("""
                        SELECT * FROM hospitals 
                        ORDER BY name 
                        LIMIT ? OFFSET ?
                    """, (page_size, offset))
                
                rows = cursor.fetchall()
                columns = [description[0] for description in cursor.description]
                items = [dict(zip(columns, row)) for row in rows]
                
                return items, total
                
        except Exception as e:
            logger.error(f"获取医院列表失败: {e}")
            return [], 0

    async def search_hospitals(self, query: str, limit: int = 20) -> list:
        """搜索医院"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute("""
                    SELECT * FROM hospitals
                    WHERE name LIKE ?
                    ORDER BY name
                    LIMIT ?
                """, (f"%{query}%", limit))

                rows = cursor.fetchall()
                columns = [description[0] for description in cursor.description]
                items = [dict(zip(columns, row)) for row in rows]

                return items

        except Exception as e:
            logger.error(f"搜索医院失败: {e}")
            return []

    async def get_hospital_by_name_and_district(self, hospital_name: str, district_id: int) -> dict:
        """根据医院名称和区县ID获取医院信息"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute("""
                    SELECT * FROM hospitals
                    WHERE name = ? AND district_id = ?
                    LIMIT 1
                """, (hospital_name, district_id))

                row = cursor.fetchone()
                if row:
                    columns = [description[0] for description in cursor.description]
                    return dict(zip(columns, row))
                else:
                    return None

        except Exception as e:
            logger.error(f"根据名称和区县查询医院失败: {e}")
            return None

    async def update_hospital(self, hospital_id: int, name: str = None, level: str = None,
                            address: str = None, phone: str = None, beds_count: int = None,
                            staff_count: int = None, departments: list = None,
                            specializations: list = None, website: str = None) -> bool:
        """更新医院信息"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # 构建更新字段列表
                update_fields = []
                update_values = []

                if name is not None:
                    update_fields.append("name = ?")
                    update_values.append(name)
                if level is not None:
                    update_fields.append("level = ?")
                    update_values.append(level)
                if address is not None:
                    update_fields.append("address = ?")
                    update_values.append(address)
                if phone is not None:
                    update_fields.append("phone = ?")
                    update_values.append(phone)
                if beds_count is not None:
                    update_fields.append("beds_count = ?")
                    update_values.append(beds_count)
                if staff_count is not None:
                    update_fields.append("staff_count = ?")
                    update_values.append(staff_count)
                if departments is not None:
                    update_fields.append("departments = ?")
                    update_values.append(json.dumps(departments, ensure_ascii=False))
                if specializations is not None:
                    update_fields.append("specializations = ?")
                    update_values.append(json.dumps(specializations, ensure_ascii=False))
                if website is not None:
                    update_fields.append("website = ?")
                    update_values.append(website)

                if not update_fields:
                    # 没有需要更新的字段
                    return True

                # 添加updated_at字段
                update_fields.append("updated_at = CURRENT_TIMESTAMP")

                # 添加hospital_id到值列表
                update_values.append(hospital_id)

                # 构建并执行更新语句
                update_sql = f"""
                    UPDATE hospitals
                    SET {', '.join(update_fields)}
                    WHERE id = ?
                """

                cursor.execute(update_sql, update_values)
                conn.commit()

                return cursor.rowcount > 0

        except Exception as e:
            logger.error(f"更新医院信息失败: {e}")
            return False

    async def get_task_info(self, task_id: str) -> dict:
        """获取任务基本信息"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                cursor.execute("""
                    SELECT task_id, hospital_name, query, status, created_at, updated_at, result, error_message
                    FROM tasks
                    WHERE task_id = ?
                """, (task_id,))

                row = cursor.fetchone()
                if row:
                    columns = [description[0] for description in cursor.description]
                    task_info = dict(zip(columns, row))

                    # 如果有结果，尝试解析JSON
                    if task_info.get('result'):
                        try:
                            import json
                            task_info['result'] = json.loads(task_info['result'])
                        except json.JSONDecodeError:
                            pass

                    return task_info

                return None

        except Exception as e:
            logger.error(f"获取任务信息失败: {e}")
            return None

    async def clear_all_tasks(self) -> bool:
        """删除所有任务记录"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # 删除所有任务记录
                cursor.execute("DELETE FROM tasks")

                # 重置自增ID（如果有的话）
                cursor.execute("DELETE FROM sqlite_sequence WHERE name='tasks'")

                conn.commit()
                logger.info("成功删除所有任务记录")
                return True

        except Exception as e:
            logger.error(f"删除所有任务失败: {e}")
            return False

    async def delete_completed_task(self, task_id: str) -> bool:
        """删除已完成的任务记录"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # 先删除相关的医院信息记录（如果有外键关系）
                cursor.execute("DELETE FROM hospital_info WHERE task_id = ?", (task_id,))

                # 删除任务记录（只删除已完成的任务）
                cursor.execute("""
                    DELETE FROM tasks
                    WHERE task_id = ? AND status IN ('completed', 'failed')
                """, (task_id,))

                deleted_count = cursor.rowcount
                conn.commit()

                if deleted_count > 0:
                    logger.info(f"✅ 已删除完成的任务记录: {task_id}")
                    return True
                else:
                    logger.warning(f"⚠️ 任务未找到或未完成，无法删除: {task_id}")
                    return False

        except Exception as e:
            logger.error(f"❌ 删除完成任务记录失败: {e}")
            return False

    async def cleanup_completed_tasks(self, older_than_hours: int = 1) -> int:
        """清理指定时间前已完成的任务"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # 计算时间边界
                cutoff_time = datetime.now().timestamp() - (older_than_hours * 3600)
                cutoff_datetime = datetime.fromtimestamp(cutoff_time).isoformat()

                # 先删除相关的医院信息记录
                cursor.execute("""
                    DELETE FROM hospital_info
                    WHERE task_id IN (
                        SELECT task_id FROM tasks
                        WHERE status IN ('completed', 'failed')
                        AND created_at < ?
                    )
                """, (cutoff_datetime,))

                # 删除完成的任务记录
                cursor.execute("""
                    DELETE FROM tasks
                    WHERE status IN ('completed', 'failed')
                    AND created_at < ?
                """, (cutoff_datetime,))

                deleted_count = cursor.rowcount
                conn.commit()

                logger.info(f"✅ 已清理 {deleted_count} 个完成的任务记录（{older_than_hours}小时前）")
                return deleted_count

        except Exception as e:
            logger.error(f"❌ 清理完成任务记录失败: {e}")
            return 0

    async def clear_all_tables_data(self) -> bool:
        """清空所有表的数据，保留表结构"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()

                # 获取所有表名
                cursor.execute("""
                    SELECT name FROM sqlite_master
                    WHERE type='table' AND name NOT LIKE 'sqlite_%'
                """)
                tables = [row[0] for row in cursor.fetchall()]

                logger.info(f"开始清空数据库表: {tables}")

                # 按依赖关系顺序清空表（先清空有外键的表）
                tables_order = [
                    'hospital_info',  # 依赖于 tasks
                    'hospitals',      # 依赖于 districts
                    'districts',      # 依赖于 cities
                    'cities',         # 依赖于 provinces
                    'provinces',      # 无外键依赖
                    'tasks'           # 无外键依赖
                ]

                # 按顺序清空存在的表
                for table_name in tables_order:
                    if table_name in tables:
                        cursor.execute(f"DELETE FROM {table_name}")
                        affected_rows = cursor.rowcount
                        logger.info(f"已清空表 {table_name}，删除了 {affected_rows} 行数据")

                # 重置自增ID
                for table_name in tables:
                    cursor.execute(f"DELETE FROM sqlite_sequence WHERE name='{table_name}'")

                conn.commit()

                logger.info("所有数据库表数据清空完成，表结构保留")
                return True

        except Exception as e:
            logger.error(f"清空数据库失败: {e}")
            return False

# 全局数据库实例
_db_instance = None

async def get_db() -> Database:
    """获取数据库实例"""
    global _db_instance
    if _db_instance is None:
        _db_instance = Database()
    return _db_instance

async def init_db():
    """初始化数据库"""
    db = await get_db()
    await db.init_db()
    return db

# 清空数据库的方法
async def clear_all_data():
    """清空所有表的数据，保留表结构"""
    db = await get_db()
    return await db.clear_all_tables_data()

# 清空所有任务的方法
async def clear_all_tasks():
    """删除所有任务记录"""
    db = await get_db()
    return await db.clear_all_tasks()
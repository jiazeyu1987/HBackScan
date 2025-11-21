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
DB_PATH = "data/hospital_scanner.db"

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
                        error_message TEXT
                    )
                """)
                
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
                        error_message TEXT
                    )
                """)
                
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
    
    async def create_task(self, task_id: str, hospital_name: str, query: str, status: str) -> bool:
        """创建任务"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                now = datetime.now().isoformat()
                
                cursor.execute("""
                    INSERT INTO tasks (task_id, hospital_name, query, status, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (task_id, hospital_name, query, status, now, now))
                
                conn.commit()
                logger.info(f"创建任务成功: {task_id}")
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
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                now = datetime.now().isoformat()
                
                cursor.execute("""
                    INSERT INTO cities (name, code, province_id, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (name, code, province_id, now, now))
                
                city_id = cursor.lastrowid
                conn.commit()
                logger.info(f"创建城市成功: {name} (ID: {city_id})")
                return city_id
                
        except Exception as e:
            logger.error(f"创建城市失败: {e}")
            return 0

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
                            specializations: list = None) -> int:
        """创建医院"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                now = datetime.now().isoformat()
                
                cursor.execute("""
                    INSERT INTO hospitals 
                    (name, level, district_id, address, phone, beds_count, staff_count, 
                     departments, specializations, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    name, level, district_id, address, phone, beds_count, staff_count,
                    json.dumps(departments or [], ensure_ascii=False),
                    json.dumps(specializations or [], ensure_ascii=False),
                    now, now
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
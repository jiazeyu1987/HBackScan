import sqlite3
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import os
from contextlib import contextmanager

# 确保数据目录存在
os.makedirs("data", exist_ok=True)
os.makedirs("logs", exist_ok=True)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/ai_debug.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class DatabaseManager:
    """SQLite连接管理器"""
    
    def __init__(self, db_path: str = "data/hospitals.db"):
        self.db_path = db_path
        self._ensure_data_directory()
        
    def _ensure_data_directory(self):
        """确保数据目录存在"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
    
    @contextmanager
    def get_connection(self):
        """获取数据库连接的上下文管理器"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # 允许通过列名访问
        conn.execute("PRAGMA foreign_keys = ON")  # 启用外键约束
        
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"数据库操作失败: {e}")
            raise
        finally:
            conn.close()


class Database:
    def __init__(self, db_path: str = "data/hospitals.db"):
        self.db_path = db_path
        self.db_manager = DatabaseManager(db_path)
        self.init_database()
    

    
    def init_database(self):
        """初始化数据库表"""
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            # 创建省份表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS province (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    code TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 创建城市表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS city (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    province_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    code TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (province_id) REFERENCES province(id),
                    UNIQUE(province_id, name)
                )
            ''')
            
            # 创建区县表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS district (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    city_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    code TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (city_id) REFERENCES city(id),
                    UNIQUE(city_id, name)
                )
            ''')
            
            # 创建医院表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS hospital (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    district_id INTEGER NOT NULL,
                    name TEXT NOT NULL,
                    website TEXT,
                    llm_confidence REAL,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (district_id) REFERENCES district(id),
                    UNIQUE(district_id, name)
                )
            ''')
            
            # 创建任务表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS task (
                    id TEXT PRIMARY KEY,
                    scope TEXT NOT NULL,
                    status TEXT NOT NULL,
                    progress REAL DEFAULT 0.0,
                    error TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            logger.info("数据库初始化完成")

    def upsert_province(self, name: str, code: Optional[str] = None) -> int:
        """插入或更新省份"""
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            try:
                cursor.execute('''
                    INSERT INTO province (name, code, updated_at)
                    VALUES (?, ?, ?)
                    ON CONFLICT(name) DO UPDATE SET
                        code = COALESCE(excluded.code, province.code),
                        updated_at = CURRENT_TIMESTAMP
                ''', (name, code, datetime.now()))
                
                province_id = cursor.lastrowid
                if province_id == 0:  # 更新操作
                    cursor.execute('SELECT id FROM province WHERE name = ?', (name,))
                    province_id = cursor.fetchone()['id']
                
                logger.info(f"Upsert province: {name} (ID: {province_id})")
                return province_id
            except Exception as e:
                logger.error(f"Error upserting province {name}: {e}")
                raise
    
    def upsert_city(self, province_id: int, name: str, code: Optional[str] = None) -> int:
        """插入或更新城市"""
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            try:
                cursor.execute('''
                    INSERT INTO city (province_id, name, code, updated_at)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(province_id, name) DO UPDATE SET
                        code = COALESCE(excluded.code, city.code),
                        updated_at = CURRENT_TIMESTAMP
                ''', (province_id, name, code, datetime.now()))
                
                city_id = cursor.lastrowid
                if city_id == 0:  # 更新操作
                    cursor.execute('SELECT id FROM city WHERE province_id = ? AND name = ?', 
                                 (province_id, name))
                    city_id = cursor.fetchone()['id']
                
                logger.info(f"Upsert city: {name} (Province: {province_id}, ID: {city_id})")
                return city_id
            except Exception as e:
                logger.error(f"Error upserting city {name}: {e}")
                raise
    
    def upsert_district(self, city_id: int, name: str, code: Optional[str] = None) -> int:
        """插入或更新区县"""
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            try:
                cursor.execute('''
                    INSERT INTO district (city_id, name, code, updated_at)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(city_id, name) DO UPDATE SET
                        code = COALESCE(excluded.code, district.code),
                        updated_at = CURRENT_TIMESTAMP
                ''', (city_id, name, code, datetime.now()))
                
                district_id = cursor.lastrowid
                if district_id == 0:  # 更新操作
                    cursor.execute('SELECT id FROM district WHERE city_id = ? AND name = ?', 
                                 (city_id, name))
                    district_id = cursor.fetchone()['id']
                
                logger.info(f"Upsert district: {name} (City: {city_id}, ID: {district_id})")
                return district_id
            except Exception as e:
                logger.error(f"Error upserting district {name}: {e}")
                raise
    
    def upsert_hospital(self, district_id: int, name: str, website: Optional[str] = None, 
                       confidence: Optional[float] = None) -> int:
        """插入或更新医院"""
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            try:
                cursor.execute('''
                    INSERT INTO hospital (district_id, name, website, llm_confidence, updated_at)
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(district_id, name) DO UPDATE SET
                        website = COALESCE(excluded.website, hospital.website),
                        llm_confidence = COALESCE(excluded.llm_confidence, hospital.llm_confidence),
                        updated_at = CURRENT_TIMESTAMP
                ''', (district_id, name, website, confidence, datetime.now()))
                
                hospital_id = cursor.lastrowid
                if hospital_id == 0:  # 更新操作
                    cursor.execute('SELECT id FROM hospital WHERE district_id = ? AND name = ?', 
                                 (district_id, name))
                    hospital_id = cursor.fetchone()['id']
                
                logger.info(f"Upsert hospital: {name} (District: {district_id}, ID: {hospital_id})")
                return hospital_id
            except Exception as e:
                logger.error(f"Error upserting hospital {name}: {e}")
                raise
    
    def get_all_provinces(self, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """获取所有省份（分页）"""
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            # 获取总数
            cursor.execute('SELECT COUNT(*) as total FROM province')
            total = cursor.fetchone()['total']
            
            # 获取分页数据
            offset = (page - 1) * page_size
            cursor.execute('''
                SELECT * FROM province 
                ORDER BY name 
                LIMIT ? OFFSET ?
            ''', (page_size, offset))
            
            items = [dict(row) for row in cursor.fetchall()]
            
            return {
                'items': items,
                'total': total,
                'page': page,
                'page_size': page_size,
                'total_pages': (total + page_size - 1) // page_size
            }
    
    def get_cities_by_province(self, province: str, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """根据省名或省code获取城市"""
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            # 先尝试按省名查找
            cursor.execute('SELECT id FROM province WHERE name = ? OR code = ?', (province, province))
            province_row = cursor.fetchone()
            
            if not province_row:
                return {
                    'items': [],
                    'total': 0,
                    'page': page,
                    'page_size': page_size,
                    'total_pages': 0
                }
            
            province_id = province_row['id']
            
            # 获取总数
            cursor.execute('SELECT COUNT(*) as total FROM city WHERE province_id = ?', (province_id,))
            total = cursor.fetchone()['total']
            
            # 获取分页数据
            offset = (page - 1) * page_size
            cursor.execute('''
                SELECT * FROM city 
                WHERE province_id = ? 
                ORDER BY name 
                LIMIT ? OFFSET ?
            ''', (province_id, page_size, offset))
            
            items = [dict(row) for row in cursor.fetchall()]
            
            return {
                'items': items,
                'total': total,
                'page': page,
                'page_size': page_size,
                'total_pages': (total + page_size - 1) // page_size
            }
    
    def get_districts_by_city(self, city: str, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """根据市名或市code获取区县"""
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            # 先尝试按市名查找
            cursor.execute('SELECT id FROM city WHERE name = ? OR code = ?', (city, city))
            city_row = cursor.fetchone()
            
            if not city_row:
                return {
                    'items': [],
                    'total': 0,
                    'page': page,
                    'page_size': page_size,
                    'total_pages': 0
                }
            
            city_id = city_row['id']
            
            # 获取总数
            cursor.execute('SELECT COUNT(*) as total FROM district WHERE city_id = ?', (city_id,))
            total = cursor.fetchone()['total']
            
            # 获取分页数据
            offset = (page - 1) * page_size
            cursor.execute('''
                SELECT * FROM district 
                WHERE city_id = ? 
                ORDER BY name 
                LIMIT ? OFFSET ?
            ''', (city_id, page_size, offset))
            
            items = [dict(row) for row in cursor.fetchall()]
            
            return {
                'items': items,
                'total': total,
                'page': page,
                'page_size': page_size,
                'total_pages': (total + page_size - 1) // page_size
            }
    
    def get_hospitals_by_district(self, district: str, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """根据区县名或区县code获取医院"""
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            # 先尝试按区县名查找
            cursor.execute('SELECT id FROM district WHERE name = ? OR code = ?', (district, district))
            district_row = cursor.fetchone()
            
            if not district_row:
                return {
                    'items': [],
                    'total': 0,
                    'page': page,
                    'page_size': page_size,
                    'total_pages': 0
                }
            
            district_id = district_row['id']
            
            # 获取总数
            cursor.execute('SELECT COUNT(*) as total FROM hospital WHERE district_id = ?', (district_id,))
            total = cursor.fetchone()['total']
            
            # 获取分页数据
            offset = (page - 1) * page_size
            cursor.execute('''
                SELECT * FROM hospital 
                WHERE district_id = ? 
                ORDER BY name 
                LIMIT ? OFFSET ?
            ''', (district_id, page_size, offset))
            
            items = [dict(row) for row in cursor.fetchall()]
            
            return {
                'items': items,
                'total': total,
                'page': page,
                'page_size': page_size,
                'total_pages': (total + page_size - 1) // page_size
            }
    
    def search_hospitals(self, query: str, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """模糊搜索医院"""
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            # 获取总数
            cursor.execute('SELECT COUNT(*) as total FROM hospital WHERE name LIKE ?', (f'%{query}%',))
            total = cursor.fetchone()['total']
            
            # 获取分页数据
            offset = (page - 1) * page_size
            cursor.execute('''
                SELECT h.*, d.name as district_name, c.name as city_name, p.name as province_name
                FROM hospital h
                JOIN district d ON h.district_id = d.id
                JOIN city c ON d.city_id = c.id
                JOIN province p ON c.province_id = p.id
                WHERE h.name LIKE ? 
                ORDER BY h.name 
                LIMIT ? OFFSET ?
            ''', (f'%{query}%', page_size, offset))
            
            items = [dict(row) for row in cursor.fetchall()]
            
            return {
                'items': items,
                'total': total,
                'page': page,
                'page_size': page_size,
                'total_pages': (total + page_size - 1) // page_size
            }
    
    # ==================== 完整CRUD操作 ====================
    
    # 省份CRUD
    def create_province(self, name: str, code: str = None) -> int:
        """创建省份"""
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO province (name, code, updated_at)
                VALUES (?, ?, ?)
            ''', (name, code, datetime.now()))
            return cursor.lastrowid
    
    def get_province(self, province_id: int = None, name: str = None, code: str = None) -> Optional[Dict]:
        """获取省份信息"""
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            if province_id:
                cursor.execute('SELECT * FROM province WHERE id = ?', (province_id,))
            elif name:
                cursor.execute('SELECT * FROM province WHERE name = ?', (name,))
            elif code:
                cursor.execute('SELECT * FROM province WHERE code = ?', (code,))
            else:
                return None
            
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def update_province(self, province_id: int, **kwargs) -> bool:
        """更新省份信息"""
        if not kwargs:
            return False
            
        set_clause = ', '.join([f"{k} = ?" for k in kwargs.keys()])
        values = list(kwargs.values()) + [datetime.now(), province_id]
        
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f'''
                UPDATE province SET {set_clause}, updated_at = ?
                WHERE id = ?
            ''', values)
            return cursor.rowcount > 0
    
    def delete_province(self, province_id: int) -> bool:
        """删除省份"""
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM province WHERE id = ?', (province_id,))
            return cursor.rowcount > 0
    
    # 城市CRUD
    def create_city(self, province_id: int, name: str, code: str = None) -> int:
        """创建城市"""
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO city (province_id, name, code, updated_at)
                VALUES (?, ?, ?, ?)
            ''', (province_id, name, code, datetime.now()))
            return cursor.lastrowid
    
    def get_city(self, city_id: int = None, province_id: int = None, name: str = None, code: str = None) -> Optional[Dict]:
        """获取城市信息"""
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            if city_id:
                cursor.execute('SELECT * FROM city WHERE id = ?', (city_id,))
            elif province_id and name:
                cursor.execute('SELECT * FROM city WHERE province_id = ? AND name = ?', (province_id, name))
            elif code:
                cursor.execute('SELECT * FROM city WHERE code = ?', (code,))
            else:
                return None
            
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def update_city(self, city_id: int, **kwargs) -> bool:
        """更新城市信息"""
        if not kwargs:
            return False
            
        set_clause = ', '.join([f"{k} = ?" for k in kwargs.keys()])
        values = list(kwargs.values()) + [datetime.now(), city_id]
        
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f'''
                UPDATE city SET {set_clause}, updated_at = ?
                WHERE id = ?
            ''', values)
            return cursor.rowcount > 0
    
    def delete_city(self, city_id: int) -> bool:
        """删除城市"""
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM city WHERE id = ?', (city_id,))
            return cursor.rowcount > 0
    
    # 区县CRUD
    def create_district(self, city_id: int, name: str, code: str = None) -> int:
        """创建区县"""
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO district (city_id, name, code, updated_at)
                VALUES (?, ?, ?, ?)
            ''', (city_id, name, code, datetime.now()))
            return cursor.lastrowid
    
    def get_district(self, district_id: int = None, city_id: int = None, name: str = None, code: str = None) -> Optional[Dict]:
        """获取区县信息"""
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            if district_id:
                cursor.execute('SELECT * FROM district WHERE id = ?', (district_id,))
            elif city_id and name:
                cursor.execute('SELECT * FROM district WHERE city_id = ? AND name = ?', (city_id, name))
            elif code:
                cursor.execute('SELECT * FROM district WHERE code = ?', (code,))
            else:
                return None
            
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def update_district(self, district_id: int, **kwargs) -> bool:
        """更新区县信息"""
        if not kwargs:
            return False
            
        set_clause = ', '.join([f"{k} = ?" for k in kwargs.keys()])
        values = list(kwargs.values()) + [datetime.now(), district_id]
        
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f'''
                UPDATE district SET {set_clause}, updated_at = ?
                WHERE id = ?
            ''', values)
            return cursor.rowcount > 0
    
    def delete_district(self, district_id: int) -> bool:
        """删除区县"""
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM district WHERE id = ?', (district_id,))
            return cursor.rowcount > 0
    
    # 医院CRUD
    def create_hospital(self, district_id: int, name: str, website: str = None, llm_confidence: float = None) -> int:
        """创建医院"""
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO hospital (district_id, name, website, llm_confidence, updated_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (district_id, name, website, llm_confidence, datetime.now()))
            return cursor.lastrowid
    
    def get_hospital(self, hospital_id: int = None, district_id: int = None, name: str = None) -> Optional[Dict]:
        """获取医院信息"""
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            if hospital_id:
                cursor.execute('SELECT * FROM hospital WHERE id = ?', (hospital_id,))
            elif district_id and name:
                cursor.execute('SELECT * FROM hospital WHERE district_id = ? AND name = ?', (district_id, name))
            else:
                return None
            
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def update_hospital(self, hospital_id: int, **kwargs) -> bool:
        """更新医院信息"""
        if not kwargs:
            return False
            
        set_clause = ', '.join([f"{k} = ?" for k in kwargs.keys()])
        values = list(kwargs.values()) + [datetime.now(), hospital_id]
        
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f'''
                UPDATE hospital SET {set_clause}, updated_at = ?
                WHERE id = ?
            ''', values)
            return cursor.rowcount > 0
    
    def delete_hospital(self, hospital_id: int) -> bool:
        """删除医院"""
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM hospital WHERE id = ?', (hospital_id,))
            return cursor.rowcount > 0
    
    # 任务CRUD
    def create_task(self, task_id: str, scope: str, status: str = "pending", progress: float = 0.0, error: str = None) -> bool:
        """创建任务"""
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO task (id, scope, status, progress, error, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (task_id, scope, status, progress, error, datetime.now()))
            return True
    
    def get_task(self, task_id: str) -> Optional[Dict]:
        """获取任务信息"""
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM task WHERE id = ?', (task_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def update_task(self, task_id: str, **kwargs) -> bool:
        """更新任务信息"""
        if not kwargs:
            return False
            
        set_clause = ', '.join([f"{k} = ?" for k in kwargs.keys()])
        values = list(kwargs.values()) + [datetime.now(), task_id]
        
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f'''
                UPDATE task SET {set_clause}, updated_at = ?
                WHERE id = ?
            ''', values)
            return cursor.rowcount > 0
    
    def delete_task(self, task_id: str) -> bool:
        """删除任务"""
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM task WHERE id = ?', (task_id,))
            return cursor.rowcount > 0
    
    # ==================== 增强查询方法 ====================
    
    def get_cities_by_province_id(self, province_id: int, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """根据省份ID查询城市"""
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            # 获取总数
            cursor.execute('SELECT COUNT(*) as total FROM city WHERE province_id = ?', (province_id,))
            total = cursor.fetchone()['total']
            
            # 获取分页数据
            offset = (page - 1) * page_size
            cursor.execute('''
                SELECT * FROM city 
                WHERE province_id = ? 
                ORDER BY name 
                LIMIT ? OFFSET ?
            ''', (province_id, page_size, offset))
            
            items = [dict(row) for row in cursor.fetchall()]
            
            return {
                'items': items,
                'total': total,
                'page': page,
                'page_size': page_size,
                'total_pages': (total + page_size - 1) // page_size
            }
    
    def get_districts_by_city_id(self, city_id: int, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """根据城市ID查询区县"""
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            # 获取总数
            cursor.execute('SELECT COUNT(*) as total FROM district WHERE city_id = ?', (city_id,))
            total = cursor.fetchone()['total']
            
            # 获取分页数据
            offset = (page - 1) * page_size
            cursor.execute('''
                SELECT * FROM district 
                WHERE city_id = ? 
                ORDER BY name 
                LIMIT ? OFFSET ?
            ''', (city_id, page_size, offset))
            
            items = [dict(row) for row in cursor.fetchall()]
            
            return {
                'items': items,
                'total': total,
                'page': page,
                'page_size': page_size,
                'total_pages': (total + page_size - 1) // page_size
            }
    
    def get_hospitals_by_district_id(self, district_id: int, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """根据区县ID查询医院"""
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            # 获取总数
            cursor.execute('SELECT COUNT(*) as total FROM hospital WHERE district_id = ?', (district_id,))
            total = cursor.fetchone()['total']
            
            # 获取分页数据
            offset = (page - 1) * page_size
            cursor.execute('''
                SELECT h.*, d.name as district_name, c.name as city_name, p.name as province_name
                FROM hospital h
                JOIN district d ON h.district_id = d.id
                JOIN city c ON d.city_id = c.id
                JOIN province p ON c.province_id = p.id
                WHERE h.district_id = ? 
                ORDER BY h.name 
                LIMIT ? OFFSET ?
            ''', (district_id, page_size, offset))
            
            items = [dict(row) for row in cursor.fetchall()]
            
            return {
                'items': items,
                'total': total,
                'page': page,
                'page_size': page_size,
                'total_pages': (total + page_size - 1) // page_size
            }
    
    def get_all_cities_detailed(self, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """获取所有城市（包含省份信息）"""
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            # 获取总数
            cursor.execute('SELECT COUNT(*) as total FROM city')
            total = cursor.fetchone()['total']
            
            # 获取分页数据
            offset = (page - 1) * page_size
            cursor.execute('''
                SELECT c.*, p.name as province_name, p.code as province_code
                FROM city c
                JOIN province p ON c.province_id = p.id
                ORDER BY p.name, c.name 
                LIMIT ? OFFSET ?
            ''', (page_size, offset))
            
            items = [dict(row) for row in cursor.fetchall()]
            
            return {
                'items': items,
                'total': total,
                'page': page,
                'page_size': page_size,
                'total_pages': (total + page_size - 1) // page_size
            }
    
    def get_all_districts_detailed(self, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """获取所有区县（包含城市和省份信息）"""
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            # 获取总数
            cursor.execute('SELECT COUNT(*) as total FROM district')
            total = cursor.fetchone()['total']
            
            # 获取分页数据
            offset = (page - 1) * page_size
            cursor.execute('''
                SELECT d.*, c.name as city_name, c.code as city_code, p.name as province_name, p.code as province_code
                FROM district d
                JOIN city c ON d.city_id = c.id
                JOIN province p ON c.province_id = p.id
                ORDER BY p.name, c.name, d.name 
                LIMIT ? OFFSET ?
            ''', (page_size, offset))
            
            items = [dict(row) for row in cursor.fetchall()]
            
            return {
                'items': items,
                'total': total,
                'page': page,
                'page_size': page_size,
                'total_pages': (total + page_size - 1) // page_size
            }
    
    def get_all_hospitals_detailed(self, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """获取所有医院（包含完整地理信息）"""
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            # 获取总数
            cursor.execute('SELECT COUNT(*) as total FROM hospital')
            total = cursor.fetchone()['total']
            
            # 获取分页数据
            offset = (page - 1) * page_size
            cursor.execute('''
                SELECT h.*, d.name as district_name, d.code as district_code, 
                       c.name as city_name, c.code as city_code,
                       p.name as province_name, p.code as province_code
                FROM hospital h
                JOIN district d ON h.district_id = d.id
                JOIN city c ON d.city_id = c.id
                JOIN province p ON c.province_id = p.id
                ORDER BY p.name, c.name, d.name, h.name 
                LIMIT ? OFFSET ?
            ''', (page_size, offset))
            
            items = [dict(row) for row in cursor.fetchall()]
            
            return {
                'items': items,
                'total': total,
                'page': page,
                'page_size': page_size,
                'total_pages': (total + page_size - 1) // page_size
            }
    
    def search_hospitals_detailed(self, query: str, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """医院模糊搜索（包含完整信息）"""
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            # 获取总数
            cursor.execute('SELECT COUNT(*) as total FROM hospital WHERE name LIKE ?', (f'%{query}%',))
            total = cursor.fetchone()['total']
            
            # 获取分页数据
            offset = (page - 1) * page_size
            cursor.execute('''
                SELECT h.*, d.name as district_name, d.code as district_code, 
                       c.name as city_name, c.code as city_code,
                       p.name as province_name, p.code as province_code
                FROM hospital h
                JOIN district d ON h.district_id = d.id
                JOIN city c ON d.city_id = c.id
                JOIN province p ON c.province_id = p.id
                WHERE h.name LIKE ? 
                ORDER BY h.name 
                LIMIT ? OFFSET ?
            ''', (f'%{query}%', page_size, offset))
            
            items = [dict(row) for row in cursor.fetchall()]
            
            return {
                'items': items,
                'total': total,
                'page': page,
                'page_size': page_size,
                'total_pages': (total + page_size - 1) // page_size
            }
    
    # ==================== 统计信息 ====================
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取数据库统计信息"""
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            stats = {}
            
            # 统计各表记录数
            tables = ['province', 'city', 'district', 'hospital', 'task']
            for table in tables:
                cursor.execute(f'SELECT COUNT(*) FROM {table}')
                stats[f'{table}_count'] = cursor.fetchone()[0]
            
            # 统计每个省份的城市数量
            cursor.execute('''
                SELECT p.name, COUNT(c.id) as city_count
                FROM province p
                LEFT JOIN city c ON p.id = c.province_id
                GROUP BY p.id, p.name
                ORDER BY city_count DESC
            ''')
            stats['provinces_with_cities'] = [dict(row) for row in cursor.fetchall()]
            
            # 统计每个城市的区县数量
            cursor.execute('''
                SELECT c.name as city_name, p.name as province_name, COUNT(d.id) as district_count
                FROM city c
                JOIN province p ON c.province_id = p.id
                LEFT JOIN district d ON c.id = d.city_id
                GROUP BY c.id, c.name, p.name
                ORDER BY district_count DESC
                LIMIT 10
            ''')
            stats['cities_with_districts'] = [dict(row) for row in cursor.fetchall()]
            
            # 统计每个区县的医院数量
            cursor.execute('''
                SELECT d.name as district_name, c.name as city_name, p.name as province_name, COUNT(h.id) as hospital_count
                FROM district d
                JOIN city c ON d.city_id = c.id
                JOIN province p ON c.province_id = p.id
                LEFT JOIN hospital h ON d.id = h.district_id
                GROUP BY d.id, d.name, c.name, p.name
                ORDER BY hospital_count DESC
                LIMIT 10
            ''')
            stats['districts_with_hospitals'] = [dict(row) for row in cursor.fetchall()]
            
            # 医院数量最多的前10个区县
            cursor.execute('''
                SELECT d.name as district_name, c.name as city_name, p.name as province_name, COUNT(h.id) as hospital_count
                FROM district d
                JOIN city c ON d.city_id = c.id
                JOIN province p ON c.province_id = p.id
                LEFT JOIN hospital h ON d.id = h.district_id
                GROUP BY d.id, d.name, c.name, p.name
                HAVING COUNT(h.id) > 0
                ORDER BY hospital_count DESC
                LIMIT 10
            ''')
            stats['top_districts_by_hospitals'] = [dict(row) for row in cursor.fetchall()]
            
            return stats
    
    # ==================== 批量操作 ====================
    
    def batch_create_provinces(self, provinces: List[Dict]) -> List[int]:
        """批量创建省份"""
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            ids = []
            
            for province in provinces:
                cursor.execute('''
                    INSERT OR IGNORE INTO province (name, code, updated_at)
                    VALUES (?, ?, ?)
                ''', (province['name'], province.get('code'), datetime.now()))
                
                if cursor.rowcount > 0:
                    ids.append(cursor.lastrowid)
                else:
                    # 如果已存在，查询ID
                    cursor.execute('SELECT id FROM province WHERE name = ?', (province['name'],))
                    result = cursor.fetchone()
                    if result:
                        ids.append(result[0])
            
            return ids
    
    def batch_create_cities(self, cities: List[Dict]) -> List[int]:
        """批量创建城市"""
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            ids = []
            
            for city in cities:
                cursor.execute('''
                    INSERT OR IGNORE INTO city (province_id, name, code, updated_at)
                    VALUES (?, ?, ?, ?)
                ''', (city['province_id'], city['name'], city.get('code'), datetime.now()))
                
                if cursor.rowcount > 0:
                    ids.append(cursor.lastrowid)
                else:
                    # 如果已存在，查询ID
                    cursor.execute('''
                        SELECT id FROM city WHERE province_id = ? AND name = ?
                    ''', (city['province_id'], city['name']))
                    result = cursor.fetchone()
                    if result:
                        ids.append(result[0])
            
            return ids
    
    def batch_create_districts(self, districts: List[Dict]) -> List[int]:
        """批量创建区县"""
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            ids = []
            
            for district in districts:
                cursor.execute('''
                    INSERT OR IGNORE INTO district (city_id, name, code, updated_at)
                    VALUES (?, ?, ?, ?)
                ''', (district['city_id'], district['name'], district.get('code'), datetime.now()))
                
                if cursor.rowcount > 0:
                    ids.append(cursor.lastrowid)
                else:
                    # 如果已存在，查询ID
                    cursor.execute('''
                        SELECT id FROM district WHERE city_id = ? AND name = ?
                    ''', (district['city_id'], district['name']))
                    result = cursor.fetchone()
                    if result:
                        ids.append(result[0])
            
            return ids
    
    def batch_create_hospitals(self, hospitals: List[Dict]) -> List[int]:
        """批量创建医院"""
        with self.db_manager.get_connection() as conn:
            cursor = conn.cursor()
            ids = []
            
            for hospital in hospitals:
                cursor.execute('''
                    INSERT OR IGNORE INTO hospital (district_id, name, website, llm_confidence, updated_at)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    hospital['district_id'], 
                    hospital['name'], 
                    hospital.get('website'), 
                    hospital.get('llm_confidence'), 
                    datetime.now()
                ))
                
                if cursor.rowcount > 0:
                    ids.append(cursor.lastrowid)
                else:
                    # 如果已存在，查询ID
                    cursor.execute('''
                        SELECT id FROM hospital WHERE district_id = ? AND name = ?
                    ''', (hospital['district_id'], hospital['name']))
                    result = cursor.fetchone()
                    if result:
                        ids.append(result[0])
            
            return ids


# 全局数据库实例
db = Database()


# 使用示例
def main():
    """使用示例"""
    # 测试数据库操作
    print("=== 测试省份操作 ===")
    
    # 创建省份
    province_id = db.upsert_province("示例省份", "EX")
    print(f"创建省份ID: {province_id}")
    
    # 查询省份
    province = db.get_province(province_id)
    print(f"查询省份: {province}")
    
    print("\n=== 测试城市操作 ===")
    
    # 创建城市
    city_id = db.upsert_city(province_id, "深圳市", "SZ")
    print(f"创建城市ID: {city_id}")
    
    # 查询城市
    city = db.get_city(city_id)
    print(f"查询城市: {city}")
    
    print("\n=== 测试区县操作 ===")
    
    # 创建区县
    district_id = db.upsert_district(city_id, "南山区", "NS")
    print(f"创建区县ID: {district_id}")
    
    # 查询区县
    district = db.get_district(district_id)
    print(f"查询区县: {district}")
    
    print("\n=== 测试医院操作 ===")
    
    # 创建医院
    hospital_id = db.upsert_hospital(district_id, "深圳市人民医院", "http://www.sz-hospital.com", 0.95)
    print(f"创建医院ID: {hospital_id}")
    
    # 查询医院
    hospital = db.get_hospital(hospital_id)
    print(f"查询医院: {hospital}")
    
    print("\n=== 测试查询方法 ===")
    
    # 按省份查询城市
    cities_result = db.get_cities_by_province("示例省份")
    print(f"示例省份城市数量: {cities_result['total']}")
    
    # 按城市查询区县
    districts_result = db.get_districts_by_city("示例城市")
    print(f"示例城市区县数量: {districts_result['total']}")
    
    # 按区县查询医院
    hospitals_result = db.get_hospitals_by_district("示例区县")
    print(f"示例区县医院数量: {hospitals_result['total']}")
    
    # 搜索医院
    search_result = db.search_hospitals("人民医院")
    print(f"搜索'人民医院'结果: {search_result['total']}条")
    
    print("\n=== 测试统计信息 ===")
    
    # 显示统计信息
    stats = db.get_statistics()
    print(f"数据库统计: {stats}")
    
    print("\n=== 测试任务操作 ===")
    
    # 创建任务
    db.create_task("task_001", "scrape_guangdong_hospitals", "running", 0.5)
    
    # 查询任务
    task = db.get_task("task_001")
    print(f"任务信息: {task}")
    
    # 更新任务
    db.update_task("task_001", status="completed", progress=1.0)
    
    # 再次查询任务
    task = db.get_task("task_001")
    print(f"更新后任务信息: {task}")
    
    print("\n=== 数据库操作测试完成 ===")


if __name__ == "__main__":
    main()
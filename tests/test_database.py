import pytest
import sqlite3
import asyncio
from unittest.mock import Mock, AsyncMock, patch
import pytest_asyncio

# 假设从 db 模块导入
try:
    from db import DatabaseManager, init_db
except ImportError:
    # 如果模块结构不同，创建模拟类
    class DatabaseManager:
        def __init__(self, db_path: str):
            self.db_path = db_path
            
        async def get_connection(self):
            return sqlite3.connect(self.db_path)
            
        async def create_task(self, query: str, query_type: str):
            pass
            
        async def update_task_status(self, task_id: str, status: str):
            pass
            
        async def save_task_result(self, task_id: str, result: str):
            pass
            
        async def get_task(self, task_id: str):
            pass
            
        async def list_tasks(self, limit: int = 10, offset: int = 0):
            pass
            
        async def fuzzy_search(self, keyword: str, limit: int = 10):
            pass
    
    async def init_db(db_path: str):
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                query TEXT NOT NULL,
                query_type TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                result TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        conn.close()

@pytest.fixture
def db_manager():
    return DatabaseManager(":memory:")

@pytest.fixture
async def mock_db_connection():
    mock_conn = AsyncMock()
    mock_cursor = AsyncMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.execute.return_value = None
    mock_cursor.fetchall.return_value = []
    mock_cursor.fetchone.return_value = None
    return mock_conn, mock_cursor

class TestDatabaseManager:
    
    @pytest.mark.asyncio
    async def test_init_db(self, db_manager):
        """测试数据库初始化"""
        with patch('sqlite3.connect') as mock_connect:
            mock_conn = Mock()
            mock_connect.return_value = mock_conn
            
            await init_db("test.db")
            
            mock_connect.assert_called_once_with("test.db")
            mock_conn.commit.assert_called_once()
            mock_conn.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_connection(self, db_manager):
        """测试获取数据库连接"""
        with patch('sqlite3.connect') as mock_connect:
            mock_connect.return_value = sqlite3.connect(":memory:")
            
            conn = await db_manager.get_connection()
            
            assert conn is not None
            mock_connect.assert_called_once_with(":memory:")
    
    @pytest.mark.asyncio
    async def test_create_task_success(self, db_manager, mock_db_connection):
        """测试创建任务成功"""
        mock_conn, mock_cursor = mock_db_connection
        
        with patch.object(db_manager, 'get_connection', return_value=mock_conn):
            task_id = "test-task-123"
            query = "查询医院层级结构信息"
            query_type = "医院层级"
            
            await db_manager.create_task(query, query_type)
            
            mock_cursor.execute.assert_called_once()
            call_args = mock_cursor.execute.call_args[0]
            assert task_id in str(call_args)
            assert query in str(call_args)
            assert query_type in str(call_args)
            mock_conn.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_task_status(self, db_manager, mock_db_connection):
        """测试更新任务状态"""
        mock_conn, mock_cursor = mock_db_connection
        
        with patch.object(db_manager, 'get_connection', return_value=mock_conn):
            task_id = "test-task-123"
            new_status = "running"
            
            await db_manager.update_task_status(task_id, new_status)
            
            mock_cursor.execute.assert_called_once()
            call_args = mock_cursor.execute.call_args[0]
            assert task_id in str(call_args)
            assert new_status in str(call_args)
            mock_conn.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_save_task_result(self, db_manager, mock_db_connection):
        """测试保存任务结果"""
        mock_conn, mock_cursor = mock_db_connection
        
        with patch.object(db_manager, 'get_connection', return_value=mock_conn):
            task_id = "test-task-123"
            result = '{"hospitals": [{"name": "北京天坛医院"}]}'
            
            await db_manager.save_task_result(task_id, result)
            
            mock_cursor.execute.assert_called_once()
            call_args = mock_cursor.execute.call_args[0]
            assert task_id in str(call_args)
            assert result in str(call_args)
            mock_conn.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_task_found(self, db_manager, mock_db_connection):
        """测试获取任务成功"""
        mock_conn, mock_cursor = mock_db_connection
        expected_task = {
            'id': 'test-task-123',
            'query': '查询医院信息',
            'status': 'pending'
        }
        mock_cursor.fetchone.return_value = expected_task
        
        with patch.object(db_manager, 'get_connection', return_value=mock_conn):
            task = await db_manager.get_task('test-task-123')
            
            assert task == expected_task
            mock_cursor.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_task_not_found(self, db_manager, mock_db_connection):
        """测试获取不存在的任务"""
        mock_conn, mock_cursor = mock_db_connection
        mock_cursor.fetchone.return_value = None
        
        with patch.object(db_manager, 'get_connection', return_value=mock_conn):
            task = await db_manager.get_task('non-existent-task')
            
            assert task is None
            mock_cursor.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_list_tasks_with_pagination(self, db_manager, mock_db_connection):
        """测试分页列出任务"""
        mock_conn, mock_cursor = mock_db_connection
        expected_tasks = [
            {'id': 'task-1', 'query': '查询1', 'status': 'pending'},
            {'id': 'task-2', 'query': '查询2', 'status': 'running'}
        ]
        mock_cursor.fetchall.return_value = expected_tasks
        
        with patch.object(db_manager, 'get_connection', return_value=mock_conn):
            tasks = await db_manager.list_tasks(limit=10, offset=0)
            
            assert tasks == expected_tasks
            mock_cursor.execute.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_fuzzy_search_success(self, db_manager, mock_db_connection):
        """测试模糊搜索成功"""
        mock_conn, mock_cursor = mock_db_connection
        expected_results = [
            {'id': 'hospital-1', 'name': '北京天坛医院', 'address': '北京市东城区天坛路'},
            {'id': 'hospital-2', 'name': '天坛医院', 'address': '北京市东城区'}
        ]
        mock_cursor.fetchall.return_value = expected_results
        
        with patch.object(db_manager, 'get_connection', return_value=mock_conn):
            results = await db_manager.fuzzy_search("天坛医院")
            
            assert len(results) == 2
            assert "天坛医院" in str(results)
    
    @pytest.mark.asyncio
    async def test_fuzzy_search_empty_result(self, db_manager, mock_db_connection):
        """测试模糊搜索无结果"""
        mock_conn, mock_cursor = mock_db_connection
        mock_cursor.fetchall.return_value = []
        
        with patch.object(db_manager, 'get_connection', return_value=mock_conn):
            results = await db_manager.fuzzy_search("不存在的医院")
            
            assert results == []
    
    @pytest.mark.asyncio
    async def test_create_task_unique_constraint(self, db_manager, mock_db_connection):
        """测试唯一约束处理"""
        mock_conn, mock_cursor = mock_db_connection
        mock_cursor.execute.side_effect = sqlite3.IntegrityError("UNIQUE constraint failed")
        
        with patch.object(db_manager, 'get_connection', return_value=mock_conn):
            query = "查询医院层级结构信息"
            query_type = "医院层级"
            
            with pytest.raises(sqlite3.IntegrityError):
                await db_manager.create_task(query, query_type)
    
    @pytest.mark.asyncio
    async def test_get_connection_error_handling(self, db_manager):
        """测试数据库连接错误处理"""
        with patch('sqlite3.connect', side_effect=sqlite3.Error("连接失败")):
            with pytest.raises(sqlite3.Error):
                await db_manager.get_connection()
    
    @pytest.mark.asyncio
    async def test_list_tasks_default_pagination(self, db_manager, mock_db_connection):
        """测试默认分页参数"""
        mock_conn, mock_cursor = mock_db_connection
        
        with patch.object(db_manager, 'get_connection', return_value=mock_conn):
            await db_manager.list_tasks()
            
            # 验证默认参数
            call_args = mock_cursor.execute.call_args[0]
            assert "LIMIT 10" in str(call_args)
            assert "OFFSET 0" in str(call_args)
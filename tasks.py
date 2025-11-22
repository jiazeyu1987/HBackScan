#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
任务管理系统
实现异步任务调度、进度跟踪、层级数据刷新等功能
"""

import asyncio
import logging
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Callable, Any
import json
import traceback
import sys
import os

# 确保根目录在路径的最前面，优先导入
project_root = os.path.dirname(__file__)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 导入根目录的LLM客户端
try:
    from llm_client import DashScopeLLMClient as RootLLMClient
except ImportError as e:
    print(f"无法导入根目录DashScopeLLMClient: {e}")
    RootLLMClient = None

# 尝试从code目录导入LLM客户端（作为备选）
try:
    code_dir = os.path.join(os.path.dirname(__file__), 'code', 'hospital_scanner')
    if code_dir not in sys.path:
        sys.path.append(code_dir)
    from llm_client import LLMClient as CodeLLMClient
except ImportError:
    CodeLLMClient = None

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入数据库模块
try:
    from db import db
except ImportError:
    logger = logging.getLogger(__name__)
    logger.warning("无法导入数据库模块，任务将无法保存数据")


class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class ProgressTracker:
    """进度跟踪器"""
    
    def __init__(self, total_steps: int):
        self.total_steps = total_steps
        self.completed_steps = 0
        self.current_step = 0
        self.current_step_name = ""
        self.callbacks: List[Callable[[int, str], None]] = []
    
    def update_progress(self, step: int, step_name: str = ""):
        """更新进度"""
        self.current_step = step
        self.current_step_name = step_name
        progress = min(100, int((step / self.total_steps) * 100))
        
        for callback in self.callbacks:
            try:
                callback(progress, step_name)
            except Exception as e:
                logging.error(f"进度回调执行失败: {e}")
        
        logging.info(f"进度更新: {progress}% - {step_name}")
    
    def add_callback(self, callback: Callable[[int, str], None]):
        """添加进度回调"""
        self.callbacks.append(callback)
    
    def get_progress(self) -> tuple:
        """获取当前进度"""
        progress = min(100, int((self.current_step / self.total_steps) * 100))
        return progress, self.current_step_name


class LLMService:
    """LLM服务接口"""

    def __init__(self):
        """初始化LLM客户端"""
        try:
            # 使用根目录的DashScopeLLMClient
            self.llm_client = RootLLMClient(
                api_key=os.getenv('LLM_API_KEY', 'sk-96bb32e240ad40b195207a088d321b90'),
                model=os.getenv('LLM_MODEL', 'qwen-turbo')
            )
        except ValueError as e:
            # 如果LLM客户端初始化失败，记录警告但不阻止服务启动
            print(f"LLM客户端初始化警告: {e}")
            self.llm_client = None

    async def get_provinces(self) -> List[str]:
        """获取省份列表"""
        try:
            if not self.llm_client:
                # 如果LLM客户端不可用，返回一些基本的省份
                return ["北京市", "上海市", "广东省", "江苏省", "浙江省", "山东省", "河南省", "湖北省", "湖南省", "四川省"]

            # 使用DashScopeLLMClient获取省份列表
            result = self.llm_client.get_provinces()

            # 从结果中提取省份名称列表
            provinces = [item['name'] for item in result.get('items', [])]

            return provinces
        except Exception as e:
            print(f"获取省份列表失败: {e}")
            # 返回基本的省份列表作为备用
            return ["北京市", "上海市", "广东省", "江苏省", "浙江省"]

    async def get_cities(self, province: str) -> List[str]:
        """获取市级列表"""
        try:
            if not self.llm_client:
                # 如果LLM客户端不可用，返回一些基本的城市
                return [f"{province}市1", f"{province}市2", f"{province}市3"]

            # 使用LLM获取城市列表
            system_prompt = f"""你是一个专业的地理信息系统专家。请列出{province}的所有主要城市。

请严格按照JSON数组格式返回，例如：
["城市1", "城市2", "城市3"]

注意：
1. 只返回该省份的地级市、自治州、直辖市辖区
2. 使用完整的官方名称
3. 按照常用顺序排列
4. 不要包含任何其他文字，只要JSON数组"""

            user_prompt = f"请列出{province}的所有主要城市"

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]

            response = await self.llm_client._make_request(messages, max_tokens=500)

            if response:
                import json
                # 清理和解析响应（与get_provinces相同的逻辑）
                response = response.strip()
                if response.startswith('```json'):
                    response = response[7:]
                if response.startswith('```'):
                    response = response[3:]
                if response.endswith('```'):
                    response = response[:-3]
                response = response.strip()

                json_start = response.find('[')
                json_end = response.rfind(']') + 1

                if json_start != -1 and json_end != -1:
                    json_str = response[json_start:json_end]
                    cities = json.loads(json_str)
                    return cities if isinstance(cities, list) else []

            return []
        except Exception as e:
            print(f"获取城市列表失败: {e}")
            return [f"{province}市1", f"{province}市2"]

    async def get_districts(self, city: str) -> List[str]:
        """获取区县级列表"""
        try:
            if not self.llm_client:
                return [f"{city}区1", f"{city}区2", f"{city}区3"]

            system_prompt = f"""你是一个专业的地理信息系统专家。请列出{city}的所有区县。

请严格按照JSON数组格式返回，例如：
["区县1", "区县2", "区县3"]

注意：
1. 只返回该城市的市辖区、县、县级市
2. 使用完整的官方名称
3. 不要包含任何其他文字，只要JSON数组"""

            user_prompt = f"请列出{city}的所有区县"

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]

            response = await self.llm_client._make_request(messages, max_tokens=500)

            if response:
                import json
                # 清理和解析响应
                response = response.strip()
                if response.startswith('```json'):
                    response = response[7:]
                if response.startswith('```'):
                    response = response[3:]
                if response.endswith('```'):
                    response = response[:-3]
                response = response.strip()

                json_start = response.find('[')
                json_end = response.rfind(']') + 1

                if json_start != -1 and json_end != -1:
                    json_str = response[json_start:json_end]
                    districts = json.loads(json_str)
                    return districts if isinstance(districts, list) else []

            return []
        except Exception as e:
            print(f"获取区县列表失败: {e}")
            return [f"{city}区1", f"{city}区2"]

    async def get_hospitals(self, district: str) -> List[str]:
        """获取医院列表"""
        try:
            if not self.llm_client:
                return [f"{district}人民医院", f"{district}中心医院", f"{district}中医院"]

            system_prompt = f"""你是一个专业的医疗信息系统专家。请列出{district}的主要医院。

请严格按照JSON数组格式返回，例如：
["医院1", "医院2", "医院3"]

注意：
1. 只返回该区县的医院名称
2. 包括综合医院、专科医院、中医院等
3. 使用完整的官方名称
4. 不要包含任何其他文字，只要JSON数组"""

            user_prompt = f"请列出{district}的主要医院"

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]

            response = await self.llm_client._make_request(messages, max_tokens=500)

            if response:
                import json
                # 清理和解析响应
                response = response.strip()
                if response.startswith('```json'):
                    response = response[7:]
                if response.startswith('```'):
                    response = response[3:]
                if response.endswith('```'):
                    response = response[:-3]
                response = response.strip()

                json_start = response.find('[')
                json_end = response.rfind(']') + 1

                if json_start != -1 and json_end != -1:
                    json_str = response[json_start:json_end]
                    hospitals = json.loads(json_str)
                    return hospitals if isinstance(hospitals, list) else []

            return []
        except Exception as e:
            print(f"获取医院列表失败: {e}")
            return [f"{district}人民医院", f"{district}中心医院"]


class TaskManager:
    """任务管理器"""
    
    def __init__(self):
        self.llm_service = LLMService()
        self.semaphore = asyncio.Semaphore(5)  # 并发控制
        self.tasks: Dict[str, Dict] = {}
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        
        # 配置日志格式
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
    
    async def create_refresh_task(self, task_type: str, target: str = None) -> str:
        """
        创建数据刷新任务
        
        Args:
            task_type: 任务类型（"full"全量刷新，"province"指定省刷新）
            target: 目标（当task_type为"province"时指定省份名称）
        
        Returns:
            任务ID
        """
        task_id = f"task_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        self.tasks[task_id] = {
            "id": task_id,
            "type": task_type,
            "target": target,
            "status": TaskStatus.PENDING,
            "progress": 0,
            "current_step": "",
            "created_at": datetime.now(),
            "started_at": None,
            "completed_at": None,
            "error": None,
            "result": {}
        }
        
        self.logger.info(f"创建任务: {task_id}, 类型: {task_type}, 目标: {target}")
        return task_id
    
    async def start_task(self, task_id: str) -> bool:
        """
        启动任务
        
        Returns:
            是否成功启动
        """
        if task_id not in self.tasks:
            self.logger.error(f"任务不存在: {task_id}")
            return False
        
        task = self.tasks[task_id]
        if task["status"] != TaskStatus.PENDING:
            self.logger.warning(f"任务状态不正确: {task_id}, 状态: {task['status']}")
            return False
        
        task["status"] = TaskStatus.RUNNING
        task["started_at"] = datetime.now()
        
        self.logger.info(f"启动任务: {task_id}")
        
        # 异步执行任务
        asyncio.create_task(self._execute_refresh_task(task_id))
        return True
    
    async def _execute_refresh_task(self, task_id: str):
        """执行刷新任务的核心逻辑"""
        try:
            task = self.tasks[task_id]
            progress_tracker = ProgressTracker(100)
            progress_tracker.add_callback(lambda p, s: self._update_task_progress(task_id, p, s))
            
            if task["type"] == "full":
                await self._execute_full_refresh(task_id, progress_tracker)
            elif task["type"] == "province":
                await self._execute_province_refresh(task_id, progress_tracker, task["target"])
            else:
                raise ValueError(f"未知的任务类型: {task['type']}")
            
            # 任务完成
            self._complete_task(task_id, TaskStatus.SUCCEEDED)
            
        except Exception as e:
            self.logger.error(f"任务执行失败: {task_id}, 错误: {str(e)}")
            self.logger.error(f"错误详情: {traceback.format_exc()}")
            self._complete_task(task_id, TaskStatus.FAILED, str(e))
    
    async def _execute_full_refresh(self, task_id: str, progress_tracker: ProgressTracker):
        """执行全量刷新"""
        self.logger.info(f"开始全量刷新任务: {task_id}")
        
        # 步骤1: 获取省份列表
        progress_tracker.update_progress(5, "正在获取省份列表...")
        provinces = await self._safe_call_with_retry(
            self.llm_service.get_provinces,
            f"获取省份列表失败"
        )
        
        if not provinces:
            raise Exception("未能获取到省份列表")
        
        self.logger.info(f"获取到 {len(provinces)} 个省份: {provinces}")
        
        # 步骤2: 处理每个省份
        total_items = len(provinces)
        for idx, province in enumerate(provinces):
            progress = 10 + int((idx / total_items) * 80)
            progress_tracker.update_progress(progress, f"正在处理省份: {province}")
            
            await self._process_province(province, task_id)
        
        progress_tracker.update_progress(100, "全量刷新完成")
        self.logger.info(f"全量刷新任务完成: {task_id}")
    
    async def _execute_province_refresh(self, task_id: str, progress_tracker: ProgressTracker, target_province: str):
        """执行指定省刷新"""
        self.logger.info(f"开始省份刷新任务: {task_id}, 目标省份: {target_province}")
        
        # 步骤1: 验证省份
        progress_tracker.update_progress(5, f"正在验证省份: {target_province}")
        provinces = await self._safe_call_with_retry(
            self.llm_service.get_provinces,
            "获取省份列表失败"
        )
        
        if target_province not in provinces:
            raise Exception(f"指定的省份不存在: {target_province}")
        
        # 步骤2: 处理指定省份
        progress_tracker.update_progress(10, f"正在处理省份: {target_province}")
        await self._process_province(target_province, task_id)
        
        progress_tracker.update_progress(100, f"省份 {target_province} 刷新完成")
        self.logger.info(f"省份刷新任务完成: {task_id}")
    
    async def _process_province(self, province: str, task_id: str):
        """处理单个省份"""
        self.logger.info(f"开始处理省份: {province}")
        
        async with self.semaphore:
            # 获取市列表
            cities = await self._safe_call_with_retry(
                lambda: self.llm_service.get_cities(province),
                f"获取 {province} 的城市列表失败"
            )
            
            self.logger.info(f"{province} 包含 {len(cities)} 个城市")
            
            # 处理每个市
            for city in cities:
                await self._process_city(city, province, task_id)
    
    async def _process_city(self, city: str, province: str, task_id: str):
        """处理单个市"""
        async with self.semaphore:
            # 获取区县级列表
            districts = await self._safe_call_with_retry(
                lambda: self.llm_service.get_districts(city),
                f"获取 {city} 的区县列表失败"
            )
            
            self.logger.info(f"{city} 包含 {len(districts)} 个区县")
            
            # 处理每个区县
            for district in districts:
                await self._process_district(district, city, province, task_id)
    
    async def _process_district(self, district: str, city: str, province: str, task_id: str):
        """处理单个区县"""
        async with self.semaphore:
            # 获取医院列表
            hospitals = await self._safe_call_with_retry(
                lambda: self.llm_service.get_hospitals(district),
                f"获取 {district} 的医院列表失败"
            )
            
            self.logger.info(f"{district} 包含 {len(hospitals)} 个医院")
            
            # 保存结果
            await self._save_district_data(province, city, district, hospitals, task_id)
    
    async def _save_district_data(self, province: str, city: str, district: str, hospitals: List[str], task_id: str):
        """保存区县数据到数据库"""
        try:
            # 检查数据库模块是否可用
            if 'db' not in globals():
                self.logger.warning("数据库模块不可用，跳过数据保存")
                return
                
            # 保存省份
            province_id = db.upsert_province(province)
            
            # 保存城市
            city_id = db.upsert_city(province_id, city)
            
            # 保存区县
            district_id = db.upsert_district(city_id, district)
            
            # 保存医院
            for hospital_name in hospitals:
                try:
                    db.upsert_hospital(district_id, hospital_name)
                except Exception as e:
                    self.logger.warning(f"保存医院 {hospital_name} 失败: {e}")
            
            self.logger.debug(f"保存数据: {province} -> {city} -> {district} -> {len(hospitals)} 个医院")
            
            # 同时保存到任务结果中（用于监控）
            task = self.tasks[task_id]
            if "data" not in task["result"]:
                task["result"]["data"] = []
            
            task["result"]["data"].append({
                "province": province,
                "city": city,
                "district": district,
                "hospitals": hospitals,
                "hospital_count": len(hospitals),
                "timestamp": datetime.now().isoformat()
            })
            
        except Exception as e:
            self.logger.error(f"保存区县数据失败: {province} -> {city} -> {district}, 错误: {e}")
            # 不抛出异常，继续处理其他数据
    
    async def _safe_call_with_retry(self, func: Callable, error_msg: str, max_retries: int = 3):
        """安全调用函数，带重试机制"""
        for attempt in range(max_retries):
            try:
                result = await func()
                return result
            except Exception as e:
                if attempt < max_retries - 1:
                    self.logger.warning(f"{error_msg}，重试 {attempt + 1}/{max_retries}: {str(e)}")
                    await asyncio.sleep(2 ** attempt)  # 指数退避
                else:
                    self.logger.error(f"{error_msg}，重试失败: {str(e)}")
                    raise
    
    def _update_task_progress(self, task_id: str, progress: int, step_name: str):
        """更新任务进度"""
        if task_id in self.tasks:
            self.tasks[task_id]["progress"] = progress
            self.tasks[task_id]["current_step"] = step_name
    
    def _complete_task(self, task_id: str, status: TaskStatus, error: str = None):
        """完成任务"""
        if task_id in self.tasks:
            self.tasks[task_id]["status"] = status
            self.tasks[task_id]["completed_at"] = datetime.now()
            self.tasks[task_id]["error"] = error
            
            if status == TaskStatus.SUCCEEDED:
                self.tasks[task_id]["progress"] = 100
                self.logger.info(f"任务完成: {task_id}")
            else:
                self.logger.error(f"任务失败: {task_id}, 错误: {error}")
    
    def get_task_status(self, task_id: str) -> Optional[Dict]:
        """获取任务状态"""
        return self.tasks.get(task_id)
    
    def list_tasks(self, status: TaskStatus = None) -> List[Dict]:
        """列出任务"""
        tasks = list(self.tasks.values())
        if status:
            tasks = [task for task in tasks if task["status"] == status]
        return sorted(tasks, key=lambda x: x["created_at"], reverse=True)
    
    def get_active_tasks(self) -> List[str]:
        """获取活跃任务ID"""
        active_tasks = []
        for task_id, task in self.tasks.items():
            if task["status"] in [TaskStatus.PENDING, TaskStatus.RUNNING]:
                active_tasks.append(task_id)
        return active_tasks
    
    async def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        if task_id not in self.tasks:
            return False
        
        task = self.tasks[task_id]
        if task["status"] in [TaskStatus.PENDING, TaskStatus.RUNNING]:
            task["status"] = TaskStatus.FAILED
            task["completed_at"] = datetime.now()
            task["error"] = "用户取消"
            self.logger.info(f"任务已取消: {task_id}")
            return True
        
        return False
    
    async def cleanup_old_tasks(self, hours: int = 24):
        """清理旧任务"""
        cutoff_time = datetime.now().timestamp() - (hours * 3600)
        to_remove = []
        
        for task_id, task in self.tasks.items():
            if task["created_at"].timestamp() < cutoff_time:
                to_remove.append(task_id)
        
        for task_id in to_remove:
            del self.tasks[task_id]
            self.logger.info(f"清理旧任务: {task_id}")
        
        return len(to_remove)


# 使用示例和测试函数
async def demo_usage():
    """演示任务管理器的使用"""
    print("=== 任务管理系统演示 ===\n")
    
    # 创建任务管理器
    manager = TaskManager()
    
    # 演示1: 创建全量刷新任务
    print("1. 创建全量刷新任务")
    task_id = await manager.create_refresh_task("full")
    print(f"任务ID: {task_id}")
    
    # 启动任务
    print("启动任务...")
    await manager.start_task(task_id)
    
    # 监控任务进度
    for _ in range(50):  # 最多等待25秒
        task_status = manager.get_task_status(task_id)
        if task_status:
            status = task_status["status"]
            progress = task_status["progress"]
            current_step = task_status["current_step"]
            
            print(f"任务状态: {status}, 进度: {progress}%, 当前步骤: {current_step}")
            
            if status in [TaskStatus.SUCCEEDED, TaskStatus.FAILED]:
                break
        
        await asyncio.sleep(0.5)
    
    print("\n" + "="*50 + "\n")
    
    # 演示2: 创建指定省刷新任务
    print("2. 创建指定省刷新任务")
    province_task_id = await manager.create_refresh_task("province", "示例省份")
    print(f"任务ID: {province_task_id}")
    
    await manager.start_task(province_task_id)
    
    # 监控任务进度
    for _ in range(30):
        task_status = manager.get_task_status(province_task_id)
        if task_status:
            status = task_status["status"]
            progress = task_status["progress"]
            current_step = task_status["current_step"]
            
            print(f"任务状态: {status}, 进度: {progress}%, 当前步骤: {current_step}")
            
            if status in [TaskStatus.SUCCEEDED, TaskStatus.FAILED]:
                break
        
        await asyncio.sleep(0.5)
    
    # 显示所有任务
    print("\n3. 所有任务列表")
    all_tasks = manager.list_tasks()
    for task in all_tasks:
        print(f"任务: {task['id']}, 类型: {task['type']}, 状态: {task['status']}, 进度: {task['progress']}%")
    
    print("\n=== 演示完成 ===")


if __name__ == "__main__":
    # 运行演示
    asyncio.run(demo_usage())
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
医院扫描仪API使用示例
展示如何使用医院扫描仪微服务的各种API接口

主要功能：
1. 健康检查和基本信息获取
2. 数据查询接口（省市区医院）
3. 搜索功能
4. 任务管理接口
5. 统计数据接口
"""

import requests
import time
import json
from typing import Dict, List, Optional
from datetime import datetime


class HospitalScannerAPIClient:
    """医院扫描仪API客户端"""
    
    def __init__(self, base_url: str = "http://localhost:8000", timeout: int = 30):
        """
        初始化API客户端
        
        Args:
            base_url: API基础URL
            timeout: 请求超时时间（秒）
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict:
        """
        发送HTTP请求的通用方法
        
        Args:
            method: HTTP方法（GET, POST, DELETE等）
            endpoint: API端点（不包含基础URL）
            **kwargs: 其他请求参数
            
        Returns:
            解析后的JSON响应
            
        Raises:
            requests.RequestException: 请求失败时抛出
        """
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = self.session.request(method, url, timeout=self.timeout, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"请求失败: {method} {url} - {e}")
            raise
    
    def get_health_status(self) -> Dict:
        """
        获取服务健康状态
        
        Returns:
            健康检查结果
        """
        return self._make_request("GET", "/health")
    
    def get_root_info(self) -> Dict:
        """
        获取根路径信息
        
        Returns:
            根路径信息
        """
        return self._make_request("GET", "/")
    
    def get_provinces(self, page: int = 1, page_size: int = 20) -> Dict:
        """
        获取省份列表
        
        Args:
            page: 页码（从1开始）
            page_size: 每页数量（1-100）
            
        Returns:
            分页的省份列表
        """
        params = {"page": page, "page_size": page_size}
        return self._make_request("GET", "/provinces", params=params)
    
    def get_cities(self, province: str, page: int = 1, page_size: int = 20) -> Dict:
        """
        获取城市列表
        
        Args:
            province: 省份名称或编码
            page: 页码
            page_size: 每页数量
            
        Returns:
            分页的城市列表
        """
        params = {"province": province, "page": page, "page_size": page_size}
        return self._make_request("GET", "/cities", params=params)
    
    def get_districts(self, city: str, page: int = 1, page_size: int = 20) -> Dict:
        """
        获取区县列表
        
        Args:
            city: 城市名称或编码
            page: 页码
            page_size: 每页数量
            
        Returns:
            分页的区县列表
        """
        params = {"city": city, "page": page, "page_size": page_size}
        return self._make_request("GET", "/districts", params=params)
    
    def get_hospitals_by_district(self, district: str, page: int = 1, page_size: int = 20) -> Dict:
        """
        根据区县获取医院列表
        
        Args:
            district: 区县名称或编码
            page: 页码
            page_size: 每页数量
            
        Returns:
            分页的医院列表
        """
        params = {"district": district, "page": page, "page_size": page_size}
        return self._make_request("GET", "/hospitals", params=params)
    
    def search_hospitals(self, query: str, page: int = 1, page_size: int = 20) -> Dict:
        """
        搜索医院
        
        Args:
            query: 搜索关键词
            page: 页码
            page_size: 每页数量
            
        Returns:
            搜索结果
        """
        params = {"q": query, "page": page, "page_size": page_size}
        return self._make_request("GET", "/hospitals/search", params=params)
    
    def refresh_all_data(self) -> Dict:
        """
        启动全量数据刷新任务
        
        Returns:
            任务信息
        """
        return self._make_request("POST", "/refresh/all")
    
    def refresh_province_data(self, province_name: str) -> Dict:
        """
        刷新指定省份数据
        
        Args:
            province_name: 省份名称
            
        Returns:
            任务信息
        """
        return self._make_request("POST", f"/refresh/province/{province_name}")
    
    def get_task_status(self, task_id: str) -> Dict:
        """
        获取任务状态
        
        Args:
            task_id: 任务ID
            
        Returns:
            任务状态信息
        """
        return self._make_request("GET", f"/tasks/{task_id}")
    
    def list_tasks(self, status: Optional[str] = None, limit: int = 50) -> Dict:
        """
        列出任务
        
        Args:
            status: 任务状态过滤（pending, running, succeeded, failed）
            limit: 返回数量限制（1-200）
            
        Returns:
            任务列表
        """
        params = {}
        if status:
            params["status"] = status
        params["limit"] = limit
        return self._make_request("GET", "/tasks", params=params)
    
    def get_active_tasks(self) -> Dict:
        """
        获取活跃任务
        
        Returns:
            活跃任务列表
        """
        return self._make_request("GET", "/tasks/active")
    
    def cancel_task(self, task_id: str) -> Dict:
        """
        取消任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            取消结果
        """
        return self._make_request("DELETE", f"/tasks/{task_id}")
    
    def cleanup_old_tasks(self, hours: int = 24) -> Dict:
        """
        清理旧任务
        
        Args:
            hours: 保留最近多少小时的任务（1-168）
            
        Returns:
            清理结果
        """
        params = {"hours": hours}
        return self._make_request("POST", "/tasks/cleanup", params=params)
    
    def get_statistics(self) -> Dict:
        """
        获取数据统计信息
        
        Returns:
            统计数据
        """
        return self._make_request("GET", "/statistics")


def demo_basic_operations():
    """演示基本操作"""
    print("=" * 60)
    print("医院扫描仪API基本操作演示")
    print("=" * 60)
    
    # 创建API客户端
    client = HospitalScannerAPIClient()
    
    try:
        # 1. 健康检查
        print("\n1. 健康检查")
        health = client.get_health_status()
        print(f"状态: {health['message']}")
        print(f"数据库: {health['data']['database']}")
        print(f"统计数据: {health['data']['stats']}")
        
        # 2. 获取根路径信息
        print("\n2. 根路径信息")
        root = client.get_root_info()
        print(f"服务信息: {root['data']['service']}")
        print(f"版本: {root['data']['version']}")
        
        # 3. 获取省份列表
        print("\n3. 获取省份列表（前10个）")
        provinces = client.get_provinces(page=1, page_size=10)
        print(f"总省份数: {provinces['data']['total']}")
        for i, province in enumerate(provinces['data']['items'][:5], 1):
            print(f"  {i}. {province['name']} (编码: {province['code']})")
        
    except Exception as e:
        print(f"基本操作演示失败: {e}")


def demo_data_query():
    """演示数据查询操作"""
    print("\n" + "=" * 60)
    print("医院扫描仪API数据查询演示")
    print("=" * 60)
    
    client = HospitalScannerAPIClient()
    
    try:
        # 1. 获取省份列表
        print("\n1. 获取省份列表")
        provinces = client.get_provinces(page=1, page_size=5)
        if provinces['data']['items']:
            first_province = provinces['data']['items'][0]
            province_name = first_province['name']
            print(f"选择省份: {province_name}")
            
            # 2. 获取该省份的城市
            print(f"\n2. 获取省份 {province_name} 的城市")
            cities = client.get_cities(province_name, page=1, page_size=10)
            print(f"城市数量: {cities['data']['total']}")
            for i, city in enumerate(cities['data']['items'][:3], 1):
                print(f"  {i}. {city['name']} (编码: {city['code']})")
            
            # 3. 选择第一个城市获取区县
            if cities['data']['items']:
                first_city = cities['data']['items'][0]
                city_name = first_city['name']
                print(f"\n3. 获取城市 {city_name} 的区县")
                districts = client.get_districts(city_name, page=1, page_size=10)
                print(f"区县数量: {districts['data']['total']}")
                for i, district in enumerate(districts['data']['items'][:3], 1):
                    print(f"  {i}. {district['name']} (编码: {district['code']})")
                
                # 4. 选择第一个区县获取医院
                if districts['data']['items']:
                    first_district = districts['data']['items'][0]
                    district_name = first_district['name']
                    print(f"\n4. 获取区县 {district_name} 的医院")
                    hospitals = client.get_hospitals_by_district(district_name, page=1, page_size=5)
                    print(f"医院数量: {hospitals['data']['total']}")
                    for i, hospital in enumerate(hospitals['data']['items'][:3], 1):
                        print(f"  {i}. {hospital['name']}")
                        if hospital.get('website'):
                            print(f"     官网: {hospital['website']}")
                        if hospital.get('llm_confidence'):
                            print(f"     LLM可信度: {hospital['llm_confidence']:.2f}")
        
        # 5. 搜索医院
        print(f"\n5. 搜索医院（关键词：'医院'）")
        search_results = client.search_hospitals("医院", page=1, page_size=5)
        print(f"搜索结果总数: {search_results['data']['total']}")
        for i, hospital in enumerate(search_results['data']['items'][:3], 1):
            print(f"  {i}. {hospital['name']}")
            if hospital.get('website'):
                print(f"     官网: {hospital['website']}")
    
    except Exception as e:
        print(f"数据查询演示失败: {e}")


def demo_task_management():
    """演示任务管理操作"""
    print("\n" + "=" * 60)
    print("医院扫描仪API任务管理演示")
    print("=" * 60)
    
    client = HospitalScannerAPIClient()
    
    try:
        # 1. 获取活跃任务
        print("\n1. 获取活跃任务")
        active_tasks = client.get_active_tasks()
        print(f"活跃任务数量: {active_tasks['data']['count']}")
        for task in active_tasks['data']['active_tasks']:
            print(f"  - 任务ID: {task['id'][:8]}...")
            print(f"    范围: {task['scope']}")
            print(f"    状态: {task['status']}")
            print(f"    进度: {task['progress']:.1f}%")
        
        # 2. 获取所有任务
        print(f"\n2. 获取任务列表（限制5个）")
        all_tasks = client.list_tasks(limit=5)
        print(f"返回任务数: {all_tasks['data']['total']}")
        for task in all_tasks['data']['tasks']:
            print(f"  - 任务ID: {task['id'][:8]}...")
            print(f"    范围: {task['scope']}")
            print(f"    状态: {task['status']}")
            print(f"    进度: {task['progress']:.1f}%")
            print(f"    创建时间: {task['created_at']}")
        
        # 3. 获取统计数据
        print(f"\n3. 获取统计数据")
        stats = client.get_statistics()
        print(f"省份数: {stats['data']['provinces']}")
        print(f"城市数: {stats['data']['cities']}")
        print(f"区县数: {stats['data']['districts']}")
        print(f"医院数: {stats['data']['hospitals']}")
        print(f"总任务数: {stats['data']['total_tasks']}")
        
        # 4. 演示启动数据刷新任务（可选）
        print(f"\n4. 演示启动省份数据刷新任务")
        refresh_result = client.refresh_province_data("北京市")
        task_id = refresh_result['data']['task_id']
        print(f"刷新任务已启动: {task_id}")
        
        # 5. 监控任务状态
        print(f"\n5. 监控任务状态")
        for i in range(3):
            time.sleep(1)
            task_status = client.get_task_status(task_id)
            status_info = task_status['data']
            print(f"  检查 {i+1}: 状态={status_info['status']}, 进度={status_info['progress']:.1f}%")
            
            if status_info['status'] in ['succeeded', 'failed']:
                break
        
        # 6. 清理旧任务
        print(f"\n6. 清理24小时前的旧任务")
        cleanup_result = client.cleanup_old_tasks(hours=24)
        print(f"清理结果: {cleanup_result['message']}")
        print(f"清理数量: {cleanup_result['data']['cleaned_count']}")
    
    except Exception as e:
        print(f"任务管理演示失败: {e}")


def demo_error_handling():
    """演示错误处理"""
    print("\n" + "=" * 60)
    print("医院扫描仪API错误处理演示")
    print("=" * 60)
    
    client = HospitalScannerAPIClient()
    
    try:
        # 1. 请求不存在的任务
        print("\n1. 请求不存在的任务")
        try:
            task_status = client.get_task_status("nonexistent_task_id")
        except Exception as e:
            print(f"预期的错误: {type(e).__name__}: {e}")
        
        # 2. 使用无效的查询参数
        print("\n2. 使用无效的省份查询")
        try:
            cities = client.get_cities("", page=0, page_size=101)  # page=0和page_size=101都超出范围
        except Exception as e:
            print(f"预期的错误: {type(e).__name__}: {e}")
        
        # 3. 访问无效的端点
        print("\n3. 访问无效的API端点")
        try:
            invalid_response = client._make_request("GET", "/invalid/endpoint")
        except Exception as e:
            print(f"预期的错误: {type(e).__name__}: {e}")
    
    except Exception as e:
        print(f"错误处理演示中出现问题: {e}")


def main():
    """主演示函数"""
    print("医院扫描仪API使用示例")
    print("=" * 60)
    print("此演示展示了如何使用医院扫描仪微服务的各种API接口")
    print("确保API服务在 http://localhost:8000 运行")
    print("=" * 60)
    
    # 检查API服务是否可用
    try:
        client = HospitalScannerAPIClient()
        health = client.get_health_status()
        print(f"\n✅ API服务连接成功: {health['data']['status']}")
    except Exception as e:
        print(f"\n❌ 无法连接到API服务: {e}")
        print("请确保在另一个终端中运行: python main.py")
        return
    
    # 运行各种演示
    try:
        demo_basic_operations()
        demo_data_query()
        demo_task_management()
        demo_error_handling()
        
        print("\n" + "=" * 60)
        print("✅ 所有演示完成！")
        print("=" * 60)
        
    except KeyboardInterrupt:
        print("\n\n演示被用户中断")
    except Exception as e:
        print(f"\n\n演示过程中发生错误: {e}")


if __name__ == "__main__":
    main()
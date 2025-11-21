#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FastAPI服务测试客户端
用于验证医院层级扫查微服务的各项功能
"""

import requests
import json
import time
from typing import Optional, Dict, Any


class HospitalAPI:
    """医院API客户端"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
    
    def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """发送HTTP请求"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ API请求失败: {method} {url}")
            print(f"   错误: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"   响应: {e.response.text}")
            return None
    
    def health_check(self) -> bool:
        """健康检查"""
        print("🔍 检查服务健康状态...")
        result = self._request('GET', '/health')
        
        if result and result.get('code') == 200:
            print("✅ 服务健康")
            return True
        else:
            print("❌ 服务不可用")
            return False
    
    def get_provinces(self, page: int = 1, page_size: int = 20) -> Optional[Dict]:
        """获取省份列表"""
        print(f"📍 获取省份列表 (页码: {page})...")
        result = self._request('GET', f'/provinces?page={page}&page_size={page_size}')
        
        if result:
            print(f"✅ 成功获取 {result['data']['total']} 个省份")
            return result
        else:
            print("❌ 获取省份列表失败")
            return None
    
    def get_cities(self, province: str, page: int = 1, page_size: int = 20) -> Optional[Dict]:
        """获取城市列表"""
        print(f"🏙️  获取 {province} 的城市列表...")
        result = self._request('GET', f'/cities?province={province}&page={page}&page_size={page_size}')
        
        if result:
            print(f"✅ 成功获取 {result['data']['total']} 个城市")
            return result
        else:
            print(f"❌ 获取 {province} 城市列表失败")
            return None
    
    def get_districts(self, city: str, page: int = 1, page_size: int = 20) -> Optional[Dict]:
        """获取区县列表"""
        print(f"🏘️  获取 {city} 的区县列表...")
        result = self._request('GET', f'/districts?city={city}&page={page}&page_size={page_size}')
        
        if result:
            print(f"✅ 成功获取 {result['data']['total']} 个区县")
            return result
        else:
            print(f"❌ 获取 {city} 区县列表失败")
            return None
    
    def get_hospitals(self, district: str, page: int = 1, page_size: int = 20) -> Optional[Dict]:
        """获取医院列表"""
        print(f"🏥 获取 {district} 的医院列表...")
        result = self._request('GET', f'/hospitals?district={district}&page={page}&page_size={page_size}')
        
        if result:
            print(f"✅ 成功获取 {result['data']['total']} 个医院")
            return result
        else:
            print(f"❌ 获取 {district} 医院列表失败")
            return None
    
    def search_hospitals(self, query: str, page: int = 1, page_size: int = 20) -> Optional[Dict]:
        """搜索医院"""
        print(f"🔍 搜索医院: '{query}'...")
        result = self._request('GET', f'/hospitals/search?q={query}&page={page}&page_size={page_size}')
        
        if result:
            print(f"✅ 搜索到 {result['data']['total']} 个相关医院")
            return result
        else:
            print(f"❌ 搜索医院失败")
            return None
    
    def start_full_refresh(self) -> Optional[str]:
        """启动全量刷新"""
        print("🔄 启动全量刷新任务...")
        result = self._request('POST', '/refresh/all')
        
        if result and result.get('code') == 200:
            task_id = result['data']['task_id']
            print(f"✅ 全量刷新任务已启动，任务ID: {task_id}")
            return task_id
        else:
            print("❌ 启动全量刷新失败")
            return None
    
    def start_province_refresh(self, province_name: str) -> Optional[str]:
        """启动省份刷新"""
        print(f"🔄 启动省份 {province_name} 刷新任务...")
        result = self._request('POST', f'/refresh/province/{province_name}')
        
        if result and result.get('code') == 200:
            task_id = result['data']['task_id']
            print(f"✅ 省份刷新任务已启动，任务ID: {task_id}")
            return task_id
        else:
            print(f"❌ 启动省份 {province_name} 刷新失败")
            return None
    
    def get_task_status(self, task_id: str) -> Optional[Dict]:
        """获取任务状态"""
        result = self._request('GET', f'/tasks/{task_id}')
        
        if result:
            return result['data']
        else:
            return None
    
    def wait_for_task(self, task_id: str, timeout: int = 60) -> bool:
        """等待任务完成"""
        print(f"⏳ 等待任务 {task_id} 完成...")
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            status = self.get_task_status(task_id)
            if not status:
                print("❌ 无法获取任务状态")
                return False
            
            current_status = status.get('status')
            progress = status.get('progress', 0)
            current_step = status.get('current_step', '')
            
            print(f"   状态: {current_status}, 进度: {progress}%, 步骤: {current_step}")
            
            if current_status in ['succeeded', 'failed']:
                if current_status == 'succeeded':
                    print(f"✅ 任务 {task_id} 执行成功")
                    return True
                else:
                    error = status.get('error', '未知错误')
                    print(f"❌ 任务 {task_id} 执行失败: {error}")
                    return False
            
            time.sleep(2)
        
        print(f"⏰ 任务 {task_id} 超时")
        return False
    
    def get_statistics(self) -> Optional[Dict]:
        """获取统计信息"""
        print("📊 获取统计信息...")
        result = self._request('GET', '/statistics')
        
        if result:
            print("✅ 统计信息获取成功")
            return result['data']
        else:
            print("❌ 获取统计信息失败")
            return None
    
    def test_complete_flow(self):
        """测试完整的数据流程"""
        print("\n" + "="*50)
        print("🏥 医院层级扫查微服务功能测试")
        print("="*50)
        
        # 1. 健康检查
        if not self.health_check():
            return False
        
        print("\n" + "-"*30)
        
        # 2. 检查现有数据
        print("📊 检查当前数据库状态")
        stats = self.get_statistics()
        if stats:
            print(f"   省份: {stats.get('provinces', 0)} 个")
            print(f"   城市: {stats.get('cities', 0)} 个")
            print(f"   区县: {stats.get('districts', 0)} 个")
            print(f"   医院: {stats.get('hospitals', 0)} 个")
        
        print("\n" + "-"*30)
        
        # 3. 测试查询接口
        print("🔍 测试查询接口")
        provinces = self.get_provinces()
        if provinces and provinces['data']['items']:
            first_province = provinces['data']['items'][0]['name']
            print(f"   测试省份: {first_province}")
            
            cities = self.get_cities(first_province)
            if cities and cities['data']['items']:
                first_city = cities['data']['items'][0]['name']
                print(f"   测试城市: {first_city}")
                
                districts = self.get_districts(first_city)
                if districts and districts['data']['items']:
                    first_district = districts['data']['items'][0]['name']
                    print(f"   测试区县: {first_district}")
                    
                    hospitals = self.get_hospitals(first_district)
                    if hospitals:
                        print(f"   医院数量: {hospitals['data']['total']}")
        
        print("\n" + "-"*30)
        
        # 4. 测试搜索接口
        print("🔍 测试搜索接口")
        search_result = self.search_hospitals("医院")
        if search_result:
            print(f"   搜索'医院'结果: {search_result['data']['total']} 条")
        
        print("\n" + "-"*30)
        
        # 5. 测试刷新功能
        print("🔄 测试刷新功能")
        task_id = self.start_province_refresh("北京市")
        if task_id:
            self.wait_for_task(task_id)
        
        print("\n" + "="*50)
        print("✅ 功能测试完成")
        print("="*50)
        
        return True


def main():
    """主函数"""
    api = HospitalAPI()
    
    try:
        # 等待服务启动
        print("⏳ 等待服务启动...")
        time.sleep(3)
        
        # 运行完整测试
        api.test_complete_flow()
        
    except KeyboardInterrupt:
        print("\n\n👋 测试被用户中断")
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")


if __name__ == "__main__":
    main()
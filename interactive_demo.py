#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
医院扫描仪交互式演示程序
提供命令行交互界面，让用户可以直观地体验医院扫描仪的各种功能

主要功能：
1. 交互式菜单系统
2. 实时API测试
3. 数据可视化展示
4. 任务管理演示
5. 错误处理和用户友好的提示
"""

import os
import sys
import time
import json
import requests
from datetime import datetime
from typing import Dict, List, Optional

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入示例模块
from examples.api_usage_examples import HospitalScannerAPIClient


class InteractiveDemo:
    """交互式演示程序"""
    
    def __init__(self):
        """初始化演示程序"""
        self.api_client = None
        self.setup_api_client()
        self.setup_display()
    
    def setup_api_client(self):
        """设置API客户端"""
        try:
            self.api_client = HospitalScannerAPIClient()
            print("✅ API客户端初始化成功")
        except Exception as e:
            print(f"❌ API客户端初始化失败: {e}")
            print("将使用模拟模式进行演示")
    
    def setup_display(self):
        """设置显示配置"""
        # 设置颜色代码（如果支持）
        self.colors = {
            'HEADER': '\033[95m',
            'OKBLUE': '\033[94m',
            'OKCYAN': '\033[96m',
            'OKGREEN': '\033[92m',
            'WARNING': '\033[93m',
            'FAIL': '\033[91m',
            'ENDC': '\033[0m',
            'BOLD': '\033[1m',
            'UNDERLINE': '\033[4m'
        }
    
    def print_header(self, title: str):
        """打印标题头"""
        print(f"\n{self.colors['HEADER']}{'='*60}{self.colors['ENDC']}")
        print(f"{self.colors['BOLD']}{title.center(60)}{self.colors['ENDC']}")
        print(f"{self.colors['HEADER']}{'='*60}{self.colors['ENDC']}")
    
    def print_section(self, title: str):
        """打印章节标题"""
        print(f"\n{self.colors['OKBLUE']}{'='*40}{self.colors['ENDC']}")
        print(f"{self.colors['BOLD']}{title}{self.colors['ENDC']}")
        print(f"{self.colors['OKBLUE']}{'='*40}{self.colors['ENDC']}")
    
    def print_success(self, message: str):
        """打印成功信息"""
        print(f"{self.colors['OKGREEN']}✅ {message}{self.colors['ENDC']}")
    
    def print_error(self, message: str):
        """打印错误信息"""
        print(f"{self.colors['FAIL']}❌ {message}{self.colors['ENDC']}")
    
    def print_warning(self, message: str):
        """打印警告信息"""
        print(f"{self.colors['WARNING']}⚠️  {message}{self.colors['ENDC']}")
    
    def print_info(self, message: str):
        """打印信息"""
        print(f"{self.colors['OKCYAN']}ℹ️  {message}{self.colors['ENDC']}")
    
    def clear_screen(self):
        """清屏"""
        os.system('clear' if os.name == 'posix' else 'cls')
    
    def wait_for_user(self, message: str = "按回车键继续..."):
        """等待用户输入"""
        input(f"\n{self.colors['WARNING']}{message}{self.colors['ENDC']}")
    
    def get_user_choice(self, options: List[str], prompt: str = "请选择: ") -> int:
        """
        获取用户选择
        
        Args:
            options: 选项列表
            prompt: 提示文字
            
        Returns:
            用户选择的索引（0-based）
        """
        while True:
            try:
                print(f"\n{prompt}")
                for i, option in enumerate(options, 1):
                    print(f"  {i}. {option}")
                
                choice = input(f"\n{prompt}")
                choice_num = int(choice) - 1
                
                if 0 <= choice_num < len(options):
                    return choice_num
                else:
                    print(self.colors['WARNING'] + f"请输入1-{len(options)}之间的数字" + self.colors['ENDC'])
                    
            except ValueError:
                print(self.colors['WARNING'] + "请输入有效的数字" + self.colors['ENDC'])
    
    def demo_welcome(self):
        """欢迎界面"""
        self.clear_screen()
        
        print(f"\n{self.colors['HEADER']}")
        print("██╗   ██╗ █████╗ ███╗   ███╗██████╗ ██╗   ██╗")
        print("╝██╗ ██╔╝██╔══██╗████╗ ████║██╔══██╗║██║   ██║")
        print(" ╚████╔╝ ███████║██╔████╔██║██║  ██║║██║   ██║")
        print("  ╚██╔╝  ██╔══██║██║╚██╔╝██║██║  ██║║██║   ██║")
        print("   ██║   ██║  ██║██║ ╚═╝ ██║██████╔╝╚██████╔╝")
        print("   ╚═╝   ╚═╝  ╚═╝╚═╝     ╚═╝╚═════╝  ╚═════╝")
        print(f"{self.colors['ENDC']}")
        
        print(f"\n{self.colors['BOLD']}医院扫描仪项目交互式演示{self.colors['ENDC']}")
        print("=" * 60)
        print("欢迎使用医院扫描仪项目的交互式演示程序！")
        print("\n本演示将带您体验:")
        print("• API接口功能测试")
        print("• 数据库查询操作")
        print("• LLM智能分析")
        print("• 任务管理系统")
        print("• 数据可视化展示")
        
        self.wait_for_user()
    
    def demo_api_connection(self):
        """演示API连接"""
        self.print_section("API连接测试")
        
        if not self.api_client:
            self.print_warning("API客户端未初始化，使用模拟模式")
            return
        
        try:
            print("\n正在测试API连接...")
            
            # 测试健康检查
            health = self.api_client.get_health_status()
            if health and health.get('code') == 200:
                self.print_success("API连接成功!")
                print(f"服务状态: {health['data']['status']}")
                print(f"数据库状态: {health['data']['database']}")
                
                if 'stats' in health['data']:
                    stats = health['data']['stats']
                    print(f"\n数据统计:")
                    for key, value in stats.items():
                        print(f"  {key}: {value}")
                
            else:
                self.print_error("API健康检查失败")
                
        except Exception as e:
            self.print_error(f"API连接测试失败: {e}")
            self.print_info("请确保API服务正在运行: python main.py")
    
    def demo_data_exploration(self):
        """演示数据探索"""
        self.print_section("数据探索")
        
        if not self.api_client:
            self.demo_api_connection()
            if not self.api_client:
                return
        
        try:
            # 1. 探索省份数据
            print("\n🏛️  探索省份数据...")
            provinces = self.api_client.get_provinces(1, 10)
            if provinces and provinces.get('code') == 200:
                data = provinces['data']
                print(f"总共找到 {data['total']} 个省份")
                print("前10个省份:")
                for i, province in enumerate(data['items'], 1):
                    print(f"  {i}. {province['name']} (编码: {province['code']})")
                
                # 让用户选择省份
                if data['items']:
                    choice = self.get_user_choice(
                        [p['name'] for p in data['items'][:5]] + ["返回"],
                        "选择要探索的省份 (显示前5个):"
                    )
                    
                    if choice < 5:
                        selected_province = data['items'][choice]
                        self.explore_cities(selected_province['name'])
            else:
                self.print_error("获取省份数据失败")
                
        except Exception as e:
            self.print_error(f"数据探索失败: {e}")
    
    def explore_cities(self, province_name: str):
        """探索城市数据"""
        print(f"\n🏙️  探索省份 {province_name} 的城市...")
        
        try:
            cities = self.api_client.get_cities(province_name, 1, 10)
            if cities and cities.get('code') == 200:
                data = cities['data']
                print(f"省份 {province_name} 有 {data['total']} 个城市")
                print("前10个城市:")
                for i, city in enumerate(data['items'], 1):
                    print(f"  {i}. {city['name']} (编码: {city['code']})")
                
                # 让用户选择城市
                if data['items']:
                    choice = self.get_user_choice(
                        [c['name'] for c in data['items'][:5]] + ["返回"],
                        "选择要探索的城市 (显示前5个):"
                    )
                    
                    if choice < 5:
                        selected_city = data['items'][choice]
                        self.explore_districts(selected_city['name'])
            else:
                self.print_error("获取城市数据失败")
                
        except Exception as e:
            self.print_error(f"城市探索失败: {e}")
    
    def explore_districts(self, city_name: str):
        """探索区县数据"""
        print(f"\n🏘️  探索城市 {city_name} 的区县...")
        
        try:
            districts = self.api_client.get_districts(city_name, 1, 10)
            if districts and districts.get('code') == 200:
                data = districts['data']
                print(f"城市 {city_name} 有 {data['total']} 个区县")
                print("前10个区县:")
                for i, district in enumerate(data['items'], 1):
                    print(f"  {i}. {district['name']} (编码: {district['code']})")
                
                # 让用户选择区县
                if data['items']:
                    choice = self.get_user_choice(
                        [d['name'] for d in data['items'][:5]] + ["返回"],
                        "选择要探索的区县 (显示前5个):"
                    )
                    
                    if choice < 5:
                        selected_district = data['items'][choice]
                        self.explore_hospitals(selected_district['name'])
            else:
                self.print_error("获取区县数据失败")
                
        except Exception as e:
            self.print_error(f"区县探索失败: {e}")
    
    def explore_hospitals(self, district_name: str):
        """探索医院数据"""
        print(f"\n🏥  探索区县 {district_name} 的医院...")
        
        try:
            hospitals = self.api_client.get_hospitals_by_district(district_name, 1, 10)
            if hospitals and hospitals.get('code') == 200:
                data = hospitals['data']
                print(f"区县 {district_name} 有 {data['total']} 个医院")
                print("前10个医院:")
                for i, hospital in enumerate(data['items'], 1):
                    print(f"  {i}. {hospital['name']}")
                    if hospital.get('website'):
                        print(f"     官网: {hospital['website']}")
                    if hospital.get('llm_confidence'):
                        print(f"     LLM可信度: {hospital['llm_confidence']:.2f}")
                    
                # 让用户选择医院进行详细查看
                if data['items']:
                    choices = [h['name'][:30] + "..." if len(h['name']) > 30 else h['name'] 
                              for h in data['items'][:5]] + ["返回"]
                    
                    choice = self.get_user_choice(
                        choices,
                        "选择要查看详情的医院 (显示前5个):"
                    )
                    
                    if choice < 5:
                        selected_hospital = data['items'][choice]
                        self.show_hospital_details(selected_hospital)
            else:
                self.print_error("获取医院数据失败")
                
        except Exception as e:
            self.print_error(f"医院探索失败: {e}")
    
    def show_hospital_details(self, hospital: Dict):
        """显示医院详情"""
        print(f"\n📋 医院详情")
        print("=" * 40)
        print(f"医院名称: {hospital['name']}")
        
        if hospital.get('website'):
            print(f"官网地址: {hospital['website']}")
        
        if hospital.get('llm_confidence'):
            confidence = hospital['llm_confidence']
            confidence_text = "高" if confidence >= 0.8 else "中" if confidence >= 0.5 else "低"
            print(f"LLM可信度: {confidence:.2f} ({confidence_text})")
        
        print(f"更新时间: {hospital['updated_at']}")
        
        self.wait_for_user()
    
    def demo_search_function(self):
        """演示搜索功能"""
        self.print_section("医院搜索功能")
        
        if not self.api_client:
            self.print_error("API客户端不可用")
            return
        
        print("\n🔍 医院搜索功能演示")
        print("支持模糊搜索，可以输入医院名称的关键词")
        
        search_queries = [
            ("医院", "通用医院搜索"),
            ("人民", "人民医院搜索"),
            ("中心", "医疗中心搜索"),
            ("大学", "大学附属医院搜索"),
            ("自定义", "输入自定义搜索词")
        ]
        
        choice = self.get_user_choice([item[1] for item in search_queries], "选择搜索类型:")
        
        search_query = search_queries[choice][0]
        
        if search_query == "自定义":
            search_query = input("\n请输入搜索关键词: ").strip()
            if not search_query:
                self.print_warning("搜索词不能为空")
                return
        
        try:
            print(f"\n🔍 正在搜索: '{search_query}'")
            results = self.api_client.search_hospitals(search_query, 1, 10)
            
            if results and results.get('code') == 200:
                data = results['data']
                print(f"\n找到 {data['total']} 个相关医院:")
                print("-" * 50)
                
                for i, hospital in enumerate(data['items'][:10], 1):
                    print(f"{i:2d}. {hospital['name']}")
                    if hospital.get('website'):
                        print(f"     官网: {hospital['website']}")
                    if hospital.get('llm_confidence'):
                        print(f"     可信度: {hospital['llm_confidence']:.2f}")
                    print()
                
                # 让用户选择查看详情
                if data['items']:
                    choices = [h['name'][:30] + "..." if len(h['name']) > 30 else h['name'] 
                              for h in data['items'][:5]] + ["跳过"]
                    
                    choice = self.get_user_choice(
                        choices,
                        "选择要查看详情的医院 (前5个):"
                    )
                    
                    if choice < 5:
                        selected_hospital = data['items'][choice]
                        self.show_hospital_details(selected_hospital)
            else:
                self.print_error("搜索失败")
                
        except Exception as e:
            self.print_error(f"搜索出错: {e}")
    
    def demo_task_management(self):
        """演示任务管理"""
        self.print_section("任务管理系统")
        
        if not self.api_client:
            self.print_error("API客户端不可用")
            return
        
        print("\n⚡ 任务管理演示")
        print("医院扫描仪支持后台异步任务处理")
        
        task_options = [
            ("查看活跃任务", "查看当前正在运行的任务"),
            ("启动省份刷新", "启动指定省份的数据刷新任务"),
            ("监控任务状态", "实时监控任务执行状态"),
            ("清理旧任务", "清理指定时间之前的旧任务")
        ]
        
        choice = self.get_user_choice([item[0] for item in task_options], "选择任务操作:")
        
        try:
            if choice == 0:  # 查看活跃任务
                print("\n📊 查看活跃任务...")
                active_tasks = self.api_client.get_active_tasks()
                
                if active_tasks and active_tasks.get('code') == 200:
                    data = active_tasks['data']
                    if data['count'] > 0:
                        print(f"当前有 {data['count']} 个活跃任务:")
                        for i, task in enumerate(data['active_tasks'], 1):
                            print(f"  {i}. 任务ID: {task['id'][:8]}...")
                            print(f"     范围: {task['scope']}")
                            print(f"     状态: {task['status']}")
                            print(f"     进度: {task['progress']:.1f}%")
                            print()
                    else:
                        print("当前没有活跃任务")
                else:
                    self.print_error("获取活跃任务失败")
            
            elif choice == 1:  # 启动省份刷新
                provinces = self.api_client.get_provinces(1, 10)
                if provinces and provinces.get('code') == 200:
                    province_list = provinces['data']['items']
                    print("\n🗺️ 选择要刷新的省份:")
                    for i, province in enumerate(province_list[:5], 1):
                        print(f"  {i}. {province['name']}")
                    
                    province_choice = self.get_user_choice([p['name'] for p in province_list[:5]], "选择省份:")
                    selected_province = province_list[province_choice]
                    
                    print(f"\n🚀 启动省份 {selected_province['name']} 的数据刷新...")
                    refresh_result = self.api_client.refresh_province_data(selected_province['name'])
                    
                    if refresh_result and refresh_result.get('code') == 200:
                        task_id = refresh_result['data']['task_id']
                        self.print_success(f"刷新任务已启动: {task_id}")
                        
                        # 自动监控任务状态
                        self.monitor_task(task_id)
                    else:
                        self.print_error("启动刷新任务失败")
            
            elif choice == 2:  # 监控任务状态
                task_id = input("\n请输入要监控的任务ID: ").strip()
                if task_id:
                    self.monitor_task(task_id)
                else:
                    self.print_warning("任务ID不能为空")
            
            elif choice == 3:  # 清理旧任务
                print("\n🧹 清理旧任务...")
                hours = input("保留最近多少小时的任务 (默认24): ").strip()
                try:
                    hours = int(hours) if hours else 24
                except ValueError:
                    hours = 24
                
                cleanup_result = self.api_client.cleanup_old_tasks(hours)
                if cleanup_result and cleanup_result.get('code') == 200:
                    cleaned_count = cleanup_result['data']['cleaned_count']
                    self.print_success(f"清理完成，删除了 {cleaned_count} 个旧任务")
                else:
                    self.print_error("清理任务失败")
        
        except Exception as e:
            self.print_error(f"任务管理操作失败: {e}")
    
    def monitor_task(self, task_id: str):
        """监控任务状态"""
        print(f"\n👀 监控任务状态: {task_id[:8]}...")
        
        for i in range(5):
            try:
                task_status = self.api_client.get_task_status(task_id)
                if task_status and task_status.get('code') == 200:
                    data = task_status['data']
                    print(f"检查 {i+1}: 状态={data['status']}, 进度={data['progress']:.1f}%")
                    
                    if data['status'] in ['succeeded', 'failed']:
                        if data['status'] == 'succeeded':
                            self.print_success("任务执行成功!")
                        else:
                            self.print_error(f"任务执行失败: {data.get('error', '未知错误')}")
                        break
                    
                    if i < 4:  # 不是最后一次检查
                        print("等待3秒后继续检查...")
                        time.sleep(3)
                else:
                    self.print_error(f"获取任务状态失败")
                    break
                    
            except Exception as e:
                self.print_error(f"监控任务失败: {e}")
                break
    
    def demo_statistics(self):
        """演示统计功能"""
        self.print_section("数据统计分析")
        
        if not self.api_client:
            self.print_error("API客户端不可用")
            return
        
        print("\n📊 数据统计概览")
        
        try:
            # 获取统计数据
            stats = self.api_client.get_statistics()
            if stats and stats.get('code') == 200:
                data = stats['data']
                
                print(f"\n数据库统计信息:")
                print(f"  省份数量: {data['provinces']}")
                print(f"  城市数量: {data['cities']}")
                print(f"  区县数量: {data['districts']}")
                print(f"  医院数量: {data['hospitals']}")
                print(f"  总任务数: {data['total_tasks']}")
                print(f"  活跃任务: {data['active_tasks']}")
                
                # 计算一些比率
                if data['cities'] > 0:
                    avg_cities_per_province = data['cities'] / data['provinces']
                    print(f"\n平均每个省份的城市数: {avg_cities_per_province:.1f}")
                
                if data['districts'] > 0:
                    avg_districts_per_city = data['districts'] / data['cities']
                    print(f"平均每个城市的区县数: {avg_districts_per_city:.1f}")
                
                if data['hospitals'] > 0:
                    avg_hospitals_per_district = data['hospitals'] / data['districts']
                    print(f"平均每个区县的医院数: {avg_hospitals_per_district:.1f}")
                
                print(f"\n统计时间: {data['timestamp']}")
                
            else:
                self.print_error("获取统计信息失败")
                
        except Exception as e:
            self.print_error(f"统计分析失败: {e}")
    
    def demo_performance_test(self):
        """演示性能测试"""
        self.print_section("性能测试")
        
        if not self.api_client:
            self.print_error("API客户端不可用")
            return
        
        print("\n⚡ 性能测试演示")
        print("将对API接口进行简单的性能测试")
        
        try:
            test_endpoints = [
                ("/health", "健康检查"),
                ("/provinces?page=1&page_size=10", "省份查询"),
                ("/statistics", "统计信息")
            ]
            
            for endpoint, description in test_endpoints:
                print(f"\n测试 {description}...")
                
                response_times = []
                success_count = 0
                
                # 连续测试5次
                for i in range(5):
                    start_time = time.time()
                    
                    try:
                        if endpoint == "/health":
                            result = self.api_client.get_health_status()
                        elif endpoint == "/provinces?page=1&page_size=10":
                            result = self.api_client.get_provinces(1, 10)
                        elif endpoint == "/statistics":
                            result = self.api_client.get_statistics()
                        else:
                            result = None
                        
                        end_time = time.time()
                        response_time = end_time - start_time
                        response_times.append(response_time)
                        
                        if result and result.get('code') == 200:
                            success_count += 1
                            
                    except Exception as e:
                        end_time = time.time()
                        response_times.append(end_time - start_time)
                        print(f"  第{i+1}次请求失败: {e}")
                
                # 计算统计信息
                if response_times:
                    avg_time = sum(response_times) / len(response_times)
                    min_time = min(response_times)
                    max_time = max(response_times)
                    success_rate = success_count / 5 * 100
                    
                    print(f"  平均响应时间: {avg_time:.3f}秒")
                    print(f"  最快响应时间: {min_time:.3f}秒")
                    print(f"  最慢响应时间: {max_time:.3f}秒")
                    print(f"  成功率: {success_rate:.1f}%")
                
        except Exception as e:
            self.print_error(f"性能测试失败: {e}")
    
    def show_menu(self):
        """显示主菜单"""
        self.print_header("医院扫描仪交互式演示")
        
        menu_options = [
            "🔗 API连接测试",
            "🗺️ 数据探索",
            "🔍 医院搜索",
            "⚡ 任务管理",
            "📊 数据统计",
            "⚡ 性能测试",
            "ℹ️  系统信息",
            "❌ 退出"
        ]
        
        choice = self.get_user_choice(menu_options, "主菜单:")
        
        return choice
    
    def show_system_info(self):
        """显示系统信息"""
        self.print_section("系统信息")
        
        print("\n🏗️ 系统架构信息:")
        print("  后端: Python FastAPI")
        print("  数据库: SQLite")
        print("  LLM: 阿里百炼 (DashScope)")
        print("  架构: 微服务架构")
        
        print("\n📚 主要功能模块:")
        print("  • 数据库管理 (db.py)")
        print("  • API接口 (main.py)")
        print("  • 数据模型 (schemas.py)")
        print("  • 任务管理 (tasks.py)")
        print("  • LLM客户端 (llm_client.py)")
        
        print("\n🌐 API端点:")
        print("  健康检查: GET /health")
        print("  省份查询: GET /provinces")
        print("  城市查询: GET /cities")
        print("  区县查询: GET /districts")
        print("  医院查询: GET /hospitals")
        print("  医院搜索: GET /hospitals/search")
        print("  任务管理: GET/POST /tasks/*")
        print("  数据刷新: POST /refresh/*")
        
        if self.api_client:
            print(f"\n🔗 当前API地址: {self.api_client.base_url}")
        
        print(f"\n⏰ 当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    def run_demo(self):
        """运行交互式演示"""
        try:
            self.demo_welcome()
            
            while True:
                choice = self.show_menu()
                
                if choice == 0:  # API连接测试
                    self.demo_api_connection()
                    
                elif choice == 1:  # 数据探索
                    self.demo_data_exploration()
                    
                elif choice == 2:  # 医院搜索
                    self.demo_search_function()
                    
                elif choice == 3:  # 任务管理
                    self.demo_task_management()
                    
                elif choice == 4:  # 数据统计
                    self.demo_statistics()
                    
                elif choice == 5:  # 性能测试
                    self.demo_performance_test()
                    
                elif choice == 6:  # 系统信息
                    self.show_system_info()
                    
                elif choice == 7:  # 退出
                    self.print_header("演示结束")
                    print("感谢使用医院扫描仪交互式演示！")
                    print("希望这次演示让您对项目有了更好的了解。")
                    print("\n📚 更多信息:")
                    print("  • 项目文档: README.md")
                    print("  • API文档: /docs")
                    print("  • 示例代码: examples/")
                    print("  • 测试报告: reports/")
                    break
                
                self.wait_for_user()
        
        except KeyboardInterrupt:
            print(f"\n\n{self.colors['WARNING']}演示被用户中断{self.colors['ENDC']}")
        except Exception as e:
            print(f"\n{self.colors['FAIL']}演示过程中发生错误: {e}{self.colors['ENDC']}")


def main():
    """主函数"""
    demo = InteractiveDemo()
    demo.run_demo()


if __name__ == "__main__":
    main()
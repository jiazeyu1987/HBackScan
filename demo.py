#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
医院层级扫查微服务演示程序
展示完整的API功能和数据流程
"""

import os
import sys
import time
import asyncio
import json
from datetime import datetime

# 添加当前目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from db import db
from tasks import TaskManager
from llm_client import DashScopeLLMClient


def init_sample_data():
    """初始化示例数据"""
    print("📊 初始化示例数据...")
    
    try:
        # 添加示例省份
        provinces = [
            {"name": "北京市", "code": "BJ"},
            {"name": "上海市", "code": "SH"},
            {"name": "广东省", "code": "GD"},
            {"name": "江苏省", "code": "JS"},
            {"name": "浙江省", "code": "ZJ"}
        ]
        
        province_ids = []
        for province in provinces:
            province_id = db.upsert_province(province["name"], province["code"])
            province_ids.append((province_id, province["name"]))
            print(f"  ✅ 添加省份: {province['name']}")
        
        # 添加示例城市
        cities_data = {
            "北京市": [("北京市", "BJ"), ("海淀区", "HD"), ("朝阳区", "CY")],
            "上海市": [("上海市", "SH"), ("黄浦区", "HP"), ("徐汇区", "XH")],
            "广东省": [("广州市", "GZ"), ("深圳市", "SZ"), ("珠海市", "ZH")],
            "江苏省": [("南京市", "NJ"), ("苏州市", "SZ"), ("无锡市", "WX")],
            "浙江省": [("杭州市", "HZ"), ("宁波市", "NB"), ("温州市", "WZ")]
        }
        
        for province_id, province_name in province_ids:
            cities = cities_data.get(province_name, [])
            for city_name, city_code in cities:
                city_id = db.upsert_city(province_id, city_name, city_code)
                print(f"  ✅ 添加城市: {city_name}")
        
        # 添加示例区县
        districts_data = {
            "北京市": [("东城区", "DC"), ("西城区", "XC")],
            "海淀区": [("中关村街道", "ZGC"), ("万柳街道", "WL")],
            "朝阳区": [("朝外街道", "CW"), ("建外街道", "JW")],
            "上海市": [("南京东路街道", "ND"), ("外滩街道", "WT")],
            "黄浦区": [("豫园街道", "YY"), ("老西门街道", "LXM")],
            "徐汇区": [("天平路街道", "TPL"), ("湖南路街道", "HL")],
            "广州市": [("越秀区", "YX"), ("荔湾区", "LW")],
            "天河区": [("天河南街道", "THN"), ("冼村街道", "XC")],
            "深圳市": [("罗湖区", "LH"), ("福田区", "FQ")],
            "福田区": [("华强北街道", "HQB"), ("福田街道", "FT")],
            "南京市": [("玄武区", "XW"), ("秦淮区", "QH")],
            "苏州市": [("姑苏区", "GS"), ("吴中区", "WZ")],
            "杭州市": [("上城区", "SC"), ("西湖区", "XH")],
            "宁波市": [("海曙区", "HS"), ("江北区", "JB")]
        }
        
        # 获取所有城市ID
        for province_id, province_name in province_ids:
            cities = cities_data.get(province_name, [])
            for city_name, city_code in cities:
                city = db.get_city(name=city_name)
                if city:
                    city_id = city["id"]
                    districts = districts_data.get(city_name, [])
                    for district_name, district_code in districts:
                        district_id = db.upsert_district(city_id, district_name, district_code)
                        print(f"  ✅ 添加区县: {district_name}")
        
        # 添加示例医院
        hospitals_data = {
            "东城区": [("北京协和医院", "http://www.pumch.cn"), ("北京大学第一医院", "http://www.bddyyy.com")],
            "西城区": [("中日友好医院", "http://www.zryhyy.com"), ("北京大学口腔医院", "http://ss.bjmu.edu.cn")],
            "海淀区": [("北京301医院", "http://www.301 hospital.mil.cn"), ("北京大学第三医院", "http://www.puh3.net.cn")],
            "朝阳区": [("北京朝阳医院", "http://www.bjcyh.com"), ("北京中医药大学东方医院", "http://www.dongfang hospital.cn")],
            "黄浦区": [("上海瑞金医院", "http://www.rjh.com.cn"), ("上海华东医院", "http://www.huadonghospital.com")],
            "徐汇区": [("上海第六人民医院", "http://www.6hosp.com"), ("上海第八人民医院", "http://www.8hosp.com")],
            "越秀区": [("中山大学附属第一医院", "http://www.gzsums.edu.cn"), ("广东省人民医院", "http://www.gdhospital.com.cn")],
            "天河区": [("中山大学附属第三医院", "http://zssy.gzsums.edu.cn"), ("暨南大学附属第一医院", "http://www.jnu.edu.cn")],
            "罗湖区": [("深圳市人民医院", "http://www.szph.com"), ("深圳市第二人民医院", "http://www.szsyy.com")],
            "福田区": [("北京大学深圳医院", "http://www.pkuszh.com"), ("深圳市中医院", "http://www.szszyy.com")],
            "玄武区": [("南京市鼓楼医院", "http://www.njglyy.com"), ("南京市第一医院", "http://www.njsdyy.com")],
            "姑苏区": [("苏州大学附属第一医院", "http://www.sdfyy.cn"), ("苏州市立医院", "http://www.szph.com")],
            "上城区": [("浙江大学医学院附属第一医院", "http://www.zy91.com"), ("杭州市第一人民医院", "http://www.hz1y.cn")],
            "海曙区": [("宁波市第一医院", "http://www.nbdyyy.com"), ("宁波市医疗中心", "http://www.nbch.com")]
        }
        
        # 获取所有区县ID并添加医院
        all_districts = db.get_all_districts_detailed(page=1, page_size=1000)
        for district in all_districts["items"]:
            district_name = district["name"]
            hospitals = hospitals_data.get(district_name, [])
            for hospital_name, website in hospitals:
                try:
                    hospital_id = db.upsert_hospital(district["id"], hospital_name, website)
                    print(f"  ✅ 添加医院: {hospital_name}")
                except Exception as e:
                    print(f"  ⚠️  添加医院失败: {hospital_name}, {e}")
        
        print("✅ 示例数据初始化完成")
        return True
        
    except Exception as e:
        print(f"❌ 初始化示例数据失败: {e}")
        return False


def demonstrate_database_operations():
    """演示数据库操作"""
    print("\n" + "="*50)
    print("🗄️  数据库操作演示")
    print("="*50)
    
    # 获取统计数据
    stats = db.get_statistics()
    print(f"\n📊 数据库统计:")
    print(f"  省份数量: {stats.get('province_count', 0)}")
    print(f"  城市数量: {stats.get('city_count', 0)}")
    print(f"  区县数量: {stats.get('district_count', 0)}")
    print(f"  医院数量: {stats.get('hospital_count', 0)}")
    
    # 演示层级查询
    print(f"\n🔍 层级查询演示:")
    
    # 查询省份
    provinces = db.get_all_provinces(page=1, page_size=5)
    print(f"  省份示例: {[p['name'] for p in provinces['items']]}")
    
    if provinces['items']:
        province_name = provinces['items'][0]['name']
        
        # 查询城市
        cities = db.get_cities_by_province(province_name, page=1, page_size=5)
        print(f"  {province_name}的城市: {[c['name'] for c in cities['items']]}")
        
        if cities['items']:
            city_name = cities['items'][0]['name']
            
            # 查询区县
            districts = db.get_districts_by_city(city_name, page=1, page_size=5)
            print(f"  {city_name}的区县: {[d['name'] for d in districts['items']]}")
            
            if districts['items']:
                district_name = districts['items'][0]['name']
                
                # 查询医院
                hospitals = db.get_hospitals_by_district(district_name, page=1, page_size=5)
                print(f"  {district_name}的医院: {[h['name'] for h in hospitals['items']]}")
    
    # 演示搜索
    print(f"\n🔍 搜索演示:")
    search_result = db.search_hospitals("人民", page=1, page_size=10)
    print(f"  搜索'人民'的医院: {search_result['total']} 个")
    if search_result['items']:
        print(f"  示例: {[h['name'] for h in search_result['items'][:5]]}")


def demonstrate_task_management():
    """演示任务管理"""
    print("\n" + "="*50)
    print("📋 任务管理演示")
    print("="*50)
    
    try:
        task_manager = TaskManager()
        
        # 创建任务
        print("\n🔄 创建刷新任务...")
        task_id = asyncio.run(task_manager.create_refresh_task("full"))
        print(f"  任务ID: {task_id}")
        
        # 启动任务
        print("  启动任务...")
        success = asyncio.run(task_manager.start_task(task_id))
        print(f"  启动状态: {'成功' if success else '失败'}")
        
        # 监控任务进度
        print("\n  监控任务进度:")
        for i in range(10):  # 最多监控10秒
            task_status = task_manager.get_task_status(task_id)
            if task_status:
                status = task_status["status"]
                progress = task_status["progress"]
                current_step = task_status["current_step"]
                
                print(f"    {i+1}. 状态: {status}, 进度: {progress}%, 步骤: {current_step}")
                
                if status in ["succeeded", "failed"]:
                    break
            
            time.sleep(1)
        
        # 列出所有任务
        print("\n📋 任务列表:")
        all_tasks = task_manager.list_tasks()
        for task in all_tasks[:3]:  # 显示前3个任务
            print(f"  任务ID: {task['id']}")
            print(f"    类型: {task['type']}")
            print(f"    状态: {task['status']}")
            print(f"    进度: {task['progress']}%")
            print(f"    创建时间: {task['created_at']}")
            print()
        
    except Exception as e:
        print(f"❌ 任务管理演示失败: {e}")


def show_api_endpoints():
    """显示API端点说明"""
    print("\n" + "="*50)
    print("🌐 API接口说明")
    print("="*50)
    
    endpoints = {
        "基础接口": [
            "GET  / - 根路径",
            "GET  /health - 健康检查",
            "GET  /statistics - 数据统计"
        ],
        "刷新接口": [
            "POST /refresh/all - 全量刷新",
            "POST /refresh/province/{province_name} - 指定省刷新"
        ],
        "查询接口": [
            "GET  /provinces - 省份列表 (支持分页)",
            "GET  /cities?province= - 城市列表 (按省份查询)",
            "GET  /districts?city= - 区县列表 (按城市查询)",
            "GET  /hospitals?district= - 医院列表 (按区县查询)",
            "GET  /hospitals/search?q= - 医院搜索 (模糊搜索)"
        ],
        "任务管理": [
            "GET  /tasks/{task_id} - 查看任务状态",
            "GET  /tasks - 任务列表",
            "GET  /tasks/active - 活跃任务",
            "DELETE /tasks/{task_id} - 取消任务",
            "POST /tasks/cleanup - 清理旧任务"
        ]
    }
    
    for category, endpoints_list in endpoints.items():
        print(f"\n📋 {category}:")
        for endpoint in endpoints_list:
            print(f"  {endpoint}")
    
    print(f"\n📚 API文档:")
    print(f"  Swagger UI: http://localhost:8000/docs")
    print(f"  ReDoc: http://localhost:8000/redoc")


def main():
    """主函数"""
    print("🏥 医院层级扫查微服务演示")
    print("="*50)
    print(f"⏰ 演示时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 显示API接口说明
    show_api_endpoints()
    
    # 初始化示例数据
    if not init_sample_data():
        print("❌ 无法继续演示")
        return
    
    # 演示数据库操作
    demonstrate_database_operations()
    
    # 演示任务管理
    demonstrate_task_management()
    
    print("\n" + "="*50)
    print("✅ 演示完成!")
    print("="*50)
    print("\n🚀 可以使用以下方式启动服务:")
    print("  方式1: python main.py")
    print("  方式2: ./start.sh")
    print("  方式3: uvicorn main:app --host 0.0.0.0 --port 8000")
    print("\n📖 服务启动后，访问:")
    print("  API文档: http://localhost:8000/docs")
    print("  健康检查: http://localhost:8000/health")
    print("  测试客户端: python test_api.py")


if __name__ == "__main__":
    main()
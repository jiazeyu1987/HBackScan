#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库层功能演示脚本
展示完整的医院数据库操作功能
"""

from db import db
import json


def print_section(title):
    """打印分节标题"""
    print(f"\n{'='*50}")
    print(f" {title}")
    print('='*50)


def demo_basic_crud():
    """演示基本CRUD操作"""
    print_section("基本CRUD操作演示")
    
    # 1. 创建省份
    print("\n1. 创建省份")
    province_id = db.upsert_province("浙江省", "ZJ")
    print(f"   创建浙江省，ID: {province_id}")
    
    # 2. 查询省份
    print("\n2. 查询省份")
    province = db.get_province(province_id)
    print(f"   查询结果: {province}")
    
    # 3. 更新省份
    print("\n3. 更新省份")
    db.update_province(province_id, code="ZJ-2024")
    updated_province = db.get_province(province_id)
    print(f"   更新后: {updated_province['code']}")
    
    # 4. 创建城市
    print("\n4. 创建城市")
    city_id = db.upsert_city(province_id, "杭州市", "HZ")
    print(f"   创建杭州市，ID: {city_id}")
    
    # 5. 创建区县
    print("\n5. 创建区县")
    district_id = db.upsert_district(city_id, "西湖区", "XH")
    print(f"   创建西湖区，ID: {district_id}")
    
    # 6. 创建医院
    print("\n6. 创建医院")
    hospital_id = db.upsert_hospital(district_id, "浙江大学医学院附属第一医院", 
                                   "http://www.zy91.com", 0.98)
    print(f"   创建医院，ID: {hospital_id}")
    
    return province_id, city_id, district_id, hospital_id


def demo_query_methods(province_id, city_id, district_id):
    """演示查询方法"""
    print_section("查询方法演示")
    
    # 1. 按省查询城市
    print("\n1. 按省份ID查询城市")
    cities = db.get_cities_by_province_id(province_id, page=1, page_size=10)
    print(f"   浙江省城市数量: {cities['total']}")
    for city in cities['items']:
        print(f"   - {city['name']} ({city['code']})")
    
    # 2. 按市查询区县
    print("\n2. 按城市ID查询区县")
    districts = db.get_districts_by_city_id(city_id, page=1, page_size=10)
    print(f"   杭州市区县数量: {districts['total']}")
    for district in districts['items']:
        print(f"   - {district['name']} ({district['code']})")
    
    # 3. 按区县查询医院
    print("\n3. 按区县ID查询医院")
    hospitals = db.get_hospitals_by_district_id(district_id, page=1, page_size=10)
    print(f"   西湖区医院数量: {hospitals['total']}")
    for hospital in hospitals['items']:
        print(f"   - {hospital['name']}")
        print(f"     网站: {hospital['website']}")
        print(f"     置信度: {hospital['llm_confidence']}")
    
    # 4. 医院搜索
    print("\n4. 医院模糊搜索")
    search_results = db.search_hospitals("医院", page=1, page_size=10)
    print(f"   搜索'医院'结果: {search_results['total']}条")
    for hospital in search_results['items']:
        print(f"   - {hospital['name']} ({hospital['province_name']})")


def demo_detailed_queries():
    """演示详细查询方法"""
    print_section("详细查询方法演示")
    
    # 1. 获取所有城市（包含省份信息）
    print("\n1. 获取所有城市（包含省份信息）")
    cities_detailed = db.get_all_cities_detailed(page=1, page_size=10)
    print(f"   城市总数: {cities_detailed['total']}")
    for city in cities_detailed['items'][:3]:  # 只显示前3条
        print(f"   - {city['name']} ({city['province_name']})")
    
    # 2. 获取所有区县（包含城市和省份信息）
    print("\n2. 获取所有区县（包含城市和省份信息）")
    districts_detailed = db.get_all_districts_detailed(page=1, page_size=10)
    print(f"   区县总数: {districts_detailed['total']}")
    for district in districts_detailed['items'][:3]:  # 只显示前3条
        print(f"   - {district['name']} ({district['city_name']}, {district['province_name']})")
    
    # 3. 获取所有医院（包含完整地理信息）
    print("\n3. 获取所有医院（包含完整地理信息）")
    hospitals_detailed = db.get_all_hospitals_detailed(page=1, page_size=10)
    print(f"   医院总数: {hospitals_detailed['total']}")
    for hospital in hospitals_detailed['items'][:3]:  # 只显示前3条
        print(f"   - {hospital['name']}")
        print(f"     位置: {hospital['district_name']} - {hospital['city_name']} - {hospital['province_name']}")


def demo_batch_operations():
    """演示批量操作"""
    print_section("批量操作演示")
    
    # 1. 批量创建省份
    print("\n1. 批量创建省份")
    provinces_data = [
        {"name": "江苏省", "code": "JS"},
        {"name": "山东省", "code": "SD"},
        {"name": "河南省", "code": "HN"}
    ]
    province_ids = db.batch_create_provinces(provinces_data)
    print(f"   批量创建省份ID: {province_ids}")
    
    # 2. 批量创建城市
    print("\n2. 批量创建城市")
    cities_data = [
        {"province_id": province_ids[0], "name": "南京市", "code": "NJ"},
        {"province_id": province_ids[0], "name": "苏州市", "code": "SZ"},
        {"province_id": province_ids[1], "name": "济南市", "code": "JN"}
    ]
    city_ids = db.batch_create_cities(cities_data)
    print(f"   批量创建城市ID: {city_ids}")
    
    # 3. 批量创建区县
    print("\n3. 批量创建区县")
    districts_data = [
        {"city_id": city_ids[0], "name": "玄武区", "code": "XW"},
        {"city_id": city_ids[0], "name": "秦淮区", "code": "QH"},
        {"city_id": city_ids[1], "name": "姑苏区", "code": "GS"}
    ]
    district_ids = db.batch_create_districts(districts_data)
    print(f"   批量创建区县ID: {district_ids}")
    
    # 4. 批量创建医院
    print("\n4. 批量创建医院")
    hospitals_data = [
        {"district_id": district_ids[0], "name": "南京鼓楼医院", "website": "http://www.njglyy.com"},
        {"district_id": district_ids[0], "name": "南京市第一医院", "website": "http://www.njsdyyy.com"},
        {"district_id": district_ids[1], "name": "苏州大学附属第一医院", "website": "http://www.sdfyy.com"}
    ]
    hospital_ids = db.batch_create_hospitals(hospitals_data)
    print(f"   批量创建医院ID: {hospital_ids}")
    
    return province_ids, city_ids, district_ids, hospital_ids


def demo_statistics():
    """演示统计功能"""
    print_section("数据库统计信息")
    
    stats = db.get_statistics()
    
    print("\n1. 表记录统计:")
    print(f"   省份数量: {stats['province_count']}")
    print(f"   城市数量: {stats['city_count']}")
    print(f"   区县数量: {stats['district_count']}")
    print(f"   医院数量: {stats['hospital_count']}")
    print(f"   任务数量: {stats['task_count']}")
    
    print("\n2. 各省份城市数量:")
    for province in stats['provinces_with_cities']:
        print(f"   - {province['name']}: {province['city_count']}个城市")
    
    print("\n3. 医院数量最多的区县:")
    for district in stats['top_districts_by_hospitals'][:5]:
        print(f"   - {district['province_name']} {district['city_name']} {district['district_name']}: {district['hospital_count']}家医院")


def demo_task_management():
    """演示任务管理"""
    print_section("任务管理演示")
    
    # 1. 创建任务
    print("\n1. 创建任务")
    db.create_task("task_scan_2024_001", "广东省医院数据扫描", "running", 0.3)
    db.create_task("task_scan_2024_002", "江苏省医院数据扫描", "pending", 0.0)
    db.create_task("task_scan_2024_003", "山东省医院数据扫描", "completed", 1.0, "任务成功完成")
    print("   创建了3个任务")
    
    # 2. 查询任务
    print("\n2. 查询任务")
    task = db.get_task("task_scan_2024_001")
    print(f"   任务详情: {task}")
    
    # 3. 更新任务
    print("\n3. 更新任务")
    db.update_task("task_scan_2024_001", status="completed", progress=1.0, error=None)
    updated_task = db.get_task("task_scan_2024_001")
    print(f"   更新后状态: {updated_task['status']}, 进度: {updated_task['progress']}")


def main():
    """主演示函数"""
    print("🏥 医院数据库层功能演示")
    print("展示完整的数据库CRUD操作和查询功能")
    
    try:
        # 基本CRUD操作演示
        province_id, city_id, district_id, hospital_id = demo_basic_crud()
        
        # 查询方法演示
        demo_query_methods(province_id, city_id, district_id)
        
        # 详细查询方法演示
        demo_detailed_queries()
        
        # 批量操作演示
        demo_batch_operations()
        
        # 统计信息演示
        demo_statistics()
        
        # 任务管理演示
        demo_task_management()
        
        print_section("演示完成")
        print("✅ 所有数据库功能演示成功完成！")
        print("\n📊 数据库文件位置: data/hospitals.db")
        print("📝 日志文件位置: logs/ai_debug.log")
        
    except Exception as e:
        print(f"❌ 演示过程中出现错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
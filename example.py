#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
阿里百炼LLM客户端使用示例
"""

from llm_client import DashScopeLLMClient


def example_usage():
    """使用示例"""
    
    # 方式1：通过环境变量设置API密钥
    # export DASHSCOPE_API_KEY="your-api-key-here"
    # client = DashScopeLLMClient()
    
    # 方式2：直接传入API密钥
    client = DashScopeLLMClient(
        api_key="your-api-key-here",  # 请替换为实际的API密钥
        # proxy="http://proxy.company.com:8080"  # 可选：如果需要代理
    )
    
    try:
        # 1. 获取所有省份
        print("=== 获取省份列表 ===")
        provinces = client.get_provinces()
        print(f"共获取到 {len(provinces['items'])} 个省级行政区域")
        
        # 显示前几个省份
        for i, province in enumerate(provinces['items'][:5]):
            print(f"{i+1}. {province['name']}")
        
        # 2. 获取特定省份的城市
        if provinces['items']:
            province_name = provinces['items'][0]['name']  # 使用第一个省份
            print(f"\n=== 获取{province_name}的市级数据 ===")
            cities = client.get_cities(province_name)
            print(f"共获取到 {len(cities['items'])} 个市级行政区域")
            
            # 显示前几个城市
            for i, city in enumerate(cities['items'][:5]):
                print(f"{i+1}. {city['name']}")
        
        # 3. 获取特定城市的区县
        if provinces['items'] and cities['items']:
            # 尝试获取广东省的广州市数据
            print(f"\n=== 获取广州市的区县级数据 ===")
            districts = client.get_districts("广州市")
            print(f"共获取到 {len(districts['items'])} 个区县级行政区域")
            
            # 显示前几个区县
            for i, district in enumerate(districts['items'][:5]):
                print(f"{i+1}. {district['name']}")
        
        # 4. 获取特定区县的医院
        if districts['items']:
            district_name = districts['items'][0]['name']  # 使用第一个区县
            print(f"\n=== 获取{district_name}的医院数据 ===")
            hospitals = client.get_hospitals(district_name)
            print(f"共获取到 {len(hospitals['items'])} 个医院")
            
            # 显示前几个医院
            for i, hospital in enumerate(hospitals['items'][:3]):
                print(f"{i+1}. {hospital['name']}")
                print(f"   网站: {hospital.get('website', 'N/A')}")
                print(f"   可信度: {hospital.get('confidence', 0.7)}")
        
        print("\n✅ 所有示例执行完成")
        
    except Exception as e:
        print(f"❌ 执行失败: {e}")


def batch_query_example():
    """批量查询示例"""
    client = DashScopeLLMClient(api_key="your-api-key-here")
    
    # 批量查询多个省份的城市
    provinces_to_query = ["广东省", "江苏省", "浙江省"]
    
    for province in provinces_to_query:
        try:
            print(f"\n=== 查询{province}的市级数据 ===")
            cities = client.get_cities(province)
            print(f"{province}共有 {len(cities['items'])} 个市级行政区域")
            
            # 显示前3个
            for city in cities['items'][:3]:
                print(f"- {city['name']}")
                
        except Exception as e:
            print(f"查询{province}失败: {e}")


if __name__ == "__main__":
    example_usage()
    print("\n" + "="*50)
    batch_query_example()
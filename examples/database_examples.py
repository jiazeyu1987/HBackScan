#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库操作示例
展示如何使用医院扫描仪项目的数据库管理系统

主要功能：
1. 数据库初始化和连接管理
2. 基础数据操作（增删改查）
3. 层级数据查询（省市区医院）
4. 统计和分析功能
5. 事务处理和错误恢复
6. 数据导入导出
"""

import sys
import os
import json
import sqlite3
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from contextlib import contextmanager

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db import DatabaseManager, db


class HospitalDatabaseExamples:
    """医院数据库操作示例类"""
    
    def __init__(self, db_manager: DatabaseManager):
        """
        初始化数据库示例类
        
        Args:
            db_manager: 数据库管理器实例
        """
        self.db = db_manager
        self.setup_logging()
    
    def setup_logging(self):
        """设置日志"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def demo_database_connection(self):
        """演示数据库连接管理"""
        print("\n" + "=" * 60)
        print("数据库连接管理演示")
        print("=" * 60)
        
        try:
            # 1. 测试连接
            print("\n1. 测试数据库连接")
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT sqlite_version()")
                version = cursor.fetchone()[0]
                print(f"SQLite版本: {version}")
                print(f"数据库路径: {self.db.db_path}")
            
            # 2. 检查数据库结构
            print("\n2. 检查数据库表结构")
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name NOT LIKE 'sqlite_%'
                    ORDER BY name
                """)
                tables = cursor.fetchall()
                print(f"数据库中的表: {[table[0] for table in tables]}")
                
                # 查看每个表的结构
                for table in tables:
                    table_name = table[0]
                    print(f"\n表 {table_name} 的结构:")
                    cursor.execute(f"PRAGMA table_info({table_name})")
                    columns = cursor.fetchall()
                    for col in columns:
                        print(f"  - {col[1]} {col[2]} {'(PK)' if col[5] else ''}")
            
            # 3. 测试事务
            print("\n3. 测试事务处理")
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                # 插入测试数据
                test_id = f"test_{int(datetime.now().timestamp())}"
                cursor.execute("""
                    INSERT INTO test_data (id, name, created_at) 
                    VALUES (?, ?, ?)
                """, (test_id, "测试记录", datetime.now()))
                
                # 查询验证
                cursor.execute("SELECT * FROM test_data WHERE id = ?", (test_id,))
                result = cursor.fetchone()
                if result:
                    print(f"插入成功: {result[1]}")
                
                # 回滚测试
                conn.rollback()
                cursor.execute("SELECT COUNT(*) FROM test_data WHERE id = ?", (test_id,))
                count = cursor.fetchone()[0]
                print(f"回滚后记录数: {count} (应该为0)")
        
        except Exception as e:
            print(f"数据库连接演示失败: {e}")
    
    def demo_basic_operations(self):
        """演示基础数据操作"""
        print("\n" + "=" * 60)
        print("基础数据操作演示")
        print("=" * 60)
        
        try:
            # 1. 查询省份
            print("\n1. 查询省份数据")
            provinces = self.db.get_all_provinces(1, 10)
            print(f"省份总数: {provinces['total']}")
            print("前5个省份:")
            for i, province in enumerate(provinces['items'][:5], 1):
                print(f"  {i}. {province['name']} (编码: {province['code']})")
                print(f"     ID: {province['id']}")
                print(f"     更新时间: {province['updated_at']}")
            
            # 2. 查询城市
            print("\n2. 查询城市数据")
            if provinces['items']:
                province_name = provinces['items'][0]['name']
                cities = self.db.get_cities_by_province(province_name, 1, 10)
                print(f"省份 '{province_name}' 的城市数: {cities['total']}")
                print("前5个城市:")
                for i, city in enumerate(cities['items'][:5], 1):
                    print(f"  {i}. {city['name']} (编码: {city['code']})")
                    print(f"     省份ID: {city['province_id']}")
            
            # 3. 查询区县
            print("\n3. 查询区县数据")
            if cities['items']:
                city_name = cities['items'][0]['name']
                districts = self.db.get_districts_by_city(city_name, 1, 10)
                print(f"城市 '{city_name}' 的区县数: {districts['total']}")
                print("前5个区县:")
                for i, district in enumerate(districts['items'][:5], 1):
                    print(f"  {i}. {district['name']} (编码: {district['code']})")
                    print(f"     城市ID: {district['city_id']}")
            
            # 4. 查询医院
            print("\n4. 查询医院数据")
            if districts['items']:
                district_name = districts['items'][0]['name']
                hospitals = self.db.get_hospitals_by_district(district_name, 1, 10)
                print(f"区县 '{district_name}' 的医院数: {hospitals['total']}")
                print("前5个医院:")
                for i, hospital in enumerate(hospitals['items'][:5], 1):
                    print(f"  {i}. {hospital['name']}")
                    print(f"     区县ID: {hospital['district_id']}")
                    if hospital.get('website'):
                        print(f"     官网: {hospital['website']}")
                    if hospital.get('llm_confidence'):
                        print(f"     LLM可信度: {hospital['llm_confidence']:.2f}")
        
        except Exception as e:
            print(f"基础操作演示失败: {e}")
    
    def demo_search_operations(self):
        """演示搜索操作"""
        print("\n" + "=" * 60)
        print("搜索操作演示")
        print("=" * 60)
        
        try:
            # 1. 医院名称搜索
            print("\n1. 医院名称搜索")
            search_terms = ["医院", "医疗", "中心"]
            
            for term in search_terms:
                print(f"\n搜索关键词: '{term}'")
                results = self.db.search_hospitals(term, 1, 5)
                print(f"搜索结果数: {results['total']}")
                
                for i, hospital in enumerate(results['items'][:3], 1):
                    print(f"  {i}. {hospital['name']}")
                    if hospital.get('website'):
                        print(f"     官网: {hospital['website']}")
            
            # 2. 模糊搜索演示
            print(f"\n2. 模糊搜索示例")
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                # 搜索包含"人民"的医院
                cursor.execute("""
                    SELECT name, website, llm_confidence, updated_at 
                    FROM hospitals 
                    WHERE name LIKE '%人民%' 
                    ORDER BY updated_at DESC 
                    LIMIT 5
                """)
                
                results = cursor.fetchall()
                print(f"包含'人民'的医院数: {len(results)}")
                
                for i, result in enumerate(results, 1):
                    print(f"  {i}. {result[0]}")
                    if result[1]:
                        print(f"     官网: {result[1]}")
                    if result[2]:
                        print(f"     LLM可信度: {result[2]:.2f}")
        
        except Exception as e:
            print(f"搜索操作演示失败: {e}")
    
    def demo_statistics_analysis(self):
        """演示统计和分析功能"""
        print("\n" + "=" * 60)
        print("统计和分析功能演示")
        print("=" * 60)
        
        try:
            # 1. 基本统计
            print("\n1. 数据统计概览")
            stats = self.db.get_statistics()
            print(f"省份数: {stats.get('province_count', 0)}")
            print(f"城市数: {stats.get('city_count', 0)}")
            print(f"区县数: {stats.get('district_count', 0)}")
            print(f"医院数: {stats.get('hospital_count', 0)}")
            
            # 2. 省份城市分布统计
            print("\n2. 省份城市分布统计")
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                # 各省份城市数量统计
                cursor.execute("""
                    SELECT p.name as province_name, COUNT(c.id) as city_count
                    FROM provinces p
                    LEFT JOIN cities c ON p.id = c.province_id
                    GROUP BY p.id, p.name
                    ORDER BY city_count DESC
                    LIMIT 10
                """)
                
                results = cursor.fetchall()
                print("城市数量最多的10个省份:")
                for i, result in enumerate(results, 1):
                    print(f"  {i}. {result[0]}: {result[1]} 个城市")
            
            # 3. 区县医院分布统计
            print("\n3. 区县医院分布统计")
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                # 各区县医院数量统计
                cursor.execute("""
                    SELECT d.name as district_name, c.name as city_name, COUNT(h.id) as hospital_count
                    FROM districts d
                    LEFT JOIN cities c ON d.city_id = c.id
                    LEFT JOIN hospitals h ON d.id = h.district_id
                    GROUP BY d.id, d.name, c.name
                    ORDER BY hospital_count DESC
                    LIMIT 10
                """)
                
                results = cursor.fetchall()
                print("医院数量最多的10个区县:")
                for i, result in enumerate(results, 1):
                    print(f"  {i}. {result[1]} - {result[0]}: {result[2]} 个医院")
            
            # 4. 医院官网统计分析
            print("\n4. 医院官网统计分析")
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                # 统计有官网的医院数量
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_hospitals,
                        COUNT(website) as hospitals_with_website,
                        COUNT(*) - COUNT(website) as hospitals_without_website,
                        ROUND(COUNT(website) * 100.0 / COUNT(*), 2) as website_percentage
                    FROM hospitals
                """)
                
                result = cursor.fetchone()
                print(f"总医院数: {result[0]}")
                print(f"有官网的医院: {result[1]}")
                print(f"无官网的医院: {result[2]}")
                print(f"官网覆盖率: {result[3]}%")
            
            # 5. LLM可信度分析
            print("\n5. LLM可信度分析")
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                # 统计LLM可信度分布
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total,
                        AVG(llm_confidence) as avg_confidence,
                        MIN(llm_confidence) as min_confidence,
                        MAX(llm_confidence) as max_confidence,
                        COUNT(CASE WHEN llm_confidence >= 0.8 THEN 1 END) as high_confidence_count,
                        COUNT(CASE WHEN llm_confidence < 0.5 THEN 1 END) as low_confidence_count
                    FROM hospitals 
                    WHERE llm_confidence IS NOT NULL
                """)
                
                result = cursor.fetchone()
                if result[0] > 0:
                    print(f"有可信度评分的医院数: {result[0]}")
                    print(f"平均可信度: {result[1]:.3f}")
                    print(f"最低可信度: {result[2]:.3f}")
                    print(f"最高可信度: {result[3]:.3f}")
                    print(f"高可信度医院数(>=0.8): {result[4]}")
                    print(f"低可信度医院数(<0.5): {result[5]}")
        
        except Exception as e:
            print(f"统计分析演示失败: {e}")
    
    def demo_data_export_import(self):
        """演示数据导入导出"""
        print("\n" + "=" * 60)
        print("数据导入导出演示")
        print("=" * 60)
        
        try:
            # 1. 导出省份数据为JSON
            print("\n1. 导出省份数据")
            provinces = self.db.get_all_provinces(1, 100)
            
            export_data = {
                "export_time": datetime.now().isoformat(),
                "total_count": provinces['total'],
                "data": provinces['items']
            }
            
            export_file = f"provinces_export_{int(datetime.now().timestamp())}.json"
            with open(export_file, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2, default=str)
            
            print(f"省份数据已导出到: {export_file}")
            print(f"导出记录数: {provinces['total']}")
            
            # 2. 导出医院数据样例
            print("\n2. 导出医院数据样例")
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT h.id, h.name, h.website, h.llm_confidence,
                           d.name as district_name, c.name as city_name, p.name as province_name
                    FROM hospitals h
                    JOIN districts d ON h.district_id = d.id
                    JOIN cities c ON d.city_id = c.id
                    JOIN provinces p ON c.province_id = p.id
                    LIMIT 20
                """)
                
                results = cursor.fetchall()
                
                hospital_data = []
                for result in results:
                    hospital_data.append({
                        "id": result[0],
                        "name": result[1],
                        "website": result[2],
                        "llm_confidence": result[3],
                        "location": {
                            "district": result[4],
                            "city": result[5],
                            "province": result[6]
                        }
                    })
                
                export_file = f"hospitals_export_{int(datetime.now().timestamp())}.json"
                with open(export_file, 'w', encoding='utf-8') as f:
                    json.dump({
                        "export_time": datetime.now().isoformat(),
                        "total_count": len(hospital_data),
                        "data": hospital_data
                    }, f, ensure_ascii=False, indent=2)
                
                print(f"医院数据已导出到: {export_file}")
                print(f"导出记录数: {len(hospital_data)}")
            
            # 3. 数据验证
            print("\n3. 验证导出数据")
            with open(export_file, 'r', encoding='utf-8') as f:
                imported_data = json.load(f)
            
            print(f"验证结果: 成功导入 {len(imported_data['data'])} 条医院记录")
            print(f"导出时间: {imported_data['export_time']}")
            
            # 显示样例数据
            if imported_data['data']:
                sample = imported_data['data'][0]
                print(f"样例记录:")
                print(f"  医院名称: {sample['name']}")
                print(f"  所在位置: {sample['location']['province']} - {sample['location']['city']} - {sample['location']['district']}")
                if sample.get('website'):
                    print(f"  官网: {sample['website']}")
        
        except Exception as e:
            print(f"数据导入导出演示失败: {e}")
    
    def demo_performance_optimization(self):
        """演示性能优化技巧"""
        print("\n" + "=" * 60)
        print("性能优化演示")
        print("=" * 60)
        
        try:
            # 1. 创建索引分析
            print("\n1. 数据库索引分析")
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                # 查看现有索引
                cursor.execute("""
                    SELECT name, tbl_name, sql 
                    FROM sqlite_master 
                    WHERE type='index' AND name NOT LIKE 'sqlite_%'
                """)
                
                indexes = cursor.fetchall()
                print(f"现有索引数: {len(indexes)}")
                for index in indexes:
                    print(f"  - {index[0]} (表: {index[1]})")
            
            # 2. 查询性能测试
            print("\n2. 查询性能测试")
            
            # 测试不带索引的查询
            start_time = datetime.now()
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT h.name, d.name as district, c.name as city
                    FROM hospitals h
                    JOIN districts d ON h.district_id = d.id
                    JOIN cities c ON d.city_id = c.id
                    WHERE h.name LIKE '%医院%'
                    LIMIT 100
                """)
                results = cursor.fetchall()
            end_time = datetime.now()
            
            print(f"模糊搜索查询时间: {(end_time - start_time).total_seconds():.3f}秒")
            print(f"返回结果数: {len(results)}")
            
            # 3. 分页查询性能
            print("\n3. 分页查询性能测试")
            page_sizes = [10, 50, 100]
            
            for page_size in page_sizes:
                start_time = datetime.now()
                provinces = self.db.get_all_provinces(1, page_size)
                end_time = datetime.now()
                
                print(f"分页大小 {page_size}: {(end_time - start_time).total_seconds():.3f}秒, "
                      f"返回 {len(provinces['items'])} 条记录")
            
            # 4. 数据库维护
            print("\n4. 数据库维护操作")
            with self.db.get_connection() as conn:
                cursor = conn.cursor()
                
                # 分析数据库
                cursor.execute("ANALYZE")
                print("数据库分析完成")
                
                # 优化数据库
                cursor.execute("VACUUM")
                print("数据库优化完成")
        
        except Exception as e:
            print(f"性能优化演示失败: {e}")
    
    def run_all_demos(self):
        """运行所有演示"""
        print("医院扫描仪数据库操作示例")
        print("=" * 60)
        print("此演示展示医院扫描仪项目的各种数据库操作功能")
        print("=" * 60)
        
        try:
            self.demo_database_connection()
            self.demo_basic_operations()
            self.demo_search_operations()
            self.demo_statistics_analysis()
            self.demo_data_export_import()
            self.demo_performance_optimization()
            
            print("\n" + "=" * 60)
            print("✅ 所有数据库演示完成！")
            print("=" * 60)
            
        except KeyboardInterrupt:
            print("\n\n演示被用户中断")
        except Exception as e:
            print(f"\n\n演示过程中发生错误: {e}")


def main():
    """主演示函数"""
    try:
        # 使用项目中的数据库管理器
        database_examples = HospitalDatabaseExamples(db)
        database_examples.run_all_demos()
        
    except Exception as e:
        print(f"数据库示例运行失败: {e}")
        print("请确保数据库文件存在且路径正确")


if __name__ == "__main__":
    main()
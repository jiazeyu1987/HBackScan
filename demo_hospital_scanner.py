#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
医院层级扫查系统演示脚本
"""

import requests
import json
import time
import sys

BASE_URL = "http://localhost:8002"

def print_section(title):
    """打印章节标题"""
    print(f"\n{'='*60}")
    print(f"🔹 {title}")
    print('='*60)

def print_response(response, title=""):
    """美化打印响应"""
    if title:
        print(f"\n📋 {title}:")
    if isinstance(response, dict):
        print(json.dumps(response, ensure_ascii=False, indent=2))
    else:
        print(response)

def test_health():
    """测试健康检查"""
    print_section("健康检查")
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print_response(response.json(), "服务状态 ✅")
            return True
        else:
            print(f"❌ 健康检查失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 连接服务失败: {e}")
        return False

def get_provinces():
    """获取省份列表"""
    print_section("获取省份列表")
    try:
        response = requests.get(f"{BASE_URL}/provinces")
        if response.status_code == 200:
            data = response.json()
            print_response(data, "省份列表")
            return data
        else:
            print(f"❌ 获取省份失败: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return None

def refresh_all_data():
    """全量刷新数据"""
    print_section("启动全量数据刷新")
    try:
        response = requests.post(f"{BASE_URL}/refresh/all")
        if response.status_code == 200:
            data = response.json()
            print_response(data, "刷新任务已启动 🔄")
            return data.get('task_id')
        else:
            print(f"❌ 启动刷新失败: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return None

def get_task_status(task_id):
    """获取任务状态"""
    if not task_id:
        return None

    print_section(f"任务状态监控: {task_id}")
    try:
        response = requests.get(f"{BASE_URL}/task/{task_id}")
        if response.status_code == 200:
            data = response.json()
            print_response(data, "任务详情")
            return data
        else:
            print(f"❌ 获取任务状态失败: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return None

def get_all_tasks():
    """获取所有任务列表"""
    print_section("任务列表")
    try:
        response = requests.get(f"{BASE_URL}/tasks")
        if response.status_code == 200:
            tasks = response.json()
            # 简化显示
            print(f"📊 总任务数: {len(tasks)}")
            status_count = {}
            for task in tasks:
                status = task.get('status', 'unknown')
                status_count[status] = status_count.get(status, 0) + 1

            print("📈 任务状态统计:")
            for status, count in status_count.items():
                emoji = "🔄" if status == "running" else "⏳" if status == "pending" else "✅" if status == "completed" else "❌"
                print(f"   {emoji} {status}: {count}")

            # 显示最近几个任务
            print("\n📝 最近任务:")
            for i, task in enumerate(tasks[-3:], 1):
                print(f"   {i}. {task.get('hospital_name', 'N/A')} - {task.get('status', 'N/A')}")

            return tasks
        else:
            print(f"❌ 获取任务列表失败: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return None

def search_hospitals(keyword="协和"):
    """搜索医院"""
    print_section(f"搜索医院: {keyword}")
    try:
        response = requests.get(f"{BASE_URL}/hospitals/search", params={"q": keyword})
        if response.status_code == 200:
            data = response.json()
            print_response(data, "搜索结果")
            return data
        else:
            print(f"❌ 搜索失败: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return None

def scan_hospital(hospital_name):
    """扫描指定医院"""
    print_section(f"扫描医院: {hospital_name}")
    try:
        payload = {
            "hospital_name": hospital_name,
            "query": "获取医院层级结构和详细信息"
        }
        response = requests.post(f"{BASE_URL}/scan", json=payload)
        if response.status_code == 200:
            data = response.json()
            print_response(data, "扫描任务已启动")
            return data.get('task_id')
        else:
            print(f"❌ 扫描失败: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return None

def monitor_task(task_id, max_wait=30):
    """监控任务执行"""
    if not task_id:
        return

    print(f"\n⏱️  监控任务执行: {task_id}")
    start_time = time.time()

    while time.time() - start_time < max_wait:
        task_data = get_task_status(task_id)
        if task_data:
            status = task_data.get('status', 'unknown')
            print(f"   当前状态: {status}")

            if status in ['completed', 'failed']:
                print(f"   任务{'完成' if status == 'completed' else '失败'}")
                if status == 'completed' and task_data.get('result'):
                    try:
                        result = json.loads(task_data['result'])
                        print_response(result, "执行结果")
                    except:
                        print(f"   结果: {task_data['result']}")
                break

        time.sleep(3)

    if time.time() - start_time >= max_wait:
        print(f"   ⏰ 监控超时 ({max_wait}秒)，任务可能仍在执行中")

def main():
    """主演示函数"""
    print("🏥 医院层级扫查系统演示")
    print("=" * 60)

    # 1. 健康检查
    if not test_health():
        print("❌ 服务不可用，请确保服务已启动")
        sys.exit(1)

    # 2. 获取省份数据
    provinces_data = get_provinces()

    # 3. 查看现有任务
    get_all_tasks()

    # 4. 搜索医院
    search_hospitals("协和")

    # 5. 启动全量数据刷新
    refresh_task_id = refresh_all_data()

    # 6. 监控刷新任务（如果启动成功）
    if refresh_task_id:
        print(f"\n🔄 监控全量刷新任务 (最多等待30秒)...")
        monitor_task(refresh_task_id, max_wait=30)

    # 7. 扫描特定医院
    scan_task_id = scan_hospital("北京协和医院")

    # 8. 监控扫描任务（如果启动成功）
    if scan_task_id:
        print(f"\n🔬 监控医院扫描任务 (最多等待20秒)...")
        monitor_task(scan_task_id, max_wait=20)

    # 9. 最终任务状态
    get_all_tasks()

    print_section("演示完成")
    print("📚 更多功能请访问:")
    print(f"   📖 API文档: {BASE_URL}/docs")
    print(f"   🔍 ReDoc: {BASE_URL}/redoc")
    print(f"   ❤️  健康检查: {BASE_URL}/health")

if __name__ == "__main__":
    main()
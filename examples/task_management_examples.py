#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
任务管理示例
展示如何使用医院扫描仪项目的任务管理系统

主要功能：
1. 任务创建和启动
2. 任务状态监控
3. 任务取消和清理
4. 批量任务处理
5. 任务进度跟踪
6. 异步任务管理
"""

import sys
import os
import time
import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tasks import TaskManager, TaskStatus


class TaskManagementExamples:
    """任务管理示例类"""
    
    def __init__(self):
        """初始化任务管理示例"""
        self.task_manager = TaskManager()
        self.setup_logging()
    
    def setup_logging(self):
        """设置日志"""
        import logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def demo_task_creation(self):
        """演示任务创建"""
        print("\n" + "=" * 60)
        print("任务创建演示")
        print("=" * 60)
        
        # 1. 创建全量刷新任务
        print("\n1. 创建全量数据刷新任务")
        try:
            full_task_id = asyncio.run(self.task_manager.create_refresh_task("full"))
            print(f"全量刷新任务已创建: {full_task_id}")
            
            # 启动任务
            asyncio.run(self.task_manager.start_task(full_task_id))
            print("全量刷新任务已启动")
            
        except Exception as e:
            print(f"全量刷新任务创建失败: {e}")
        
        # 2. 创建省份刷新任务
        print("\n2. 创建省份数据刷新任务")
        provinces_to_refresh = ["北京市", "上海市", "广东省"]
        
        province_task_ids = []
        for province in provinces_to_refresh:
            try:
                task_id = asyncio.run(self.task_manager.create_refresh_task("province", province))
                province_task_ids.append((task_id, province))
                print(f"省份 {province} 刷新任务已创建: {task_id}")
                
                # 立即启动任务
                asyncio.run(self.task_manager.start_task(task_id))
                
            except Exception as e:
                print(f"省份 {province} 刷新任务创建失败: {e}")
        
        return full_task_id, province_task_ids
    
    def demo_task_monitoring(self, task_ids: List[str]):
        """演示任务监控"""
        print("\n" + "=" * 60)
        print("任务监控演示")
        print("=" * 60)
        
        # 监控任务状态
        print("\n1. 实时任务状态监控")
        monitoring_tasks = []
        
        for task_id in task_ids:
            if task_id:  # 确保task_id不为None
                monitoring_tasks.append(task_id)
        
        if not monitoring_tasks:
            print("没有可监控的任务")
            return
        
        print(f"开始监控 {len(monitoring_tasks)} 个任务的状态变化...")
        
        # 监控循环
        max_checks = 10
        for check_round in range(max_checks):
            print(f"\n第 {check_round + 1} 次状态检查:")
            print("-" * 40)
            
            all_completed = True
            for task_id in monitoring_tasks:
                try:
                    task = asyncio.run(self.task_manager.get_task_status(task_id))
                    if task:
                        status = task.get('status', 'unknown')
                        progress = task.get('progress', 0)
                        scope = task.get('scope', 'unknown')
                        
                        print(f"任务 {task_id[:8]}... - {scope}")
                        print(f"  状态: {status}")
                        print(f"  进度: {progress:.1f}%")
                        
                        if status not in ['succeeded', 'failed']:
                            all_completed = False
                        
                        # 显示错误信息（如果有）
                        if task.get('error'):
                            print(f"  错误: {task['error']}")
                    else:
                        print(f"任务 {task_id[:8]}... - 任务不存在")
                        
                except Exception as e:
                    print(f"获取任务状态失败 {task_id[:8]}...: {e}")
            
            if all_completed:
                print("\n所有任务已完成监控")
                break
            
            # 等待一段时间再检查
            if check_round < max_checks - 1:
                print("等待5秒后继续检查...")
                time.sleep(5)
    
    def demo_task_operations(self):
        """演示任务操作"""
        print("\n" + "=" * 60)
        print("任务操作演示")
        print("=" * 60)
        
        # 1. 列出所有任务
        print("\n1. 列出所有任务")
        try:
            all_tasks = asyncio.run(self.task_manager.list_tasks())
            if all_tasks:
                print(f"总任务数: {len(all_tasks)}")
                print("最近10个任务:")
                for i, task in enumerate(all_tasks[:10], 1):
                    print(f"  {i}. {task['id'][:8]}... - {task['scope']} - {task['status']}")
            else:
                print("暂无任务")
        except Exception as e:
            print(f"列出任务失败: {e}")
        
        # 2. 按状态过滤任务
        print("\n2. 按状态过滤任务")
        statuses = ['pending', 'running', 'succeeded', 'failed']
        
        for status in statuses:
            try:
                filtered_tasks = asyncio.run(self.task_manager.list_tasks(status))
                print(f"{status}状态的任务数: {len(filtered_tasks)}")
                
                # 显示前3个任务
                for task in filtered_tasks[:3]:
                    print(f"  - {task['id'][:8]}... - 进度: {task['progress']:.1f}%")
                    
            except Exception as e:
                print(f"获取{status}状态任务失败: {e}")
        
        # 3. 获取活跃任务
        print("\n3. 获取活跃任务")
        try:
            active_tasks = asyncio.run(self.task_manager.get_active_tasks())
            print(f"活跃任务数: {len(active_tasks)}")
            
            for task in active_tasks:
                print(f"  - {task['id'][:8]}... - {task['scope']} - {task['status']}")
                
        except Exception as e:
            print(f"获取活跃任务失败: {e}")
        
        # 4. 获取任务统计
        print("\n4. 任务统计信息")
        try:
            all_tasks = asyncio.run(self.task_manager.list_tasks())
            if all_tasks:
                stats = {
                    'pending': 0,
                    'running': 0,
                    'succeeded': 0,
                    'failed': 0
                }
                
                for task in all_tasks:
                    status = task.get('status', 'unknown')
                    if status in stats:
                        stats[status] += 1
                
                total = sum(stats.values())
                print(f"任务统计:")
                print(f"  总计: {total}")
                for status, count in stats.items():
                    percentage = (count / total * 100) if total > 0 else 0
                    print(f"  {status}: {count} ({percentage:.1f}%)")
            else:
                print("暂无任务数据")
        except Exception as e:
            print(f"任务统计失败: {e}")
    
    def demo_task_cancellation(self):
        """演示任务取消"""
        print("\n" + "=" * 60)
        print("任务取消演示")
        print("=" * 60)
        
        # 1. 创建可取消的任务
        print("\n1. 创建可取消的测试任务")
        test_tasks = []
        
        for i in range(3):
            try:
                task_id = asyncio.run(self.task_manager.create_refresh_task("test", f"测试任务{i+1}"))
                test_tasks.append(task_id)
                print(f"测试任务 {i+1} 已创建: {task_id}")
                
                # 启动任务
                asyncio.run(self.task_manager.start_task(task_id))
                
            except Exception as e:
                print(f"测试任务 {i+1} 创建失败: {e}")
        
        # 等待一下让任务开始运行
        time.sleep(2)
        
        # 2. 取消部分任务
        print(f"\n2. 取消 {len(test_tasks)//2} 个任务")
        for i, task_id in enumerate(test_tasks[:len(test_tasks)//2]):
            try:
                success = asyncio.run(self.task_manager.cancel_task(task_id))
                if success:
                    print(f"任务 {task_id[:8]}... 已成功取消")
                else:
                    print(f"任务 {task_id[:8]}... 取消失败")
            except Exception as e:
                print(f"取消任务失败 {task_id[:8]}...: {e}")
        
        # 3. 验证取消结果
        print("\n3. 验证取消结果")
        for task_id in test_tasks:
            try:
                task = asyncio.run(self.task_manager.get_task_status(task_id))
                if task:
                    status = task.get('status', 'unknown')
                    print(f"任务 {task_id[:8]}... 当前状态: {status}")
                else:
                    print(f"任务 {task_id[:8]}... 不存在")
            except Exception as e:
                print(f"检查任务状态失败 {task_id[:8]}...: {e}")
    
    def demo_batch_operations(self):
        """演示批量操作"""
        print("\n" + "=" * 60)
        print("批量操作演示")
        print("=" * 60)
        
        # 1. 创建批量刷新任务
        print("\n1. 创建批量省份刷新任务")
        provinces = ["浙江省", "江苏省", "山东省", "河南省", "四川省"]
        batch_task_ids = []
        
        for province in provinces:
            try:
                task_id = asyncio.run(self.task_manager.create_refresh_task("province", province))
                batch_task_ids.append((task_id, province))
                print(f"省份 {province} 刷新任务已排队: {task_id}")
                
            except Exception as e:
                print(f"省份 {province} 刷新任务创建失败: {e}")
        
        # 2. 并发启动任务
        print(f"\n2. 并发启动 {len(batch_task_ids)} 个任务")
        start_tasks = []
        
        for task_id, province in batch_task_ids:
            try:
                start_tasks.append(
                    (task_id, asyncio.create_task(self.task_manager.start_task(task_id)))
                )
                print(f"启动任务 {province}: {task_id}")
            except Exception as e:
                print(f"启动任务失败 {province}: {e}")
        
        # 3. 监控批量任务
        print("\n3. 监控批量任务执行")
        task_ids = [task_id for task_id, _ in batch_task_ids]
        
        self.demo_task_monitoring(task_ids)
        
        return batch_task_ids
    
    def demo_task_cleanup(self):
        """演示任务清理"""
        print("\n" + "=" * 60)
        print("任务清理演示")
        print("=" * 60)
        
        # 1. 检查清理前的任务数量
        print("\n1. 清理前的任务统计")
        try:
            all_tasks_before = asyncio.run(self.task_manager.list_tasks())
            print(f"清理前任务总数: {len(all_tasks_before)}")
            
            # 按创建时间分类
            now = datetime.now()
            old_tasks = []
            recent_tasks = []
            
            for task in all_tasks_before:
                created_at = task.get('created_at')
                if isinstance(created_at, str):
                    try:
                        created_time = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                        if now - created_time > timedelta(hours=1):
                            old_tasks.append(task)
                        else:
                            recent_tasks.append(task)
                    except:
                        recent_tasks.append(task)
                else:
                    recent_tasks.append(task)
            
            print(f"1小时前的旧任务: {len(old_tasks)}")
            print(f"1小时内的任务: {len(recent_tasks)}")
            
        except Exception as e:
            print(f"统计任务失败: {e}")
        
        # 2. 执行清理操作
        print("\n2. 执行任务清理")
        try:
            # 创建一些旧的测试任务来演示清理
            cleanup_hours = 1
            cleaned_count = asyncio.run(self.task_manager.cleanup_old_tasks(cleanup_hours))
            print(f"清理完成，清理了 {cleaned_count} 个旧任务")
            
        except Exception as e:
            print(f"任务清理失败: {e}")
        
        # 3. 检查清理后的状态
        print("\n3. 清理后的任务统计")
        try:
            all_tasks_after = asyncio.run(self.task_manager.list_tasks())
            print(f"清理后任务总数: {len(all_tasks_after)}")
            print(f"净减少: {len(all_tasks_before) - len(all_tasks_after)}")
            
        except Exception as e:
            print(f"清理后统计失败: {e}")
    
    def demo_error_scenarios(self):
        """演示错误场景处理"""
        print("\n" + "=" * 60)
        print("错误场景演示")
        print("=" * 60)
        
        # 1. 操作不存在的任务
        print("\n1. 操作不存在的任务")
        fake_task_id = "nonexistent_task_12345"
        
        try:
            task = asyncio.run(self.task_manager.get_task_status(fake_task_id))
            print(f"不应该到达这里: {task}")
        except Exception as e:
            print(f"✅ 预期的错误: 获取不存在的任务状态失败 - {type(e).__name__}")
        
        try:
            success = asyncio.run(self.task_manager.cancel_task(fake_task_id))
            print(f"不应该到达这里: {success}")
        except Exception as e:
            print(f"✅ 预期的错误: 取消不存在的任务失败 - {type(e).__name__}")
        
        # 2. 创建无效范围的任务
        print("\n2. 创建无效范围的任务")
        try:
            task_id = asyncio.run(self.task_manager.create_refresh_task("invalid_scope", "测试"))
            print(f"不应该到达这里: {task_id}")
        except Exception as e:
            print(f"✅ 预期的错误: 创建无效范围的任务失败 - {type(e).__name__}")
        
        # 3. 批量任务创建压力测试
        print("\n3. 批量任务创建压力测试")
        try:
            task_ids = []
            for i in range(10):
                task_id = asyncio.run(self.task_manager.create_refresh_task("stress_test", f"压力测试{i+1}"))
                task_ids.append(task_id)
            
            print(f"✅ 成功创建 {len(task_ids)} 个压力测试任务")
            
            # 清理测试任务
            for task_id in task_ids:
                try:
                    asyncio.run(self.task_manager.cancel_task(task_id))
                except:
                    pass
            
            print("✅ 压力测试任务已清理")
            
        except Exception as e:
            print(f"压力测试失败: {e}")
    
    def run_all_demos(self):
        """运行所有演示"""
        print("医院扫描仪任务管理示例")
        print("=" * 60)
        print("此示例展示医院扫描仪项目的任务管理功能")
        print("=" * 60)
        
        try:
            # 演示任务生命周期
            full_task_id, province_tasks = self.demo_task_creation()
            
            # 收集所有任务ID进行监控
            all_task_ids = [full_task_id]
            for task_id, province in province_tasks:
                if task_id:
                    all_task_ids.append(task_id)
            
            if all_task_ids:
                self.demo_task_monitoring(all_task_ids)
            
            self.demo_task_operations()
            self.demo_task_cancellation()
            self.demo_batch_operations()
            self.demo_task_cleanup()
            self.demo_error_scenarios()
            
            print("\n" + "=" * 60)
            print("✅ 所有任务管理演示完成！")
            print("=" * 60)
            
        except KeyboardInterrupt:
            print("\n\n演示被用户中断")
        except Exception as e:
            print(f"\n\n演示过程中发生错误: {e}")
            import traceback
            traceback.print_exc()


def main():
    """主演示函数"""
    try:
        examples = TaskManagementExamples()
        examples.run_all_demos()
        
    except Exception as e:
        print(f"任务管理示例运行失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
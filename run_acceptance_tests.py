#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验收测试运行脚本
执行完整的验收测试套件并生成报告
"""

import os
import sys
import time
import shutil
import argparse
import subprocess
from pathlib import Path
from datetime import datetime


class AcceptanceTestRunner:
    """验收测试运行器"""
    
    def __init__(self, test_dir="tests", report_dir="reports/acceptance"):
        self.test_dir = Path(test_dir)
        self.report_dir = Path(report_dir)
        self.start_time = None
        self.end_time = None
        
    def setup_environment(self):
        """设置测试环境"""
        print("🔧 设置测试环境...")
        
        # 创建报告目录
        self.report_dir.mkdir(parents=True, exist_ok=True)
        
        # 确保测试数据目录存在
        (self.report_dir / "data").mkdir(exist_ok=True)
        
        print(f"✅ 测试环境设置完成，报告目录: {self.report_dir}")
    
    def run_pytest(self, args=None, description=""):
        """运行pytest测试"""
        if args is None:
            args = []
            
        cmd = ["pytest"] + args
        
        print(f"🚀 {description}")
        print(f"执行命令: {' '.join(cmd)}")
        print("-" * 50)
        
        start_time = time.time()
        
        try:
            result = subprocess.run(
                cmd,
                cwd=Path.cwd(),
                capture_output=False,  # 显示实时输出
                text=True
            )
            
            end_time = time.time()
            duration = end_time - start_time
            
            print(f"✅ {description} 完成，耗时: {duration:.2f}秒")
            return result.returncode == 0, duration
            
        except Exception as e:
            print(f"❌ {description} 失败: {e}")
            return False, 0
    
    def run_fast_acceptance_tests(self):
        """运行快速验收测试"""
        args = [
            str(self.test_dir),
            "-v",
            "-m", "acceptance and fast",
            "--html", str(self.report_dir / "fast_acceptance_report.html"),
            "--self-contained-html",
            "--tb=short",
            "--timeout=60"
        ]
        
        return self.run_pytest(args, "快速验收测试")
    
    def run_performance_tests(self):
        """运行性能验收测试"""
        args = [
            str(self.test_dir),
            "-v", 
            "-m", "acceptance and performance",
            "--html", str(self.report_dir / "performance_acceptance_report.html"),
            "--self-contained-html",
            "--tb=short",
            "--timeout=180"
        ]
        
        return self.run_pytest(args, "性能验收测试")
    
    def run_workflow_tests(self):
        """运行工作流验收测试"""
        args = [
            str(self.test_dir / "test_acceptance.py::TestAcceptanceScenarios::test_complete_refresh_workflow"),
            "-v",
            "--html", str(self.report_dir / "workflow_acceptance_report.html"),
            "--self-contained-html",
            "--tb=long",
            "--timeout=300"
        ]
        
        return self.run_pytest(args, "完整工作流验收测试")
    
    def run_complete_acceptance_suite(self):
        """运行完整验收测试套件"""
        args = [
            str(self.test_dir),
            "-v",
            "-m", "acceptance",
            "--html", str(self.report_dir / "complete_acceptance_report.html"),
            "--self-contained-html",
            "--junit-xml", str(self.report_dir / "junit.xml"),
            "--cov=.",
            "--cov-report=html:" + str(self.report_dir / "coverage"),
            "--cov-report=term-missing",
            "--cov-report=xml:" + str(self.report_dir / "coverage.xml"),
            "--cov-fail-under=75",
            "--tb=short",
            "--timeout=300"
        ]
        
        return self.run_pytest(args, "完整验收测试套件")
    
    def generate_summary_report(self, results):
        """生成摘要报告"""
        summary_file = self.report_dir / "acceptance_summary.md"
        
        total_duration = self.end_time - self.start_time if self.start_time and self.end_time else 0
        
        summary_content = f"""# 验收测试执行报告

**执行时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**总耗时**: {total_duration:.2f}秒

## 测试结果概览

"""
        
        for test_name, (success, duration) in results.items():
            status = "✅ 通过" if success else "❌ 失败"
            summary_content += f"- **{test_name}**: {status} (耗时: {duration:.2f}秒)\n"
        
        passed_count = sum(1 for _, (success, _) in results.items() if success)
        total_count = len(results)
        success_rate = (passed_count / total_count * 100) if total_count > 0 else 0
        
        summary_content += f"""
## 测试统计

- **总测试数**: {total_count}
- **通过数**: {passed_count}
- **失败数**: {total_count - passed_count}
- **成功率**: {success_rate:.1f}%

## 生成的报告文件

- 快速验收测试: `fast_acceptance_report.html`
- 性能验收测试: `performance_acceptance_report.html`
- 工作流验收测试: `workflow_acceptance_report.html`
- 完整验收测试: `complete_acceptance_report.html`
- 覆盖率报告: `coverage/index.html`
- JUnit报告: `junit.xml`

## 覆盖率要求

- 最低覆盖率: 75%
- 实际覆盖率: 查看覆盖率报告

## 性能要求

- API响应时间: < 500ms
- 测试完成时间: < 5分钟（主要工作流）

## 验收标准

- [ ] 完整刷新工作流测试通过
- [ ] API性能要求满足
- [ ] 重复刷新防护生效
- [ ] 空数据库初始化正常
- [ ] 部分数据缺失处理正确
- [ ] 网络超时和错误恢复正常
- [ ] 边界条件处理正确
- [ ] 数据一致性验证通过

"""
        
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write(summary_content)
        
        print(f"📄 摘要报告已生成: {summary_file}")
        return summary_file
    
    def copy_logs(self):
        """复制日志文件"""
        logs_source = Path("logs")
        logs_dest = self.report_dir / "logs"
        
        if logs_source.exists():
            shutil.copytree(logs_source, logs_dest, dirs_exist_ok=True)
            print(f"📁 日志文件已复制到: {logs_dest}")
    
    def run(self, test_type="all"):
        """运行验收测试"""
        self.start_time = time.time()
        
        print("🎯 开始执行验收测试套件")
        print(f"📅 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        # 设置环境
        self.setup_environment()
        
        results = {}
        
        # 根据测试类型运行相应的测试
        if test_type == "fast" or test_type == "all":
            success, duration = self.run_fast_acceptance_tests()
            results["快速验收测试"] = (success, duration)
            
            if not success and test_type == "fast":
                print("❌ 快速验收测试失败，停止执行")
                return False
            
            print()
        
        if test_type == "performance" or test_type == "all":
            success, duration = self.run_performance_tests()
            results["性能验收测试"] = (success, duration)
            print()
        
        if test_type == "workflow" or test_type == "all":
            success, duration = self.run_workflow_tests()
            results["工作流验收测试"] = (success, duration)
            print()
        
        if test_type == "complete" or test_type == "all":
            success, duration = self.run_complete_acceptance_suite()
            results["完整验收测试套件"] = (success, duration)
            print()
        
        # 生成报告
        self.end_time = time.time()
        summary_file = self.generate_summary_report(results)
        self.copy_logs()
        
        # 总结结果
        print("\n" + "=" * 60)
        print("📊 验收测试执行完成")
        
        passed_count = sum(1 for _, (success, _) in results.items() if success)
        total_count = len(results)
        success_rate = (passed_count / total_count * 100) if total_count > 0 else 0
        
        print(f"✅ 通过: {passed_count}/{total_count} ({success_rate:.1f}%)")
        print(f"📄 详细报告: {self.report_dir}")
        print(f"📄 摘要报告: {summary_file}")
        
        if success_rate >= 80:  # 80%通过率认为通过
            print("🎉 验收测试总体通过!")
            return True
        else:
            print("❌ 验收测试未达到通过标准")
            return False


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="运行验收测试套件")
    parser.add_argument(
        "--type", 
        choices=["fast", "performance", "workflow", "complete", "all"],
        default="all",
        help="测试类型"
    )
    parser.add_argument(
        "--test-dir",
        default="tests",
        help="测试目录"
    )
    parser.add_argument(
        "--report-dir", 
        default="reports/acceptance",
        help="报告目录"
    )
    
    args = parser.parse_args()
    
    runner = AcceptanceTestRunner(args.test_dir, args.report_dir)
    success = runner.run(args.type)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
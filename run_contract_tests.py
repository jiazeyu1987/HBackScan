#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
契约测试运行器
用于运行和验证API契约测试
"""

import subprocess
import sys
import os
import json
from pathlib import Path

def run_contract_tests():
    """运行契约测试"""
    print("🏗️  开始运行契约测试...")
    
    # 检查测试文件是否存在
    test_file = Path("tests/test_contracts.py")
    if not test_file.exists():
        print(f"❌ 测试文件不存在: {test_file}")
        return False
    
    try:
        # 运行契约测试
        print("📋 运行契约测试...")
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            "tests/test_contracts.py",
            "-v",
            "--tb=short"
        ], capture_output=True, text=True)
        
        # 输出结果
        if result.stdout:
            print("📊 测试输出:")
            print(result.stdout)
        
        if result.stderr:
            print("⚠️ 错误输出:")
            print(result.stderr)
        
        if result.returncode == 0:
            print("✅ 所有契约测试通过!")
            return True
        else:
            print("❌ 契约测试失败!")
            return False
            
    except Exception as e:
        print(f"❌ 运行测试时发生错误: {e}")
        return False

def check_dependencies():
    """检查测试依赖"""
    print("🔍 检查测试依赖...")
    
    required_packages = [
        "pytest",
        "jsonschema", 
        "fastapi",
        "pydantic"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package} - 已安装")
        except ImportError:
            print(f"❌ {package} - 未安装")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n❌ 缺少依赖包: {', '.join(missing_packages)}")
        print("请运行: pip install " + " ".join(missing_packages))
        return False
    
    print("✅ 所有依赖包已安装")
    return True

def validate_api_schema():
    """验证API schema"""
    print("🔍 验证API schema...")
    
    try:
        # 导入FastAPI应用
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        from main import app
        
        # 获取OpenAPI schema
        openapi_schema = app.openapi()
        
        # 检查基本结构
        required_keys = ["openapi", "info", "paths", "components"]
        for key in required_keys:
            if key not in openapi_schema:
                print(f"❌ OpenAPI schema 缺少关键字段: {key}")
                return False
        
        # 检查paths
        paths = openapi_schema.get("paths", {})
        if not paths:
            print("❌ OpenAPI schema 没有定义路径")
            return False
        
        print(f"✅ OpenAPI schema 有效，包含 {len(paths)} 个路径")
        
        # 保存schema到文件
        schema_file = "openapi_schema.json"
        with open(schema_file, 'w', encoding='utf-8') as f:
            json.dump(openapi_schema, f, indent=2, ensure_ascii=False)
        print(f"✅ OpenAPI schema 已保存到: {schema_file}")
        
        return True
        
    except Exception as e:
        print(f"❌ 验证API schema时发生错误: {e}")
        return False

def generate_test_report():
    """生成测试报告"""
    print("📊 生成测试报告...")
    
    try:
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            "tests/test_contracts.py",
            "--html=contract_test_report.html",
            "--self-contained-html"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ 测试报告已生成: contract_test_report.html")
        else:
            print("⚠️ 测试报告生成失败，但测试已运行")
            
    except Exception as e:
        print(f"⚠️ 生成测试报告时发生错误: {e}")

def main():
    """主函数"""
    print("=" * 60)
    print("🧪 契约测试验证工具")
    print("=" * 60)
    
    # 检查依赖
    if not check_dependencies():
        print("\n❌ 依赖检查失败，请安装缺少的包")
        sys.exit(1)
    
    # 验证API schema
    if not validate_api_schema():
        print("\n❌ API schema验证失败")
        sys.exit(1)
    
    # 运行契约测试
    if not run_contract_tests():
        print("\n❌ 契约测试失败")
        sys.exit(1)
    
    # 生成测试报告
    generate_test_report()
    
    print("\n" + "=" * 60)
    print("🎉 契约测试验证完成!")
    print("=" * 60)

if __name__ == "__main__":
    main()
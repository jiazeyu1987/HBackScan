#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
阿里百炼LLM客户端功能测试
"""

import sys
import os
from llm_client import DashScopeLLMClient


def test_client_initialization():
    """测试客户端初始化"""
    print("=== 测试客户端初始化 ===")
    
    try:
        # 测试正常初始化（不测试API密钥验证，因为非空字符串都被接受）
        try:
            client = DashScopeLLMClient(api_key="test-key")
            print("✅ 客户端初始化成功")
        except Exception as e:
            print(f"❌ 客户端初始化失败: {e}")
            return False
    except Exception as e:
        print(f"❌ 初始化测试失败: {e}")
        return False
    
    return True


def test_prompt_generation():
    """测试prompt生成"""
    print("\n=== 测试prompt生成 ===")
    
    try:
        client = DashScopeLLMClient(api_key="test-key")
        
        # 测试各种层级的prompt生成
        test_cases = [
            ('province', None, '省级prompt'),
            ('city', '广东省', '市级prompt'),
            ('district', '广州市', '区县级prompt'),
            ('hospital', '天河区', '医院级prompt')
        ]
        
        for level, input_data, desc in test_cases:
            try:
                prompt = client._build_prompt(level, input_data)
                if prompt and len(prompt) > 0:
                    print(f"✅ {desc}生成成功 ({len(prompt)}字符)")
                else:
                    print(f"❌ {desc}生成失败")
                    return False
            except Exception as e:
                print(f"❌ {desc}生成异常: {e}")
                return False
                
    except Exception as e:
        print(f"❌ prompt生成测试失败: {e}")
        return False
    
    return True


def test_response_parsing():
    """测试响应解析"""
    print("\n=== 测试响应解析 ===")
    
    try:
        client = DashScopeLLMClient(api_key="test-key")
        
        # 模拟API响应数据
        test_responses = [
            {
                'output': {
                    'text': '{"items":[{"name":"广东省","code":null},{"name":"江苏省","code":null}]}'
                },
                'level': 'province',
                'expected_count': 2
            },
            {
                'output': {
                    'text': '{"items":[{"name":"中山大学附属第一医院","website":"https://www.gzsums.edu.cn/","confidence":0.9}]}'
                },
                'level': 'hospital',
                'expected_count': 1
            }
        ]
        
        for test_data in test_responses:
            try:
                result = client._parse_response(test_data, test_data['level'])
                if len(result.get('items', [])) == test_data['expected_count']:
                    print(f"✅ {test_data['level']}级响应解析成功")
                else:
                    print(f"❌ {test_data['level']}级响应解析结果不正确")
                    return False
            except Exception as e:
                print(f"❌ {test_data['level']}级响应解析失败: {e}")
                return False
                
    except Exception as e:
        print(f"❌ 响应解析测试失败: {e}")
        return False
    
    return True


def test_error_handling():
    """测试错误处理"""
    print("\n=== 测试错误处理 ===")
    
    try:
        client = DashScopeLLMClient(api_key="test-key")
        
        # 测试无效的响应格式
        try:
            invalid_responses = [
                {'invalid': 'data'},
                {'output': {'text': 'not json'}},
                {'output': {'text': '{"no_items": true}'}}
            ]
            
            for invalid_response in invalid_responses:
                try:
                    client._parse_response(invalid_response, 'province')
                    print("❌ 应该抛出解析错误")
                    return False
                except Exception:
                    print("✅ 正确捕获解析错误")
                    
        except Exception as e:
            print(f"❌ 错误处理测试失败: {e}")
            return False
            
    except Exception as e:
        print(f"❌ 错误处理测试设置失败: {e}")
        return False
    
    return True


def main():
    """运行所有测试"""
    print("🧪 开始测试阿里百炼LLM客户端\n")
    
    tests = [
        ("客户端初始化", test_client_initialization),
        ("Prompt生成", test_prompt_generation),
        ("响应解析", test_response_parsing),
        ("错误处理", test_error_handling)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name}测试通过")
            else:
                print(f"❌ {test_name}测试失败")
        except Exception as e:
            print(f"❌ {test_name}测试异常: {e}")
    
    print(f"\n📊 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！客户端功能正常。")
        print("\n📝 使用说明:")
        print("1. 设置环境变量: export DASHSCOPE_API_KEY='your-api-key'")
        print("2. 运行示例: python example.py")
        print("3. 查看详细文档: README.md")
        return True
    else:
        print("⚠️  部分测试失败，请检查代码实现。")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
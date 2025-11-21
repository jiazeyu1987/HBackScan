#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LLM客户端使用示例
展示如何使用阿里百炼LLM客户端进行智能数据处理

主要功能：
1. LLM客户端初始化和配置
2. 基本文本生成功能
3. 医院数据智能分析
4. 层级数据结构化输出
5. 错误处理和重试机制
6. 自定义prompt模板
"""

import os
import sys
import json
import time
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Union

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from llm_client import DashScopeLLMClient
except ImportError:
    print("警告: 无法导入LLM客户端模块，将使用模拟功能")
    DashScopeLLMClient = None


class HospitalLLMExamples:
    """医院LLM应用示例类"""
    
    def __init__(self):
        """初始化LLM示例类"""
        self.client = None
        self.setup_client()
    
    def setup_client(self):
        """设置LLM客户端"""
        if DashScopeLLMClient is None:
            print("LLM客户端模块不可用，将使用模拟功能")
            return
        
        try:
            # 尝试从环境变量获取API密钥
            api_key = os.getenv('DASHSCOPE_API_KEY')
            if api_key:
                self.client = DashScopeLLMClient(
                    api_key=api_key,
                    model="qwen-plus",
                    timeout=30,
                    max_retries=2
                )
                print("✅ LLM客户端初始化成功")
            else:
                print("⚠️  未设置DASHSCOPE_API_KEY环境变量，将使用模拟功能")
        except Exception as e:
            print(f"❌ LLM客户端初始化失败: {e}")
            print("将使用模拟功能")
    
    def demo_basic_text_generation(self):
        """演示基本文本生成功能"""
        print("\n" + "=" * 60)
        print("基本文本生成演示")
        print("=" * 60)
        
        # 测试用例
        test_prompts = [
            "请介绍一下中国医疗体系的基本结构",
            "解释一下医院等级划分标准",
            "描述三甲医院的特点和标准"
        ]
        
        for i, prompt in enumerate(test_prompts, 1):
            print(f"\n{i}. 文本生成测试")
            print(f"提示词: {prompt}")
            print("-" * 40)
            
            try:
                if self.client:
                    # 使用真实的LLM客户端
                    response = self.client.generate_text(prompt)
                    print(f"响应: {response}")
                else:
                    # 使用模拟响应
                    print("模拟响应: 这是一个关于医疗体系结构的专业回答，包含了三甲医院的详细说明和特点分析。")
                
                time.sleep(1)  # 避免请求过于频繁
                
            except Exception as e:
                print(f"生成失败: {e}")
    
    def demo_hospital_data_analysis(self):
        """演示医院数据分析功能"""
        print("\n" + "=" * 60)
        print("医院数据分析演示")
        print("=" * 60)
        
        # 模拟医院数据
        sample_hospitals = [
            {
                "name": "北京协和医院",
                "type": "三甲医院",
                "location": "北京市东城区",
                "website": "https://www.pumch.cn/",
                "description": "大型综合性医院，医疗技术水平国内领先"
            },
            {
                "name": "上海瑞金医院",
                "type": "三甲医院", 
                "location": "上海市黄浦区",
                "website": "https://www.rjh.com.cn/",
                "description": "综合性医疗中心，在消化科等领域享有盛誉"
            },
            {
                "name": "中山大学附属第一医院",
                "type": "三甲医院",
                "location": "广东省广州市",
                "website": "https://www.gzsums.edu.cn/",
                "description": "华南地区重要的医疗教学科研基地"
            }
        ]
        
        analysis_prompt = f"""
请分析以下医院信息，并从以下角度进行评估：

医院数据:
{json.dumps(sample_hospitals, ensure_ascii=False, indent=2)}

请提供分析结果，包括：
1. 医院分布特点
2. 医疗资源配置分析
3. 地理分布合理性评估
4. 数字化程度分析
5. 发展建议

请以结构化的方式输出分析结果。
"""
        
        print("\n1. 医院数据分析")
        print(f"分析数据量: {len(sample_hospitals)} 个医院")
        print("-" * 40)
        
        try:
            if self.client:
                response = self.client.generate_text(analysis_prompt)
                print("分析结果:")
                print(response)
            else:
                print("模拟分析结果:")
                print("""
1. 医院分布特点：
   - 主要集中在北上广等一线城市
   - 覆盖了华北、华东、华南三大区域
   - 体现了优质医疗资源的集聚效应

2. 医疗资源配置分析：
   - 均为三甲医院，医疗技术实力雄厚
   - 具备完整的科室设置和先进设备
   - 承担大量疑难病症的诊治任务

3. 地理分布合理性评估：
   - 分布相对均衡，覆盖主要经济区域
   - 有利于患者就近就医
   - 建议在西部地区增加优质医疗资源

4. 数字化程度分析：
   - 所有医院均建立官方网站
   - 信息化建设水平较高
   - 建议进一步提升互联网医疗服务

5. 发展建议：
   - 加强区域医疗协同
   - 推进分级诊疗制度
   - 提升基层医疗服务能力
                """)
        except Exception as e:
            print(f"分析失败: {e}")
    
    def demo_structured_output(self):
        """演示结构化输出功能"""
        print("\n" + "=" * 60)
        print("结构化输出演示")
        print("=" * 60)
        
        # 医院信息提取任务
        extract_prompt = """
请从以下文本中提取医院信息，并按照指定格式返回JSON格式数据：

文本内容：
"北京协和医院位于北京市东城区王府井大街1号，是一家三甲综合医院，成立于1921年。医院网址为 https://www.pumch.cn/。该医院在心血管内科、神经内科等领域具有较强实力。"

提取要求：
- 医院名称
- 医院等级（三甲、二甲等）
- 详细地址
- 成立年份
- 官方网址
- 特色科室（如果有）
- 医院类型（综合、专科等）

请严格按照以下JSON格式返回：
{
  "医院名称": "",
  "医院等级": "",
  "详细地址": "",
  "成立年份": "",
  "官方网址": "",
  "特色科室": [],
  "医院类型": ""
}
"""
        
        print("\n1. 医院信息提取")
        print("-" * 40)
        
        try:
            if self.client:
                response = self.client.generate_text(extract_prompt)
                print("提取结果:")
                print(response)
                
                # 尝试解析JSON
                try:
                    # 提取JSON部分
                    if '{' in response and '}' in response:
                        start_idx = response.find('{')
                        end_idx = response.rfind('}') + 1
                        json_str = response[start_idx:end_idx]
                        data = json.loads(json_str)
                        print("\n解析后的结构化数据:")
                        print(json.dumps(data, ensure_ascii=False, indent=2))
                except json.JSONDecodeError:
                    print("无法解析JSON格式响应")
                
            else:
                # 模拟结构化输出
                mock_result = {
                    "医院名称": "北京协和医院",
                    "医院等级": "三甲",
                    "详细地址": "北京市东城区王府井大街1号",
                    "成立年份": "1921年",
                    "官方网址": "https://www.pumch.cn/",
                    "特色科室": ["心血管内科", "神经内科"],
                    "医院类型": "综合医院"
                }
                print("模拟提取结果:")
                print(json.dumps(mock_result, ensure_ascii=False, indent=2))
        
        except Exception as e:
            print(f"结构化输出失败: {e}")
    
    def demo_medical_text_analysis(self):
        """演示医疗文本分析功能"""
        print("\n" + "=" * 60)
        print("医疗文本分析演示")
        print("=" * 60)
        
        # 医疗相关文本样本
        medical_texts = [
            {
                "title": "医院简介",
                "content": "本院是一所集医疗、教学、科研、预防、保健、康复于一体的现代化三级甲等综合性医院。医院编制床位2000张，设有临床科室50个，医技科室15个。"
            },
            {
                "title": "科室介绍", 
                "content": "心血管内科是本院重点科室，擅长冠心病介入治疗、心律失常射频消融术、心脏起搏器植入术等先进技术。年完成介入手术3000余例。"
            },
            {
                "title": "科研成果",
                "content": "近三年承担国家自然科学基金重点项目5项，省部级科研项目30余项。获得省部级科技成果奖8项，发表SCI论文150余篇。"
            }
        ]
        
        analysis_tasks = [
            ("关键词提取", "请提取文本中的医疗关键词"),
            ("实体识别", "请识别文本中的医疗实体（科室、设备、技术等）"),
            ("分类标签", "请为文本分配合适的分类标签"),
            ("质量评估", "请评估文本的信息完整性和专业性")
        ]
        
        for task_name, task_description in analysis_tasks:
            print(f"\n{task_name}任务")
            print(f"任务描述: {task_description}")
            print("-" * 40)
            
            try:
                if self.client:
                    for text_sample in medical_texts[:1]:  # 只测试第一个样本
                        prompt = f"{task_description}:\n\n标题: {text_sample['title']}\n内容: {text_sample['content']}"
                        response = self.client.generate_text(prompt)
                        print(f"分析结果: {response}")
                        time.sleep(1)
                else:
                    # 模拟分析结果
                    if task_name == "关键词提取":
                        print("提取结果: 三级甲等综合性医院、临床科室、医技科室、医疗、教学、科研")
                    elif task_name == "实体识别":
                        print("识别实体: 心血管内科、冠心病介入治疗、射频消融术、起搏器植入术")
                    elif task_name == "分类标签":
                        print("分类标签: 医院简介、科室介绍、科研成果、医疗技术")
                    elif task_name == "质量评估":
                        print("质量评估: 信息完整度高，专业术语使用准确，结构清晰")
                
            except Exception as e:
                print(f"分析失败: {e}")
    
    def demo_error_handling(self):
        """演示错误处理机制"""
        print("\n" + "=" * 60)
        print("错误处理机制演示")
        print("=" * 60)
        
        # 错误场景测试
        error_scenarios = [
            ("空提示词", ""),
            ("超长文本", "A" * 10000),  # 模拟超长文本
            ("无效格式", "###@@@***"),
            ("网络超时模拟", "生成一个需要很长时间的复杂报告内容"),
        ]
        
        for scenario_name, test_input in error_scenarios:
            print(f"\n{scenario_name}测试")
            print(f"输入: {test_input[:50]}{'...' if len(test_input) > 50 else ''}")
            print("-" * 30)
            
            try:
                if self.client:
                    response = self.client.generate_text(test_input)
                    print(f"响应: {response[:100]}{'...' if len(response) > 100 else ''}")
                else:
                    if scenario_name == "空提示词":
                        print("处理结果: 返回默认提示信息")
                    elif scenario_name == "超长文本":
                        print("处理结果: 自动截断并处理前1000字符")
                    elif scenario_name == "无效格式":
                        print("处理结果: 提示输入格式不正确")
                    elif scenario_name == "网络超时模拟":
                        print("处理结果: 超时异常，已重试3次后返回")
                
            except Exception as e:
                print(f"错误处理: {type(e).__name__}: {e}")
    
    def demo_prompt_templates(self):
        """演示提示词模板"""
        print("\n" + "=" * 60)
        print("提示词模板演示")
        print("=" * 60)
        
        # 定义提示词模板
        templates = {
            "医院信息提取": """
角色：医疗信息提取专家
任务：从给定的医院描述文本中提取结构化信息

输入格式：
医院描述文本：[在这里插入文本]

输出要求：
请严格按照以下JSON格式返回：
{{
  "医院名称": "",
  "医院等级": "",
  "地址信息": "",
  "联系电话": "",
  "官方网址": "",
  "主要科室": [],
  "医院类型": ""
}}

注意事项：
1. 仅提取文本中明确提到的信息
2. 如果某些信息不存在，字段留空
3. 主要科室使用数组格式
4. 返回结果必须是有效的JSON格式
            """,
            
            "医疗文本摘要": """
角色：医疗文本摘要专家
任务：为医疗相关文本生成简洁准确的摘要

摘要要求：
1. 保持医学专业术语的准确性
2. 突出核心医疗信息
3. 控制在200字以内
4. 使用客观中性的语言

输入文本：[在这里插入要摘要的医疗文本]

请生成摘要：
            """,
            
            "科室匹配": """
角色：医院科室分类专家
任务：根据科室名称匹配标准的科室分类

匹配规则：
1. 优先匹配标准科室名称
2. 如果匹配不到相近科室，返回"其他科室"
3. 不区分大小写

输入科室名称：[在这里输入科室名称]

请返回标准分类：
            """
        }
        
        # 测试不同模板
        test_inputs = {
            "医院信息提取": "北京大学第三医院位于北京市海淀区花园北路49号，是一家三甲综合性医院。",
            "医疗文本摘要": "本院心血管内科成功开展多例复杂冠心病介入治疗手术，患者术后恢复良好。",
            "科室匹配": "心脏外科"
        }
        
        for template_name, prompt_template in templates.items():
            print(f"\n{template_name}模板测试")
            print("-" * 40)
            
            try:
                test_input = test_inputs.get(template_name, "测试输入")
                full_prompt = prompt_template + "\n\n" + test_input
                
                if self.client:
                    response = self.client.generate_text(full_prompt)
                    print(f"响应: {response[:200]}{'...' if len(response) > 200 else ''}")
                else:
                    print("模拟响应: 模板测试成功，返回结构化结果")
                
            except Exception as e:
                print(f"模板测试失败: {e}")
    
    def run_all_demos(self):
        """运行所有演示"""
        print("医院扫描仪LLM客户端使用示例")
        print("=" * 60)
        print("此示例展示如何使用阿里百炼LLM客户端处理医疗数据")
        print("=" * 60)
        
        try:
            self.demo_basic_text_generation()
            self.demo_hospital_data_analysis()
            self.demo_structured_output()
            self.demo_medical_text_analysis()
            self.demo_error_handling()
            self.demo_prompt_templates()
            
            print("\n" + "=" * 60)
            print("✅ 所有LLM演示完成！")
            print("=" * 60)
            
        except KeyboardInterrupt:
            print("\n\n演示被用户中断")
        except Exception as e:
            print(f"\n\n演示过程中发生错误: {e}")


def main():
    """主演示函数"""
    print("开始LLM客户端示例演示...")
    
    # 检查环境配置
    api_key = os.getenv('DASHSCOPE_API_KEY')
    if not api_key:
        print("\n⚠️  提示: 未设置DASHSCOPE_API_KEY环境变量")
        print("要使用真实的LLM功能，请：")
        print("1. 获取阿里百炼API密钥")
        print("2. 设置环境变量: export DASHSCOPE_API_KEY=your_api_key")
        print("3. 重新运行此示例")
        print("\n将继续使用模拟功能进行演示...")
    
    try:
        llm_examples = HospitalLLMExamples()
        llm_examples.run_all_demos()
        
    except Exception as e:
        print(f"LLM示例运行失败: {e}")


if __name__ == "__main__":
    main()
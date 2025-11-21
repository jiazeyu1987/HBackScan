#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
医院层级扫查微服务 - LLM客户端
"""

import os
import json
import logging
from typing import Dict, Any, Optional
import requests
from datetime import datetime

logger = logging.getLogger(__name__)

class LLMClient:
    """大语言模型客户端"""
    
    def __init__(self):
        self.api_key = os.getenv("LLM_API_KEY", "")
        self.base_url = os.getenv("LLM_BASE_URL", "https://api.minimax.chat/v1/text/chatcompletion_pro")
        self.model = os.getenv("LLM_MODEL", "abab6.5s-chat")
        self.timeout = 30
        
        if not self.api_key:
            logger.warning("LLM_API_KEY未设置，将使用模拟模式")
        
    def _make_request(self, messages: list, max_tokens: int = 2000) -> Optional[str]:
        """发起API请求"""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": self.model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": 0.7,
                "stream": False
            }
            
            response = requests.post(
                self.base_url,
                headers=headers,
                json=data,
                timeout=self.timeout
            )
            
            response.raise_for_status()
            result = response.json()
            
            if "choices" in result and len(result["choices"]) > 0:
                return result["choices"][0]["message"]["content"]
            else:
                logger.error(f"API响应格式异常: {result}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"API请求失败: {e}")
            return None
        except Exception as e:
            logger.error(f"请求处理失败: {e}")
            return None
    
    def _mock_analysis(self, hospital_name: str, query: str) -> Dict[str, Any]:
        """模拟LLM分析结果（用于开发测试）"""
        logger.info(f"使用模拟模式分析医院: {hospital_name}")
        
        # 模拟不同类型医院的层级结构
        mock_data = {
            "hospital_name": hospital_name,
            "level": "三级甲等" if "人民医院" in hospital_name or "中心医院" in hospital_name else "二级医院",
            "address": f"北京市朝阳区{hospital_name}路123号",
            "phone": "010-12345678",
            "departments": [
                "内科", "外科", "妇产科", "儿科", "急诊科",
                "骨科", "神经内科", "心血管内科", "肿瘤科", "中医科"
            ],
            "beds_count": 800 if "人民" in hospital_name else 300,
            "staff_count": 1200 if "人民" in hospital_name else 450,
            "specializations": [
                "心血管疾病治疗", "肿瘤综合治疗", "神经系统疾病",
                "骨科创伤治疗", "妇产科疑难病症"
            ],
            "management_structure": {
                "院长": 1,
                "副院长": 3,
                "科室主任": 15,
                "科室副主任": 25,
                "护士长": 20
            },
            "operating_hours": "24小时急诊，门诊时间：8:00-17:00",
            "website": f"www.{hospital_name.replace('医院', '').lower()}.com"
        }
        
        return mock_data
    
    async def analyze_hospital_hierarchy(self, hospital_name: str, query: str = "") -> Dict[str, Any]:
        """分析医院层级结构"""
        try:
            logger.info(f"开始分析医院层级结构: {hospital_name}")
            
            # 构造提示词
            system_prompt = """你是一个专业的医院管理顾问。请根据用户提供的医院名称，分析并返回该医院的详细层级结构信息。

请以JSON格式返回，包含以下字段：
- hospital_name: 医院全名
- level: 医院等级（如：三级甲等、二级医院等）
- address: 医院地址
- phone: 联系电话
- departments: 科室列表（数组）
- beds_count: 床位数
- staff_count: 员工总数
- specializations: 特色专科（数组）
- management_structure: 管理层级结构（对象）
- operating_hours: 营业时间
- website: 官方网站（如果有）

如果无法获取确切信息，请基于医院名称的规律和常见情况进行合理推断，并标注为模拟数据。"""

            user_prompt = f"请分析以下医院的层级结构信息：\n医院名称：{hospital_name}\n查询需求：{query if query else '获取完整的医院层级结构信息'}"

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            # 检查API密钥
            if not self.api_key:
                logger.warning("未配置API密钥，使用模拟数据")
                return self._mock_analysis(hospital_name, query)
            
            # 调用LLM API
            response = self._make_request(messages)
            
            if not response:
                logger.warning("LLM API调用失败，使用模拟数据")
                return self._mock_analysis(hospital_name, query)
            
            # 解析JSON响应
            try:
                # 尝试提取JSON部分
                json_start = response.find('{')
                json_end = response.rfind('}') + 1
                
                if json_start != -1 and json_end != -1:
                    json_str = response[json_start:json_end]
                    result = json.loads(json_str)
                else:
                    logger.warning("响应中未找到JSON格式数据，使用模拟数据")
                    result = self._mock_analysis(hospital_name, query)
                
                # 验证必要字段
                if not isinstance(result, dict):
                    raise ValueError("响应不是有效的字典格式")
                
                required_fields = ['hospital_name', 'level', 'departments']
                for field in required_fields:
                    if field not in result:
                        logger.warning(f"缺少必要字段: {field}")
                        result[field] = self._mock_analysis(hospital_name, query).get(field, "")
                
                logger.info(f"医院层级结构分析完成: {hospital_name}")
                return result
                
            except json.JSONDecodeError as e:
                logger.error(f"JSON解析失败: {e}")
                return self._mock_analysis(hospital_name, query)
            
        except Exception as e:
            logger.error(f"医院层级结构分析失败: {e}")
            return self._mock_analysis(hospital_name, query)
    
    async def generate_hierarchy_report(self, hospital_data: Dict[str, Any]) -> str:
        """生成层级结构报告"""
        try:
            system_prompt = """你是一个医院管理分析师。请基于提供的医院数据，生成一份专业的医院层级结构分析报告。

报告应包含：
1. 医院基本概况
2. 组织架构分析
3. 科室设置评估
4. 人力资源结构
5. 管理层级分析
6. 改进建议"""

            user_prompt = f"""请为以下医院数据生成层级结构分析报告：

{json.dumps(hospital_data, ensure_ascii=False, indent=2)}"""

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            if not self.api_key:
                # 模拟报告生成
                return f"""医院层级结构分析报告

医院名称：{hospital_data.get('hospital_name', '')}
分析时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

一、医院基本概况
- 医院等级：{hospital_data.get('level', '')}
- 床位数量：{hospital_data.get('beds_count', 0)}张
- 员工总数：{hospital_data.get('staff_count', 0)}人

二、组织架构分析
医院设置了{len(hospital_data.get('departments', []))}个主要科室，形成了较为完整的医疗服务体系。

三、科室设置评估
主要科室包括：{', '.join(hospital_data.get('departments', [])[:5])}等

四、人力资源结构
根据现有数据，医院人员配置合理，能够满足基本医疗服务需求。

五、管理层级分析
管理层级清晰，科室主任和副主任的配置符合医院运营需要。

六、改进建议
1. 继续完善科室设置，增加特色专科
2. 加强人才培养和引进
3. 优化管理流程，提高运营效率"""

            response = self._make_request(messages, max_tokens=3000)
            
            if response:
                return response
            else:
                return "报告生成失败，请稍后重试。"
                
        except Exception as e:
            logger.error(f"报告生成失败: {e}")
            return f"报告生成过程中出现错误: {str(e)}"
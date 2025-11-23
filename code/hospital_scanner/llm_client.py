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

# 使用主应用创建的LLM专用日志记录器
logger = logging.getLogger('llm_client')
main_logger = logging.getLogger(__name__)  # 主日志记录器用于关键错误

class LLMClient:
    """大语言模型客户端"""
    
    def __init__(self):
        self.api_key = os.getenv("DASHSCOPE_API_KEY", "")
        self.base_url = os.getenv("LLM_BASE_URL", "https://dashscope.aliyuncs.com/api/v1/")
        self.model = os.getenv("LLM_MODEL", "deepseek-r1")
        self.timeout = 300

        # 初始化logger
        self.logger = logging.getLogger(__name__)

        if not self.api_key:
            logger.error("❌ DASHSCOPE_API_KEY未设置！请检查.env文件配置")
            raise ValueError("DASHSCOPE_API_KEY环境变量未设置，无法初始化LLM客户端")
        
    def _make_request(self, messages: list, max_tokens: int = 2000) -> Optional[str]:
        """发起API请求"""
        # 记录详细的提示词内容用于调试
        self.logger.info(f"📝 LLM API请求提示词内容:")
        for i, message in enumerate(messages):
            self.logger.info(f"  消息 {i+1} [{message.get('role', 'unknown')}]: {message.get('content', '')}")

        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            # 根据不同的API提供商调整请求格式
            if "dashscope" in self.base_url:
                # 阿里云DashScope API格式
                data = {
                    "model": self.model,
                    "input": {
                        "messages": messages
                    },
                    "parameters": {
                        "max_tokens": max_tokens,
                        "temperature": 0.7,
                        "stream": False
                    }
                }
                response_field = "output"
                content_field = "text"
            else:
                # 通用OpenAI兼容格式
                data = {
                    "model": self.model,
                    "messages": messages,
                    "max_tokens": max_tokens,
                    "temperature": 0.7,
                    "stream": False
                }
                response_field = "choices"
                content_field = "message"

            logger.info(f"🔄 正在调用LLM API: {self.base_url}")
            logger.info(f"📝 使用模型: {self.model}")

            response = requests.post(
                self.base_url,
                headers=headers,
                json=data,
                timeout=self.timeout
            )

            # 记录响应状态
            logger.info(f"📊 API响应状态: {response.status_code}")

            if response.status_code == 401:
                main_logger.error(f"❌ API认证失败！请检查LLM_API_KEY是否正确配置。")
                raise ValueError(f"❌ API认证失败！请检查LLM_API_KEY是否正确配置。API响应: {response.text}")
            elif response.status_code == 429:
                main_logger.error(f"❌ API调用频率超限！请稍后重试。")
                raise ValueError(f"❌ API调用频率超限！请稍后重试。API响应: {response.text}")
            elif response.status_code == 500:
                main_logger.error(f"❌ API服务器内部错误！请联系API提供商。")
                raise ValueError(f"❌ API服务器内部错误！请联系API提供商。API响应: {response.text}")
            elif response.status_code != 200:
                main_logger.error(f"❌ API调用失败！状态码: {response.status_code}")
                raise ValueError(f"❌ API调用失败！状态码: {response.status_code}, 响应: {response.text}")

            result = response.json()
            # 记录完整的API响应内容用于调试
            self.logger.info(f"📋 完整API响应 (状态码: {response.status_code}):\n{json.dumps(result, ensure_ascii=False, indent=2)}")
            logger.debug(f"🔍 API原始响应: {result}")

            # 智能解析API响应，兼容多种格式
            logger.info(f"🔍 开始解析API响应，期望格式: {response_field}")
            logger.debug(f"📥 完整响应结构: {json.dumps(result, ensure_ascii=False, indent=2)}")

            # 尝试OpenAI兼容格式 (output.choices[0].message.content)
            if ("output" in result and
                isinstance(result["output"], dict) and
                "choices" in result["output"] and
                len(result["output"]["choices"]) > 0):
                choice = result["output"]["choices"][0]
                if ("message" in choice and
                    "content" in choice["message"]):
                    content = choice["message"]["content"]
                    logger.info("🔍 使用OpenAI兼容格式解析: output.choices[0].message.content")
                    logger.debug(f"📝 提取的内容长度: {len(content)} 字符")
                    return content
                else:
                    logger.warning(f"⚠️ OpenAI格式结构不完整: {choice}")

            # 尝试DashScope格式 (output.text)
            if ("output" in result and
                isinstance(result["output"], dict) and
                "text" in result["output"]):
                text = result["output"]["text"]
                logger.info("🔍 使用DashScope格式解析: output.text")
                logger.debug(f"📝 提取的文本长度: {len(text)} 字符")
                return text

            # 尝试标准OpenAI格式 (直接在根级别)
            if ("choices" in result and
                len(result["choices"]) > 0):
                choice = result["choices"][0]
                if ("message" in choice and
                    "content" in choice["message"]):
                    content = choice["message"]["content"]
                    logger.info("🔍 使用标准OpenAI格式解析: choices[0].message.content")
                    logger.debug(f"📝 提取的内容长度: {len(content)} 字符")
                    return content
                else:
                    logger.warning(f"⚠️ 标准OpenAI格式结构不完整: {choice}")

            # 如果所有格式都不匹配，记录详细错误信息
            logger.error(f"❌ 无法解析API响应！响应结构分析:")
            logger.error(f"   - 响应字段: {list(result.keys())}")
            if "output" in result:
                logger.error(f"   - output字段类型: {type(result['output'])}")
                if isinstance(result["output"], dict):
                    logger.error(f"   - output字段内容: {list(result['output'].keys())}")
            logger.error(f"   - 完整响应: {json.dumps(result, ensure_ascii=False, indent=2)}")
            raise ValueError(f"❌ API响应格式无法识别！期望output.text或choices格式，但得到: {list(result.keys())}")

        except requests.exceptions.Timeout:
            main_logger.error(f"❌ API请求超时！等待时间超过{self.timeout}秒。")
            raise ValueError(f"❌ API请求超时！等待时间超过{self.timeout}秒。请检查网络连接或增加timeout设置。")
        except requests.exceptions.ConnectionError:
            main_logger.error(f"❌ 网络连接失败！无法连接到API服务器: {self.base_url}。")
            raise ValueError(f"❌ 网络连接失败！无法连接到API服务器: {self.base_url}。请检查网络连接和API地址。")
        except requests.exceptions.RequestException as e:
            main_logger.error(f"❌ API请求失败！网络错误: {str(e)}。")
            raise ValueError(f"❌ API请求失败！网络错误: {str(e)}。请检查网络配置和API设置。")
        except Exception as e:
            main_logger.error(f"❌ LLM API调用过程中发生未知错误: {str(e)}。")
            raise ValueError(f"❌ LLM API调用过程中发生未知错误: {str(e)}。请检查所有配置参数。")
    
    async def analyze_hospital_hierarchy(self, hospital_name: str, query: str = "") -> Dict[str, Any]:
        """分析医院层级结构（仅使用真实LLM API）"""
        try:
            # 只记录关键错误信息
            main_logger.info(f"开始分析医院: {hospital_name}")

            if not hospital_name or len(hospital_name.strip()) < 2:
                raise ValueError(f"医院名称无效！'{hospital_name}' 请提供有效的医院名称（至少2个字符）")

            # 构造提示词
            system_prompt = """你是一个专业的医院管理顾问。请根据用户提供的医院名称，分析并返回该医院的详细层级结构信息。

请严格按照JSON格式返回，包含以下字段：
- hospital_name: 医院全名（字符串）
- level: 医院等级（如：三级甲等、二级医院等，字符串）
- address: 医院地址（字符串）
- phone: 联系电话（字符串）
- departments: 科室列表（字符串数组）
- beds_count: 床位数（整数）
- staff_count: 员工总数（整数）
- specializations: 特色专科（字符串数组）
- management_structure: 管理层级结构（对象）
- operating_hours: 营业时间（字符串）
- website: 官方网站（字符串，如果没有可以写"暂无"）

注意：
1. 必须返回有效的JSON格式
2. 所有字段都必须提供
3. 如果某些信息确实无法获取，请根据医院等级和规模进行合理推断
4. 不要在JSON前后添加其他说明文字"""

            user_prompt = f"""请分析以下医院的层级结构信息：

医院名称：{hospital_name.strip()}
查询需求：{query if query else '获取完整的医院层级结构信息'}

请返回标准的JSON格式数据，不要添加任何解释文字。"""

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]

            # 记录发送给LLM的提示词
            logger.info(f"=== LLM提示词 ===")
            logger.info(f"系统提示词: {system_prompt}")
            logger.info(f"用户提示词: {user_prompt}")
            logger.info(f"=================")

            # 调用LLM API
            response = self._make_request(messages)

            if not response:
                raise ValueError("LLM API返回空响应！请检查API服务是否正常。")

            # 记录LLM的回复
            logger.info(f"=== LLM回复 ===")
            logger.info(f"原始回复: {response}")
            logger.info(f"回复长度: {len(response)} 字符")
            logger.info(f"=================")

            # 解析JSON响应
            try:
                # 清理响应文本，移除可能的markdown格式
                response = response.strip()
                if response.startswith('```json'):
                    response = response[7:]
                if response.startswith('```'):
                    response = response[3:]
                if response.endswith('```'):
                    response = response[:-3]
                response = response.strip()

                # 尝试提取JSON部分
                json_start = response.find('{')
                json_end = response.rfind('}') + 1

                if json_start == -1 or json_end == -1:
                    raise ValueError(f"响应中未找到有效的JSON格式！原始响应: {response[:500]}...")

                json_str = response[json_start:json_end]

                # 记录解析后的JSON
                logger.info(f"=== 解析结果 ===")
                logger.info(f"解析的JSON: {json_str}")
                logger.info(f"=================")

                result = json.loads(json_str)

                # 验证必要字段
                if not isinstance(result, dict):
                    raise ValueError(f"响应不是有效的字典格式！类型: {type(result)}")

                required_fields = ['hospital_name', 'level', 'departments']
                missing_fields = []

                for field in required_fields:
                    if field not in result:
                        missing_fields.append(field)
                    elif not result[field]:
                        missing_fields.append(f"{field}(空值)")

                if missing_fields:
                    raise ValueError(f"缺少必要字段或字段为空: {', '.join(missing_fields)}")

                # 验证数据类型
                if not isinstance(result.get('departments'), list):
                    raise ValueError("departments字段必须是数组格式")

                # 记录最终存储的数据
                logger.info(f"=== 存储的数据 ===")
                logger.info(f"医院名称: {result.get('hospital_name')}")
                logger.info(f"医院等级: {result.get('level')}")
                logger.info(f"科室数量: {len(result.get('departments', []))}")
                logger.info(f"地址: {result.get('address')}")
                logger.info(f"电话: {result.get('phone')}")
                logger.info(f"床位数量: {result.get('beds_count')}")
                logger.info(f"员工数量: {result.get('staff_count')}")
                logger.info(f"特色专科: {result.get('specializations', [])}")
                logger.info(f"==================")

                main_logger.info(f"医院层级结构分析完成: {hospital_name}")
                return result

            except json.JSONDecodeError as e:
                logger.error(f"JSON解析失败: {e}")
                logger.error(f"原始响应内容: {response}")
                raise ValueError(f"无法解析LLM返回的JSON数据！解析错误: {str(e)}")

        except ValueError as e:
            # 重新抛出已知错误
            raise e
        except Exception as e:
            main_logger.error(f"医院层级结构分析失败: {str(e)}")
            raise ValueError(f"医院层级结构分析失败: {str(e)}")
    
    async def generate_hierarchy_report(self, hospital_data: Dict[str, Any]) -> str:
        """生成层级结构报告（仅使用真实LLM API）"""
        try:
            # 验证输入数据
            if not hospital_data or not isinstance(hospital_data, dict):
                raise ValueError("❌ 医院数据无效！请提供有效的医院信息字典。")

            if 'hospital_name' not in hospital_data:
                raise ValueError("❌ 医院数据中缺少hospital_name字段！")

            logger.info(f"📊 开始生成医院层级结构报告: {hospital_data.get('hospital_name', '未知医院')}")

            system_prompt = """你是一个专业的医院管理分析师。请基于提供的医院数据，生成一份详细、专业的医院层级结构分析报告。

报告格式要求：
1. 使用标准的中文报告格式
2. 包含清晰的标题和分段
3. 数据分析和专业建议相结合
4. 语言简洁专业，避免冗余

报告必须包含以下部分：
1. **医院基本概况** - 包含等级、规模、基本信息
2. **组织架构分析** - 分析整体架构合理性
3. **科室设置评估** - 评估科室配置和专业性
4. **人力资源结构** - 分析人员配置合理性
5. **管理层级分析** - 评估管理架构效率
6. **综合评估与建议** - 提供改进建议和发展方向

注意：
- 报告应该基于提供的数据进行分析
- 如果某些数据缺失，请明确指出并给出建议
- 报告长度应在800-1500字之间"""

            user_prompt = f"""请为以下医院数据生成专业的层级结构分析报告：

```json
{json.dumps(hospital_data, ensure_ascii=False, indent=2)}
```

请根据上述数据生成详细的医院层级结构分析报告，严格按照要求的格式和内容进行编写。"""

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]

            logger.info("🔄 正在调用LLM API生成医院分析报告...")

            response = self._make_request(messages, max_tokens=3000)

            if not response:
                raise ValueError("❌ LLM API返回空响应！无法生成报告。")

            logger.info(f"✅ 医院分析报告生成完成，报告长度: {len(response)} 字符")
            return response

        except ValueError as e:
            # 重新抛出已知错误
            raise e
        except Exception as e:
            main_logger.error(f"❌ 医院分析报告生成过程中发生未知错误: {str(e)}")
            raise ValueError(f"❌ 医院分析报告生成过程中发生未知错误: {str(e)}")

    async def get_cities_by_province(self, province_name: str) -> Dict[str, Any]:
        """获取指定省份的城市数据（仅使用真实LLM API）"""
        try:
            main_logger.info(f"开始获取省份城市数据: {province_name}")

            if not province_name or len(province_name.strip()) < 2:
                raise ValueError(f"省份名称无效！'{province_name}' 请提供有效的省份名称（至少2个字符）")

            # 构造提示词
            system_prompt = """你是一个专业的地理信息系统专家。请根据用户指定的省份名称，返回该省份下辖的所有地级市、自治州、地区等行政区划信息。

请严格按照JSON格式返回，包含以下字段：
- cities: 城市列表（字符串数组）
- count: 城市总数（整数）
- province: 省份全名（字符串）

注意：
1. 必须返回有效的JSON格式
2. 只返回地级市、自治州、地区等，不包含县级市
3. 如果某些信息不确定，请根据公开行政区划信息进行合理推断
4. 不要在JSON前后添加其他说明文字"""

            user_prompt = f"""请查询以下省份的地级市、自治州、地区等行政区划：

省份名称：{province_name.strip()}

请返回该省份下辖的所有地级行政区划的标准JSON格式数据。"""

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]

            # 记录发送给LLM的提示词
            logger.info(f"=== LLM省份城市查询提示词 ===")
            logger.info(f"系统提示词: {system_prompt}")
            logger.info(f"用户提示词: {user_prompt}")
            logger.info(f"============================")

            # 调用LLM API
            response = self._make_request(messages)

            if not response:
                raise ValueError("LLM API返回空响应！请检查API服务是否正常。")

            # 记录LLM的回复
            logger.info(f"=== LLM省份城市查询回复 ===")
            logger.info(f"原始回复: {response}")
            logger.info(f"回复长度: {len(response)} 字符")
            logger.info(f"===========================")

            # 解析JSON响应
            try:
                # 清理响应文本，移除可能的markdown格式
                response = response.strip()
                if response.startswith('```json'):
                    response = response[7:]
                if response.startswith('```'):
                    response = response[3:]
                if response.endswith('```'):
                    response = response[:-3]
                response = response.strip()

                # 尝试提取JSON部分
                json_start = response.find('{')
                json_end = response.rfind('}') + 1

                if json_start == -1 or json_end == -1:
                    raise ValueError(f"响应中未找到有效的JSON格式！原始响应: {response[:500]}...")

                json_str = response[json_start:json_end]

                # 记录解析后的JSON
                logger.info(f"=== 解析后的省份城市JSON ===")
                logger.info(f"解析的JSON: {json_str}")
                logger.info(f"=============================")

                result = json.loads(json_str)

                # 验证必要字段
                if not isinstance(result, dict):
                    raise ValueError(f"响应不是有效的字典格式！类型: {type(result)}")

                required_fields = ['cities', 'count', 'province']
                missing_fields = []

                for field in required_fields:
                    if field not in result:
                        missing_fields.append(field)
                    elif result[field] is None:
                        missing_fields.append(f"{field}(空值)")

                if missing_fields:
                    raise ValueError(f"缺少必要字段或字段为空: {', '.join(missing_fields)}")

                # 验证数据类型
                if not isinstance(result.get('cities'), list):
                    raise ValueError("cities字段必须是数组格式")

                # 验证cities中的每个城市对象
                for city in result['cities']:
                    if not isinstance(city, str):
                        raise ValueError("cities中的每个元素都必须是字符串格式")

                # 记录最终存储的数据
                logger.info(f"=== 存储的省份城市数据 ===")
                logger.info(f"省份名称: {result.get('province')}")
                logger.info(f"城市数量: {len(result.get('cities', []))}")
                for i, city in enumerate(result.get('cities', [])[:5]):  # 只显示前5个
                    logger.info(f"  城市{i+1}: {city}")
                if len(result.get('cities', [])) > 5:
                    logger.info(f"  ... 还有 {len(result.get('cities', [])) - 5} 个城市")
                logger.info(f"========================")

                main_logger.info(f"省份城市数据获取完成: {province_name}，共 {len(result.get('cities', []))} 个城市")
                return result

            except json.JSONDecodeError as e:
                logger.error(f"JSON解析失败: {e}")
                logger.error(f"原始响应内容: {response}")
                raise ValueError(f"无法解析LLM返回的省份城市JSON数据！解析错误: {str(e)}")

        except ValueError as e:
            # 重新抛出已知错误
            raise e
        except Exception as e:
            main_logger.error(f"省份城市数据获取失败: {str(e)}")
            raise ValueError(f"省份城市数据获取失败: {str(e)}")

    async def get_districts_by_city(self, city_name: str) -> Dict[str, Any]:
        """获取指定城市的区县数据（仅使用真实LLM API）"""
        try:
            main_logger.info(f"开始获取城市区县数据: {city_name}")

            if not city_name or len(city_name.strip()) < 2:
                raise ValueError(f"城市名称无效！'{city_name}' 请提供有效的城市名称（至少2个字符）")

            # 构造提示词
            system_prompt = """你是一个专业的地理信息系统专家。请根据用户指定的城市名称，返回该城市下辖的所有区县级行政区划信息。

请严格按照JSON格式返回，包含以下字段：
- items: 区县列表（对象数组）
- count: 区县总数（整数）
- city: 城市全名（字符串）

每个区县对象包含：
- name: 区县名称（字符串）
- code: 行政区划代码（字符串，可为null）

注意：
1. 必须返回有效的JSON格式
2. 包含市辖区、县级市、县、自治县等所有区县级行政区划
3. 如果某些信息不确定，请根据公开行政区划信息进行合理推断
4. 不要在JSON前后添加其他说明文字"""

            user_prompt = f"""请查询以下城市的区县级行政区划：

城市名称：{city_name.strip()}

请返回该城市下辖的所有区县、县级市、县、自治县等行政区划的标准JSON格式数据。"""

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]

            # 记录发送给LLM的提示词
            logger.info(f"=== LLM区县查询提示词 ===")
            logger.info(f"系统提示词: {system_prompt}")
            logger.info(f"用户提示词: {user_prompt}")
            logger.info(f"=========================")

            # 调用LLM API
            response = self._make_request(messages)

            if not response:
                raise ValueError("LLM API返回空响应！请检查API服务是否正常。")

            # 记录LLM的回复
            logger.info(f"=== LLM区县查询回复 ===")
            logger.info(f"原始回复: {response}")
            logger.info(f"回复长度: {len(response)} 字符")
            logger.info(f"========================")

            # 解析JSON响应
            try:
                # 清理响应文本，移除可能的markdown格式
                response = response.strip()
                if response.startswith('```json'):
                    response = response[7:]
                if response.startswith('```'):
                    response = response[3:]
                if response.endswith('```'):
                    response = response[:-3]
                response = response.strip()

                # 尝试提取JSON部分
                json_start = response.find('{')
                json_end = response.rfind('}') + 1

                if json_start == -1 or json_end == -1:
                    raise ValueError(f"响应中未找到有效的JSON格式！原始响应: {response[:500]}...")

                json_str = response[json_start:json_end]

                # 记录解析后的JSON
                logger.info(f"=== 解析后的区县JSON ===")
                logger.info(f"解析的JSON: {json_str}")
                logger.info(f"=========================")

                result = json.loads(json_str)

                # 验证必要字段
                if not isinstance(result, dict):
                    raise ValueError(f"响应不是有效的字典格式！类型: {type(result)}")

                required_fields = ['items', 'count', 'city']
                missing_fields = []

                for field in required_fields:
                    if field not in result:
                        missing_fields.append(field)
                    elif result[field] is None:
                        missing_fields.append(f"{field}(空值)")

                if missing_fields:
                    raise ValueError(f"缺少必要字段或字段为空: {', '.join(missing_fields)}")

                # 验证数据类型
                if not isinstance(result.get('items'), list):
                    raise ValueError("items字段必须是数组格式")

                # 验证items中的每个区县对象
                for item in result['items']:
                    if not isinstance(item, dict):
                        raise ValueError("items中的每个元素都必须是对象格式")
                    if 'name' not in item or not item['name']:
                        raise ValueError("items中的每个区县都必须有name字段")

                # 记录最终存储的数据
                logger.info(f"=== 存储的区县数据 ===")
                logger.info(f"城市名称: {result.get('city')}")
                logger.info(f"区县数量: {len(result.get('items', []))}")
                for i, district in enumerate(result.get('items', [])[:5]):  # 只显示前5个
                    logger.info(f"  区县{i+1}: {district.get('name')}")
                if len(result.get('items', [])) > 5:
                    logger.info(f"  ... 还有 {len(result.get('items', [])) - 5} 个区县")
                logger.info(f"======================")

                main_logger.info(f"城市区县数据获取完成: {city_name}，共 {len(result.get('items', []))} 个区县")
                return result

            except json.JSONDecodeError as e:
                logger.error(f"JSON解析失败: {e}")
                logger.error(f"原始响应内容: {response}")
                raise ValueError(f"无法解析LLM返回的区县JSON数据！解析错误: {str(e)}")

        except ValueError as e:
            # 重新抛出已知错误
            raise e
        except Exception as e:
            main_logger.error(f"城市区县数据获取失败: {str(e)}")
            raise ValueError(f"城市区县数据获取失败: {str(e)}")

    async def get_hospitals_from_district(self, province_name: str, city_name: str, district_name: str) -> list:
        """获取指定区县的医院数据（仅使用真实LLM API）"""
        try:
            main_logger.info(f"开始获取区县医院数据: {province_name} -> {city_name} -> {district_name}")

            if not district_name or len(district_name.strip()) < 2:
                raise ValueError(f"区县名称无效！'{district_name}' 请提供有效的区县名称（至少2个字符）")

            # 构造提示词
            system_prompt = """你是一个专业的医疗信息系统专家。请根据用户指定的省市区县信息，返回该区县内的所有医院信息。

请严格按照JSON数组格式返回，每个医院对象包含以下字段：
- name: 医院名称（字符串）
- level: 医院等级（字符串，如：三甲、三乙、二甲、二乙、一甲、一乙等，可为null）
- address: 医院地址（字符串，可为null）
- phone: 联系电话（字符串，可为null）
- website: 官方网站（字符串，可为null）
- type: 医院类型（字符串，如：综合医院、专科医院、中医医院等，可为null）

注意：
1. 必须返回有效的JSON数组格式
2. 包含该区县内的所有公立医院和重要的私立医院
3. 优先提供准确的官方网站信息
4. 如果某些信息不确定，请根据公开信息进行合理推断
5. 不要在JSON前后添加其他说明文字"""

            user_prompt = f"""请查询以下区县的医院信息：

省份：{province_name.strip()}
城市：{city_name.strip()}
区县：{district_name.strip()}

请返回该区县内所有医院的详细信息。"""

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]

            # 记录发送给LLM的提示词
            logger.info(f"=== LLM医院查询提示词 ===")
            logger.info(f"系统提示词: {system_prompt}")
            logger.info(f"用户提示词: {user_prompt}")
            logger.info(f"=========================")

            # 调用LLM API
            response = self._make_request(messages)

            if not response:
                raise ValueError("LLM API返回空响应！请检查API服务是否正常。")

            # 记录LLM的回复
            logger.info(f"=== LLM医院查询回复 ===")
            logger.info(f"原始回复: {response}")
            logger.info(f"回复长度: {len(response)} 字符")
            logger.info(f"========================")

            # 解析JSON响应
            try:
                # 清理响应文本，移除可能的markdown格式
                response = response.strip()
                if response.startswith('```json'):
                    response = response[7:]
                if response.startswith('```'):
                    response = response[3:]
                if response.endswith('```'):
                    response = response[:-3]
                response = response.strip()

                # 尝试提取JSON部分
                json_start = response.find('[')
                json_end = response.rfind(']') + 1

                if json_start == -1 or json_end == -1:
                    raise ValueError(f"响应中未找到有效的JSON数组格式！原始响应: {response[:500]}...")

                json_str = response[json_start:json_end]

                # 记录解析后的JSON
                logger.info(f"=== 解析后的医院JSON ===")
                logger.info(f"解析的JSON: {json_str}")
                logger.info(f"=========================")

                result = json.loads(json_str)

                # 验证数据类型
                if not isinstance(result, list):
                    raise ValueError(f"响应不是有效的数组格式！类型: {type(result)}")

                # 验证数组中的每个医院对象
                for i, item in enumerate(result):
                    if not isinstance(item, dict):
                        raise ValueError(f"数组中第{i+1}个元素不是对象格式")
                    if 'name' not in item or not item['name']:
                        raise ValueError(f"数组中第{i+1}个医院缺少name字段")

                # 记录最终存储的数据
                logger.info(f"=== 存储的医院数据 ===")
                logger.info(f"区县名称: {district_name}")
                logger.info(f"医院数量: {len(result)}")
                for i, hospital in enumerate(result[:5]):  # 只显示前5个
                    logger.info(f"  医院{i+1}: {hospital.get('name')} ({hospital.get('level', 'N/A')})")
                if len(result) > 5:
                    logger.info(f"  ... 还有 {len(result) - 5} 家医院")
                logger.info(f"======================")

                main_logger.info(f"区县医院数据获取完成: {district_name}，共 {len(result)} 家医院")
                return result

            except json.JSONDecodeError as e:
                logger.error(f"JSON解析失败: {e}")
                logger.error(f"原始响应内容: {response}")
                raise ValueError(f"无法解析LLM返回的医院JSON数据！解析错误: {str(e)}")

        except ValueError as e:
            # 重新抛出已知错误
            raise e
        except Exception as e:
            main_logger.error(f"区县医院数据获取失败: {str(e)}")
            raise ValueError(f"区县医院数据获取失败: {str(e)}")
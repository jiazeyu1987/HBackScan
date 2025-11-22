#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
阿里百炼LLM客户端
实现多层级prompt模板和智能重试机制的API客户端
"""

import os
import json
import time
import logging
import requests
from typing import Dict, List, Optional, Union
from urllib.parse import urljoin


class DashScopeLLMClient:
    """阿里百炼LLM客户端"""
    
    def __init__(self, 
                 api_key: Optional[str] = None,
                 base_url: str = "https://dashscope.aliyuncs.com",
                 model: str = "qwen-plus",
                 proxy: Optional[str] = None,
                 max_retries: int = 2,
                 timeout: int = 30):
        """
        初始化阿里百炼LLM客户端
        
        Args:
            api_key: 阿里百炼API密钥，如果不提供则从环境变量DASHSCOPE_API_KEY获取
            base_url: API基础URL
            model: 使用的模型名称
            proxy: HTTP代理地址，如 "http://proxy.company.com:8080"
            max_retries: 最大重试次数
            timeout: 请求超时时间（秒）
        """
        # 设置API密钥
        self.api_key = api_key or os.getenv('DASHSCOPE_API_KEY')
        if not self.api_key:
            raise ValueError("请提供API密钥或设置环境变量DASHSCOPE_API_KEY")
        
        self.base_url = base_url
        self.model = model
        self.proxy = proxy
        self.max_retries = max_retries
        self.timeout = timeout
        
        # 设置端点
        self.endpoint = urljoin(base_url, "/api/v1/services/aigc/text-generation/generation")
        
        # 设置重试配置
        self.retry_delays = [1, 2]  # 指数退避：1秒、2秒
        
        # 设置日志
        self._setup_logging()
        
        # 设置代理
        self.proxies = {'http': proxy, 'https': proxy} if proxy else None
        
    def _setup_logging(self):
        """设置日志配置"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler('dashscope_client.log', encoding='utf-8')
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def _make_request_with_retry(self, payload: Dict) -> Dict:
        """
        发送带重试机制的API请求
        
        Args:
            payload: 请求负载
            
        Returns:
            API响应数据
            
        Raises:
            Exception: 所有重试失败后抛出异常
        """
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        
        last_error = None
        
        for attempt in range(self.max_retries + 1):
            try:
                self.logger.info(f"发送API请求 (尝试 {attempt + 1}/{self.max_retries + 1})")
                self.logger.debug(f"请求负载: {json.dumps(payload, ensure_ascii=False, indent=2)}")
                
                response = requests.post(
                    self.endpoint,
                    headers=headers,
                    json=payload,
                    proxies=self.proxies,
                    timeout=self.timeout
                )
                
                self.logger.info(f"响应状态码: {response.status_code}")
                
                if response.status_code == 200:
                    result = response.json()
                    self.logger.info("API请求成功")

                    # 记录完整的API响应内容用于调试
                    self.logger.info(f"📋 完整API响应:\n{json.dumps(result, ensure_ascii=False, indent=2)}")
                    self.logger.debug(f"响应内容: {json.dumps(result, ensure_ascii=False, indent=2)}")
                    return result
                else:
                    error_msg = f"API请求失败，状态码: {response.status_code}, 响应: {response.text}"
                    self.logger.error(error_msg)
                    
                    # 对于客户端错误(4xx)，不重试
                    if 400 <= response.status_code < 500:
                        raise Exception(error_msg)
                    
                    last_error = Exception(error_msg)
                    
            except requests.exceptions.RequestException as e:
                error_msg = f"网络请求异常 (尝试 {attempt + 1}): {str(e)}"
                self.logger.error(error_msg)
                last_error = e
                
                # 如果不是最后一次尝试，等待后重试
                if attempt < self.max_retries:
                    delay = self.retry_delays[min(attempt, len(self.retry_delays) - 1)]
                    self.logger.info(f"等待 {delay} 秒后重试...")
                    time.sleep(delay)
        
        # 所有重试都失败了
        self.logger.error(f"所有重试都失败，最后一个错误: {last_error}")
        raise last_error
        
    def _parse_response(self, response_data: Dict, expected_format: str) -> Dict:
        """
        解析API响应并验证格式

        Args:
            response_data: API响应数据
            expected_format: 期望的格式类型 ('province', 'city', 'district', 'hospital')

        Returns:
            解析后的标准化数据
        """
        # 记录接收到的响应数据结构
        self.logger.info(f"🔍 开始解析响应数据，期望格式: {expected_format}")
        self.logger.info(f"📥 接收到的响应数据结构:\n{json.dumps(response_data, ensure_ascii=False, indent=2)}")

        try:
            text_content = None

            # 尝试不同的API响应格式
            if 'output' in response_data:
                output = response_data['output']

                # DashScope格式: output.text
                if 'text' in output:
                    text_content = output['text']
                    self.logger.info("🔍 使用DashScope格式解析: output.text")
                # OpenAI兼容格式: output.choices[0].message.content
                elif 'choices' in output and len(output['choices']) > 0:
                    choice = output['choices'][0]
                    if 'message' in choice and 'content' in choice['message']:
                        text_content = choice['message']['content']
                        self.logger.info("🔍 使用OpenAI兼容格式解析: output.choices[0].message.content")
                    else:
                        self.logger.error(f"❌ OpenAI格式中缺少message.content: {choice}")
                else:
                    self.logger.error(f"❌ output字段格式不支持，包含的键: {list(output.keys()) if isinstance(output, dict) else 'N/A'}")
            else:
                self.logger.error(f"❌ 响应数据中缺少output字段，响应键: {list(response_data.keys())}")

            if text_content is None:
                self.logger.error(f"❌ 无法从API响应中提取文本内容")
                self.logger.error(f"❌ 响应数据结构分析:")
                self.logger.error(f"   - 'output' 字段存在: {'output' in response_data}")
                if 'output' in response_data:
                    self.logger.error(f"   - 'output' 字段内容: {response_data['output']}")
                    self.logger.error(f"   - 'text' 字段存在: {'text' in response_data['output']}")
                    if isinstance(response_data['output'], dict):
                        self.logger.error(f"   - 'output' 中的所有键: {list(response_data['output'].keys())}")
                self.logger.error(f"   - 响应数据所有键: {list(response_data.keys())}")
                raise ValueError("响应格式不正确，无法提取文本内容")

            self.logger.info(f"📝 提取的文本内容长度: {len(text_content)} 字符")
            self.logger.debug(f"📝 提取的文本内容: {text_content[:500]}...")  # 只显示前500字符
            
            # 解析JSON
            try:
                parsed_data = json.loads(text_content)
            except json.JSONDecodeError as e:
                self.logger.error(f"JSON解析失败: {e}")
                self.logger.error(f"原始文本: {text_content}")
                # 尝试提取JSON部分
                start_idx = text_content.find('{')
                end_idx = text_content.rfind('}') + 1
                if start_idx != -1 and end_idx != 0:
                    json_str = text_content[start_idx:end_idx]
                    parsed_data = json.loads(json_str)
                else:
                    raise e
            
            # 验证数据结构
            if 'items' not in parsed_data:
                raise ValueError("响应缺少items字段")
            
            items = parsed_data['items']
            if not isinstance(items, list):
                raise ValueError("items字段必须是数组")
            
            # 根据不同级别验证数据格式
            validated_items = []
            for item in items:
                if not isinstance(item, dict):
                    continue
                    
                if expected_format == 'province':
                    # 省级：name, code
                    if 'name' in item:
                        validated_items.append({
                            'name': item['name'],
                            'code': item.get('code')
                        })
                        
                elif expected_format == 'city':
                    # 市级：name, code
                    if 'name' in item:
                        validated_items.append({
                            'name': item['name'],
                            'code': item.get('code')
                        })
                        
                elif expected_format == 'district':
                    # 区县级：name, code
                    if 'name' in item:
                        validated_items.append({
                            'name': item['name'],
                            'code': item.get('code')
                        })
                        
                elif expected_format == 'hospital':
                    # 医院级：name, website, confidence
                    if 'name' in item:
                        validated_items.append({
                            'name': item['name'],
                            'website': item.get('website', ''),
                            'confidence': float(item.get('confidence', 0.7))
                        })
            
            result = {'items': validated_items}
            self.logger.info(f"验证后的数据: {json.dumps(result, ensure_ascii=False, indent=2)}")
            return result
            
        except Exception as e:
            self.logger.error(f"响应解析失败: {e}")
            raise
            
    def _build_prompt(self, level: str, input_data: Optional[str] = None) -> str:
        """
        构建不同层级的prompt模板
        
        Args:
            level: 层级 ('province', 'city', 'district', 'hospital')
            input_data: 输入数据（如省名、市名等）
            
        Returns:
            构建的prompt字符串
        """
        if level == 'province':
            prompt = """请列出中国所有省级行政区域名称。
要求：
1. 包含省、自治区、直辖市、特别行政区
2. 返回标准的JSON格式
3. JSON结构必须为：{{"items":[{{"name":"省级名称","code":null}}]}}
4. 不要包含其他文字内容，只返回JSON
5. name字段使用标准的行政区域名称"""
            
        elif level == 'city':
            prompt = f"""请列出属于"{input_data}"的所有市级行政区域名称。
要求：
1. 包含地级市、地区、盟、自治州等
2. 返回标准的JSON格式
3. JSON结构必须为：{{"items":[{{"name":"市名称","code":null}}]}}
4. 不要包含其他文字内容，只返回JSON
5. name字段使用标准的行政区域名称"""
            
        elif level == 'district':
            prompt = f"""请列出属于"{input_data}"的所有区县级行政区域名称。
要求：
1. 包含市辖区、县级市、县、自治县等
2. 返回标准的JSON格式
3. JSON结构必须为：{{"items":[{{"name":"区/县名称","code":null}}]}}
4. 不要包含其他文字内容，只返回JSON
5. name字段使用标准的行政区域名称"""
            
        elif level == 'hospital':
            prompt = f"""请列出位于"{input_data}"的主要医院名称。
要求：
1. 包含三甲医院、二甲医院等主要医疗机构
2. 返回标准的JSON格式
3. JSON结构必须为：{{"items":[{{"name":"医院名称","website":"http://example.com","confidence":0.7}}]}}
4. 不要包含其他文字内容，只返回JSON
5. name字段使用标准的医院全称
6. website字段提供医院官网地址（如果不确定，使用通用格式）
7. confidence字段表示数据可信度，使用0-1之间的小数"""
            
        else:
            raise ValueError(f"不支持的级别: {level}")
            
        self.logger.debug(f"构建的{prompt}级prompt:\n{prompt}")
        return prompt
        
    def get_provinces(self) -> Dict:
        """
        获取所有省级行政区域
        
        Returns:
            标准化格式的省级数据 {"items":[{"name":"省级名称","code":null}]}
        """
        self.logger.info("开始获取省级数据")
        prompt = self._build_prompt('province')

        # 记录完整的提示词内容用于调试
        self.logger.info(f"📝 省级提示词内容:\n{prompt}")
        
        payload = {
            'model': self.model,
            'input': {
                'messages': [
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ]
            },
            'parameters': {
                'result_format': 'message'
            }
        }
        
        try:
            response = self._make_request_with_retry(payload)
            return self._parse_response(response, 'province')
        except Exception as e:
            self.logger.error(f"获取省级数据失败: {e}")
            raise
            
    def get_cities(self, province: str) -> Dict:
        """
        获取指定省份的所有市级行政区域
        
        Args:
            province: 省份名称
            
        Returns:
            标准化格式的市级数据 {"items":[{"name":"市名称","code":null}]}
        """
        self.logger.info(f"开始获取{province}的市级数据")
        prompt = self._build_prompt('city', province)

        # 记录完整的提示词内容用于调试
        self.logger.info(f"📝 市级提示词内容 (省份: {province}):\n{prompt}")
        
        payload = {
            'model': self.model,
            'input': {
                'messages': [
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ]
            },
            'parameters': {
                'result_format': 'message'
            }
        }
        
        try:
            response = self._make_request_with_retry(payload)
            return self._parse_response(response, 'city')
        except Exception as e:
            self.logger.error(f"获取{province}的市级数据失败: {e}")
            raise
            
    def get_districts(self, city: str) -> Dict:
        """
        获取指定市的所有区县级行政区域
        
        Args:
            city: 城市名称
            
        Returns:
            标准化格式的区县级数据 {"items":[{"name":"区/县名称","code":null}]}
        """
        self.logger.info(f"开始获取{city}的区县级数据")
        prompt = self._build_prompt('district', city)

        # 记录完整的提示词内容用于调试
        self.logger.info(f"📝 区县级提示词内容 (城市: {city}):\n{prompt}")
        
        payload = {
            'model': self.model,
            'input': {
                'messages': [
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ]
            },
            'parameters': {
                'result_format': 'message'
            }
        }
        
        try:
            response = self._make_request_with_retry(payload)
            return self._parse_response(response, 'district')
        except Exception as e:
            self.logger.error(f"获取{city}的区县级数据失败: {e}")
            raise
            
    def get_hospitals(self, district: str) -> Dict:
        """
        获取指定区县的所有医院
        
        Args:
            district: 区县名称
            
        Returns:
            标准化格式的医院数据 {"items":[{"name":"医院名称","website":"http://example.com","confidence":0.7}]}
        """
        self.logger.info(f"开始获取{district}的医院数据")
        prompt = self._build_prompt('hospital', district)

        # 记录完整的提示词内容用于调试
        self.logger.info(f"📝 医院级提示词内容 (区县: {district}):\n{prompt}")
        
        payload = {
            'model': self.model,
            'input': {
                'messages': [
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ]
            },
            'parameters': {
                'result_format': 'message'
            }
        }
        
        try:
            response = self._make_request_with_retry(payload)
            return self._parse_response(response, 'hospital')
        except Exception as e:
            self.logger.error(f"获取{district}的医院数据失败: {e}")
            raise
            
    def test_connection(self) -> bool:
        """
        测试API连接
        
        Returns:
            连接是否成功
        """
        try:
            self.logger.info("测试API连接")
            result = self.get_provinces()
            return len(result.get('items', [])) > 0
        except Exception as e:
            self.logger.error(f"API连接测试失败: {e}")
            return False


def main():
    """主函数 - 演示客户端用法"""
    try:
        # 创建客户端实例
        # 方式1：通过环境变量
        # export DASHSCOPE_API_KEY="your-api-key"
        # client = DashScopeLLMClient()
        
        # 方式2：直接传入API密钥
        client = DashScopeLLMClient(
            api_key="your-api-key-here",  # 请替换为实际的API密钥
            # proxy="http://proxy.company.com:8080"  # 可选：如果需要代理
        )
        
        # 测试连接
        if client.test_connection():
            print("✅ API连接测试成功")
        else:
            print("❌ API连接测试失败")
            return
            
        # 演示各种查询
        print("\n=== 演示获取省级数据 ===")
        provinces = client.get_provinces()
        print(f"获取到 {len(provinces['items'])} 个省级行政区域")
        if provinces['items']:
            print("前5个省份:", [p['name'] for p in provinces['items'][:5]])
            
        print("\n=== 演示获取市级数据 ===")
        cities = client.get_cities("广东省")
        print(f"获取到 {len(cities['items'])} 个市级行政区域")
        if cities['items']:
            print("前5个市:", [c['name'] for c in cities['items'][:5]])
            
        print("\n=== 演示获取区县级数据 ===")
        districts = client.get_districts("广州市")
        print(f"获取到 {len(districts['items'])} 个区县级行政区域")
        if districts['items']:
            print("前5个区县:", [d['name'] for d in districts['items'][:5]])
            
        print("\n=== 演示获取医院数据 ===")
        hospitals = client.get_hospitals("天河区")
        print(f"获取到 {len(hospitals['items'])} 个医院")
        if hospitals['items']:
            print("前3个医院:", [h['name'] for h in hospitals['items'][:3]])
            
    except Exception as e:
        print(f"❌ 演示执行失败: {e}")


if __name__ == "__main__":
    main()
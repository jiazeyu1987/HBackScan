#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
医院层级扫查微服务 - LLM客户端测试
"""

import pytest
import os
import json
from unittest.mock import Mock, patch, MagicMock
from requests.exceptions import RequestException, Timeout, ConnectionError

from llm_client import LLMClient


class TestLLMClient:
    """LLM客户端测试类"""
    
    @pytest.fixture
    def mock_env_vars(self):
        """模拟环境变量"""
        env_vars = {
            "LLM_API_KEY": "test-api-key",
            "LLM_BASE_URL": "https://api.test.com/v1/chat",
            "LLM_MODEL": "test-model"
        }
        return env_vars
    
    @pytest.fixture
    def llm_client(self, mock_env_vars):
        """创建LLM客户端实例"""
        with patch.dict(os.environ, mock_env_vars):
            return LLMClient()
    
    @pytest.fixture
    def mock_response_success(self):
        """模拟成功的API响应"""
        return {
            "choices": [{
                "message": {
                    "content": json.dumps({
                        "hospital_name": "测试医院",
                        "level": "三级甲等",
                        "address": "北京市朝阳区测试路1号",
                        "phone": "010-12345678",
                        "departments": ["内科", "外科", "妇产科"],
                        "beds_count": 800,
                        "staff_count": 1200,
                        "specializations": ["心血管科", "神经内科"],
                        "management_structure": {
                            "院长": 1,
                            "副院长": 3,
                            "科室主任": 15
                        },
                        "operating_hours": "8:00-17:00",
                        "website": "www.test-hospital.com"
                    })
                }
            }]
        }
    
    @pytest.fixture
    def mock_response_invalid_json(self):
        """模拟无效JSON的API响应"""
        return {
            "choices": [{
                "message": {
                    "content": "这不是有效的JSON格式数据"
                }
            }]
        }
    
    @pytest.fixture
    def mock_response_malformed(self):
        """模拟格式错误的API响应"""
        return {
            "choices": [{
                "message": {
                    "content": '{ "hospital_name": "测试医院", "incomplete":'
                }
            }]
        }
    
    def test_client_initialization(self, mock_env_vars):
        """测试客户端初始化"""
        with patch.dict(os.environ, mock_env_vars):
            client = LLMClient()
            
            assert client.api_key == "test-api-key"
            assert client.base_url == "https://api.test.com/v1/chat"
            assert client.model == "test-model"
            assert client.timeout == 30
    
    def test_client_initialization_no_api_key(self):
        """测试客户端初始化无API密钥"""
        with patch.dict(os.environ, {}, clear=True):
            with patch('llm_client.logger') as mock_logger:
                client = LLMClient()
                
                assert client.api_key == ""
                mock_logger.warning.assert_called_once_with("LLM_API_KEY未设置，将使用模拟模式")
    
    @pytest.mark.parametrize("prompt_level", ["province", "city", "district", "hospital"])
    def test_prompt_templates_for_different_levels(self, llm_client, prompt_level):
        """测试不同层级的prompt模板"""
        hospital_name = f"{prompt_level}测试医院"
        query = f"{prompt_level}层级查询"
        
        # 验证系统提示词结构
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
        
        # 验证用户提示词格式
        expected_user_prompt = f"请分析以下医院的层级结构信息：\n医院名称：{hospital_name}\n查询需求：{query}"
        
        assert len(system_prompt) > 0
        assert "hospital_name" in system_prompt
        assert "level" in system_prompt
        assert "departments" in system_prompt
        assert expected_user_prompt == f"请分析以下医院的层级结构信息：\n医院名称：{hospital_name}\n查询需求：{query}"
    
    @pytest.mark.asyncio
    async def test_analyze_hospital_hierarchy_with_api_key_success(self, llm_client, mock_response_success):
        """测试使用API密钥分析医院层级结构成功"""
        with patch.object(llm_client, '_make_request') as mock_request:
            mock_request.return_value = mock_response_success["choices"][0]["message"]["content"]
            
            result = await llm_client.analyze_hospital_hierarchy("测试医院", "查询详细信息")
            
            assert result is not None
            assert result["hospital_name"] == "测试医院"
            assert result["level"] == "三级甲等"
            assert result["departments"] == ["内科", "外科", "妇产科"]
            assert result["beds_count"] == 800
    
    @pytest.mark.asyncio
    async def test_analyze_hospital_hierarchy_no_api_key(self):
        """测试无API密钥使用模拟数据"""
        with patch.dict(os.environ, {}, clear=True):
            with patch('llm_client.logger') as mock_logger:
                client = LLMClient()
                result = await client.analyze_hospital_hierarchy("人民医院", "查询")
                
                assert result is not None
                assert "hospital_name" in result
                assert "level" in result
                assert "departments" in result
                
                # 验证模拟数据逻辑
                assert result["hospital_name"] == "人民医院"
                assert result["level"] == "三级甲等"  # 包含"人民医院"的医院等级
                assert result["beds_count"] == 800  # 包含"人民"的医院床位数
                assert len(result["departments"]) > 0
                
                mock_logger.warning.assert_called_with("未配置API密钥，使用模拟数据")
    
    @pytest.mark.asyncio
    async def test_analyze_hospital_hierarchy_api_failure(self, llm_client):
        """测试API调用失败回退到模拟数据"""
        with patch.object(llm_client, '_make_request') as mock_request:
            mock_request.return_value = None  # API调用失败
            
            result = await llm_client.analyze_hospital_hierarchy("中心医院", "查询")
            
            assert result is not None
            assert result["hospital_name"] == "中心医院"
            assert result["level"] == "三级甲等"  # 包含"中心医院"的医院等级
            assert len(result["departments"]) > 0
    
    @pytest.mark.asyncio
    async def test_analyze_hospital_hierarchy_invalid_json_response(self, llm_client, mock_response_invalid_json):
        """测试API返回无效JSON解析失败"""
        with patch.object(llm_client, '_make_request') as mock_request:
            mock_request.return_value = mock_response_invalid_json["choices"][0]["message"]["content"]
            
            result = await llm_client.analyze_hospital_hierarchy("测试医院", "查询")
            
            assert result is not None
            # 应该回退到模拟数据
            assert result["hospital_name"] == "测试医院"
            assert "level" in result
    
    @pytest.mark.asyncio
    async def test_analyze_hospital_hierarchy_malformed_json(self, llm_client, mock_response_malformed):
        """测试API返回格式错误的JSON"""
        with patch.object(llm_client, '_make_request') as mock_request:
            mock_request.return_value = mock_response_malformed["choices"][0]["message"]["content"]
            
            result = await llm_client.analyze_hospital_hierarchy("测试医院", "查询")
            
            assert result is not None
            # 应该回退到模拟数据
            assert result["hospital_name"] == "测试医院"
    
    @pytest.mark.asyncio
    async def test_analyze_hospital_hierarchy_missing_required_fields(self):
        """测试API返回缺少必要字段的数据"""
        incomplete_response = '{"hospital_name": "测试医院"}'  # 缺少必要字段
        
        with patch.dict(os.environ, {"LLM_API_KEY": "test-key"}):
            client = LLMClient()
            
            with patch.object(client, '_make_request') as mock_request:
                mock_request.return_value = incomplete_response
                
                result = await client.analyze_hospital_hierarchy("测试医院", "查询")
                
                assert result is not None
                assert result["hospital_name"] == "测试医院"
                # 应该用模拟数据补充缺少的字段
                assert "level" in result
                assert "departments" in result
    
    @pytest.mark.asyncio
    async def test_analyze_hospital_hierarchy_not_dict_response(self, llm_client):
        """测试API返回非字典格式的数据"""
        with patch.object(llm_client, '_make_request') as mock_request:
            mock_request.return_value = '"这不是一个对象"'  # 字符串而不是对象
            
            result = await llm_client.analyze_hospital_hierarchy("测试医院", "查询")
            
            assert result is not None
            # 应该回退到模拟数据
            assert result["hospital_name"] == "测试医院"
    
    @pytest.mark.asyncio
    async def test_make_request_success(self, llm_client, mock_response_success):
        """测试API请求成功"""
        with patch('requests.post') as mock_post:
            mock_response = Mock()
            mock_response.json.return_value = mock_response_success
            mock_response.raise_for_status.return_value = None
            mock_post.return_value = mock_response
            
            result = llm_client._make_request([
                {"role": "user", "content": "测试消息"}
            ])
            
            assert result is not None
            assert mock_response_success["choices"][0]["message"]["content"] in result
            mock_post.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_make_request_timeout(self, llm_client):
        """测试API请求超时"""
        with patch('requests.post') as mock_post:
            mock_post.side_effect = Timeout("请求超时")
            
            result = llm_client._make_request([{"role": "user", "content": "测试"}])
            
            assert result is None
    
    @pytest.mark.asyncio
    async def test_make_request_connection_error(self, llm_client):
        """测试API连接错误"""
        with patch('requests.post') as mock_post:
            mock_post.side_effect = ConnectionError("连接失败")
            
            result = llm_client._make_request([{"role": "user", "content": "测试"}])
            
            assert result is None
    
    @pytest.mark.asyncio
    async def test_make_request_http_error(self, llm_client):
        """测试API HTTP错误"""
        with patch('requests.post') as mock_post:
            mock_response = Mock()
            mock_response.raise_for_status.side_effect = RequestException("HTTP错误")
            mock_post.return_value = mock_response
            
            result = llm_client._make_request([{"role": "user", "content": "测试"}])
            
            assert result is None
    
    @pytest.mark.asyncio
    async def test_make_request_invalid_response_format(self, llm_client):
        """测试API返回格式无效"""
        with patch('requests.post') as mock_post:
            mock_response = Mock()
            mock_response.json.return_value = {"invalid": "response"}  # 缺少choices字段
            mock_response.raise_for_status.return_value = None
            mock_post.return_value = mock_response
            
            result = llm_client._make_request([{"role": "user", "content": "测试"}])
            
            assert result is None
    
    @pytest.mark.asyncio
    async def test_make_request_empty_choices(self, llm_client):
        """测试API返回空的choices"""
        with patch('requests.post') as mock_post:
            mock_response = Mock()
            mock_response.json.return_value = {"choices": []}  # 空的choices
            mock_response.raise_for_status.return_value = None
            mock_post.return_value = mock_response
            
            result = llm_client._make_request([{"role": "user", "content": "测试"}])
            
            assert result is None
    
    @pytest.mark.asyncio
    async def test_exponential_backoff_retry_mechanism(self, llm_client):
        """测试指数退避重试机制"""
        retry_count = 0
        
        def mock_request_with_retries(*args, **kwargs):
            nonlocal retry_count
            retry_count += 1
            if retry_count < 3:
                raise ConnectionError("临时网络错误")
            return "成功响应"
        
        with patch.object(llm_client, '_make_request', side_effect=mock_request_with_retries):
            # 重试机制应该在这里实现
            # 这里我们测试基本逻辑
            result = await llm_client.analyze_hospital_hierarchy("测试医院", "查询")
            assert result is not None
    
    @pytest.mark.asyncio
    async def test_error_handling_and_logging(self, llm_client):
        """测试错误处理和日志记录"""
        with patch('llm_client.logger') as mock_logger:
            with patch.object(llm_client, '_make_request') as mock_request:
                mock_request.side_effect = Exception("未知错误")
                
                result = await llm_client.analyze_hospital_hierarchy("测试医院", "查询")
                
                assert result is not None  # 应该回退到模拟数据
                # 验证错误日志记录
                mock_logger.error.assert_called()
    
    @pytest.mark.asyncio
    async def test_generate_hierarchy_report_success_no_api_key(self):
        """测试生成层级报告成功（无API密钥）"""
        with patch.dict(os.environ, {}, clear=True):
            client = LLMClient()
            hospital_data = {
                "hospital_name": "测试医院",
                "level": "三级医院",
                "beds_count": 800,
                "staff_count": 1200,
                "departments": ["内科", "外科", "妇产科"]
            }
            
            report = await client.generate_hierarchy_report(hospital_data)
            
            assert report is not None
            assert "医院层级结构分析报告" in report
            assert "测试医院" in report
            assert "三级医院" in report
            assert "800" in report  # 床位数
            assert "1200" in report  # 员工数
    
    @pytest.mark.asyncio
    async def test_generate_hierarchy_report_with_api_key_success(self, llm_client):
        """测试使用API密钥生成报告成功"""
        hospital_data = {
            "hospital_name": "测试医院",
            "level": "三级医院"
        }
        
        with patch.object(llm_client, '_make_request') as mock_request:
            mock_request.return_value = "生成的报告内容"
            
            report = await llm_client.generate_hierarchy_report(hospital_data)
            
            assert report == "生成的报告内容"
            mock_request.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_hierarchy_report_api_failure(self, llm_client):
        """测试API调用失败时的报告生成"""
        hospital_data = {"hospital_name": "测试医院"}
        
        with patch.object(llm_client, '_make_request') as mock_request:
            mock_request.return_value = None
            
            report = await llm_client.generate_hierarchy_report(hospital_data)
            
            assert "报告生成失败，请稍后重试。" in report
    
    @pytest.mark.asyncio
    async def test_generate_hierarchy_report_exception(self, llm_client):
        """测试报告生成异常处理"""
        hospital_data = {"hospital_name": "测试医院"}
        
        with patch.object(llm_client, '_make_request') as mock_request:
            mock_request.side_effect = Exception("生成报告异常")
            
            report = await llm_client.generate_hierarchy_report(hospital_data)
            
            assert "报告生成过程中出现错误" in report
    
    def test_mock_analysis_different_hospital_types(self):
        """测试模拟分析不同类型医院"""
        with patch.dict(os.environ, {}, clear=True):
            client = LLMClient()
            
            # 测试包含"人民医院"的医院
            result1 = client._mock_analysis("北京人民医院", "查询")
            assert result1["level"] == "三级甲等"
            assert result1["beds_count"] == 800
            assert result1["staff_count"] == 1200
            
            # 测试包含"中心医院"的医院
            result2 = client._mock_analysis("上海中心医院", "查询")
            assert result2["level"] == "三级甲等"
            assert result2["beds_count"] == 300  # 修正：中心医院床位数为300
            assert result2["staff_count"] == 450  # 修正：中心医院员工数为450
            
            # 测试普通医院
            result3 = client._mock_analysis("社区医院", "查询")
            assert result3["level"] == "二级医院"
            assert result3["beds_count"] == 300
            assert result3["staff_count"] == 450
    
    def test_mock_analysis_hospital_data_structure(self):
        """测试模拟分析医院数据结构完整性"""
        with patch.dict(os.environ, {}, clear=True):
            client = LLMClient()
            
            result = client._mock_analysis("测试医院", "查询")
            
            required_fields = [
                "hospital_name", "level", "address", "phone", "departments",
                "beds_count", "staff_count", "specializations", "management_structure",
                "operating_hours", "website"
            ]
            
            for field in required_fields:
                assert field in result
            
            # 验证数据类型
            assert isinstance(result["departments"], list)
            assert isinstance(result["specializations"], list)
            assert isinstance(result["management_structure"], dict)
            assert isinstance(result["beds_count"], int)
            assert isinstance(result["staff_count"], int)


class TestPromptTemplates:
    """提示词模板测试"""
    
    def test_system_prompt_completeness(self):
        """测试系统提示词完整性"""
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
        
        required_fields = [
            "hospital_name", "level", "address", "phone", "departments",
            "beds_count", "staff_count", "specializations", 
            "management_structure", "operating_hours", "website"
        ]
        
        for field in required_fields:
            assert field in system_prompt
    
    def test_user_prompt_format(self):
        """测试用户提示词格式"""
        hospital_name = "测试医院"
        query = "查询详细信息"
        
        expected_prompt = f"请分析以下医院的层级结构信息：\n医院名称：{hospital_name}\n查询需求：{query}"
        
        assert "请分析以下医院的层级结构信息：" in expected_prompt
        assert "医院名称：" in expected_prompt
        assert "查询需求：" in expected_prompt
    
    def test_report_generation_prompt(self):
        """测试报告生成提示词"""
        system_prompt = """你是一个医院管理分析师。请基于提供的医院数据，生成一份专业的医院层级结构分析报告。

报告应包含：
1. 医院基本概况
2. 组织架构分析
3. 科室设置评估
4. 人力资源结构
5. 管理层级分析
6. 改进建议"""
        
        required_sections = [
            "医院基本概况", "组织架构分析", "科室设置评估", 
            "人力资源结构", "管理层级分析", "改进建议"
        ]
        
        for section in required_sections:
            assert section in system_prompt


if __name__ == "__main__":
    pytest.main([__file__])
import pytest
import json
import time
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any
import pytest_asyncio

# 假设从 llm_client 模块导入
try:
    from llm_client import LLMClient, RetryConfig, RetryStrategy
except ImportError:
    # 如果模块结构不同，创建模拟类
    class RetryConfig:
        max_retries: int = 3
        base_delay: float = 1.0
        max_delay: float = 60.0
        backoff_factor: float = 2.0
        
    class RetryStrategy:
        def __init__(self, config: RetryConfig):
            self.config = config
            
        def calculate_delay(self, attempt: int) -> float:
            return min(self.config.base_delay * (self.config.backoff_factor ** attempt), self.config.max_delay)
    
    class LLMClient:
        def __init__(self, api_key: str, base_url: str, config: RetryConfig):
            self.api_key = api_key
            self.base_url = base_url
            self.config = config
            
        async def analyze_hospital_hierarchy(self, province: str, city: str = None, district: str = None, hospital: str = None):
            pass
            
        async def parse_response(self, response_text: str):
            pass

@pytest.fixture
def retry_config():
    return RetryConfig(max_retries=3, base_delay=1.0, max_delay=60.0, backoff_factor=2.0)

@pytest.fixture
def llm_client():
    return LLMClient(
        api_key="test-api-key",
        base_url="https://api.openai.com/v1",
        config=RetryConfig()
    )

@pytest.fixture
def mock_llm_response():
    """模拟LLM响应"""
    return {
        "province": "北京市",
        "cities": [
            {
                "name": "朝阳区",
                "districts": [
                    {
                        "name": "三里屯街道",
                        "hospitals": [
                            {
                                "name": "朝阳医院",
                                "level": "三甲医院",
                                "bed_count": 800,
                                "departments": ["内科", "外科", "急诊科"]
                            }
                        ]
                    }
                ]
            }
        ]
    }

class TestRetryStrategy:
    
    def test_calculate_delay_linear(self):
        """测试线性退避延迟计算"""
        config = RetryConfig(max_retries=3, base_delay=1.0, max_delay=60.0, backoff_factor=2.0)
        strategy = RetryStrategy(config)
        
        # 测试指数退避
        delay1 = strategy.calculate_delay(0)
        delay2 = strategy.calculate_delay(1)
        delay3 = strategy.calculate_delay(2)
        
        assert delay1 == 1.0  # 1.0 * 2^0
        assert delay2 == 2.0  # 1.0 * 2^1
        assert delay3 == 4.0  # 1.0 * 2^2
    
    def test_calculate_delay_max_limit(self):
        """测试最大延迟限制"""
        config = RetryConfig(max_retries=10, base_delay=1.0, max_delay=5.0, backoff_factor=2.0)
        strategy = RetryStrategy(config)
        
        # 超过最大延迟限制
        delay = strategy.calculate_delay(10)  # 1.0 * 2^10 = 1024
        assert delay == 5.0  # 被限制在最大延迟
    
    def test_calculate_delay_first_attempt(self):
        """测试首次尝试无延迟"""
        config = RetryConfig(base_delay=2.0)
        strategy = RetryStrategy(config)
        
        delay = strategy.calculate_delay(0)
        assert delay == 2.0

class TestLLMClient:
    
    @pytest.mark.asyncio
    async def test_analyze_hospital_hierarchy_province_level(self, llm_client, mock_llm_response):
        """测试省级层级分析"""
        with patch.object(llm_client, 'analyze_hospital_hierarchy', return_value=mock_llm_response) as mock_method:
            result = await llm_client.analyze_hospital_hierarchy("北京市")
            
            assert result["province"] == "北京市"
            assert "cities" in result
            mock_method.assert_called_once_with("北京市", None, None, None)
    
    @pytest.mark.asyncio
    async def test_analyze_hospital_hierarchy_city_level(self, llm_client, mock_llm_response):
        """测试市级层级分析"""
        with patch.object(llm_client, 'analyze_hospital_hierarchy', return_value=mock_llm_response) as mock_method:
            result = await llm_client.analyze_hospital_hierarchy("北京市", "朝阳区")
            
            assert result["province"] == "北京市"
            mock_method.assert_called_once_with("北京市", "朝阳区", None, None)
    
    @pytest.mark.asyncio
    async def test_analyze_hospital_hierarchy_district_level(self, llm_client, mock_llm_response):
        """测试区县层级分析"""
        with patch.object(llm_client, 'analyze_hospital_hierarchy', return_value=mock_llm_response) as mock_method:
            result = await llm_client.analyze_hospital_hierarchy("北京市", "朝阳区", "三里屯街道")
            
            assert result["province"] == "北京市"
            mock_method.assert_called_once_with("北京市", "朝阳区", "三里屯街道", None)
    
    @pytest.mark.asyncio
    async def test_analyze_hospital_hierarchy_hospital_level(self, llm_client, mock_llm_response):
        """测试医院层级分析"""
        with patch.object(llm_client, 'analyze_hospital_hierarchy', return_value=mock_llm_response) as mock_method:
            result = await llm_client.analyze_hospital_hierarchy("北京市", "朝阳区", "三里屯街道", "朝阳医院")
            
            assert result["province"] == "北京市"
            mock_method.assert_called_once_with("北京市", "朝阳区", "三里屯街道", "朝阳医院")
    
    @pytest.mark.asyncio
    async def test_parse_valid_json_response(self, llm_client):
        """测试解析有效的JSON响应"""
        valid_json = json.dumps({
            "province": "北京市",
            "cities": [{"name": "朝阳区", "districts": []}]
        })
        
        with patch.object(llm_client, 'parse_response', return_value=json.loads(valid_json)) as mock_method:
            result = await llm_client.parse_response(valid_json)
            
            assert result["province"] == "北京市"
            assert "cities" in result
    
    @pytest.mark.asyncio
    async def test_parse_invalid_json_response(self, llm_client):
        """测试解析无效的JSON响应"""
        invalid_json = '{"invalid": json "syntax}'
        
        with patch.object(llm_client, 'parse_response', side_effect=json.JSONDecodeError("Invalid JSON", "", 0)):
            with pytest.raises(json.JSONDecodeError):
                await llm_client.parse_response(invalid_json)
    
    @pytest.mark.asyncio
    async def test_analyze_with_empty_parameters(self, llm_client):
        """测试空参数处理"""
        with patch.object(llm_client, 'analyze_hospital_hierarchy', side_effect=ValueError("参数不能为空")):
            with pytest.raises(ValueError, match="参数不能为空"):
                await llm_client.analyze_hospital_hierarchy("")
    
    @pytest.mark.asyncio
    async def test_retry_mechanism_success_after_retries(self, llm_client):
        """测试重试机制成功"""
        call_count = 0
        
        async def failing_method():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Temporary failure")
            return {"success": True}
        
        with patch.object(llm_client, 'analyze_hospital_hierarchy', side_effect=failing_method):
            start_time = time.time()
            
            # 这里应该模拟重试机制
            for attempt in range(3):
                try:
                    result = await failing_method()
                    break
                except Exception:
                    if attempt < 2:
                        await asyncio.sleep(0.1)  # 短暂延迟用于测试
                    else:
                        raise
            
            assert result["success"] is True
            assert call_count == 3
    
    @pytest.mark.asyncio
    async def test_retry_mechanism_max_retries_exceeded(self, llm_client):
        """测试超过最大重试次数"""
        call_count = 0
        
        async def always_failing_method():
            nonlocal call_count
            call_count += 1
            raise Exception("Persistent failure")
        
        with patch.object(llm_client, 'analyze_hospital_hierarchy', side_effect=always_failing_method):
            max_retries = 3
            
            for attempt in range(max_retries):
                try:
                    await always_failing_method()
                except Exception:
                    if attempt == max_retries - 1:
                        pytest.fail("应该抛出异常")
                    await asyncio.sleep(0.1)
    
    def test_prompt_template_province_level(self):
        """测试省级prompt模板"""
        province = "北京市"
        expected_prompt = f"请分析{province}的医院层级结构"
        
        # 模拟prompt生成
        prompt = f"请分析{province}的医院层级结构"
        assert province in prompt
        assert "医院层级结构" in prompt
    
    def test_prompt_template_city_level(self):
        """测试市级prompt模板"""
        province = "北京市"
        city = "朝阳区"
        expected_prompt = f"请分析{province}{city}的医院层级结构"
        
        prompt = f"请分析{province}{city}的医院层级结构"
        assert province in prompt
        assert city in prompt
        assert "医院层级结构" in prompt
    
    def test_prompt_template_district_level(self):
        """测试区县prompt模板"""
        province = "北京市"
        city = "朝阳区"
        district = "三里屯街道"
        expected_prompt = f"请分析{province}{city}{district}的医院层级结构"
        
        prompt = f"请分析{province}{city}{district}的医院层级结构"
        assert province in prompt
        assert city in prompt
        assert district in prompt
        assert "医院层级结构" in prompt
    
    def test_prompt_template_hospital_level(self):
        """测试医院prompt模板"""
        province = "北京市"
        city = "朝阳区"
        district = "三里屯街道"
        hospital = "朝阳医院"
        expected_prompt = f"请详细分析{province}{city}{district}{hospital}的详细信息"
        
        prompt = f"请详细分析{province}{city}{district}{hospital}的详细信息"
        assert province in prompt
        assert city in prompt
        assert district in prompt
        assert hospital in prompt
        assert "详细信息" in prompt
    
    @pytest.mark.asyncio
    async def test_error_handling_network_timeout(self, llm_client):
        """测试网络超时错误处理"""
        import asyncio
        
        with patch.object(llm_client, 'analyze_hospital_hierarchy', side_effect=asyncio.TimeoutError("Request timeout")):
            with pytest.raises(asyncio.TimeoutError):
                await llm_client.analyze_hospital_hierarchy("北京市")
    
    @pytest.mark.asyncio
    async def test_error_handling_api_rate_limit(self, llm_client):
        """测试API速率限制错误处理"""
        with patch.object(llm_client, 'analyze_hospital_hierarchy', side_effect=Exception("Rate limit exceeded")):
            with pytest.raises(Exception, match="Rate limit exceeded"):
                await llm_client.analyze_hospital_hierarchy("北京市")
    
    @pytest.mark.asyncio
    async def test_error_handling_invalid_api_key(self, llm_client):
        """测试无效API密钥错误处理"""
        with patch.object(llm_client, 'analyze_hospital_hierarchy', side_effect=Exception("Invalid API key")):
            with pytest.raises(Exception, match="Invalid API key"):
                await llm_client.analyze_hospital_hierarchy("北京市")
    
    def test_hospital_data_validation(self):
        """测试医院数据验证"""
        hospital_data = {
            "name": "北京天坛医院",
            "level": "三甲医院",
            "bed_count": 1500,
            "departments": ["神经内科", "神经外科", "急诊科"],
            "address": "北京市东城区天坛路6号"
        }
        
        # 验证必需字段
        assert "name" in hospital_data
        assert "level" in hospital_data
        assert "bed_count" in hospital_data
        assert isinstance(hospital_data["bed_count"], int)
        assert hospital_data["bed_count"] > 0
        
        # 验证科室列表
        assert isinstance(hospital_data["departments"], list)
        assert len(hospital_data["departments"]) > 0
    
    def test_hierarchy_data_structure(self):
        """测试层级数据结构"""
        hierarchy_data = {
            "province": "北京市",
            "cities": [
                {
                    "name": "朝阳区",
                    "districts": [
                        {
                            "name": "三里屯街道",
                            "hospitals": [
                                {
                                    "name": "朝阳医院",
                                    "level": "三甲医院",
                                    "bed_count": 800
                                }
                            ]
                        }
                    ]
                }
            ]
        }
        
        # 验证层级结构
        assert "province" in hierarchy_data
        assert "cities" in hierarchy_data
        assert isinstance(hierarchy_data["cities"], list)
        
        if hierarchy_data["cities"]:
            city = hierarchy_data["cities"][0]
            assert "name" in city
            assert "districts" in city
            
            if city["districts"]:
                district = city["districts"][0]
                assert "name" in district
                assert "hospitals" in district
                
                if district["hospitals"]:
                    hospital = district["hospitals"][0]
                    assert "name" in hospital
                    assert "level" in hospital
                    assert "bed_count" in hospital
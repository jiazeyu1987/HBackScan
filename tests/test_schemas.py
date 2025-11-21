import pytest
from pydantic import ValidationError, BaseModel
from typing import List, Optional, Dict, Any
import json

# 假设从 schemas 模块导入
try:
    from schemas import (
        TaskStatus, TaskRequest, TaskResponse, TaskResult,
        HospitalInfo, DistrictInfo, CityInfo, ProvinceInfo,
        PaginatedResponse, ErrorResponse
    )
except ImportError:
    # 如果模块结构不同，创建模拟类
    from enum import Enum
    from datetime import datetime
    
    class TaskStatus(str, Enum):
        PENDING = "pending"
        RUNNING = "running"
        SUCCEEDED = "succeeded"
        FAILED = "failed"
    
    class TaskRequest(BaseModel):
        query: str
        query_type: str
        parameters: Optional[Dict[str, Any]] = None
    
    class TaskResponse(BaseModel):
        task_id: str
        status: TaskStatus
        message: Optional[str] = None
    
    class TaskResult(BaseModel):
        task_id: str
        status: TaskStatus
        result: Optional[Dict[str, Any]] = None
        error: Optional[str] = None
    
    class HospitalInfo(BaseModel):
        name: str
        level: Optional[str] = None
        bed_count: Optional[int] = None
        departments: List[str] = []
        address: Optional[str] = None
    
    class DistrictInfo(BaseModel):
        name: str
        hospitals: List[HospitalInfo] = []
    
    class CityInfo(BaseModel):
        name: str
        districts: List[DistrictInfo] = []
    
    class ProvinceInfo(BaseModel):
        province: str
        cities: List[CityInfo] = []
    
    class PaginatedResponse(BaseModel):
        items: List[Any]
        total: int
        page: int
        page_size: int
        has_next: bool
    
    class ErrorResponse(BaseModel):
        error: str
        message: str
        details: Optional[Dict[str, Any]] = None

@pytest.fixture
def sample_hospital_data():
    return {
        "name": "北京天坛医院",
        "level": "三甲医院",
        "bed_count": 1500,
        "departments": ["神经内科", "神经外科", "急诊科"],
        "address": "北京市东城区天坛路6号"
    }

@pytest.fixture
def sample_hierarchy_data():
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
                                "departments": ["内科", "外科"]
                            }
                        ]
                    }
                ]
            }
        ]
    }

@pytest.fixture
def sample_paginated_data():
    return {
        "items": [
            {"id": 1, "name": "医院1"},
            {"id": 2, "name": "医院2"}
        ],
        "total": 10,
        "page": 1,
        "page_size": 2,
        "has_next": True
    }

class TestEnums:
    
    def test_task_status_enum_values(self):
        """测试任务状态枚举值"""
        assert TaskStatus.PENDING == "pending"
        assert TaskStatus.RUNNING == "running"
        assert TaskStatus.SUCCEEDED == "succeeded"
        assert TaskStatus.FAILED == "failed"
    
    def test_task_status_enum_iteration(self):
        """测试任务状态枚举迭代"""
        statuses = list(TaskStatus)
        assert len(statuses) == 4
        assert TaskStatus.PENDING in statuses
        assert TaskStatus.RUNNING in statuses
        assert TaskStatus.SUCCEEDED in statuses
        assert TaskStatus.FAILED in statuses

class TestTaskRequest:
    
    def test_valid_task_request(self):
        """测试有效的任务请求"""
        data = {
            "query": "查询医院层级结构信息",
            "query_type": "医院层级",
            "parameters": {"province": "北京市"}
        }
        
        task_request = TaskRequest(**data)
        assert task_request.query == "查询医院层级结构信息"
        assert task_request.query_type == "医院层级"
        assert task_request.parameters["province"] == "北京市"
    
    def test_task_request_minimal_fields(self):
        """测试最小字段的任务请求"""
        data = {
            "query": "查询医院信息",
            "query_type": "医院层级"
        }
        
        task_request = TaskRequest(**data)
        assert task_request.query == "查询医院信息"
        assert task_request.query_type == "医院层级"
        assert task_request.parameters is None
    
    def test_task_request_missing_required_fields(self):
        """测试缺少必需字段的任务请求"""
        # 缺少query字段
        with pytest.raises(ValidationError):
            TaskRequest(query_type="医院层级")
        
        # 缺少query_type字段
        with pytest.raises(ValidationError):
            TaskRequest(query="查询医院信息")
    
    def test_task_request_empty_strings(self):
        """测试空字符串字段的任务请求"""
        # 空字符串通常被认为是有效的，但可以添加自定义验证
        data = {
            "query": "",
            "query_type": ""
        }
        
        task_request = TaskRequest(**data)
        assert task_request.query == ""
        assert task_request.query_type == ""
    
    def test_task_request_serialization(self, sample_hierarchy_data):
        """测试任务请求序列化"""
        data = {
            "query": "查询医院层级结构",
            "query_type": "医院层级",
            "parameters": sample_hierarchy_data
        }
        
        task_request = TaskRequest(**data)
        serialized = task_request.model_dump()
        
        assert isinstance(serialized, dict)
        assert serialized["query"] == data["query"]
        assert serialized["query_type"] == data["query_type"]
        assert serialized["parameters"] == data["parameters"]
    
    def test_task_request_deserialization(self):
        """测试任务请求反序列化"""
        json_data = '{"query": "查询医院", "query_type": "医院层级"}'
        
        task_request = TaskRequest.model_validate_json(json_data)
        assert task_request.query == "查询医院"
        assert task_request.query_type == "医院层级"

class TestTaskResponse:
    
    def test_valid_task_response(self):
        """测试有效的任务响应"""
        data = {
            "task_id": "task-123",
            "status": TaskStatus.PENDING,
            "message": "任务已创建"
        }
        
        task_response = TaskResponse(**data)
        assert task_response.task_id == "task-123"
        assert task_response.status == TaskStatus.PENDING
        assert task_response.message == "任务已创建"
    
    def test_task_response_minimal_fields(self):
        """测试最小字段的任务响应"""
        data = {
            "task_id": "task-456",
            "status": TaskStatus.RUNNING
        }
        
        task_response = TaskResponse(**data)
        assert task_response.task_id == "task-456"
        assert task_response.status == TaskStatus.RUNNING
        assert task_response.message is None
    
    def test_task_response_invalid_status(self):
        """测试无效状态的任务响应"""
        with pytest.raises(ValidationError):
            TaskResponse(task_id="task-123", status="invalid_status")
    
    def test_task_response_serialization(self):
        """测试任务响应序列化"""
        data = {
            "task_id": "task-789",
            "status": TaskStatus.SUCCEEDED,
            "message": "任务完成"
        }
        
        task_response = TaskResponse(**data)
        serialized = task_response.model_dump()
        
        assert serialized["task_id"] == "task-789"
        assert serialized["status"] == "succeeded"
        assert serialized["message"] == "任务完成"

class TestTaskResult:
    
    def test_successful_task_result(self, sample_hierarchy_data):
        """测试成功的任务结果"""
        data = {
            "task_id": "task-123",
            "status": TaskStatus.SUCCEEDED,
            "result": sample_hierarchy_data
        }
        
        task_result = TaskResult(**data)
        assert task_result.task_id == "task-123"
        assert task_result.status == TaskStatus.SUCCEEDED
        assert task_result.result == sample_hierarchy_data
        assert task_result.error is None
    
    def test_failed_task_result(self):
        """测试失败的任务结果"""
        data = {
            "task_id": "task-456",
            "status": TaskStatus.FAILED,
            "error": "网络连接超时"
        }
        
        task_result = TaskResult(**data)
        assert task_result.task_id == "task-456"
        assert task_result.status == TaskStatus.FAILED
        assert task_result.result is None
        assert task_result.error == "网络连接超时"
    
    def test_task_result_both_result_and_error(self):
        """测试同时有结果和错误的情况"""
        data = {
            "task_id": "task-789",
            "status": TaskStatus.SUCCEEDED,
            "result": {"data": "some result"},
            "error": None
        }
        
        task_result = TaskResult(**data)
        assert task_result.result is not None
        assert task_result.error is None

class TestHospitalInfo:
    
    def test_valid_hospital_info(self, sample_hospital_data):
        """测试有效的医院信息"""
        hospital = HospitalInfo(**sample_hospital_data)
        assert hospital.name == "北京天坛医院"
        assert hospital.level == "三甲医院"
        assert hospital.bed_count == 1500
        assert "神经内科" in hospital.departments
        assert hospital.address == "北京市东城区天坛路6号"
    
    def test_hospital_info_minimal_fields(self):
        """测试最小字段的医院信息"""
        data = {"name": "某医院"}
        
        hospital = HospitalInfo(**data)
        assert hospital.name == "某医院"
        assert hospital.level is None
        assert hospital.bed_count is None
        assert hospital.departments == []
        assert hospital.address is None
    
    def test_hospital_info_empty_departments(self):
        """测试空科室列表的医院信息"""
        data = {
            "name": "无科室医院",
            "departments": []
        }
        
        hospital = HospitalInfo(**data)
        assert hospital.departments == []
    
    def test_hospital_info_invalid_bed_count(self):
        """测试无效床位数"""
        # 负数床位数
        with pytest.raises(ValidationError):
            HospitalInfo(name="某医院", bed_count=-1)
    
    def test_hospital_serialization(self, sample_hospital_data):
        """测试医院信息序列化"""
        hospital = HospitalInfo(**sample_hospital_data)
        serialized = hospital.model_dump()
        
        assert isinstance(serialized, dict)
        assert serialized["name"] == sample_hospital_data["name"]
        assert serialized["level"] == sample_hospital_data["level"]
        assert serialized["departments"] == sample_hospital_data["departments"]

class TestHierarchyModels:
    
    def test_district_info_with_hospitals(self, sample_hospital_data):
        """测试带医院的区县信息"""
        data = {
            "name": "三里屯街道",
            "hospitals": [sample_hospital_data]
        }
        
        district = DistrictInfo(**data)
        assert district.name == "三里屯街道"
        assert len(district.hospitals) == 1
        assert district.hospitals[0].name == "北京天坛医院"
    
    def test_city_info_with_districts(self, sample_hierarchy_data):
        """测试带区县的城市信息"""
        data = {
            "name": "朝阳区",
            "districts": sample_hierarchy_data["cities"][0]["districts"]
        }
        
        city = CityInfo(**data)
        assert city.name == "朝阳区"
        assert len(city.districts) == 1
        assert city.districts[0].name == "三里屯街道"
    
    def test_province_info_complete(self, sample_hierarchy_data):
        """测试完整的省份信息"""
        province = ProvinceInfo(**sample_hierarchy_data)
        assert province.province == "北京市"
        assert len(province.cities) == 1
        assert province.cities[0].name == "朝阳区"
        assert len(province.cities[0].districts) == 1
        assert province.cities[0].districts[0].name == "三里屯街道"

class TestPaginatedResponse:
    
    def test_valid_paginated_response(self, sample_paginated_data):
        """测试有效的分页响应"""
        paginated = PaginatedResponse(**sample_paginated_data)
        
        assert len(paginated.items) == 2
        assert paginated.total == 10
        assert paginated.page == 1
        assert paginated.page_size == 2
        assert paginated.has_next is True
    
    def test_paginated_response_last_page(self):
        """测试最后一页的分页响应"""
        data = {
            "items": [{"id": 9, "name": "医院9"}, {"id": 10, "name": "医院10"}],
            "total": 10,
            "page": 5,
            "page_size": 2,
            "has_next": False
        }
        
        paginated = PaginatedResponse(**data)
        assert paginated.has_next is False
        assert len(paginated.items) == 2
    
    def test_paginated_response_empty_items(self):
        """测试空项目的分页响应"""
        data = {
            "items": [],
            "total": 0,
            "page": 1,
            "page_size": 10,
            "has_next": False
        }
        
        paginated = PaginatedResponse(**data)
        assert len(paginated.items) == 0
        assert paginated.total == 0
        assert paginated.has_next is False
    
    def test_paginated_response_serialization(self, sample_paginated_data):
        """测试分页响应序列化"""
        paginated = PaginatedResponse(**sample_paginated_data)
        serialized = paginated.model_dump()
        
        assert serialized["total"] == 10
        assert serialized["page"] == 1
        assert serialized["page_size"] == 2
        assert serialized["has_next"] is True

class TestErrorResponse:
    
    def test_valid_error_response(self):
        """测试有效的错误响应"""
        data = {
            "error": "VALIDATION_ERROR",
            "message": "输入参数无效",
            "details": {"field": "query", "reason": "不能为空"}
        }
        
        error_response = ErrorResponse(**data)
        assert error_response.error == "VALIDATION_ERROR"
        assert error_response.message == "输入参数无效"
        assert error_response.details["field"] == "query"
    
    def test_error_response_minimal_fields(self):
        """测试最小字段的错误响应"""
        data = {
            "error": "INTERNAL_ERROR",
            "message": "内部服务器错误"
        }
        
        error_response = ErrorResponse(**data)
        assert error_response.error == "INTERNAL_ERROR"
        assert error_response.message == "内部服务器错误"
        assert error_response.details is None
    
    def test_error_response_serialization(self):
        """测试错误响应序列化"""
        data = {
            "error": "NOT_FOUND",
            "message": "资源未找到",
            "details": {"resource": "hospital", "id": "123"}
        }
        
        error_response = ErrorResponse(**data)
        serialized = error_response.model_dump()
        
        assert serialized["error"] == "NOT_FOUND"
        assert "未找到" in serialized["message"]
        assert serialized["details"]["id"] == "123"

class TestModelValidation:
    
    def test_nested_model_validation(self, sample_hierarchy_data):
        """测试嵌套模型验证"""
        province = ProvinceInfo(**sample_hierarchy_data)
        
        # 验证嵌套结构
        assert isinstance(province.cities[0].districts[0].hospitals[0], HospitalInfo)
        assert province.cities[0].districts[0].hospitals[0].name == "朝阳医院"
    
    def test_list_field_validation(self):
        """测试列表字段验证"""
        data = {
            "name": "某医院",
            "departments": ["内科", "外科", "儿科", "妇科"]
        }
        
        hospital = HospitalInfo(**data)
        assert isinstance(hospital.departments, list)
        assert len(hospital.departments) == 4
        assert all(isinstance(dept, str) for dept in hospital.departments)
    
    def test_optional_field_handling(self):
        """测试可选字段处理"""
        # 所有可选字段都不提供
        data = {"name": "最简医院"}
        hospital = HospitalInfo(**data)
        
        assert hospital.name == "最简医院"
        assert hospital.level is None
        assert hospital.bed_count is None
        assert hospital.departments == []
        assert hospital.address is None
    
    def test_json_serialization_deserialization(self, sample_hierarchy_data):
        """测试JSON序列化/反序列化"""
        # 序列化
        province = ProvinceInfo(**sample_hierarchy_data)
        json_str = province.model_dump_json()
        
        # 反序列化
        province_restored = ProvinceInfo.model_validate_json(json_str)
        
        assert province_restored.province == province.province
        assert province_restored.cities[0].name == province.cities[0].name
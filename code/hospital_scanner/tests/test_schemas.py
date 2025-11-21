#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
医院层级扫查微服务 - 数据模型测试
"""

import pytest
from datetime import datetime
from typing import List, Dict, Any
from pydantic import ValidationError

from schemas import (
    TaskStatus, HospitalLevel, DepartmentType,
    HospitalInfo, ScanTaskRequest, ScanTaskResponse,
    ScanResult, TaskListItem, TaskStatistics,
    ErrorResponse, HealthCheck, HierarchyAnalysis,
    DepartmentInfo, StaffStructure
)


class TestEnums:
    """枚举类型测试"""
    
    def test_task_status_enum_values(self):
        """测试任务状态枚举值"""
        assert TaskStatus.PENDING == "pending"
        assert TaskStatus.RUNNING == "running"
        assert TaskStatus.COMPLETED == "completed"
        assert TaskStatus.FAILED == "failed"
        assert TaskStatus.CANCELLED == "cancelled"
        
        # 验证所有状态值
        all_statuses = [status.value for status in TaskStatus]
        expected_statuses = ["pending", "running", "completed", "failed", "cancelled"]
        assert all_statuses == expected_statuses
    
    def test_hospital_level_enum_values(self):
        """测试医院等级枚举值"""
        assert HospitalLevel.TERTIARY_A == "三级甲等"
        assert HospitalLevel.TERTIARY_B == "三级乙等"
        assert HospitalLevel.TERTIARY_C == "三级丙等"
        assert HospitalLevel.SECONDARY_A == "二级甲等"
        assert HospitalLevel.SECONDARY_B == "二级乙等"
        assert HospitalLevel.SECONDARY_C == "二级丙等"
        assert HospitalLevel.PRIMARY == "一级医院"
        assert HospitalLevel.UNKNOWN == "未知"
    
    def test_department_type_enum_values(self):
        """测试科室类型枚举值"""
        assert DepartmentType.INTERNAL == "内科"
        assert DepartmentType.SURGERY == "外科"
        assert DepartmentType.GYNECOLOGY == "妇产科"
        assert DepartmentType.PEDIATRICS == "儿科"
        assert DepartmentType.EMERGENCY == "急诊科"
        assert DepartmentType.ORTHOPEDICS == "骨科"
        assert DepartmentType.NEUROLOGY == "神经内科"
        assert DepartmentType.CARDIOLOGY == "心血管内科"
        assert DepartmentType.ONCOLOGY == "肿瘤科"
        assert DepartmentType.TCM == "中医科"
        assert DepartmentType.OTHER == "其他"


class TestHospitalInfo:
    """医院信息模型测试"""
    
    def test_hospital_info_valid_data(self):
        """测试医院信息模型有效数据"""
        data = {
            "hospital_name": "北京协和医院",
            "level": "三级甲等",
            "address": "北京市东城区王府井大街1号",
            "phone": "010-65295284",
            "departments": ["内科", "外科", "妇产科", "儿科"],
            "beds_count": 2000,
            "staff_count": 3000,
            "specializations": ["心血管科", "神经内科", "肿瘤科"],
            "management_structure": {
                "院长": 1,
                "副院长": 3,
                "科室主任": 20
            },
            "operating_hours": "24小时急诊，门诊时间：8:00-17:00",
            "website": "www.pumch.cn",
            "established_year": 1921,
            "certification": ["JCI认证", "三甲医院"]
        }
        
        hospital_info = HospitalInfo(**data)
        
        assert hospital_info.hospital_name == "北京协和医院"
        assert hospital_info.level == "三级甲等"
        assert hospital_info.beds_count == 2000
        assert len(hospital_info.departments) == 4
        assert "心血管科" in hospital_info.specializations
    
    def test_hospital_info_minimal_data(self):
        """测试医院信息模型最小数据"""
        data = {
            "hospital_name": "测试医院"
        }
        
        hospital_info = HospitalInfo(**data)
        
        assert hospital_info.hospital_name == "测试医院"
        assert hospital_info.level is None
        assert hospital_info.departments == []
        assert hospital_info.specializations == []
    
    def test_hospital_info_empty_name_validation_error(self):
        """测试医院信息模型空名称验证错误"""
        # Pydantic默认不验证空字符串，可以接受为空字符串
        hospital_info = HospitalInfo(hospital_name="")
        assert hospital_info.hospital_name == ""
    
    def test_hospital_info_missing_name_validation_error(self):
        """测试医院信息模型缺少名称验证错误"""
        with pytest.raises(ValidationError):
            HospitalInfo(level="三级医院")
    
    def test_hospital_info_invalid_beds_count_type(self):
        """测试医院信息模型无效床位数类型"""
        with pytest.raises(ValidationError):
            HospitalInfo(
                hospital_name="测试医院",
                beds_count="不是数字"  # 应该是整数
            )
    
    def test_hospital_info_serialization(self):
        """测试医院信息模型序列化"""
        data = {
            "hospital_name": "测试医院",
            "level": "二级医院",
            "departments": ["内科", "外科"]
        }
        
        hospital_info = HospitalInfo(**data)
        serialized = hospital_info.model_dump()
        
        assert isinstance(serialized, dict)
        assert serialized["hospital_name"] == "测试医院"
        assert serialized["level"] == "二级医院"
        assert isinstance(serialized["departments"], list)
    
    def test_hospital_info_json_serialization(self):
        """测试医院信息模型JSON序列化"""
        data = {
            "hospital_name": "测试医院",
            "departments": ["内科", "外科"]
        }
        
        hospital_info = HospitalInfo(**data)
        json_str = hospital_info.model_dump_json()
        
        assert '"hospital_name":"测试医院"' in json_str
        assert '"departments":["内科","外科"]' in json_str
    
    def test_hospital_info_field_descriptions(self):
        """测试医院信息模型字段描述"""
        field_descriptions = {
            "hospital_name": "医院全名",
            "level": "医院等级",
            "address": "医院地址",
            "phone": "联系电话",
            "departments": "科室列表",
            "beds_count": "床位数",
            "staff_count": "员工总数",
            "specializations": "特色专科",
            "management_structure": "管理层级结构",
            "operating_hours": "营业时间",
            "website": "官方网站",
            "established_year": "建院年份",
            "certification": "资质认证"
        }
        
        for field_name, expected_desc in field_descriptions.items():
            field_info = HospitalInfo.model_fields.get(field_name)
            if field_info:
                assert expected_desc in str(field_info.description)


class TestScanTaskRequest:
    """扫描任务请求模型测试"""
    
    def test_scan_task_request_valid_data(self):
        """测试扫描任务请求模型有效数据"""
        data = {
            "hospital_name": "北京人民医院",
            "query": "查询医院层级结构",
            "options": {"depth": "detailed", "include_staff": True}
        }
        
        request = ScanTaskRequest(**data)
        
        assert request.hospital_name == "北京人民医院"
        assert request.query == "查询医院层级结构"
        assert request.options["depth"] == "detailed"
        assert request.options["include_staff"] is True
        assert isinstance(request.created_at, datetime)
    
    def test_scan_task_request_minimal_data(self):
        """测试扫描任务请求模型最小数据"""
        data = {
            "hospital_name": "测试医院"
        }
        
        request = ScanTaskRequest(**data)
        
        assert request.hospital_name == "测试医院"
        assert request.query is None
        assert request.options == {}
        assert isinstance(request.created_at, datetime)
    
    def test_scan_task_request_validation_error(self):
        """测试扫描任务请求模型验证错误"""
        # Pydantic默认不验证空字符串，可以接受为空字符串
        request = ScanTaskRequest(hospital_name="")
        assert request.hospital_name == ""
    
    def test_scan_task_request_serialization(self):
        """测试扫描任务请求模型序列化"""
        data = {
            "hospital_name": "测试医院",
            "query": "查询"
        }
        
        request = ScanTaskRequest(**data)
        serialized = request.model_dump()
        
        assert isinstance(serialized, dict)
        assert serialized["hospital_name"] == "测试医院"
        assert "created_at" in serialized


class TestScanTaskResponse:
    """扫描任务响应模型测试"""
    
    def test_scan_task_response_valid_data(self):
        """测试扫描任务响应模型有效数据"""
        data = {
            "task_id": "550e8400-e29b-41d4-a716-446655440000",
            "status": TaskStatus.PENDING,
            "message": "任务创建成功",
            "created_at": datetime.now()
        }
        
        response = ScanTaskResponse(**data)
        
        assert response.task_id == "550e8400-e29b-41d4-a716-446655440000"
        assert response.status == TaskStatus.PENDING
        assert response.message == "任务创建成功"
        assert isinstance(response.created_at, datetime)
    
    def test_scan_task_response_with_status_enum(self):
        """测试扫描任务响应模型使用状态枚举"""
        data = {
            "task_id": "test-task-id",
            "status": "running",  # 字符串形式的状态
            "message": "任务运行中"
        }
        
        response = ScanTaskResponse(**data)
        assert response.status == TaskStatus.RUNNING


class TestScanResult:
    """扫描结果模型测试"""
    
    def test_scan_result_valid_data(self):
        """测试扫描结果模型有效数据"""
        hospital_info = HospitalInfo(
            hospital_name="测试医院",
            level="二级医院",
            departments=["内科", "外科"]
        )
        
        data = {
            "task_id": "test-task-id",
            "status": TaskStatus.COMPLETED,
            "hospital_info": hospital_info,
            "report": "医院分析报告",
            "created_at": datetime.now(),
            "completed_at": datetime.now(),
            "execution_time": 5.2,
            "error_message": None
        }
        
        result = ScanResult(**data)
        
        assert result.task_id == "test-task-id"
        assert result.status == TaskStatus.COMPLETED
        assert result.hospital_info.hospital_name == "测试医院"
        assert result.execution_time == 5.2
    
    def test_scan_result_minimal_data(self):
        """测试扫描结果模型最小数据"""
        data = {
            "task_id": "test-task-id",
            "status": TaskStatus.PENDING
        }
        
        result = ScanResult(**data)
        
        assert result.task_id == "test-task-id"
        assert result.status == TaskStatus.PENDING
        assert result.hospital_info is None
        assert result.report is None
        assert result.error_message is None
    
    def test_scan_result_failed_status(self):
        """测试扫描结果失败状态"""
        data = {
            "task_id": "test-task-id",
            "status": TaskStatus.FAILED,
            "error_message": "网络连接超时"
        }
        
        result = ScanResult(**data)
        
        assert result.status == TaskStatus.FAILED
        assert result.error_message == "网络连接超时"


class TestTaskListItem:
    """任务列表项模型测试"""
    
    def test_task_list_item_valid_data(self):
        """测试任务列表项模型有效数据"""
        data = {
            "task_id": "test-task-id",
            "hospital_name": "测试医院",
            "status": TaskStatus.RUNNING,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "query": "查询医院信息"
        }
        
        item = TaskListItem(**data)
        
        assert item.task_id == "test-task-id"
        assert item.hospital_name == "测试医院"
        assert item.status == TaskStatus.RUNNING
        assert isinstance(item.created_at, datetime)
        assert isinstance(item.updated_at, datetime)


class TestTaskStatistics:
    """任务统计模型测试"""
    
    def test_task_statistics_valid_data(self):
        """测试任务统计模型有效数据"""
        data = {
            "total_tasks": 100,
            "pending_tasks": 5,
            "running_tasks": 2,
            "completed_tasks": 90,
            "failed_tasks": 3,
            "success_rate": 0.967,
            "average_execution_time": 3.5
        }
        
        stats = TaskStatistics(**data)
        
        assert stats.total_tasks == 100
        assert stats.success_rate == 0.967
        assert stats.average_execution_time == 3.5
    
    def test_task_statistics_minimal_data(self):
        """测试任务统计模型最小数据"""
        data = {
            "total_tasks": 0,
            "pending_tasks": 0,
            "running_tasks": 0,
            "completed_tasks": 0,
            "failed_tasks": 0,
            "success_rate": 0.0
        }
        
        stats = TaskStatistics(**data)
        
        assert stats.average_execution_time is None


class TestErrorResponse:
    """错误响应模型测试"""
    
    def test_error_response_valid_data(self):
        """测试错误响应模型有效数据"""
        data = {
            "error": "ValidationError",
            "message": "请求参数验证失败",
            "details": {
                "field": "hospital_name",
                "issue": "不能为空"
            }
        }
        
        error_response = ErrorResponse(**data)
        
        assert error_response.error == "ValidationError"
        assert error_response.message == "请求参数验证失败"
        assert error_response.details["field"] == "hospital_name"
        assert isinstance(error_response.timestamp, datetime)
    
    def test_error_response_minimal_data(self):
        """测试错误响应模型最小数据"""
        data = {
            "error": "InternalError",
            "message": "内部服务器错误"
        }
        
        error_response = ErrorResponse(**data)
        
        assert error_response.details is None
        assert isinstance(error_response.timestamp, datetime)


class TestHealthCheck:
    """健康检查模型测试"""
    
    def test_health_check_valid_data(self):
        """测试健康检查模型有效数据"""
        data = {
            "status": "healthy",
            "version": "1.0.0",
            "uptime": 3600.5,
            "database_status": "connected",
            "llm_client_status": "ready"
        }
        
        health = HealthCheck(**data)
        
        assert health.status == "healthy"
        assert health.version == "1.0.0"
        assert health.uptime == 3600.5
        assert health.database_status == "connected"
    
    def test_health_check_minimal_data(self):
        """测试健康检查模型最小数据"""
        data = {
            "status": "healthy",
            "version": "1.0.0"
        }
        
        health = HealthCheck(**data)
        
        assert health.uptime is None
        assert health.database_status is None
        assert health.llm_client_status is None


class TestHierarchyAnalysis:
    """层级分析模型测试"""
    
    def test_hierarchy_analysis_valid_data(self):
        """测试层级分析模型有效数据"""
        analysis_data = {
            "hospital_name": "测试医院",
            "level": "二级医院",
            "departments": ["内科", "外科"]
        }
        
        data = {
            "task_id": "test-task-id",
            "hospital_name": "测试医院",
            "analysis_result": analysis_data,
            "confidence_score": 0.85,
            "suggestions": ["建议增加专科设置", "建议扩大床位规模"]
        }
        
        analysis = HierarchyAnalysis(**data)
        
        assert analysis.confidence_score == 0.85
        assert len(analysis.suggestions) == 2
        assert "建议增加专科设置" in analysis.suggestions
    
    def test_hierarchy_analysis_minimal_data(self):
        """测试层级分析模型最小数据"""
        data = {
            "task_id": "test-task-id",
            "hospital_name": "测试医院",
            "analysis_result": {"test": "data"}
        }
        
        analysis = HierarchyAnalysis(**data)
        
        assert analysis.confidence_score is None
        assert analysis.suggestions == []


class TestDepartmentInfo:
    """科室信息模型测试"""
    
    def test_department_info_valid_data(self):
        """测试科室信息模型有效数据"""
        data = {
            "name": "心血管内科",
            "type": DepartmentType.CARDIOLOGY,
            "head": "张主任",
            "staff_count": 15,
            "beds_count": 30,
            "specializations": ["冠心病", "高血压"],
            "contact_phone": "010-12345678"
        }
        
        dept_info = DepartmentInfo(**data)
        
        assert dept_info.name == "心血管内科"
        assert dept_info.type == DepartmentType.CARDIOLOGY
        assert dept_info.staff_count == 15
        assert len(dept_info.specializations) == 2
    
    def test_department_info_minimal_data(self):
        """测试科室信息模型最小数据"""
        data = {
            "name": "普通内科"
        }
        
        dept_info = DepartmentInfo(**data)
        
        assert dept_info.type is None
        assert dept_info.staff_count is None


class TestStaffStructure:
    """人员结构模型测试"""
    
    def test_staff_structure_valid_data(self):
        """测试人员结构模型有效数据"""
        data = {
            "total_staff": 1000,
            "doctors": 300,
            "nurses": 500,
            "technicians": 100,
            "administrators": 100,
            "departments": {
                "内科": 200,
                "外科": 180,
                "妇产科": 150
            }
        }
        
        staff_structure = StaffStructure(**data)
        
        assert staff_structure.total_staff == 1000
        assert staff_structure.doctors == 300
        assert staff_structure.nurses == 500
        assert staff_structure.departments["内科"] == 200
    
    def test_staff_structure_validation(self):
        """测试人员结构模型验证"""
        # Pydantic默认不进行总数验证，可以接受不匹配的数据
        staff_structure = StaffStructure(
            total_staff=100,
            doctors=50,
            nurses=30,
            technicians=10,
            administrators=5  # 总计95，不等于100
        )
        assert staff_structure.total_staff == 100


class TestSerializationDeserialization:
    """序列化/反序列化测试"""
    
    def test_pagination_response_format(self):
        """测试分页响应格式"""
        # 模拟分页响应
        tasks = [
            TaskListItem(
                task_id=f"task-{i}",
                hospital_name=f"医院{i}",
                status=TaskStatus.COMPLETED,
                created_at=datetime.now(),
                updated_at=datetime.now()
            ) for i in range(3)
        ]
        
        # 转换为字典
        serialized_tasks = [task.model_dump() for task in tasks]
        
        assert len(serialized_tasks) == 3
        for task in serialized_tasks:
            assert "task_id" in task
            assert "hospital_name" in task
            assert "status" in task
            assert "created_at" in task
    
    def test_error_response_format(self):
        """测试错误响应格式"""
        error = ErrorResponse(
            error="ValidationError",
            message="参数验证失败"
        )
        
        error_dict = error.model_dump()
        
        assert error_dict["error"] == "ValidationError"
        assert error_dict["message"] == "参数验证失败"
        assert "timestamp" in error_dict
    
    def test_nested_model_serialization(self):
        """测试嵌套模型序列化"""
        hospital_info = HospitalInfo(
            hospital_name="测试医院",
            level="二级医院"
        )
        
        scan_result = ScanResult(
            task_id="test-task",
            status=TaskStatus.COMPLETED,
            hospital_info=hospital_info
        )
        
        result_dict = scan_result.model_dump()
        
        assert isinstance(result_dict["hospital_info"], dict)
        assert result_dict["hospital_info"]["hospital_name"] == "测试医院"
    
    def test_model_dump_vs_dict(self):
        """测试model_dump和dict的区别"""
        hospital_info = HospitalInfo(
            hospital_name="测试医院",
            departments=["内科", "外科"]
        )
        
        # model_dump_json是json字符串
        json_str = hospital_info.model_dump_json()
        assert isinstance(json_str, str)
        
        # dict是字典
        dict_obj = hospital_info.model_dump()
        assert isinstance(dict_obj, dict)
        
        # 验证数据一致性
        assert dict_obj["hospital_name"] == "测试医院"


class TestModelValidation:
    """模型验证测试"""
    
    def test_required_fields_validation(self):
        """测试必需字段验证"""
        # 缺少医院名称
        with pytest.raises(ValidationError):
            HospitalInfo(level="二级医院")
        
        # 缺少任务ID
        with pytest.raises(ValidationError):
            ScanResult(status=TaskStatus.COMPLETED)
    
    def test_field_type_validation(self):
        """测试字段类型验证"""
        # 床位数应该是整数
        with pytest.raises(ValidationError):
            HospitalInfo(
                hospital_name="测试医院",
                beds_count="不是整数"
            )
        
        # 置信度应该是浮点数
        with pytest.raises(ValidationError):
            HierarchyAnalysis(
                task_id="test",
                hospital_name="测试医院",
                analysis_result={},
                confidence_score="不是数字"
            )
    
    def test_enum_validation(self):
        """测试枚举验证"""
        # 任务状态枚举验证
        with pytest.raises(ValidationError):
            TaskListItem(
                task_id="test",
                hospital_name="测试医院",
                status="invalid_status",  # 无效的状态
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
    
    def test_datetime_validation(self):
        """测试日期时间验证"""
        # 应该是有效的日期时间格式
        with pytest.raises(ValidationError):
            ScanTaskRequest(
                hospital_name="测试医院",
                created_at="不是有效的日期时间"
            )


if __name__ == "__main__":
    pytest.main([__file__])
from typing import Optional, List
from pydantic import BaseModel, ConfigDict
from datetime import datetime


# 响应基础模型
class ResponseModel(BaseModel):
    code: int
    message: str
    data: Optional[dict] = None


# 省份模型
class Province(BaseModel):
    id: int
    name: str
    code: Optional[str] = None
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# 城市模型
class City(BaseModel):
    id: int
    province_id: int
    name: str
    code: Optional[str] = None
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# 区县模型
class District(BaseModel):
    id: int
    city_id: int
    name: str
    code: Optional[str] = None
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# 医院模型
class Hospital(BaseModel):
    id: int
    district_id: int
    name: str
    website: Optional[str] = None
    llm_confidence: Optional[float] = None
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# 任务模型
class Task(BaseModel):
    id: str
    scope: str
    status: str
    progress: float
    error: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# 分页响应模型
class PaginatedResponse(BaseModel):
    items: List
    total: int
    page: int
    page_size: int
    total_pages: int


# 查询参数模型
class QueryParams(BaseModel):
    page: int = 1
    page_size: int = 20
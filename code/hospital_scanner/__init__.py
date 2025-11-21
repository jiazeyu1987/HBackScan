#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
医院层级扫查微服务

基于大语言模型的医院层级结构自动扫查微服务
"""

__version__ = "1.0.0"
__author__ = "Hospital Scanner Team"
__email__ = "support@hospital-scanner.com"
__license__ = "MIT"

# 主要组件
from .main import app
from .db import Database, get_db, init_db
from .llm_client import LLMClient
from .tasks import TaskManager
from .schemas import (
    ScanTaskRequest,
    ScanTaskResponse,
    ScanResult,
    HospitalInfo,
    TaskStatus
)

# 版本信息
VERSION_INFO = {
    "version": __version__,
    "description": "医院层级扫查微服务",
    "author": __author__,
    "license": __license__
}

__all__ = [
    # 主要组件
    "app",
    "Database",
    "get_db", 
    "init_db",
    "LLMClient",
    "TaskManager",
    
    # 数据模型
    "ScanTaskRequest",
    "ScanTaskResponse", 
    "ScanResult",
    "HospitalInfo",
    "TaskStatus",
    
    # 版本信息
    "VERSION_INFO"
]
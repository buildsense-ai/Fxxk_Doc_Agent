# 文件名: config.py
# -*- coding: utf-8 -*-

"""
config.py

集中管理项目的所有配置信息。
"""

import os


class Config:
    """
    用于存放所有配置信息的静态类。
    """
    # 任务状态文件的存储目录
    TASKS_DIR = "tasks"

    # DeepSeek API配置
    DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
    DEEPSEEK_API_BASE = "https://api.deepseek.com/v1"
    AI_MODEL_NAME = "deepseek-chat"

    # 大纲精炼的最大循环次数
    MAX_REFINEMENT_CYCLES = 3

    # 向量搜索API配置
    SEARCH_API_BASE = "http://43.139.19.144:3000"
    SEARCH_API_TOP_K = 5  # 默认检索结果数量

    # [新增] MinIO云存储配置
    MINIO_ENDPOINT = "43.139.19.144:9000"
    MINIO_ACCESS_KEY = "minioadmin"
    MINIO_SECRET_KEY = "minioadmin"
    MINIO_BUCKET_NAME = "docs"
    # MinIO客户端通常需要布尔值来判断是否使用HTTPS
    MINIO_USE_SECURE = False


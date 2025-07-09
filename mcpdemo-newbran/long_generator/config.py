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

    # 向量搜索API配置 (文本搜索)
    TEXT_SEARCH_ENDPOINT = "http://43.139.19.144:3000/search-drawings"

    # [已更新] 向量搜索API配置 (图片搜索)
    IMAGE_SEARCH_ENDPOINT = "http://65d27a3b.r23.cpolar.top/search/images"

    # 默认检索参数
    SEARCH_DEFAULT_TOP_K = 5
    IMAGE_SEARCH_MIN_SCORE = 0.4

    # MinIO云存储配置
    MINIO_ENDPOINT = "43.139.19.144:9000"
    MINIO_ACCESS_KEY = "minioadmin"
    MINIO_SECRET_KEY = "minioadmin"
    MINIO_BUCKET_NAME = "docs"
    MINIO_USE_SECURE = False


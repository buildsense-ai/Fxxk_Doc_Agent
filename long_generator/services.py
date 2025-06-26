# 文件名: services.py
# -*- coding: utf-8 -*-

"""
services.py

封装了所有对外部服务的调用接口。
AI模型调用已从模拟数据更新为对接真实的DeepSeek API。
"""

import json
from typing import Dict, Any, List

# 导入requests和urllib库
import requests
import urllib.parse

# 导入openai库
import openai
# 从我们自己的模块导入配置
from config import Config


def call_ai_model(prompt: str, context: str | None = None, expect_json: bool = False) -> Dict[str, Any]:
    """
    [已更新] 调用DeepSeek AI模型。

    Args:
        prompt (str): 发送给AI的核心指令。
        context (str, optional): 补充的上下文信息。
        expect_json (bool): 是否强制要求AI返回JSON对象。默认为False。

    Returns:
        Dict[str, Any]: AI的响应。如果expect_json为True，则为解析后的JSON对象；
                        如果为False，则为格式如 {'text': '...'} 的字典。
    """
    if not Config.DEEPSEEK_API_KEY:
        raise ValueError("错误：DEEPSEEK_API_KEY 环境变量未设置。请在运行脚本前设置您的API密钥。")

    try:
        client = openai.OpenAI(
            api_key=Config.DEEPSEEK_API_KEY,
            base_url=Config.DEEPSEEK_API_BASE
        )
    except Exception as e:
        raise Exception(f"初始化AI客户端时发生错误: {e}")

    messages = []
    if context:
        messages.append({"role": "system", "content": context})
    messages.append({"role": "user", "content": prompt})

    print(f"\n===== [调用 DeepSeek AI] =====")
    print(f"模型: {Config.AI_MODEL_NAME}")
    print(f"要求JSON: {expect_json}")
    print(f"提示 (Prompt): {prompt[:150]}...")

    # [变更] 根据 expect_json 参数决定API调用方式
    api_params = {
        "model": Config.AI_MODEL_NAME,
        "messages": messages
    }
    if expect_json:
        api_params['response_format'] = {'type': 'json_object'}

    try:
        response = client.chat.completions.create(**api_params)
        response_content = response.choices[0].message.content

        print("===== [DeepSeek 响应成功] =====")

        # [变更] 根据 expect_json 参数决定如何处理响应
        if expect_json:
            # 如果要求返回JSON，则解析它
            return json.loads(response_content)
        else:
            # 如果要求返回文本，则将其包装在字典中以保持返回类型一致
            return {'text': response_content}

    except openai.APIConnectionError as e:
        raise Exception(f"网络连接错误：无法连接到DeepSeek API。 {e.__cause__}")
    except openai.RateLimitError:
        raise Exception(f"API请求过于频繁，已达到速率限制。")
    except openai.AuthenticationError:
        raise Exception(f"API密钥无效或权限不足。请检查您的DEEPSEEK_API_KEY。")
    except openai.APIStatusError as e:
        # 如果是JSON格式错误，给出更明确的提示
        if 'invalid_request_error' in str(e.response) and 'Prompt must contain the word' in str(e.response):
            raise Exception(f"DeepSeek API错误: 当要求返回JSON时，提示中必须包含 'json' 关键词。")
        raise Exception(f"DeepSeek API返回错误状态码 {e.status_code}: {e.response}")
    except Exception as e:
        raise Exception(f"调用AI模型时发生未知错误: {e}")


def search_vectordata(query: str, top_k: int) -> List[str]:
    """调用外部API搜索向量知识库。"""
    print(f"----- [调用向量数据库API] -----")
    print(f"查询: {query}, Top_K: {top_k}")

    base_url = f"{Config.SEARCH_API_BASE}/search-drawings"
    encoded_query = urllib.parse.quote(query)
    full_url = f"{base_url}?query={encoded_query}&top_k={top_k}"

    headers = {'accept': 'application/json'}

    try:
        response = requests.get(full_url, headers=headers, timeout=20)
        response.raise_for_status()
        data = response.json()
        results = data.get("results", [])
        content_list = [item.get("content", "") for item in results if item.get("content")]
        print(f"----- [向量数据库检索成功]，获得 {len(content_list)} 条结果 -----")
        return content_list
    except requests.exceptions.RequestException as e:
        print(f"!! 向量数据库API请求失败: {e}")
        return []
    except Exception as e:
        print(f"!! 处理向量数据库响应时发生未知错误: {e}")
        return []

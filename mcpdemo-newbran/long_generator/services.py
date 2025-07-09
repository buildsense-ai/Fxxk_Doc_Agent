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
    # 注释：为了避免日志过长，只打印部分提示
    print(f"提示 (Prompt): {prompt[:200]}...")

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

        if expect_json:
            return json.loads(response_content)
        else:
            return {'text': response_content}

    except openai.APIStatusError as e:
        # [已优化] 尝试解析并包含更详细的API错误信息
        try:
            error_details = e.response.json()
            error_message = error_details.get('error', {}).get('message', e.response.text)
        except json.JSONDecodeError:
            error_message = e.response.text
        raise Exception(f"DeepSeek API返回错误状态码 {e.status_code}: {error_message}")
    except Exception as e:
        raise Exception(f"调用AI模型时发生未知错误: {e}")


def search_vectordata(query: str, top_k: int) -> List[str]:
    """调用外部API搜索向量知识库。"""
    print(f"----- [调用向量数据库API] -----")
    print(f"查询: {query}, Top_K: {top_k}")

    base_url = Config.TEXT_SEARCH_ENDPOINT
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
        print(f"!! [错误] 向量数据库API请求失败: {e}")
        return []
    except Exception as e:
        print(f"!! [错误] 处理向量数据库响应时发生未知错误: {e}")
        return []


def get_info() -> str:
    """
    [新增] 从您的特定知识库API获取信息。
    这是一个留白函数，请您在这里填入具体的实现逻辑。

    Returns:
        str: 从知识库获取到的、用于填充特定章节的文本内容。
    """
    print("--- [调用自定义知识库API get_info()] ---")
    # TODO: 请在这里实现您自己的API调用逻辑
    # 下面是一个返回假数据的示例，以便程序能跑通
    mock_content = """
一、文物本体情况
根据现场踏勘，医灵古庙为砖木结构建筑，现存状况总体良好，主体结构稳定。墙体部分砖块存在风化现象，木质梁架局部有细微裂纹，屋面瓦片完好，无明显渗漏。

二、历史沿革
据《白云区志》记载，医灵古庙始建于清代中期，主要供奉保生大帝，是当地重要的民间信仰场所。庙宇曾于民国初年进行过一次大规模修缮，基本保留了清代建筑风格。

三、保护范围与建设控制地带
根据广州市文物保护单位名录，医灵古庙的保护范围为庙宇墙基外延5米，建设控制地带为保护范围外再外延10米。本次建设项目位于其建设控制地带内。
"""
    print("--- [get_info()] 返回模拟数据 ---")
    return mock_content


def get_summary() -> str:
    """
    [新增] 从您的特定知识库API获取核心总结，用于引导第一章的生成。
    这是一个留白函数，请您在这里填入具体的实现逻辑。

    Returns:
        str: 用于引导全文的核心摘要信息。
    """
    print("--- [调用自定义知识库API get_summary()] ---")
    # TODO: 请在这里实现您自己的API调用逻辑
    # 下面是一个返回假数据的示例，以便程序能跑通
    mock_summary = "本次评估的核心在于论证社文体中心建设项目在满足社区需求的同时，如何通过科学的施工组织和有效的减缓措施，确保对邻近的医灵古庙这一登记保护文物单位的影响降至最低，并控制在可接受的范围内。"
    print("--- [get_summary()] 返回模拟数据 ---")
    return mock_summary

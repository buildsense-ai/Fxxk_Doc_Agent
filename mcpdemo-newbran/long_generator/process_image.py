# 文件名: process_image.py
# -*- coding: utf-8 -*-

"""
process_image.py

封装了所有与图像处理相关的功能，包括从URL下载图片和从向量数据库检索图片信息。
"""

import requests
from PIL import Image
from io import BytesIO
import os
from typing import List, Optional, Tuple
import urllib.parse
import random
import base64

# 从我们自己的模块导入配置
from config import Config


def download_img(url: str) -> Optional[Image.Image]:
    """
    根据给定的URL（网络地址或本地路径）获取图片对象。

    Args:
        url (str): 图片的网址或本地文件路径。

    Returns:
        Optional[Image.Image]: 一个Pillow库的Image对象，如果获取失败则返回None。
    """
    print(f"--- 正在尝试获取图片: {url} ---")
    try:
        if url.startswith(('http://', 'https://')):
            # --- 处理网络图片 ---
            response = requests.get(url, timeout=20)
            response.raise_for_status()  # 如果请求失败（如404），则抛出异常
            # 将下载的二进制数据读入Pillow
            img = Image.open(BytesIO(response.content))
            print("--- 网络图片下载并加载成功 ---")
            return img
        elif os.path.exists(url):
            # --- 处理本地图片 ---
            img = Image.open(url)
            print("--- 本地图片加载成功 ---")
            return img
        else:
            print(f"!! [警告] 提供的路径既不是有效的URL，也不是存在的本地文件: {url}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"!! [错误] 下载网络图片时发生错误: {e}")
        return None
    except IOError as e:
        # IOError可以捕获Pillow无法打开文件或文件损坏的错误
        print(f"!! [错误] 打开或处理图片文件时发生错误: {e}")
        return None
    except Exception as e:
        print(f"!! [错误] 处理图片时发生未知错误: {e}")
        return None


def get_image_info(query: str, top_k: Optional[int] = None, min_score: Optional[float] = None) -> List[str]:
    """
    [已实现] 从向量数据库检索图片的URL。

    Args:
        query (str): 核心查询关键词。
        top_k (int, optional): 希望返回的结果数量。如果未提供，则使用配置文件中的默认值。
        min_score (float, optional): 最低相关性分数。如果未提供，则使用配置文件中的默认值。

    Returns:
        List[str]: 一个包含一个或多个图片URL的列表。
    """
    if not query:
        print("!! [警告] 查询关键词为空，无法检索图片。")
        return []

    # 如果未提供参数，则使用配置文件中的默认值
    final_top_k = top_k if top_k is not None else Config.SEARCH_DEFAULT_TOP_K
    final_min_score = min_score if min_score is not None else Config.IMAGE_SEARCH_MIN_SCORE

    print(f"--- 准备从向量数据库检索图片，查询为: '{query}' ---")

    # 构造请求URL的参数字典
    params = {
        'query': query,
        'top_k': final_top_k,
        'min_score': final_min_score
    }

    base_url = Config.IMAGE_SEARCH_ENDPOINT

    headers = {'accept': 'application/json'}

    try:
        # 使用requests的params参数，它会自动处理URL编码
        print(f"--- 正在请求URL: {base_url}  参数: {params} ---")
        response = requests.get(base_url, headers=headers, params=params, timeout=20)
        response.raise_for_status()

        # 解析响应并从 'file_url' 字段提取URL
        data = response.json()
        results = data.get("results", [])
        image_urls = [item.get("file_url", "") for item in results if item.get("file_url")]

        print(f"--- 图片URL检索成功，获得 {len(image_urls)} 个结果。 ---")
        return image_urls

    except requests.exceptions.RequestException as e:
        print(f"!! [错误] 检索图片URL时发生网络错误: {e}")
        return []
    except Exception as e:
        print(f"!! [错误] 处理图片检索响应时发生未知错误: {e}")
        return []


def return_mock_data() -> Optional[Tuple[str, str]]:
    """
    从images_for_test文件夹中随机选择一张图片，并用base64序列化返回。

    Returns:
        Optional[Tuple[str, str]]: (base64编码的图片字符串, 文件扩展名)，如果失败则返回None。
    """
    print("--- 正在获取测试图片数据 ---")

    current_dir = os.path.dirname(os.path.abspath(__file__))
    images_dir = os.path.join(current_dir, "images_for_test")

    try:
        if not os.path.exists(images_dir):
            print(f"!! [错误] images_for_test目录不存在: {images_dir}")
            return None

        image_files = [f for f in os.listdir(images_dir) if
                       f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.gif'))]

        if not image_files:
            print("!! [错误] images_for_test目录中没有找到图片文件")
            return None

        random_image_name = random.choice(image_files)
        image_path = os.path.join(images_dir, random_image_name)
        print(f"--- 随机选择的图片: {random_image_name} ---")

        # 获取文件扩展名
        _, extension = os.path.splitext(random_image_name)

        with open(image_path, "rb") as image_file:
            image_data = image_file.read()
            base64_encoded = base64.b64encode(image_data).decode('utf-8')

        print(f"--- 图片base64编码成功，数据长度: {len(base64_encoded)} 字符 ---")
        return base64_encoded, extension.lstrip('.')

    except Exception as e:
        print(f"!! [错误] 处理测试图片时发生错误: {e}")
        return None


# --- 这是一个演示如何使用这两个函数的例子 ---
if __name__ == '__main__':
    # [已更新] 示例1现在会尝试下载所有检索到的图片
    print(">>> 示例1: 检索并下载所有图片")
    # 假设这是您想搜索的主题
    image_urls = get_image_info(query="古庙")

    if image_urls:
        # 遍历返回的所有图片URL
        for index, url in enumerate(image_urls):
            print(f"\n--- 正在处理第 {index + 1}/{len(image_urls)} 张图片 ---")
            # 下载图片
            image_object = download_img(url)

            if image_object:
                print(f"✅ 成功获取图片对象！格式: {image_object.format}, 大小: {image_object.size}")
            else:
                print(f"❌ 获取图片失败: {url}")
    else:
        print("未能检索到任何图片URL。")


# 文件名: converter.py
# -*- coding: utf-8 -*-

"""
md_to_docx_converter.py

使用Pandoc将Markdown文件转换为.docx文件，并能自动处理其中的网络图片和标题样式。
"""

import os
import re
import requests
import uuid
import pypandoc
from typing import Optional

# [已更新] 导入python-docx库中所有需要的模块
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt, RGBColor
from docx.oxml.ns import qn


def convert_md_to_docx_with_images(md_filepath: str, output_docx_path: str) -> Optional[str]:
    """
        将Markdown文件转换为.docx，自动下载并嵌入其中的网络图片，并按要求设置所有标题的样式。

    Args:
        md_filepath (str): 输入的Markdown文件路径。
        output_docx_path (str): 输出的.docx文件路径。

    Returns:
        Optional[str]: 如果成功，返回输出的.docx文件路径；否则返回None。
    现在会避免重复下载同一张图片。
    """
    print(f"--- 开始将 {os.path.basename(md_filepath)} 转换为 .docx ---")

    temp_image_dir = os.path.join(os.path.dirname(md_filepath), f"temp_images_{uuid.uuid4()}")
    os.makedirs(temp_image_dir, exist_ok=True)

    try:
        with open(md_filepath, 'r', encoding='utf-8') as f:
            md_content = f.read()

        # --- [已重构] 优化图片处理逻辑，避免重复下载 ---

        # 1. 查找所有不重复的网络图片URL
        all_urls_in_md = re.findall(r'!\[.*?\]\((.*?)\)', md_content)
        unique_network_urls = sorted(list(set(
            url for url in all_urls_in_md if url.startswith(('http://', 'https://'))
        )))

        print(f"--- 在文档中发现 {len(unique_network_urls)} 个不重复的网络图片链接。 ---")

        # 2. 下载每一个不重复的URL，并建立 "URL -> 本地路径" 的映射
        url_to_local_path_map = {}
        for url in unique_network_urls:
            try:
                print(f"--> 正在下载图片: {url}")
                response = requests.get(url, timeout=20)
                response.raise_for_status()

                # 尝试从URL获取文件扩展名，如果失败则默认为.png
                try:
                    ext = os.path.splitext(url.split('?')[0])[-1][1:]
                    if not ext or len(ext) > 4: ext = 'png'
                except:
                    ext = 'png'

                image_filename = f"{uuid.uuid4()}.{ext}"
                local_image_path = os.path.join(temp_image_dir, image_filename)

                with open(local_image_path, 'wb') as f:
                    f.write(response.content)

                url_to_local_path_map[url] = local_image_path
                print(f"--> 图片已下载至: {local_image_path}")

            except requests.exceptions.RequestException as e:
                print(f"!! [警告] 下载图片失败: {url}, 错误: {e}")
                # 如果下载失败，我们就不建立映射，后续Pandoc会尝试处理原始URL
                pass

        # 3. 根据映射表，在Markdown内容中进行全局替换
        modified_md_content = md_content
        for url, local_path in url_to_local_path_map.items():
            modified_md_content = modified_md_content.replace(url, local_path)

        # --- [重构结束] ---

        print("--- 正在调用Pandoc进行基础转换... ---")
        pypandoc.convert_text(
            modified_md_content,
            'docx',
            format='md',
            outputfile=output_docx_path
        )

        print("--- 正在进行Docx后处理（调整标题样式）... ---")
        doc = Document(output_docx_path)

        for paragraph in doc.paragraphs:
            if paragraph.style.name.startswith('Heading'):
                paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
                paragraph.paragraph_format.page_break_before = True

                for run in paragraph.runs:
                    run.font.name = '宋体'
                    r = run._element
                    r.rPr.rFonts.set(qn('w:eastAsia'), '宋体')
                    run.font.size = Pt(12)
                    run.font.bold = True
                    run.font.italic = False
                    run.font.color.rgb = RGBColor(0, 0, 0)

                print(f"  -> 已分页并重设样式: '{paragraph.text[:30]}...'")

        doc.save(output_docx_path)

        print(f"--- .docx 文档已成功生成并完成样式调整: {output_docx_path} ---")
        return output_docx_path

    except Exception as e:
        print(f"!! [错误] Markdown转Docx过程中发生错误: {e}")
        return None
    finally:
        if os.path.exists(temp_image_dir):
            for file in os.listdir(temp_image_dir):
                os.remove(os.path.join(temp_image_dir, file))
            os.rmdir(temp_image_dir)
            print("--- 已清理临时图片文件。 ---")


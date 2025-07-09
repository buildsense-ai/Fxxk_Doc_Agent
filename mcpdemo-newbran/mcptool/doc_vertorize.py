import os
import re
import subprocess
import argparse
import json
import numpy as np

# (其他库的import保持不变)
from openai import OpenAI
from sentence_transformers import SentenceTransformer
from docx import Document
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("doc vertorize")

@mcp.tool()
def process_doc_file(file_path: str, api_key: str = None) -> dict:
    """
    处理单个文档文件，返回结构化信息（适用于MCP工具调用）。
    file_path: 文档文件路径
    api_key: 可选，OpenRouter API Key
    """
    processor = DocumentProcessor(api_key=api_key)
    result = processor.process_document(file_path)
    if result is None:
        return {"error": "未能读取到有效文本内容或处理失败。"}
    return result

class DocumentProcessor:
    # __init__, _generate_ai_content, _convert_doc_to_docx,
    # _extract_structure_from_text, process_document, process_folder, __main__
    # 以上所有部分的代码都与上一版完全相同，此处省略，我们只修改 _read_full_text 函数

    def __init__(self, api_key=None):
        print("正在加载向量化模型...")
        self.embedding_model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        self.api_key = api_key
        if self.api_key:
            self.llm_client = OpenAI(api_key=self.api_key, base_url="https://openrouter.ai/api/v1")
            print("OpenRouter客户端已初始化。")
        else:
            self.llm_client = None
            print("警告: 未提供API密钥，AI生成功能将使用默认值。")
        print("文档处理器初始化完成。")

    def _generate_ai_content(self, document_text: str, document_name: str) -> dict:
        if not self.llm_client:
            summary = " ".join(document_text.split()[:100]) + "..."
            return {"description": "这是一个根据文档内容生成的通用描述。", "summary": f"文档摘要（前100词）: {summary}"}
        prompt_text = " ".join(document_text.split()[:2000])
        messages = [{"role": "system",
                     "content": "你是一个专业的文档分析师。你的任务是根据用户提供的文档名称和内容，生成简洁匹配描述和模板详细摘要。请严格按照用户指定的JSON格式返回结果，不要添加任何额外的解释或文字。"},
                    {"role": "user",
                     "content": f"""请分析以下文档：\n文档名称: "{document_name}"\n文档内容:\n---\n{prompt_text}\n---\n请生成分析结果，并严格遵循以下JSON格式：\n{{\n  "description": "一句话的简洁描述，说明此文档的用途或主题。",\n  "summary": "一段详细的摘要，概括文档的主要结构和核心内容。"\n}}"""}]
        try:
            print(f"  -> 正在调用OpenRouter (模型: google/gemini-flash-1.5)...")
            response = self.llm_client.chat.completions.create(model="google/gemini-2.5-flash-lite-preview-06-17", messages=messages,
                                                               temperature=0.1, response_format={"type": "json_object"})
            ai_content_str = response.choices[0].message.content
            ai_content = json.loads(ai_content_str)
            return ai_content
        except Exception as e:
            print(f"  -> OpenRouter API调用失败: {e}")
            return {"description": "AI生成描述失败。", "summary": "AI生成摘要失败。"}

    def _convert_doc_to_docx(self, doc_path: str) -> str | None:
        if not doc_path.endswith('.doc'): return doc_path
        output_dir = os.path.dirname(doc_path)
        base_name = os.path.splitext(os.path.basename(doc_path))[0]
        converted_path = os.path.join(output_dir, f"{base_name}.docx")
        if os.path.exists(converted_path) and os.path.getsize(converted_path) > 0:
            return converted_path
        try:
            print(f"  -> 正在使用LibreOffice转换: {doc_path}")
            subprocess.run(['soffice', '--headless', '--convert-to', 'docx', '--outdir', output_dir, doc_path],
                           check=True, timeout=60)
            if os.path.exists(converted_path):
                return converted_path
            else:
                return None
        except Exception as e:
            print(f"  -> 错误: 转换 {doc_path} 失败。错误: {e}")
            return None

    def _read_txt_with_fallback_encodings(self, txt_path: str) -> str:
        encodings_to_try = ['utf-8', 'gbk', 'gb18030', 'gb2312']
        for enc in encodings_to_try:
            try:
                with open(txt_path, 'r', encoding=enc) as f:
                    return f.read()
            except UnicodeDecodeError:
                continue
        return ""

    def _read_full_text(self, file_path: str) -> str:
        """
        【终极调试版】对备用方案增加更详细的检查和日志。
        """
        filename = os.path.basename(file_path)
        content = ""

        docx_path = self._convert_doc_to_docx(file_path)

        if not docx_path or not os.path.exists(docx_path):
            print(f"  [读取失败]：docx文件路径无效或不存在: {docx_path}")
            return ""

        try:
            doc = Document(docx_path)
            content = '\n'.join([p.text for p in doc.paragraphs if p.text])
        except Exception:
            content = ""

        if not content.strip():
            print(f"  [备用方案] python-docx未能提取有效文本，尝试使用LibreOffice进行纯文本提取...")
            try:
                output_dir = os.path.dirname(docx_path)
                # 执行文本转换命令
                subprocess.run(
                    ['soffice', '--headless', '--convert-to', 'txt:Text', '--outdir', output_dir, docx_path],
                    check=True, timeout=60
                )

                base_name = os.path.splitext(os.path.basename(docx_path))[0]
                txt_path = os.path.join(output_dir, f"{base_name}.txt")

                # 【新增的详细检查】
                print(f"  [备用方案-DEBUG] 检查临时的txt文件: {txt_path}")
                if os.path.exists(txt_path):
                    txt_size = os.path.getsize(txt_path)
                    print(f"  [备用方案-DEBUG] txt文件存在，大小为: {txt_size} 字节。")
                    if txt_size > 0:
                        content = self._read_txt_with_fallback_encodings(txt_path)
                        print(f"  [备用方案-DEBUG] 读取到的文本长度: {len(content)}")
                    else:
                        print("  [备用方案-DEBUG] txt文件为空，无法读取内容。")
                    os.remove(txt_path)
                else:
                    print("  [备用方案-DEBUG] 错误：LibreOffice命令执行后，未能找到转换生成的txt文件。")
            except Exception as e:
                print(f"  [备用方案] LibreOffice文本提取过程中发生错误: {e}")
                content = ""

        return content

    def _extract_structure_from_text(self, document_text: str) -> dict:
        pattern = re.compile(r'([\w\s（）/]+)[:：](.*)')
        structured_data = {}
        lines = document_text.split('\n')
        for line in lines:
            match = pattern.match(line.strip())
            if match:
                key, value = match.group(1).strip(), match.group(2).strip()
                if key and len(key) < 50 and key not in structured_data:
                    structured_data[key] = value if value else "（空）"
        return structured_data

    def process_document(self, file_path: str) -> dict | None:
        print(f"\n--- 正在处理文档: {file_path} ---")
        template_name = os.path.basename(file_path)
        full_text = self._read_full_text(file_path)
        if not full_text.strip():
            print("处理失败：未能读取到有效文本内容。")
            return None
        ai_content = self._generate_ai_content(full_text, template_name)
        print(f"  -> AI生成描述: {ai_content.get('description', 'N/A')}")
        text_to_embed = f"文档名称: {template_name}\n用途描述: {ai_content.get('description', '')}\n内容摘要: {ai_content.get('summary', '')}"
        embedding = self.embedding_model.encode(text_to_embed).tolist()
        print(f"  -> 已生成Embedding向量")
        template_json = self._extract_structure_from_text(full_text)
        print(f"  -> 已提取 {len(template_json)} 个结构化字段")
        output_data = {"template_name": template_name, "description": ai_content.get('description', '生成失败'),
                       "summary": ai_content.get('summary', '生成失败'), "embedding": embedding,
                       "template_json": template_json}
        return output_data

    def process_folder(self, folder_path: str, output_file: str):
        with open(output_file, 'w', encoding='utf-8') as f:
            for root, _, files in os.walk(folder_path):
                for file in files:
                    if file.startswith('~') or not file.endswith(('.doc', '.docx')):
                        continue
                    full_path = os.path.join(root, file)
                    result = self.process_document(full_path)
                    if result:
                        f.write(json.dumps(result, ensure_ascii=False) + '\n')
        print(f"\n--- 所有文档处理完毕，结果已保存至: {output_file} ---")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='文档智能处理与结构化数据提取工具 (OpenRouter版)')
    parser.add_argument('--folder', required=True, type=str, help='需要处理的本地文件夹路径')
    parser.add_argument('--output', required=True, type=str, help='输出的JSON Lines (.jsonl) 文件路径')
    args = parser.parse_args()
    OPENROUTER_API_KEY = "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 "

    if os.path.isdir(args.folder):
        processor = DocumentProcessor(api_key=OPENROUTER_API_KEY)
        processor.process_folder(args.folder, args.output)
    else:
        print(f"错误: 文件夹 '{args.folder}' 不存在。")
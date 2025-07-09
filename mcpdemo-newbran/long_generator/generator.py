# 文件名: generator.py
# -*- coding: utf-8 -*-

"""
generator.py

包含项目的核心业务逻辑：状态管理和文档生成状态机。
"""

import json
import os
import time
import uuid
from typing import Dict, Any, Optional

import docx
import base64
from io import BytesIO
from docx.shared import Inches, Pt
from docx.oxml.ns import qn

# --- 从其他模块导入依赖 ---
from config import Config
# [已更新] 导入新的get_summary函数
from services import call_ai_model, search_vectordata, get_info, get_summary
from upload_cloud import upload_to_minio
from process_image import get_image_info
from converter import convert_md_to_docx_with_images


# TaskState 类的代码保持不变
class TaskState:
    """管理单个生成任务的状态，负责JSON文件的读写和更新。"""

    def __init__(self, task_id: str):
        self.task_id = task_id
        self.filepath = os.path.join(Config.TASKS_DIR, f"task_{self.task_id}.json")
        self.data: Dict[str, Any] = {}
        os.makedirs(Config.TASKS_DIR, exist_ok=True)

    def load(self) -> bool:
        if os.path.exists(self.filepath):
            with open(self.filepath, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
            return True
        return False

    def save(self):
        self.data['lastUpdatedTimestamp'] = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
        with open(self.filepath, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
        print(f"--- 状态已保存: {self.filepath} ---")

    def initialize(self, initial_request: Dict[str, str], report_type: str):
        # [变更] 增加 report_type 和 docxPublicUrl 字段
        self.data = {
            "taskId": self.task_id, "status": "pending", "progressPercentage": 0,
            "currentStatusMessage": "任务已创建，等待初始化...", "initialRequest": initial_request,
            "reportType": report_type,
            "creativeBrief": "", "projectName": "",
            "introduction": "", "conclusion": "", "outline": {}, "finalDocument": "",
            "markdownPublicUrl": "", "docxPublicUrl": "", "errorLog": []
        }
        self.save()

    def update_status(self, status: str, message: str, progress: int):
        self.data['status'] = status
        self.data['currentStatusMessage'] = message
        self.data['progressPercentage'] = progress
        self.save()
        print(f"--- 进度更新: {progress}% - {message} ---")

    def log_error(self, stage: str, error_message: str):
        self.data['errorLog'].append({
            "timestamp": time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
            "stage": stage, "message": error_message
        })
        self.update_status("failed", f"在 {stage} 阶段发生错误。", self.data.get('progressPercentage', 0))


class LongDocumentGenerator:
    """负责执行整个长文生成任务的业务流程。"""

    def __init__(self, task_id: Optional[str] = None):
        self.task_id = task_id or str(uuid.uuid4())
        self.state = TaskState(self.task_id)

    def start_new_job(self, chathistory: str, request: str, report_type: str = 'long') -> str:
        """
        [已更新] 启动一个新任务，可以指定报告类型。
        """
        print(f"启动新任务: {self.task_id} (类型: {report_type})")
        self.state.initialize(initial_request={"chathistory": chathistory, "request": request}, report_type=report_type)
        self.run()
        return self.task_id

    def run(self):
        """
        [已更新] 主运行函数，现在会根据报告类型选择不同的工作流。
        """
        try:
            if not self.state.load():
                print(f"错误：无法加载任务 {self.task_id}。")
                return

            report_type = self.state.data.get('reportType', 'long')

            if report_type == 'short':
                self._run_short_report_workflow()
            else:  # 默认为长报告流程
                self._run_long_report_workflow()

        except Exception as e:
            error_stage = self.state.data.get('status', 'unknown')
            print(f"!! 在 {error_stage} 阶段发生严重错误: {e}")
            self.state.log_error(error_stage, str(e))
            self.state.update_status("failed", "任务因意外错误而终止。", self.state.data.get('progressPercentage', 0))

    def _run_long_report_workflow(self):
        """执行完整的长篇报告生成工作流。"""
        while self.state.data['status'] not in ['completed', 'failed']:
            current_status = self.state.data['status']
            if current_status == 'pending':
                self._prepare_creative_brief()
            elif current_status == 'brief_prepared':
                self._generate_initial_outline()
            elif current_status == 'outline_generated':
                self._refine_outline_cycle()
            elif current_status == 'outline_finalized':
                self._generate_all_chapters()
            elif current_status == 'chapters_generated':
                self._assemble_final_document()
            else:
                break  # 避免在未知状态下无限循环

        if self.state.data['status'] == 'completed':
            print(f"\n长篇报告任务 {self.task_id} 已成功完成！")

    def _run_short_report_workflow(self):
        """[新增] 执行精简的短篇报告生成工作流。"""
        while self.state.data['status'] not in ['completed', 'failed']:
            current_status = self.state.data['status']
            if current_status == 'pending':
                self._prepare_creative_brief()
            elif current_status == 'brief_prepared':
                self._generate_short_report_content()
            elif current_status == 'short_report_generated':
                # 短报告直接进入最终文件生成环节
                self._assemble_final_document(is_short_report=True)
            else:
                break

        if self.state.data['status'] == 'completed':
            print(f"\n短篇报告任务 {self.task_id} 已成功完成！")

    def _generate_short_report_content(self):
        """[新增] 为短报告直接生成全文内容。"""
        self.state.update_status("short_report_generation", "正在生成短篇报告内容...", 20)

        project_name = self.state.data.get('projectName', '')
        creative_brief = self.state.data.get('creativeBrief', '')

        # 为短报告进行一次性的知识检索
        print("--> 为短报告进行知识检索...")
        knowledge_pieces = search_vectordata(query=project_name, top_k=Config.SEARCH_DEFAULT_TOP_K)
        knowledge_context = ""
        if knowledge_pieces:
            knowledge_str = "\n\n---\n\n".join(knowledge_pieces)
            knowledge_context = f"\n请参考以下背景资料进行撰写：\n{knowledge_str}\n"

        prompt = f"""你是一位专业的报告撰写人。请根据以下项目简介和背景资料，撰写一篇结构完整、内容流畅的通用短文或报告，总字数控制在2000字以内。
文章应有逻辑地分为几个部分，并使用Markdown的二级标题（##）来标记每个部分的标题。

【项目简介】
{creative_brief}

{knowledge_context}

请直接输出完整的Markdown格式报告全文。
"""
        response = call_ai_model(prompt)
        # 短报告的全文直接存入finalDocument
        self.state.data['finalDocument'] = response.get('text', '')
        self.state.data['status'] = 'short_report_generated'
        self.state.save()

    # ... _prepare_creative_brief, _generate_initial_outline, _refine_outline_cycle 等方法保持不变 ...
    def _prepare_creative_brief(self):
        """[已优化] 阶段1: 准备创作指令, 并提取核心项目主题"""
        self.state.update_status("brief_generation", "正在分析聊天记录和用户请求...", 5)
        chathistory = self.state.data['initialRequest']['chathistory']
        request = self.state.data['initialRequest']['request']

        # 注释：这里的Prompt也调整为文物评估的视角。
        prompt_brief = f"""你是一位资深的文物影响评估专家。请根据下面的对话记录和最终请求，为即将撰写的《文物影响评估报告》提炼一份核心的“创作指令”（Creative Brief）。
这份指令需要明确评估对象、项目性质和核心的评估要求。
【对话记录】
{chathistory}
【最终请求】
{request}
请以JSON格式返回你的分析结果，包含一个'creative_brief'字段。
重要提示：所有生成的文本内容都必须使用中文。
"""
        response_brief = call_ai_model(prompt_brief, expect_json=True)
        brief = response_brief.get("creative_brief")
        if not brief:
            raise ValueError("AI未能生成有效的创作指令（creative_brief）。")
        self.state.data['creativeBrief'] = brief

        self.state.update_status("brief_generation", "正在提炼项目主题以优化检索...", 7)
        prompt_project_name = f"""从以下创作指令中，提取一个简短的核心项目名称或主题（例如，“xx路社文体中心建设项目”或“医灵古庙修缮工程”），用于优化后续的知识库检索。
请以JSON格式返回，只包含一个 'project_name' 字段。
重要提示：项目名称必须使用中文。
创作指令：{brief}
"""
        response_name = call_ai_model(prompt_project_name, expect_json=True)
        project_name = response_name.get("project_name", "")
        self.state.data['projectName'] = project_name
        print(f"--- 提炼出项目主题: {project_name} ---")

        self.state.data['status'] = 'brief_prepared'
        self.state.save()

    def _generate_initial_outline(self):
        """[已更新] 阶段2: 生成初始大纲，注入专家角色"""
        self.state.update_status("outline_generation", "正在生成初始大纲...", 10)
        prompt = f"""你是一位经验丰富的文物影响评估专家。根据以下项目信息，请为一份《文物影响评估报告》生成一份专业的、结构化的JSON格式大纲。
大纲的章节标题应遵循行业标准，例如包含“项目概况”、“建设项目涉及文物情况”、“项目建设必要性”、“项目建设概况”和“支撑法律，法规及文件”,“项目对文物影响评估”,"项目检测方案","应急方案","结论及建议"部分。
JSON的根节点应该有一个名为 'chapters' 的列表。
列表中的每个对象都应包含以下三个字段：
1. 'chapterId' (字符串, 例如 "ch_01")
2. 'title' (字符串, 章节的标题)
3. 'key_points' (字符串列表, 这一章需要论述的关键评估点)
重要提示：所有生成的标题和文本内容都必须使用中文。md格式
项目信息：{self.state.data['creativeBrief']}
"""
        response = call_ai_model(prompt, expect_json=True)
        chapters = response.get('chapters')
        if chapters is None:
            raise ValueError("AI未能生成有效的大纲（缺少'chapters'字段）。")
        self.state.data['outline'] = {"metadata": {"refinementCycles": 0}, "chapters": chapters}
        self.state.data['status'] = 'outline_generated'
        self.state.save()

    def _refine_outline_cycle(self):
        """[已更新] 阶段3: 大纲评审与精炼循环，注入专家角色"""
        self.state.update_status("outline_refinement", "开始大纲评审与精炼...", 15)
        project_name = self.state.data.get('projectName', '')

        for i in range(Config.MAX_REFINEMENT_CYCLES):
            self.state.update_status("outline_refinement", f"第 {i + 1} 轮大纲精炼：AI自我评审...", 15 + i * 5)
            current_outline_str = json.dumps(self.state.data['outline']['chapters'], ensure_ascii=False)
            prompt_critique = f"""你是一位顶级的文物保护专家，负责审查下级单位提交的《文物影响评估报告》大纲。
请严格按照国家及行业规范，评审以下大纲。
请检查大纲是否全面覆盖了评估所需的所有必要环节，例如“评估依据”、“文物现状”、“各类影响预测（施工期、运营期）”、“减缓措施”和“结论与建议”等。
请以JSON格式返回你的分析。JSON的根节点应包含一个名为 'gaps_identified' 的列表。
列表中每个对象代表一个你认为需要补充或修正的章节，并包含以下字段：
1. 'chapterId'
2. 'title'
3. 'query_keywords' (用于检索法规或案例的推荐关键词)
如果大纲结构合理、内容全面，才返回一个空的 'gaps_identified' 列表。
重要提示：所有生成的文本内容都必须使用中文。md格式。
大纲：{current_outline_str}
"""
            critique_response = call_ai_model(prompt_critique, expect_json=True)
            gaps = critique_response.get('gaps_identified')
            if not gaps:
                print("评审完成，AI认为大纲已足够完善。")
                break

            self.state.update_status("outline_refinement", f"发现信息缺口: {gaps}，正在检索知识...", 16 + i * 5)
            all_knowledge = []
            all_gap_titles = []
            for gap_info in gaps:
                gap_title = gap_info.get('title', '')
                if gap_title:
                    all_gap_titles.append(gap_title)
                query_keywords = gap_info.get('query_keywords', [])
                for keyword in query_keywords:
                    scoped_query = f"{project_name} {keyword}".strip()
                    # [已修复] 使用正确的配置项名称
                    knowledge_pieces = search_vectordata(query=scoped_query, top_k=Config.SEARCH_DEFAULT_TOP_K)
                    all_knowledge.extend(knowledge_pieces)

            if not all_knowledge:
                print("未能从向量数据库检索到有效信息，跳过本轮增强。")
                continue

            knowledge_str = "\n\n---\n\n".join(all_knowledge)
            prompt_integrate = f"""请参考以下背景资料，扩充和完善这份《文物影响评估报告》大纲，特别是关于'{','.join(all_gap_titles)}'的这些章节。
请返回完整的、更新后的JSON格式大纲。
返回的JSON结构应与原大纲一致（一个包含 'chapters' 列表的根对象）。
重要提示：所有生成的文本内容都必须使用中文。md格式
背景资料：{knowledge_str}
原大纲：{current_outline_str}
"""
            updated_outline_response = call_ai_model(prompt_integrate, expect_json=True)
            self.state.data['outline']['chapters'] = updated_outline_response.get('chapters',
                                                                                  self.state.data['outline'][
                                                                                      'chapters'])
            self.state.data['outline']['metadata']['refinementCycles'] = i + 1
            self.state.save()

        self.state.data['status'] = 'outline_finalized'
        self.state.update_status("outline_finalized", "大纲已最终确定，准备生成正文。", 30)

    def _generate_all_chapters(self):
        """
        [已更新] 阶段4: 增加了为第一章注入核心摘要的逻辑。
        """
        chapters = self.state.data['outline']['chapters']
        project_name = self.state.data.get('projectName', '')
        total_chapters = len(chapters)
        if total_chapters == 0:
            print("!! 警告：大纲为空，无法生成任何章节内容。")
            self.state.data['status'] = 'chapters_generated'
            self.state.save()
            return

        for i, chapter in enumerate(chapters):
            progress = 30 + int((i / total_chapters) * 60)
            chapter_title = chapter.get('title', '')
            self.state.update_status("content_generation", f"正在生成第 {i + 1}/{total_chapters} 章: '{chapter_title}'...",
                                     progress)

            # --- [已更新] 逻辑分叉：判断是否为特殊章节 ---
            if chapter_title == "建设项目涉及文物情况":
                print(f"--> 检测到特殊章节 '{chapter_title}'，调用自定义get_info()函数获取原始数据。")
                raw_info = get_info()

                print(f"--> 正在调用AI，将原始数据润色为专业章节...")
                rewrite_prompt = f"""你是一位经验丰富的文物影响评估专家。
这里有一份关于“建设项目涉及文物情况”的原始资料。请你严格依据这些资料，并遵循所有专业报告的写作规范（客观语气、专业术语、标准格式等），将其改写成一段格式严谨、文笔流畅的正式评估报告章节。
【原始资料】
{raw_info}
请直接输出改写后的正文内容，不要添加任何额外的解释或标题。
"""
                response = call_ai_model(rewrite_prompt)
                chapter['content'] = response.get('text', '')

            else:
                # --- 对于所有其他章节，执行标准的生成流程 ---
                print(f"--> 为章节 '{chapter_title}' 检索文本知识...")
                scoped_query = f"{project_name} {chapter_title}".strip()
                knowledge_pieces = search_vectordata(query=scoped_query, top_k=Config.SEARCH_DEFAULT_TOP_K)

                clean_outline_for_context = [
                    {"title": ch.get("title"), "key_points": ch.get("key_points")}
                    for ch in chapters
                ]
                base_context = f"这是全文大纲的结构：{json.dumps(clean_outline_for_context, ensure_ascii=False)}\n"

                # [已更新] 为第一章和后续章节注入不同的上下文
                if i == 0:
                    print("--> 检测到为第一章，调用get_summary()获取开篇总结...")
                    initial_summary = get_summary()
                    if initial_summary:
                        base_context += f"\n请基于以下核心总结，为整个报告撰写一个强有力的开篇：\n“{initial_summary}”\n"
                else:  # 对于第二章及以后的章节
                    previous_summary = chapters[i - 1].get('summary', '')
                    if previous_summary:
                        base_context += f"\n请注意：上一章的核心内容总结为：“{previous_summary}”。请确保本章的开头能与此形成自然过渡。\n"
                    else:
                        base_context += f"前一章是关于 '{chapters[i - 1].get('title', '')}' 的。\n"

                if knowledge_pieces:
                    knowledge_str = "\n\n---\n\n".join(knowledge_pieces)
                    base_context += f"\n在撰写本章时，请重点参考以下背景资料以确保内容的准确性和深度：{knowledge_str}\n"

                prompt = f"""你是一位经验丰富的文物影响评估专家...（省略以保持简洁）...
请直接输出“{chapter_title}”这一章节的正文内容，不要在开头重复章节标题。
"""
                response = call_ai_model(prompt, context=base_context)
                chapter['content'] = response.get('text', '')

                # 为标准章节生成摘要，为下一章做准备
                print(f"--> 正在为章节 '{chapter_title}' 生成摘要...")
                summary_prompt = f"请将以下文本内容总结成一到两句精炼的核心观点，用于章节间的承上启下。\n\n文本：\n{chapter['content']}"
                summary_response = call_ai_model(summary_prompt)
                chapter['summary'] = summary_response.get('text', '')
            # --- 逻辑分叉结束 ---

            # --- 图片URL检索（对所有章节都执行） ---
            print(f"--> 为章节 '{chapter_title}' 检索图片链接...")
            image_query = f"{project_name} {chapter_title}".strip()
            image_urls = get_image_info(query=image_query)
            if image_urls:
                chapter['image_urls'] = image_urls
                print(f"--- 检索到 {len(image_urls)} 个图片链接 ---")
            else:
                print("!! [警告] 未能检索到相关图片链接。")

            self.state.save()

        self.state.data['status'] = 'chapters_generated'
        self.state.save()

    def _assemble_final_document(self, is_short_report: bool = False):
        """
        [已更新] 最终文件整合与生成，会根据报告类型进行适配。
        """
        if is_short_report:
            # 对于短报告，finalDocument已经由AI直接生成，无需再拼接
            self.state.update_status("assembling", "正在准备短报告文件...", 95)
        else:
            # 对于长报告，执行原有的拼接逻辑
            self.state.update_status("assembling", "所有章节已生成，正在整合文档...", 95)
            chapters = self.state.data['outline']['chapters']
            clean_outline_for_context = [
                {"title": ch.get("title"), "key_points": ch.get("key_points")}
                for ch in chapters
            ]
            final_context_str = json.dumps(clean_outline_for_context, ensure_ascii=False)

            if not chapters:
                print("!! 警告：大纲为空，将生成通用的引言和结论。")

            intro_prompt = """你是一位经验丰富的文物影响评估专家。你将根据以下完整的报告大纲，撰写“引言”部分。

请严格遵守以下生成规范：
1. 写作风格：使用客观、中立、专业的评估语气。引言应概述项目背景、评估目的、工作流程以及报告的主要结构。
2. 格式要求：如果引言内部分小节，请使用“一、二、三……”编号。
3. 术语与用词统一：使用“项目必要性分析”、“文物现状”等专业术语。
4. 引用规范：引用法律条文或标准时，必须使用标准书写方式。

请直接输出“引言”部分的正文内容，不要附带任何AI说明语或结构解释。
"""
            intro_response = call_ai_model(intro_prompt, context=final_context_str)
            introduction_text = intro_response.get('text', '')
            self.state.data['introduction'] = introduction_text

            conclusion_prompt = """你是一位经验丰富的文物影响评估专家。你将根据以下完整的报告大纲，撰写“结论与建议”部分。

请严格遵守以下生成规范：
1. 写作风格：使用客观、中立、专业的评估语气。
2. 格式要求：如果结论内部分小节，请使用“一、二、三……”编号。
3. 术语与用词统一：使用“可接受程度”、“减缓措施”、“应急预案”等专业术语。
4. 结论表达：结论必须明确陈述建设项目对文物的影响是否在“可接受程度”内，并清晰地总结需要采取的关键“减缓措施”和“应急预案”。

请直接输出“结论与建议”部分的正文内容，不要附带任何AI说明语或结构解释。
"""
            conclusion_response = call_ai_model(conclusion_prompt, context=final_context_str)
            conclusion_text = conclusion_response.get('text', '')
            self.state.data['conclusion'] = conclusion_text

            full_text_parts = [f"## 引言\n\n{introduction_text}"]
            for chapter in chapters:
                full_text_parts.append(f"\n\n## {chapter.get('title', '')}\n\n")
                full_text_parts.append(chapter.get('content', ''))
                image_urls = chapter.get('image_urls', [])
                for url in image_urls:
                    full_text_parts.append(f"\n\n![{chapter.get('title', '章节配图')}]({url})\n")
            full_text_parts.append(f"\n\n## 结论与建议\n\n")
            full_text_parts.append(conclusion_text)

            self.state.data['finalDocument'] = "".join(full_text_parts)

        try:
            self._create_and_upload_markdown()
        except Exception as e:
            print(f"!! [警告] 创建或上传 .md 文件时发生错误: {e}")
            self.state.log_error("markdown_handling", str(e))

        try:
            self._convert_and_upload_docx()
        except Exception as e:
            print(f"!! [警告] 将Markdown转换为Docx或上传时发生错误: {e}")
            self.state.log_error("docx_conversion", str(e))

        self.state.update_status("completed", "文档已成功生成！", 100)

    def _create_and_upload_markdown(self):
        """
        生成并上传Markdown文档。
        """
        print("--- 正在生成 .md 文档... ---")
        final_text = self.state.data.get('finalDocument', '')
        if not final_text:
            print("!! [警告] finalDocument 为空，无法生成 .md 文件。")
            return None

        markdown_filename = f"task_{self.state.task_id}.md"
        markdown_filepath = os.path.join(Config.TASKS_DIR, markdown_filename)

        try:
            with open(markdown_filepath, 'w', encoding='utf-8') as f:
                f.write(final_text)
            print(f"--- .md 文档已成功保存至本地: {markdown_filepath} ---")
        except Exception as e:
            print(f"!! [错误] 写入 .md 文件时发生错误: {e}")
            return None

        public_url = upload_to_minio(
            file_path=markdown_filepath,
            object_name=markdown_filename
        )
        if public_url:
            self.state.data['markdownPublicUrl'] = public_url
            self.state.save()

        return markdown_filepath

    def _convert_and_upload_docx(self):
        """
        [新增] 将已生成的Markdown文件转换为Docx并上传。
        """
        print("--- 开始执行 Markdown 到 Docx 的转换流程 ---")
        markdown_filename = f"task_{self.state.task_id}.md"
        markdown_filepath = os.path.join(Config.TASKS_DIR, markdown_filename)

        if not os.path.exists(markdown_filepath):
            print(f"!! [错误] 找不到Markdown源文件: {markdown_filepath}，跳过Docx转换。")
            return

        docx_filename = f"task_{self.state.task_id}.docx"
        docx_filepath = os.path.join(Config.TASKS_DIR, docx_filename)

        # 调用转换器
        result_path = convert_md_to_docx_with_images(
            md_filepath=markdown_filepath,
            output_docx_path=docx_filepath
        )

        # 如果转换成功，则上传
        if result_path:
            public_url = upload_to_minio(
                file_path=result_path,
                object_name=docx_filename
            )
            if public_url:
                self.state.data['docxPublicUrl'] = public_url
                self.state.save()

    def _create_and_upload_docx(self):
        """
        [已弃用] 此函数原用于生成 .docx 文件，现已被 _create_and_upload_markdown 替代。
        保留此函数结构仅为历史参考。
        """
        pass

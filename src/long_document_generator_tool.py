#!/usr/bin/env python3
"""
长文档生成工具 - 整合long_generator到ReactAgent系统
支持多阶段长文档生成：创作指令 → 大纲生成 → 大纲精炼 → 章节生成 → 文档整合

优化特性：
- 增强错误处理和重试机制
- 智能内容质量控制
- 动态配置管理
- 改进用户体验和进度反馈
- 性能优化和缓存机制
"""

import json
import os
import time
import uuid
import threading
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
import re

from .deepseek_client import DeepSeekClient


class LongDocumentTaskState:
    """管理长文档生成任务的状态"""
    
    def __init__(self, task_id: str, tasks_dir: str = "long_document_tasks"):
        self.task_id = task_id
        self.tasks_dir = tasks_dir
        self.filepath = os.path.join(self.tasks_dir, f"task_{self.task_id}.json")
        self.data: Dict[str, Any] = {}
        os.makedirs(self.tasks_dir, exist_ok=True)
    
    def load(self) -> bool:
        """加载任务状态"""
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, 'r', encoding='utf-8') as f:
                    self.data = json.load(f)
                return True
            except Exception as e:
                print(f"加载任务状态失败: {e}")
        return False
    
    def save(self):
        """保存任务状态"""
        self.data['lastUpdatedTimestamp'] = datetime.now().isoformat()
        try:
            with open(self.filepath, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存任务状态失败: {e}")
    
    def initialize(self, initial_request: Dict[str, str]):
        """初始化任务状态"""
        self.data = {
            "taskId": self.task_id,
            "status": "pending",
            "progressPercentage": 0,
            "currentStatusMessage": "任务已创建，等待初始化...",
            "initialRequest": initial_request,
            "creativeBrief": "",
            "outline": {},
            "finalDocument": "",
            "errorLog": [],
            "createdAt": datetime.now().isoformat()
        }
        self.save()
    
    def update_status(self, status: str, message: str, progress: int):
        """更新任务状态"""
        self.data['status'] = status
        self.data['currentStatusMessage'] = message
        self.data['progressPercentage'] = progress
        self.save()
    
    def log_error(self, stage: str, error_message: str):
        """记录错误日志"""
        self.data['errorLog'].append({
            "timestamp": datetime.now().isoformat(),
            "stage": stage,
            "message": error_message
        })
        self.update_status("failed", f"在 {stage} 阶段发生错误。", 
                          self.data.get('progressPercentage', 0))


class LongDocumentGeneratorTool:
    """长文档生成工具 - ReactAgent工具接口 (优化版)"""
    
    def __init__(self, deepseek_client: DeepSeekClient):
        self.name = "long_document_generator"
        self.description = """🔥 长文档生成工具 - 专业长篇文档智能生成器！

🎯 **必用场景 (超过500字的文档)：**
- 🏗️ 施工方案、施工组织设计、工程技术方案
- 📊 技术报告、可行性研究报告、项目评估报告  
- 📋 项目实施方案、项目计划书、工作方案
- 🔧 产品设计文档、系统设计方案、技术规范
- 📚 学术论文、研究报告、调研分析
- 📄 任何需要多章节、结构化的专业文档

⚡ **智能特性：**
- 🧠 AI创作指令分析 → 📋 大纲生成与精炼 → ✍️ 章节内容生成 → 🔧 文档整合
- 🎭 专业级文档结构和内容质量
- 🔄 支持同步等待模式（ReactAgent专用）
- 📈 自动进度跟踪和错误恢复

⚠️ **关键提醒：** 任何长篇文档生成请求都应该使用此工具，而不是直接编写！

🚀 **使用方法：** Action Input = "生成XXX文档的具体需求"  或 {"action": "generate", "request": "需求描述"}"""
        self.client = deepseek_client
        self.tasks_dir = "long_document_tasks"
        os.makedirs(self.tasks_dir, exist_ok=True)
        
        # 优化配置
        self.config = {
            "max_refinement_cycles": 3,
            "max_retry_attempts": 3,
            "chapter_min_words": 500,
            "chapter_max_words": 2000,
            "quality_check_enabled": True,
            "async_generation": True,
            "save_backup": True
        }
    
    def get_tool_info(self) -> Dict[str, Any]:
        """获取工具信息"""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "action": {
                    "type": "string",
                    "description": "操作类型",
                    "enum": ["generate", "status", "list_tasks", "get_document", "configure"]
                },
                "chat_history": {
                    "type": "string", 
                    "description": "对话历史，用于理解用户需求背景"
                },
                "request": {
                    "type": "string",
                    "description": "用户的具体文档生成请求"
                },
                "task_id": {
                    "type": "string",
                    "description": "任务ID，用于查询状态或获取文档"
                },
                "config": {
                    "type": "object",
                    "description": "生成配置参数，可选项包括: max_refinement_cycles, chapter_min_words, chapter_max_words等"
                }
            },
            "required": ["action"]
        }
    
    def execute(self, **kwargs) -> str:
        """执行工具操作 (优化版)"""
        action = kwargs.get("action", "").lower()
        
        try:
            if action == "generate":
                return self._generate_document(kwargs)
            elif action == "status":
                return self._get_task_status(kwargs)
            elif action == "list_tasks":
                return self._list_tasks()
            elif action == "get_document":
                return self._get_document(kwargs)
            elif action == "configure":
                return self._configure_tool(kwargs)
            else:
                return f"❌ 不支持的操作: {action}。支持的操作: generate, status, list_tasks, get_document, configure"
                
        except Exception as e:
            error_msg = f"❌ 长文档生成工具执行失败: {str(e)}"
            self._log_error("tool_execution", error_msg, kwargs)
            return error_msg
    
    def _configure_tool(self, params: Dict[str, Any]) -> str:
        """配置工具参数"""
        config = params.get("config", {})
        if not config:
            return f"""📋 **当前配置:**
```json
{json.dumps(self.config, ensure_ascii=False, indent=2)}
```

💡 **使用说明:** 
使用 `long_document_generator configure config:{{...}}` 来修改配置"""
        
        # 验证并更新配置
        valid_keys = set(self.config.keys())
        provided_keys = set(config.keys())
        invalid_keys = provided_keys - valid_keys
        
        if invalid_keys:
            return f"❌ 无效的配置项: {', '.join(invalid_keys)}\n有效配置项: {', '.join(valid_keys)}"
        
        # 更新配置
        for key, value in config.items():
            if key in self.config:
                self.config[key] = value
        
        return f"✅ 配置已更新:\n```json\n{json.dumps(config, ensure_ascii=False, indent=2)}\n```"
    
    def _log_error(self, stage: str, error_msg: str, context: Dict[str, Any]):
        """记录错误日志"""
        error_log = {
            "timestamp": datetime.now().isoformat(),
            "stage": stage,
            "error": error_msg,
            "context": context
        }
        
        # 可以扩展为写入日志文件
        print(f"[ERROR] {error_log}")
    
    def _save_generated_document(self, task_id: str, document_content: str, request: str):
        """保存生成的文档到generated_documents目录"""
        try:
            generated_docs_dir = "generated_documents"
            os.makedirs(generated_docs_dir, exist_ok=True)
            
            # 生成文件名
            timestamp = int(time.time())
            filename = f"generated_document_{task_id[:8]}_{timestamp}.json"
            filepath = os.path.join(generated_docs_dir, filename)
            
            # 构建文档数据
            doc_data = {
                "task_id": task_id,
                "timestamp": datetime.now().isoformat(),
                "request": request,
                "document_content": document_content,
                "word_count": len(document_content.split()) if document_content else 0,
                "generated_by": "long_document_generator"
            }
            
            # 保存文档
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(doc_data, f, ensure_ascii=False, indent=2)
            
            print(f"✅ 长文档已保存: {filepath}")
            
        except Exception as e:
            print(f"⚠️ 保存生成文档失败: {e}")
    
    def _generate_document(self, params: Dict[str, Any]) -> str:
        """生成长文档 (支持同步等待模式)"""
        chat_history = params.get("chat_history", "")
        
        # 智能提取请求内容，支持多种参数格式
        request = ""
        
        # 优先使用request字段
        if params.get("request"):
            request = params.get("request")
        # 如果没有request，尝试从其他字段构建请求
        elif any(key in params for key in ["document_type", "requirements", "content_requirements"]):
            request_parts = []
            
            # 文档类型
            if params.get("document_type"):
                request_parts.append(f"生成{params['document_type']}")
            
            # 需求描述
            if params.get("requirements"):
                if isinstance(params["requirements"], str):
                    request_parts.append(params["requirements"])
                elif isinstance(params["requirements"], dict):
                    req_text = json.dumps(params["requirements"], ensure_ascii=False, indent=2)
                    request_parts.append(f"具体要求：{req_text}")
            
            # 内容要求
            if params.get("content_requirements"):
                if isinstance(params["content_requirements"], str):
                    request_parts.append(params["content_requirements"])
                elif isinstance(params["content_requirements"], dict):
                    req_text = json.dumps(params["content_requirements"], ensure_ascii=False, indent=2)
                    request_parts.append(f"内容要求：{req_text}")
            
            # 文档标题
            if params.get("document_title"):
                request_parts.append(f"标题：{params['document_title']}")
            
            # 输出格式
            if params.get("output_format"):
                request_parts.append(f"输出格式：{params['output_format']}")
            
            request = "\n".join(request_parts)
        
        # 如果还是没有请求内容，返回错误
        if not request or not request.strip():
            return f"❌ 请提供文档生成请求内容。\n\n收到的参数：{json.dumps(params, ensure_ascii=False, indent=2)}"
        
        custom_config = params.get("config", {})
        
        # 🚀 检查是否为ReactAgent调用，如果是则默认使用同步模式
        wait_for_completion = params.get("wait_for_completion", True)  # 默认等待完成
        if "async_generation" not in custom_config and wait_for_completion:
            custom_config["async_generation"] = False  # ReactAgent模式下默认同步
        
        # 合并配置
        generation_config = self.config.copy()
        generation_config.update(custom_config)
        
        # 创建新任务
        task_id = str(uuid.uuid4())
        generator = LongDocumentGenerator(task_id, self.client, self.tasks_dir, generation_config)
        
        try:
            # 🎯 ReactAgent模式：同步等待生成完成
            if not generation_config.get("async_generation", True):
                print(f"🔄 ReactAgent模式：开始同步生成长文档...")
                print(f"📋 任务ID: {task_id}")
                print(f"⏰ 预估时间: 3-8分钟，请耐心等待...")
                
                # 同步生成，等待完成
                result = generator.start_new_job(chat_history, request)
                
                # 获取最终文档
                task_state = LongDocumentTaskState(task_id, self.tasks_dir)
                if task_state.load() and task_state.data.get('status') == 'completed':
                    final_document = task_state.data.get('finalDocument', '')
                    
                    # 同时保存到generated_documents目录
                    self._save_generated_document(task_id, final_document, request)
                    
                    return f"""🎉 **长文档生成完成！**

📋 **任务信息:**
- 任务ID: `{task_id}`
- 请求内容: {request[:100]}{'...' if len(request) > 100 else ''}
- 生成状态: ✅ 已完成

📄 **文档预览:**
{final_document[:500]}{'...' if len(final_document) > 500 else ''}

💡 **获取完整文档:** `long_document_generator get_document task_id:{task_id}`
📁 **文档已保存至:** generated_documents/generated_document_{task_id[:8]}_{int(time.time())}.json
"""
                else:
                    # 如果生成失败，返回错误信息
                    error_info = ""
                    if task_state.data.get('errorLog'):
                        latest_error = task_state.data['errorLog'][-1]
                        error_info = f"\n❌ 错误信息: {latest_error.get('message', 'N/A')}"
                    
                    return f"""❌ **长文档生成失败**

📋 **任务ID:** `{task_id}`
📊 **最终状态:** {task_state.data.get('status', 'unknown')}
📈 **完成进度:** {task_state.data.get('progressPercentage', 0)}%
{error_info}

💡 **查看详情:** `long_document_generator status task_id:{task_id}`
"""
            
            else:
                # 异步模式
                thread = threading.Thread(
                    target=generator.start_new_job,
                    args=(chat_history, request),
                    daemon=True
                )
                thread.start()
                
                return f"""✅ **长文档生成任务已启动 (异步模式)**

📋 **任务信息:**
- 任务ID: `{task_id}`
- 请求内容: {request[:100]}{'...' if len(request) > 100 else ''}
- 生成模式: 异步处理
- 配置参数: {len(custom_config)} 项自定义设置

🔄 **生成流程:**
1. ✅ 任务创建完成
2. 🔄 创作指令分析
3. ⏳ 大纲生成与精炼
4. ⏳ 章节内容生成
5. ⏳ 文档整合

💡 **查询进度:** `long_document_generator status task_id:{task_id}`
💡 **获取文档:** 完成后使用 `long_document_generator get_document task_id:{task_id}`

⚡ **预估时间:** 3-8分钟 (取决于文档复杂度)
"""
            
        except Exception as e:
            error_msg = f"启动长文档生成任务失败: {str(e)}"
            self._log_error("task_creation", error_msg, params)
            return f"❌ {error_msg}"
    
    def _get_task_status(self, params: Dict[str, Any]) -> str:
        """获取任务状态"""
        task_id = params.get("task_id", "")
        if not task_id:
            return "❌ 请提供任务ID"
        
        task_state = LongDocumentTaskState(task_id, self.tasks_dir)
        if not task_state.load():
            return f"❌ 未找到任务 {task_id}"
        
        data = task_state.data
        status_emoji = {
            "pending": "⏳",
            "brief_generation": "📝",
            "brief_prepared": "✅",
            "outline_generation": "📋",
            "outline_generated": "✅", 
            "outline_refinement": "🔄",
            "outline_finalized": "✅",
            "content_generation": "✍️",
            "chapters_generated": "✅",
            "assembling": "🔧",
            "completed": "🎉",
            "failed": "❌"
        }.get(data.get('status', ''), "❓")
        
        result = f"""📊 **任务状态报告**

🆔 **任务ID:** {task_id}
{status_emoji} **当前状态:** {data.get('status', 'unknown')}
📈 **完成进度:** {data.get('progressPercentage', 0)}%
💬 **状态信息:** {data.get('currentStatusMessage', 'N/A')}
🕒 **最后更新:** {data.get('lastUpdatedTimestamp', 'N/A')}
"""
        
        # 如果有错误日志，显示最近的错误
        if data.get('errorLog'):
            latest_error = data['errorLog'][-1]
            result += f"\n⚠️ **最近错误:** {latest_error.get('message', 'N/A')}"
        
        # 如果任务完成，提供获取文档的提示
        if data.get('status') == 'completed':
            result += f"\n\n🎉 **任务已完成！** 使用以下命令获取文档:\n`long_document_generator get_document task_id:{task_id}`"
        
        return result
    
    def _list_tasks(self) -> str:
        """列出所有任务"""
        if not os.path.exists(self.tasks_dir):
            return "📂 暂无长文档生成任务"
        
        task_files = [f for f in os.listdir(self.tasks_dir) if f.startswith("task_") and f.endswith(".json")]
        
        if not task_files:
            return "📂 暂无长文档生成任务"
        
        tasks_info = []
        for task_file in task_files[-10:]:  # 显示最近10个任务
            task_id = task_file.replace("task_", "").replace(".json", "")
            task_state = LongDocumentTaskState(task_id, self.tasks_dir)
            
            if task_state.load():
                data = task_state.data
                status_emoji = {
                    "completed": "✅", "failed": "❌", "pending": "⏳"
                }.get(data.get('status', ''), "🔄")
                
                request_preview = data.get('initialRequest', {}).get('request', 'N/A')[:50]
                if len(request_preview) == 50:
                    request_preview += "..."
                
                tasks_info.append(
                    f"{status_emoji} {task_id[:8]}... | {data.get('progressPercentage', 0)}% | {request_preview}"
                )
        
        return f"""📋 **长文档生成任务列表** (最近10个)

{'='*50}
{'状态 任务ID      | 进度  | 请求内容'}
{'='*50}
{chr(10).join(tasks_info)}
{'='*50}

💡 **使用提示:**
- 查看详细状态: `long_document_generator status task_id:任务ID`
- 获取完成文档: `long_document_generator get_document task_id:任务ID`
"""
    
    def _get_document(self, params: Dict[str, Any]) -> str:
        """获取生成的文档"""
        task_id = params.get("task_id", "")
        if not task_id:
            return "❌ 请提供任务ID"
        
        task_state = LongDocumentTaskState(task_id, self.tasks_dir)
        if not task_state.load():
            return f"❌ 未找到任务 {task_id}"
        
        data = task_state.data
        if data.get('status') != 'completed':
            return f"❌ 任务尚未完成，当前状态: {data.get('status', 'unknown')}"
        
        final_document = data.get('finalDocument', '')
        if not final_document:
            return "❌ 文档内容为空"
        
        # 保存文档到文件
        doc_filename = f"long_document_{task_id[:8]}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        doc_path = os.path.join("generated_documents", doc_filename)
        
        os.makedirs("generated_documents", exist_ok=True)
        
        try:
            with open(doc_path, 'w', encoding='utf-8') as f:
                f.write(final_document)
            
            # 统计文档信息
            word_count = len(final_document)
            line_count = final_document.count('\n') + 1
            
            return f"""📄 **长文档生成完成**

🆔 **任务ID:** {task_id}
📁 **文档路径:** {doc_path}
📊 **文档统计:**
- 字符数: {word_count:,}
- 行数: {line_count:,}

📋 **文档大纲:**
{self._extract_outline_summary(data.get('outline', {}))}

✅ **文档已保存到:** `{doc_path}`

---

📖 **文档预览 (前500字符):**
{final_document[:500]}{'...' if len(final_document) > 500 else ''}
"""
            
        except Exception as e:
            return f"❌ 保存文档失败: {str(e)}\n\n📖 **文档内容:**\n{final_document}"
    
    def _extract_outline_summary(self, outline: Dict[str, Any]) -> str:
        """提取大纲摘要"""
        chapters = outline.get('chapters', [])
        if not chapters:
            return "无大纲信息"
        
        summary_lines = []
        for i, chapter in enumerate(chapters, 1):
            title = chapter.get('title', f'第{i}章')
            key_points = chapter.get('key_points', [])
            points_preview = ', '.join(key_points[:2])  # 显示前2个要点
            if len(key_points) > 2:
                points_preview += f" (共{len(key_points)}个要点)"
            
            summary_lines.append(f"{i}. {title} - {points_preview}")
        
        return '\n'.join(summary_lines)


class LongDocumentGenerator:
    """长文档生成器核心逻辑 (优化版)"""
    
    def __init__(self, task_id: str, client: DeepSeekClient, tasks_dir: str, config: Dict[str, Any]):
        self.task_id = task_id
        self.client = client
        self.state = LongDocumentTaskState(task_id, tasks_dir)
        self.config = config
        self.max_refinement_cycles = config.get("max_refinement_cycles", 3)
        self.max_retry_attempts = config.get("max_retry_attempts", 3)
        self.quality_check_enabled = config.get("quality_check_enabled", True)
    
    def _retry_with_backoff(self, func, *args, **kwargs) -> Tuple[Any, bool]:
        """带退避策略的重试机制"""
        for attempt in range(self.max_retry_attempts):
            try:
                result = func(*args, **kwargs)
                return result, True
            except Exception as e:
                if attempt == self.max_retry_attempts - 1:
                    print(f"重试失败，已达到最大尝试次数: {e}")
                    return None, False
                
                wait_time = (2 ** attempt) + 1  # 指数退避
                print(f"第{attempt + 1}次尝试失败，{wait_time}秒后重试: {e}")
                time.sleep(wait_time)
        
        return None, False
    
    def _validate_json_response(self, response: str, required_keys: List[str]) -> Tuple[Dict[str, Any], bool]:
        """验证和修复JSON响应"""
        try:
            data = json.loads(response)
            
            # 检查必需的键
            missing_keys = [key for key in required_keys if key not in data]
            if missing_keys:
                print(f"JSON响应缺少必需键: {missing_keys}")
                return {}, False
            
            return data, True
            
        except json.JSONDecodeError as e:
            print(f"JSON解析失败: {e}")
            
            # 尝试修复JSON
            fixed_response = self._fix_json_response(response)
            if fixed_response:
                try:
                    data = json.loads(fixed_response)
                    return data, True
                except:
                    pass
            
            return {}, False
    
    def _fix_json_response(self, response: str) -> Optional[str]:
        """尝试修复损坏的JSON响应"""
        # 移除markdown代码块
        response = re.sub(r'```json\s*|\s*```', '', response.strip())
        
        # 尝试找到JSON对象
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            return json_match.group(0)
        
        return None
    
    def _check_content_quality(self, content: str, content_type: str = "chapter") -> Tuple[bool, List[str]]:
        """检查内容质量"""
        if not self.quality_check_enabled:
            return True, []
        
        issues = []
        
        # 基本长度检查
        word_count = len(content.split())
        if content_type == "chapter":
            min_words = self.config.get("chapter_min_words", 500)
            max_words = self.config.get("chapter_max_words", 2000)
            
            if word_count < min_words:
                issues.append(f"内容过短，仅{word_count}字，建议至少{min_words}字")
            elif word_count > max_words:
                issues.append(f"内容过长，{word_count}字，建议不超过{max_words}字")
        
        # 内容结构检查
        if content_type == "chapter":
            # 检查是否有段落结构
            paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
            if len(paragraphs) < 2:
                issues.append("内容缺少段落结构，建议分成多个段落")
            
            # 检查是否过于重复
            sentences = content.split('。')
            if len(set(sentences)) / len(sentences) < 0.8:
                issues.append("内容重复度较高，建议增加多样性")
        
        return len(issues) == 0, issues
    
    def start_new_job(self, chat_history: str, request: str) -> str:
        """启动新的生成任务"""
        # 先初始化任务状态
        self.state.initialize({
            "chathistory": chat_history,
            "request": request
        })
        
        # 然后启动生成流程
        self.run()
        return self.task_id
    
    def run(self):
        """执行任务主循环"""
        try:
            if not self.state.load():
                raise Exception(f"无法加载任务 {self.task_id}")
            
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
                    raise Exception(f"未知任务状态: {current_status}")
                    
        except Exception as e:
            error_stage = self.state.data.get('status', 'unknown')
            self.state.log_error(error_stage, str(e))
    
    def _prepare_creative_brief(self):
        """阶段1: 准备创作指令 (优化版)"""
        self.state.update_status("brief_generation", "正在分析用户请求...", 5)
        
        chat_history = self.state.data['initialRequest']['chathistory']
        request = self.state.data['initialRequest']['request']
        
        prompt = f"""你是一个专业的文档策划助理。请根据用户的对话历史和最终请求，生成一份详细的创作指令。

【对话历史】
{chat_history}

【用户请求】
{request}

请分析用户的真实需求，生成一份结构化的创作指令，包括：
1. 文档类型和目标
2. 主要内容方向  
3. 预期读者群体
4. 写作风格要求
5. 重点关注领域
6. 预期文档长度和结构

请以JSON格式返回，包含 'creative_brief' 字段。
例如：{{"creative_brief": "根据用户要求，撰写一份关于...的技术文档，面向...读者群体，重点关注...方面"}}

请确保返回有效的JSON格式。"""

        def generate_brief():
            response, _ = self.client.chat_completion([
                {"role": "user", "content": prompt}
            ])
            return response
        
        # 使用重试机制生成创作指令
        response, success = self._retry_with_backoff(generate_brief)
        
        if not success:
            self.state.log_error("brief_generation", "多次尝试后仍无法生成创作指令")
            return
        
        # 验证JSON响应
        response_data, is_valid = self._validate_json_response(response, ["creative_brief"])
        
        if is_valid:
            brief = response_data.get("creative_brief")
            # 确保brief是字符串类型并进行质量检查
            if brief and isinstance(brief, str) and len(brief.strip()) > 20:
                self.state.data['creativeBrief'] = brief
                self.state.data['status'] = 'brief_prepared'
                self.state.update_status("brief_prepared", "创作指令准备完成", 10)
                self.state.save()
                return
            elif brief and not isinstance(brief, str):
                # 如果brief不是字符串，尝试转换
                brief_str = str(brief)
                if len(brief_str.strip()) > 20:
                    self.state.data['creativeBrief'] = brief_str
                    self.state.data['status'] = 'brief_prepared'
                    self.state.update_status("brief_prepared", "创作指令准备完成 (转换模式)", 10)
                    self.state.save()
                    return
        
        # 如果JSON解析失败，尝试提取文本内容
        if response and len(response.strip()) > 50:
            # 尝试从响应中提取有用内容
            cleaned_response = re.sub(r'[{}"\'`]', '', response).strip()
            if len(cleaned_response) > 50:
                self.state.data['creativeBrief'] = cleaned_response
                self.state.data['status'] = 'brief_prepared'
                self.state.update_status("brief_prepared", "创作指令准备完成 (文本模式)", 10)
                self.state.save()
                return
        
        # 最后的备用方案
        default_brief = f"""基于用户请求: {request[:200]}{'...' if len(request) > 200 else ''}
        
生成一份专业文档，包含：
- 详细的背景介绍和目标说明
- 全面的内容分析和解决方案
- 清晰的结构层次和逻辑关系
- 实用的结论和建议"""
        
        self.state.data['creativeBrief'] = default_brief
        self.state.data['status'] = 'brief_prepared'
        self.state.update_status("brief_prepared", "创作指令准备完成 (默认模式)", 10)
        self.state.save()
    
    def _generate_initial_outline(self):
        """阶段2: 生成初始大纲"""
        self.state.update_status("outline_generation", "正在生成文档大纲...", 15)
        
        prompt = f"""根据以下创作指令，生成一份详细的文档大纲。

创作指令：{self.state.data['creativeBrief']}

请生成JSON格式的大纲，包含以下结构：
{{
  "chapters": [
    {{
      "chapterId": "ch_01",
      "title": "章节标题",
      "key_points": ["要点1", "要点2", "要点3"]
    }}
  ]
}}

要求：
1. 章节数量控制在5-10个
2. 每个章节包含3-5个关键要点
3. 逻辑结构清晰，层次分明
4. 内容覆盖全面，重点突出

请严格按照上述JSON格式返回，确保可以被正确解析。"""

        response, _ = self.client.chat_completion([
            {"role": "user", "content": prompt}
        ])
        
        try:
            response_data = json.loads(response)
            chapters = response_data.get('chapters')
            if not chapters:
                raise ValueError("AI未能生成有效的大纲")
            
            self.state.data['outline'] = {
                "metadata": {"refinementCycles": 0},
                "chapters": chapters
            }
            self.state.data['status'] = 'outline_generated'
            self.state.save()
            
        except json.JSONDecodeError:
            # 如果JSON解析失败，创建一个默认大纲
            default_chapters = [
                {
                    "chapterId": "ch_01",
                    "title": "概述",
                    "key_points": ["背景介绍", "目标定义", "整体框架"]
                },
                {
                    "chapterId": "ch_02", 
                    "title": "主要内容",
                    "key_points": ["核心要点", "详细分析", "实施方案"]
                },
                {
                    "chapterId": "ch_03",
                    "title": "总结与展望",
                    "key_points": ["主要结论", "价值意义", "未来发展"]
                }
            ]
            
            self.state.data['outline'] = {
                "metadata": {"refinementCycles": 0},
                "chapters": default_chapters
            }
            self.state.data['status'] = 'outline_generated'
            self.state.save()
    
    def _refine_outline_cycle(self):
        """阶段3: 大纲精炼循环"""
        self.state.update_status("outline_refinement", "开始大纲精炼...", 25)
        
        for i in range(self.max_refinement_cycles):
            progress = 25 + i * 5
            self.state.update_status("outline_refinement", 
                                   f"第 {i+1} 轮大纲精炼...", progress)
            
            current_outline = json.dumps(self.state.data['outline']['chapters'], 
                                       ensure_ascii=False, indent=2)
            
            # 评审大纲
            critique_prompt = f"""请作为资深编辑评审以下大纲，识别需要补充或改进的地方。

当前大纲：
{current_outline}

请以JSON格式返回评审结果：
{{
  "gaps_identified": [
    {{
      "chapterId": "ch_01",
      "title": "章节标题", 
      "issues": ["问题1", "问题2"],
      "suggestions": ["建议1", "建议2"]
    }}
  ]
}}

如果大纲已经完善，返回空的 gaps_identified 列表：{{"gaps_identified": []}}
请严格按照JSON格式返回。"""

            critique_response, _ = self.client.chat_completion([
                {"role": "user", "content": critique_prompt}
            ])
            
            try:
                critique_data = json.loads(critique_response)
                gaps = critique_data.get('gaps_identified', [])
                
                if not gaps:
                    break
                
                # 根据评审结果改进大纲
                improve_prompt = f"""请根据以下评审意见改进大纲：

评审意见：
{json.dumps(gaps, ensure_ascii=False, indent=2)}

当前大纲：
{current_outline}

请返回改进后的完整大纲，保持JSON格式：
{{
  "chapters": [
    {{
      "chapterId": "ch_01",
      "title": "改进后的标题",
      "key_points": ["改进后的要点1", "改进后的要点2"]
    }}
  ]
}}

请严格按照JSON格式返回。"""

                improve_response, _ = self.client.chat_completion([
                    {"role": "user", "content": improve_prompt}
                ])
                
                improve_data = json.loads(improve_response)
                updated_chapters = improve_data.get('chapters')
                
                if updated_chapters:
                    self.state.data['outline']['chapters'] = updated_chapters
                    self.state.data['outline']['metadata']['refinementCycles'] = i + 1
                    self.state.save()
                
            except json.JSONDecodeError:
                continue  # 跳过这轮精炼
        
        self.state.data['status'] = 'outline_finalized'
        self.state.update_status("outline_finalized", "大纲已确定，开始生成内容...", 40)
    
    def _generate_all_chapters(self):
        """阶段4: 生成所有章节内容 (优化版)"""
        chapters = self.state.data['outline']['chapters']
        total_chapters = len(chapters)
        
        if total_chapters == 0:
            self.state.data['status'] = 'chapters_generated'
            self.state.save()
            return
        
        generated_count = 0
        quality_issues_count = 0
        
        for i, chapter in enumerate(chapters):
            progress = 40 + int((i / total_chapters) * 45)
            chapter_title = chapter.get('title', f'第{i+1}章')
            
            self.state.update_status("content_generation", 
                                   f"正在生成 {i+1}/{total_chapters}: {chapter_title}", 
                                   progress)
            
            # 准备上下文
            context_parts = [
                f"这是完整大纲：{json.dumps(self.state.data['outline']['chapters'], ensure_ascii=False)}",
                f"创作指令：{self.state.data['creativeBrief']}"
            ]
            
            if i > 0:
                prev_title = chapters[i-1].get('title', '')
                prev_content_preview = chapters[i-1].get('content', '')[:200]
                context_parts.append(f"前一章标题：{prev_title}")
                context_parts.append(f"前一章内容预览：{prev_content_preview}...")
            
            context = "\n\n".join(context_parts)
            
            # 生成章节内容
            min_words = self.config.get("chapter_min_words", 500)
            max_words = self.config.get("chapter_max_words", 2000)
            
            chapter_prompt = f"""请撰写章节《{chapter_title}》的详细内容。

要求：
1. 围绕以下关键要点展开：{', '.join(chapter.get('key_points', []))}
2. 内容详实，逻辑清晰，层次分明
3. 字数控制在{min_words}-{max_words}字之间
4. 保持专业性和可读性
5. 与整体大纲保持一致
6. 使用适当的段落结构，避免大段文字
7. 包含具体例子或数据支撑观点

请直接返回章节正文内容，无需JSON格式。"""

            def generate_chapter():
                response, _ = self.client.chat_completion([
                    {"role": "system", "content": context},
                    {"role": "user", "content": chapter_prompt}
                ])
                return response
            
            # 使用重试机制生成章节
            content, success = self._retry_with_backoff(generate_chapter)
            
            if not success:
                self.state.log_error("chapter_generation", f"无法生成章节: {chapter_title}")
                # 生成备用内容
                content = f"""# {chapter_title}

本章节围绕以下要点展开：

{chr(10).join(f"- {point}" for point in chapter.get('key_points', []))}

[注：由于生成过程中遇到技术问题，此章节内容需要进一步完善]
"""
            
            # 质量检查
            if self.quality_check_enabled:
                is_quality_ok, quality_issues = self._check_content_quality(content, "chapter")
                
                if not is_quality_ok:
                    quality_issues_count += 1
                    print(f"章节 {chapter_title} 质量问题: {', '.join(quality_issues)}")
                    
                    # 尝试改进内容（仅一次）
                    if len(quality_issues) <= 2:  # 问题不太严重
                        improve_prompt = f"""请改进以下章节内容，解决这些问题：
{', '.join(quality_issues)}

原内容：
{content}

请返回改进后的内容，保持原有结构和主题。"""
                        
                        improved_content, improve_success = self._retry_with_backoff(
                            lambda: self.client.chat_completion([
                                {"role": "user", "content": improve_prompt}
                            ])[0]
                        )
                        
                        if improve_success:
                            # 再次质量检查
                            is_improved, _ = self._check_content_quality(improved_content, "chapter")
                            if is_improved:
                                content = improved_content
                                quality_issues_count -= 1  # 问题已解决
            
            chapter['content'] = content
            generated_count += 1
            
            # 保存进度（每生成一章就保存）
            if self.config.get("save_backup", True):
                self.state.save()
        
        # 更新最终状态
        status_message = f"章节生成完成 ({generated_count}/{total_chapters})"
        if quality_issues_count > 0:
            status_message += f"，{quality_issues_count}个章节存在质量问题"
        
        self.state.data['status'] = 'chapters_generated'
        self.state.update_status("chapters_generated", status_message, 85)
        self.state.save()
    
    def _assemble_final_document(self):
        """阶段5: 组装最终文档"""
        self.state.update_status("assembling", "正在组装最终文档...", 90)
        
        chapters = self.state.data['outline']['chapters']
        
        # 生成引言
        intro_prompt = f"""根据以下大纲和创作指令，为文档撰写一段精彩的引言。

创作指令：{self.state.data['creativeBrief']}
文档大纲：{json.dumps(chapters, ensure_ascii=False)}

要求：
1. 简明扼要地介绍文档主题
2. 概述文档结构和主要内容
3. 吸引读者继续阅读
4. 字数控制在200-400字"""

        intro_response, _ = self.client.chat_completion([
            {"role": "user", "content": intro_prompt}
        ])
        
        # 生成结论
        conclusion_prompt = f"""根据所有章节内容，为文档撰写总结性结论。

要求：
1. 总结主要观点和发现
2. 强调文档的价值和意义
3. 提出未来展望或建议
4. 字数控制在300-500字"""

        conclusion_response, _ = self.client.chat_completion([
            {"role": "user", "content": conclusion_prompt}
        ])
        
        # 组装完整文档
        doc_parts = [
            "# 引言\n\n" + intro_response,
            ""  # 空行分隔
        ]
        
        for chapter in chapters:
            doc_parts.extend([
                f"# {chapter.get('title', '')}",
                "",
                chapter.get('content', ''),
                ""
            ])
        
        doc_parts.extend([
            "# 结论\n\n" + conclusion_response
        ])
        
        self.state.data['finalDocument'] = "\n".join(doc_parts)
        self.state.update_status("completed", "文档生成完成！", 100) 
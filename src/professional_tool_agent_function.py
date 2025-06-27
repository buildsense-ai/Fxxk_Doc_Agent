#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
专业工具代理（Function Call版本）：高级文档生成协调器
结合RAG检索和AI智能合并，提供专业的文档生成服务
改造为纯function call形式，供主协调代理调用
"""

import os
import json
import logging
import traceback
import requests
import tempfile
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path

# 导入新的模板插入功能模块
from .insert_template_function import (
    merge_template_with_context,
    template_insertion_with_context,  # Add the proper template insertion function
    extract_content_from_file,
    get_api_key as get_openrouter_api_key
)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

# 加载环境变量
try:
    from dotenv import load_dotenv
    load_dotenv()
    logger.info("✅ 已加载.env环境变量文件")
except ImportError:
    logger.warning("⚠️ python-dotenv未安装，将直接从系统环境变量读取配置")

class RAGService:
    """RAG服务接口 - 连接到向量化数据库"""
    
    def __init__(self):
        # 从环境变量获取RAG服务配置
        self.base_url = os.environ.get("RAG_SERVICE_URL", "http://43.139.19.144:3000")
        self.timeout = int(os.environ.get("RAG_TIMEOUT", "30"))  # 30秒超时
        
        # 支持认证（如果需要）
        self.api_key = os.environ.get("RAG_API_KEY")
        
        logger.info(f"🔍 RAG服务初始化完成，连接到: {self.base_url}")
        if self.api_key:
            logger.info("🔑 RAG服务已启用API密钥认证")
    
    def search_documents(self, query: str, template_id: str, top_k: int = 5, 
                        project_name: Optional[str] = None, 
                        drawing_type: Optional[str] = None) -> Dict[str, Any]:
        """
        搜索相关文档 - 使用 GET /search-drawings API
        
        Args:
            query: 搜索查询
            template_id: 模板ID
            top_k: 返回结果数量（默认5）
            project_name: 项目名称（可选）
            drawing_type: 图纸类型（可选）
        """
        logger.info(f"🔍 RAG搜索: {query[:100]}...")
        
        try:
            # 使用正确的API端点 /search-drawings
            search_url = f"{self.base_url}/search-drawings"
            
            # 构建符合API规范的参数
            params = {
                "query": query,
                "top_k": top_k
            }
            
            # 添加可选参数
            if project_name:
                params["project_name"] = project_name
            if drawing_type:
                params["drawing_type"] = drawing_type
            elif template_id and template_id != "general":
                # 从模板ID推断图纸类型
                if "construction" in template_id.lower():
                    params["drawing_type"] = "construction"
                elif "design" in template_id.lower():
                    params["drawing_type"] = "design"
                elif "plan" in template_id.lower():
                    params["drawing_type"] = "plan"
                elif "施工" in template_id:
                    params["drawing_type"] = "construction"
                elif "设计" in template_id:
                    params["drawing_type"] = "design"
            
            # 设置请求头
            headers = {"Content-Type": "application/json"}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            
            logger.info(f"🔍 调用RAG API: {search_url}")
            logger.info(f"📋 搜索参数: {params}")
            
            # 强制不使用代理，避免代理服务器干扰
            proxies = {'http': '', 'https': ''}
            
            response = requests.get(
                search_url,
                params=params,
                headers=headers,
                timeout=self.timeout,
                proxies=proxies
            )
            
            if response.status_code != 200:
                logger.warning(f"⚠️ RAG API响应异常: {response.status_code}")
                logger.warning(f"响应内容: {response.text}")
                return self._get_fallback_results(query, template_id)
            
            # 处理API响应
            try:
                # 处理响应数据
                if response.headers.get('content-type', '').startswith('application/json'):
                    api_results = response.json()
                    logger.info(f"📋 RAG API返回JSON格式数据")
                else:
                    api_results = response.text
                    logger.info(f"📋 RAG API返回文本格式数据")
                
                # 转换API响应格式为内部格式
                formatted_results = {
                    "query": query,
                    "template_id": template_id,
                    "results": [],
                    "total_results": 0,
                    "search_params": params
                }
                
                if isinstance(api_results, dict):
                    # JSON格式响应处理
                    formatted_results["total_results"] = api_results.get("total", len(api_results.get("documents", [])))
                    
                    # 格式化搜索结果
                    documents = api_results.get("documents", api_results.get("results", []))
                    for item in documents:
                        formatted_results["results"].append({
                            "content": item.get("content", str(item)),
                            "source": item.get("source", "RAG向量数据库"),
                            "relevance_score": item.get("score", item.get("similarity", 0.9)),
                            "metadata": {
                                "document_type": item.get("doc_type", item.get("type", "drawing")),
                                "date": item.get("created_date", item.get("date", "")),
                                "project_id": item.get("project_id", ""),
                                "drawing_id": item.get("drawing_id", item.get("id", "")),
                                "file_path": item.get("file_path", ""),
                                "chunk_id": item.get("chunk_id", "")
                            }
                        })
                        
                elif isinstance(api_results, str) and api_results.strip():
                    # 纯文本响应处理
                    formatted_results["total_results"] = 1
                    formatted_results["results"].append({
                        "content": api_results,
                        "source": "RAG向量数据库",
                        "relevance_score": 0.9,
                        "metadata": {
                            "document_type": "text_search_result",
                            "date": datetime.now().strftime("%Y-%m-%d"),
                            "project_id": "",
                            "drawing_id": ""
                        }
                    })
                else:
                    # 无效响应，使用备用结果
                    logger.warning(f"⚠️ RAG API返回无效数据格式")
                    return self._get_fallback_results(query, template_id)
                
                logger.info(f"✅ RAG搜索完成，找到 {len(formatted_results['results'])} 个相关结果")
                
                # 输出搜索结果摘要
                for i, result in enumerate(formatted_results["results"], 1):
                    content_preview = result["content"][:100] + "..." if len(result["content"]) > 100 else result["content"]
                    logger.info(f"   📄 结果{i}: {content_preview} (相关度: {result['relevance_score']:.2f})")
                
                return formatted_results
                
            except Exception as e:
                logger.error(f"❌ 处理RAG API响应时出错: {e}")
                return self._get_fallback_results(query, template_id)
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ RAG服务连接失败: {e}")
            logger.warning("🔄 使用备用模拟结果")
            return self._get_fallback_results(query, template_id)
        except Exception as e:
            logger.error(f"❌ RAG搜索过程中出现错误: {e}")
            return self._get_fallback_results(query, template_id)
    
    def search_specific_info(self, missing_info: List[str], template_id: str) -> Dict[str, Any]:
        """针对特定缺失信息进行搜索（保持原有功能）"""
        logger.info(f"🎯 针对性RAG搜索，缺失信息: {missing_info}")
        
        try:
            search_url = f"{self.base_url}/search-drawings"
            targeted_results = {
                "missing_info": missing_info,
                "template_id": template_id,
                "targeted_results": {}
            }
            
            # 对每个缺失信息进行专门搜索
            for info in missing_info:
                params = {
                    "query": f"{info} {template_id}",
                    "top_k": 3
                }
                
                try:
                    # 强制不使用代理
                    proxies = {'http': '', 'https': ''}
                    response = requests.get(search_url, params=params, timeout=15, proxies=proxies)
                    if response.status_code == 200:
                        api_results = response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
                        targeted_results["targeted_results"][info] = api_results
                    else:
                        targeted_results["targeted_results"][info] = f"搜索失败: {response.status_code}"
                except Exception as e:
                    logger.warning(f"⚠️ 针对性搜索失败 ({info}): {e}")
                    targeted_results["targeted_results"][info] = f"搜索异常: {str(e)}"
            
            logger.info(f"✅ 针对性RAG搜索完成，处理了 {len(missing_info)} 个缺失项")
            return targeted_results
            
        except Exception as e:
            logger.error(f"❌ 针对性RAG搜索失败: {e}")
            return {
                "missing_info": missing_info,
                "template_id": template_id,
                "targeted_results": {},
                "error": str(e)
            }
    
    def _get_fallback_results(self, query: str, template_id: str) -> Dict[str, Any]:
        """获取备用搜索结果（用于RAG服务不可用时）（保持原有功能）"""
        logger.info("🔄 生成备用RAG结果")
        
        fallback_content = f"""
基于查询 "{query}" 和模板 "{template_id}" 的备用结果：

这是一个模拟的RAG检索结果，用于在RAG服务不可用时提供基础信息。
在实际生产环境中，应确保RAG服务的稳定性和可用性。

常见的文档内容包括：
- 项目基本信息和背景介绍
- 技术规范和标准要求
- 实施方案和操作流程
- 质量控制和安全措施
- 相关法规和标准参考
"""
        
        return {
            "query": query,
            "template_id": template_id,
            "results": [{
                "content": fallback_content,
                "source": "备用模拟结果",
                "relevance_score": 0.5,
                "metadata": {
                    "document_type": "fallback",
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "project_id": "fallback",
                    "drawing_id": "fallback"
                }
            }],
            "total_results": 1,
            "is_fallback": True
        }

class TemplateManager:
    """模板管理器 - 根据template_id定位具体模板"""
    
    def __init__(self):
        self.template_dir = Path("templates")
        self.template_mapping = {}
        self._build_template_mapping()
        logger.info("📁 模板管理器初始化完成")
    
    def _build_template_mapping(self):
        """构建模板ID到文件路径的映射"""
        try:
            # 基础的模板ID映射
            self.template_mapping = {
                "construction_organization_design": "debug_test_template.json",
                "heritage_building_comprehensive_plan_v2.1": "debug_test_template.json",
                "construction_safety": "debug_test_template.json",
                "default": "debug_test_template.json"
            }
            
            # 扫描模板目录中的文件，创建动态映射
            if self.template_dir.exists():
                for template_file in self.template_dir.glob("*.json"):
                    template_name = template_file.stem
                    self.template_mapping[template_name] = str(template_file)
            
            logger.info(f"📋 模板映射构建完成，共 {len(self.template_mapping)} 个模板")
            
        except Exception as e:
            logger.warning(f"⚠️ 构建模板映射时出错: {e}")
            # 使用默认映射
            self.template_mapping = {"default": "debug_test_template.json"}
    
    def get_template_json(self, template_id: str) -> Dict[str, str]:
        """根据模板ID获取模板JSON"""
        try:
            # 查找模板文件路径
            template_path = self.template_mapping.get(template_id)
            if not template_path:
                logger.warning(f"⚠️ 未找到模板ID: {template_id}，使用默认模板")
                template_path = self.template_mapping.get("default", "debug_test_template.json")
            
            # 尝试从多个可能的位置加载模板
            possible_paths = [
                template_path,
                os.path.join("templates", template_path),
                os.path.join(".", template_path),
                "debug_test_template.json"  # 最后的备用选项
            ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    logger.info(f"📄 加载模板文件: {path}")
                    with open(path, 'r', encoding='utf-8') as f:
                        template_json = json.load(f)
                    
                    if isinstance(template_json, dict):
                        logger.info(f"✅ 模板加载成功，包含 {len(template_json)} 个章节")
                        return template_json
                    else:
                        logger.warning(f"⚠️ 模板格式不正确: {path}")
                        continue
            
            # 如果所有路径都失败，返回默认模板
            logger.warning("⚠️ 所有模板路径都失败，使用硬编码默认模板")
            return self._get_default_template()
            
        except Exception as e:
            logger.error(f"❌ 获取模板JSON失败: {e}")
            return self._get_default_template()
    
    def _get_default_template(self) -> Dict[str, str]:
        """获取默认模板"""
        return {
            "项目概述": "项目的基本信息和背景介绍",
            "技术方案": "具体的技术实施方案和方法",
            "安全措施": "施工安全管理措施和要求",
            "质量控制": "工程质量控制标准和方法",
            "进度计划": "项目实施的时间安排和里程碑",
            "风险管控": "项目风险识别和应对措施"
        }

# ====================================
# 核心 Function Call 接口
# ====================================

def run_professional_tool_agent(
    user_request: str,
    context: str,
    template_id: str,
    original_file_path: str,
    api_key: str,
    session_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    专业工具代理的核心function call接口
    
    Args:
        user_request: 用户请求描述
        context: 主代理提供的上下文信息
        template_id: 模板标识符
        original_file_path: 原始文档文件路径
        api_key: AI API密钥
        session_id: 可选的会话标识符
    
    Returns:
        Dict包含:
        - status: 状态（success/need_more_info/error）
        - output_path: 生成的文档路径
        - missing_fields: 缺失的字段列表
        - message: 处理消息
        - metadata: 其他元数据
    """
    logger.info("🚀 启动专业工具代理（Function Call模式）...")
    
    try:
        # 1. 初始化服务
        rag_service = RAGService()
        template_manager = TemplateManager()
        
        # 2. RAG检索相关信息
        logger.info("🔍 第一步：RAG信息检索")
        search_query = f"{user_request} {template_id}"
        
        # 尝试从上下文中提取项目信息
        project_name = None
        drawing_type = None
        
        try:
            # 如果context是JSON字符串，尝试解析
            if isinstance(context, str) and context.strip().startswith("{"):
                context_dict = json.loads(context)
                project_name = context_dict.get("project_name") or context_dict.get("项目名称")
                drawing_type = context_dict.get("drawing_type") or context_dict.get("图纸类型")
        except (json.JSONDecodeError, AttributeError):
            # 如果解析失败，尝试简单的文本匹配
            if "项目名称" in context:
                # 简单提取项目名称
                import re
                match = re.search(r'项目名称[：:]\s*([^\n\r，,。.]+)', context)
                if match:
                    project_name = match.group(1).strip()
        
        logger.info(f"📋 从上下文提取的信息 - 项目名称: {project_name}, 图纸类型: {drawing_type}")
        
        rag_results = rag_service.search_documents(
            query=search_query, 
            template_id=template_id,
            project_name=project_name,
            drawing_type=drawing_type
        )
        
        # 3. 获取模板JSON
        logger.info("📄 第二步：加载模板JSON")
        template_json = template_manager.get_template_json(template_id)
        
        # 4. 提取原始文档内容
        logger.info("📄 第三步：提取原始文档内容")
        extraction_result = extract_content_from_file(original_file_path)
        if extraction_result["status"] != "success":
            return {
                "status": "error",
                "output_path": None,
                "missing_fields": [],
                "message": f"文档提取失败: {extraction_result['message']}",
                "metadata": extraction_result.get("metadata", {}),
                "session_id": session_id,
                "timestamp": datetime.now().isoformat()
            }
        
        original_content = extraction_result["content"]
        
        # 5. 合并上下文
        logger.info("🔗 第四步：合并上下文信息")
        rag_context_str = _format_rag_context(rag_results)
        
        enhanced_content = f"""
用户请求上下文：
{context}

RAG检索到的相关信息：
{rag_context_str}

原始文档内容：
{original_content}
"""
        
        # 6. 智能选择处理方式：模板插入 vs 内容合并
        logger.info("🧠 第五步：智能选择处理方式")
        
        # 检查原始文件是否为Word模板
        if original_file_path.lower().endswith(('.doc', '.docx')):
            logger.info("📄 检测到Word模板文件，使用模板插入模式（保持原始结构）")
            merge_result = template_insertion_with_context(
                template_file_path=original_file_path,
                original_content=enhanced_content,
                api_key=api_key
            )
        else:
            logger.info("📝 使用AI智能内容合并模式（生成新文档）")
            merge_result = merge_template_with_context(
                template_json=template_json,
                original_content=enhanced_content,
                api_key=api_key
            )
        
        # 7. 检查处理结果
        if merge_result["status"] == "error":
            return {
                "status": "error",
                "output_path": None,
                "missing_fields": [],
                "message": f"文档处理失败: {merge_result['message']}",
                "metadata": merge_result.get("metadata", {}),
                "session_id": session_id,
                "timestamp": datetime.now().isoformat()
            }
        
        # 8. 分析是否需要更多信息
        missing_fields = merge_result.get("missing_fields", [])
        
        # 9. 确定最终状态（根据处理方式调整）
        if original_file_path.lower().endswith(('.doc', '.docx')):
            # 模板插入模式：更宽松的成功标准
            if merge_result["status"] == "success":
                status = "success"
                message = "Word模板插入完成，原始结构已保持"
            else:
                status = "need_more_info"
                message = f"模板插入需要更多信息，{len(missing_fields)} 个字段缺失"
        else:
            # 内容合并模式：使用原有逻辑
            if len(missing_fields) == 0:
                status = "success"
                message = "文档生成完成，所有字段填充完整"
            elif len(missing_fields) < len(template_json) / 3:
                status = "success"
                message = f"文档生成基本完成，有 {len(missing_fields)} 个字段可进一步完善"
            else:
                status = "need_more_info"
                message = f"文档生成需要更多信息，{len(missing_fields)} 个字段缺失"
        
        logger.info(f"✅ 文档生成处理完成，状态: {status}")
        
        return {
            "status": status,
            "output_path": merge_result.get("output_path"),
            "missing_fields": missing_fields,
            "message": message,
            "metadata": {
                "template_id": template_id,
                "processing_mode": "template_insertion" if original_file_path.lower().endswith(('.doc', '.docx')) else "content_merger",
                "template_file_used": original_file_path if original_file_path.lower().endswith(('.doc', '.docx')) else None,
                "completion_rate": merge_result.get("metadata", {}).get("completion_rate", 0),
                "rag_results_count": len(rag_results.get("results", [])),
                "merge_metadata": merge_result.get("metadata", {}),
                "original_content_length": len(original_content),
                "enhanced_content_length": len(enhanced_content)
            },
            "session_id": session_id,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ 专业工具代理执行失败: {e}")
        return {
            "status": "error",
            "output_path": None,
            "missing_fields": [],
            "message": f"工具代理执行失败: {str(e)}",
            "metadata": {
                "error_details": traceback.format_exc(),
                "template_id": template_id,
                "user_request": user_request[:100] + "..." if len(user_request) > 100 else user_request
            },
            "session_id": session_id,
            "timestamp": datetime.now().isoformat()
        }

def retrieve_with_rag(user_request: str, template_id: str, top_k: int = 5, 
                     project_name: Optional[str] = None, 
                     drawing_type: Optional[str] = None) -> Dict[str, Any]:
    """
    独立的RAG检索function call接口
    
    Args:
        user_request: 用户请求
        template_id: 模板ID
        top_k: 返回结果数量
        project_name: 项目名称（可选）
        drawing_type: 图纸类型（可选）
    
    Returns:
        RAG检索结果
    """
    logger.info(f"🔍 独立RAG检索调用: {user_request[:50]}...")
    
    try:
        rag_service = RAGService()
        results = rag_service.search_documents(
            query=user_request, 
            template_id=template_id, 
            top_k=top_k,
            project_name=project_name,
            drawing_type=drawing_type
        )
        
        return {
            "status": "success",
            "results": results,
            "message": f"RAG检索完成，找到 {len(results.get('results', []))} 个相关结果",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ RAG检索失败: {e}")
        return {
            "status": "error",
            "results": {},
            "message": f"RAG检索失败: {str(e)}",
            "error_details": traceback.format_exc(),
            "timestamp": datetime.now().isoformat()
        }

def _format_rag_context(rag_results: Dict[str, Any]) -> str:
    """格式化RAG检索结果为上下文字符串"""
    if not rag_results or "results" not in rag_results:
        return "未找到相关背景信息"
    
    context_parts = []
    for i, result in enumerate(rag_results["results"], 1):
        context_parts.append(f"""
第{i}个相关文档：
来源：{result.get('source', '未知')}
相关度：{result.get('relevance_score', 0):.2f}
内容：{result.get('content', '')}
""")
    
    return "\n".join(context_parts)

# ====================================
# 测试和演示函数
# ====================================

def test_api_services():
    """测试API服务连接（保持测试功能）"""
    print("🔍 测试API服务连接...")
    
    # 测试RAG服务
    print("\n1. 测试RAG服务连接...")
    try:
        rag_service = RAGService()
        test_query = "施工安全方案"
        test_template_id = "construction_safety"
        
        result = rag_service.search_documents(test_query, test_template_id)
        
        print(f"   ✅ RAG服务连接成功")
        print(f"   📊 搜索结果统计:")
        print(f"      - 查询: {result.get('query', 'N/A')}")
        print(f"      - 模板ID: {result.get('template_id', 'N/A')}")
        print(f"      - 结果数量: {len(result.get('results', []))}")
        
        rag_success = True
        
    except Exception as e:
        print(f"   ❌ RAG服务连接失败: {e}")
        rag_success = False
    
    # 测试模板管理
    print("\n2. 测试模板管理...")
    try:
        template_manager = TemplateManager()
        test_template = template_manager.get_template_json("construction_safety")
        
        print(f"   ✅ 模板管理器工作正常")
        print(f"   📄 测试模板包含 {len(test_template)} 个章节")
        
        template_success = True
        
    except Exception as e:
        print(f"   ❌ 模板管理失败: {e}")
        template_success = False
    
    return rag_success, template_success

def test_professional_tool_agent():
    """测试专业工具代理功能"""
    print("🧪 测试专业工具代理功能")
    print("=" * 60)
    
    # 测试API服务连接
    rag_success, template_success = test_api_services()
    
    print("\n" + "=" * 60)
    
    if rag_success and template_success:
        print("✅ 所有服务连接成功，开始完整流程测试...")
        
        # 准备测试数据
        test_request = {
            "user_request": "生成一份施工组织设计方案，包含安全措施和质量控制要求",
            "context": json.dumps({
                "project_name": "某大型建筑项目",
                "project_type": "商业建筑",
                "requirements": ["安全管理", "质量控制", "进度计划"],
                "location": "北京市朝阳区"
            }, ensure_ascii=False, indent=2),
            "template_id": "construction_organization_design",
            "original_file_path": "template_test copy.doc",  # 使用存在的测试文件
            "api_key": get_openrouter_api_key(),
            "session_id": "test_session_001"
        }
        
        try:
            result = run_professional_tool_agent(**test_request)
            
            print(f"\n📊 测试结果:")
            print(f"   状态: {result['status']}")
            print(f"   消息: {result['message']}")
            if result.get('output_path'):
                print(f"   生成文档: {result['output_path']}")
            if result.get('missing_fields'):
                print(f"   缺失字段: {result['missing_fields']}")
            print(f"   完成率: {result.get('metadata', {}).get('completion_rate', 0):.2%}")
            
        except Exception as e:
            print(f"❌ 测试失败: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("⚠️ 部分服务连接失败，请检查:")
        if not rag_success:
            print("   1. RAG服务是否正在运行")
            print("   2. RAG服务地址是否正确")
        if not template_success:
            print("   3. 模板文件是否存在")
            print("   4. 模板格式是否正确")
    
    print("=" * 60)
    print("🎯 测试结束")

# ====================================
# 向后兼容接口（供原有代码调用）
# ====================================

def run_professional_document_generation(
    user_request: str,
    main_agent_context: Dict[str, Any],
    template_id: str,
    session_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    向后兼容的专业文档生成接口
    （兼容原有的函数签名，但内部调用新的function call接口）
    """
    logger.info("🔄 向后兼容模式：专业文档生成")
    
    try:
        # 从主代理上下文中提取信息
        context = json.dumps(main_agent_context, ensure_ascii=False, indent=2)
        
        # 尝试从上下文中找到原始文件路径
        original_file_path = main_agent_context.get("original_file_path", "template_test copy.doc")
        
        # 获取API密钥
        api_key = get_openrouter_api_key()
        
        # 调用新的function call接口
        result = run_professional_tool_agent(
            user_request=user_request,
            context=context,
            template_id=template_id,
            original_file_path=original_file_path,
            api_key=api_key,
            session_id=session_id
        )
        
        # 转换为原有的响应格式
        return {
            "status": result["status"],
            "message": result["message"],
            "generated_document_path": result.get("output_path"),
            "missing_information": result.get("missing_fields", []),
            "result": {
                "completion_rate": result.get("metadata", {}).get("completion_rate", 0),
                "iterations": 1
            },
            "metadata": result.get("metadata", {}),
            "session_id": session_id,
            "timestamp": result.get("timestamp")
        }
        
    except Exception as e:
        logger.error(f"❌ 向后兼容模式失败: {e}")
        return {
            "status": "error",
            "message": f"向后兼容模式执行失败: {str(e)}",
            "error_details": traceback.format_exc(),
            "session_id": session_id,
            "timestamp": datetime.now().isoformat()
        }

if __name__ == "__main__":
    test_professional_tool_agent() 
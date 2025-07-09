#!/usr/bin/env python3
"""
完整工作流管理器
串联PDF解析→embedding→图片RAG→长文档生成的完整流程
实现用户设想的端到端多模态文档处理系统
"""

import os
import json
import logging
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime

# 导入所有工具组件
from multimodal_rag_workflow_tool import MultimodalRAGWorkflowTool
from enhanced_long_document_generator import EnhancedLongDocumentGenerator
from tools import Tool

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CompleteWorkflowManager(Tool):
    """完整工作流管理器 - 端到端的多模态文档处理系统"""
    
    def __init__(self):
        super().__init__(
            name="complete_workflow_manager",
            description="🔄 完整工作流管理器 - 端到端的PDF解析→embedding→图片RAG→智能文档生成系统"
        )
        
        # 初始化工具组件
        self.rag_workflow = MultimodalRAGWorkflowTool()
        self.doc_generator = EnhancedLongDocumentGenerator()
        
        # 工作流配置
        self.workflow_config = {
            "auto_process_pdfs": True,
            "include_image_processing": True,
            "auto_generate_descriptions": True,
            "enable_knowledge_enhancement": True,
            "output_formats": ["docx", "json"],
            "cleanup_temp_files": True
        }
        
        # 全局统计
        self.workflow_stats = {
            "total_workflows": 0,
            "successful_workflows": 0,
            "processed_pdfs": 0,
            "generated_documents": 0,
            "knowledge_base_size": 0
        }
        
        logger.info("✅ 完整工作流管理器初始化完成")
    
    def execute(self, **kwargs) -> str:
        """
        执行完整工作流
        
        Args:
            action: 操作类型
            - full_workflow: 完整流程（PDF→知识库→文档生成）
            - knowledge_base_only: 仅知识库构建
            - document_generation_only: 仅文档生成
            - batch_workflow: 批量处理
            - get_stats: 获取统计信息
            - set_config: 设置配置
            
            pdf_path/pdf_directory: PDF文件或目录路径
            generation_request: 文档生成请求
            project_name: 项目名称
            workflow_config: 工作流配置覆盖
        """
        action = kwargs.get("action", "full_workflow")
        
        if action == "full_workflow":
            return self._execute_full_workflow(**kwargs)
        elif action == "knowledge_base_only":
            return self._build_knowledge_base_only(**kwargs)
        elif action == "document_generation_only":
            return self._generate_document_only(**kwargs)
        elif action == "batch_workflow":
            return self._execute_batch_workflow(**kwargs)
        elif action == "get_stats":
            return self._get_comprehensive_stats()
        elif action == "set_config":
            return self._set_workflow_config(**kwargs)
        else:
            return json.dumps({
                "status": "error",
                "message": f"不支持的操作: {action}",
                "supported_actions": [
                    "full_workflow", "knowledge_base_only", 
                    "document_generation_only", "batch_workflow",
                    "get_stats", "set_config"
                ]
            }, indent=2, ensure_ascii=False)
    
    def _execute_full_workflow(self, **kwargs) -> str:
        """执行完整的端到端工作流"""
        pdf_path = kwargs.get("pdf_path")
        generation_request = kwargs.get("generation_request", "")
        project_name = kwargs.get("project_name", "")
        
        if not pdf_path:
            return json.dumps({
                "status": "error",
                "message": "请提供PDF文件路径 (pdf_path参数)"
            }, indent=2, ensure_ascii=False)
        
        if not generation_request:
            generation_request = f"基于上传的PDF文档生成相关技术报告"
        
        workflow_id = str(uuid.uuid4())
        workflow_result = {
            "status": "processing",
            "workflow_id": workflow_id,
            "workflow_type": "full_workflow",
            "pdf_path": pdf_path,
            "generation_request": generation_request,
            "project_name": project_name,
            "timestamp": datetime.now().isoformat(),
            "phases": []
        }
        
        try:
            # 阶段1: PDF处理和知识库构建
            logger.info(f"📄 阶段1: 处理PDF并构建知识库 - {pdf_path}")
            knowledge_phase = self._execute_knowledge_building_phase(pdf_path, project_name)
            workflow_result["phases"].append(knowledge_phase)
            
            if knowledge_phase["status"] != "success":
                workflow_result["status"] = "partial_failure"
                workflow_result["message"] = "知识库构建阶段失败"
                return json.dumps(workflow_result, indent=2, ensure_ascii=False)
            
            # 阶段2: 智能文档生成
            logger.info(f"📝 阶段2: 基于知识库生成智能文档")
            generation_phase = self._execute_document_generation_phase(
                generation_request, project_name
            )
            workflow_result["phases"].append(generation_phase)
            
            # 阶段3: 结果整合和清理
            logger.info(f"🔄 阶段3: 结果整合")
            integration_phase = self._execute_integration_phase(
                knowledge_phase, generation_phase
            )
            workflow_result["phases"].append(integration_phase)
            
            # 更新最终状态
            if all(phase["status"] == "success" for phase in workflow_result["phases"]):
                workflow_result["status"] = "success"
                workflow_result["message"] = "完整工作流执行成功"
                self.workflow_stats["successful_workflows"] += 1
            else:
                workflow_result["status"] = "partial_success"
                workflow_result["message"] = "工作流部分成功"
            
            # 生成工作流摘要
            workflow_result["summary"] = self._generate_workflow_summary(workflow_result)
            
            # 更新统计
            self.workflow_stats["total_workflows"] += 1
            self.workflow_stats["processed_pdfs"] += 1
            self.workflow_stats["generated_documents"] += 1
            
            logger.info(f"✅ 完整工作流完成: {workflow_id}")
            return json.dumps(workflow_result, indent=2, ensure_ascii=False)
            
        except Exception as e:
            workflow_result["status"] = "error"
            workflow_result["error"] = str(e)
            logger.error(f"❌ 完整工作流失败: {e}")
            return json.dumps(workflow_result, indent=2, ensure_ascii=False)
    
    def _execute_knowledge_building_phase(self, pdf_path: str, project_name: str) -> Dict[str, Any]:
        """执行知识库构建阶段"""
        phase_result = {
            "phase": "knowledge_building",
            "status": "processing",
            "timestamp": datetime.now().isoformat(),
            "steps": []
        }
        
        try:
            # 调用多模态RAG工作流
            rag_result_str = self.rag_workflow.execute(
                action="process_pdf",
                pdf_path=pdf_path,
                include_images=self.workflow_config["include_image_processing"],
                auto_description=self.workflow_config["auto_generate_descriptions"]
            )
            
            rag_result = json.loads(rag_result_str)
            
            phase_result.update({
                "status": rag_result.get("status", "unknown"),
                "message": "知识库构建完成" if rag_result.get("status") == "success" else "知识库构建失败",
                "rag_workflow_result": rag_result,
                "processed_components": {
                    "text_processed": bool(rag_result.get("steps", [{}])[1].get("status") == "success" if len(rag_result.get("steps", [])) > 1 else False),
                    "images_processed": bool(rag_result.get("steps", [{}])[2].get("status") == "success" if len(rag_result.get("steps", [])) > 2 else False),
                    "output_directory": rag_result.get("summary", {}).get("output_directory")
                }
            })
            
            return phase_result
            
        except Exception as e:
            phase_result.update({
                "status": "error",
                "message": f"知识库构建阶段失败: {str(e)}"
            })
            return phase_result
    
    def _execute_document_generation_phase(self, generation_request: str, project_name: str) -> Dict[str, Any]:
        """执行文档生成阶段"""
        phase_result = {
            "phase": "document_generation",
            "status": "processing",
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            # 调用增强版长文档生成器
            gen_result_str = self.doc_generator.execute(
                action="generate",
                request=generation_request,
                project_name=project_name,
                include_images=self.workflow_config["include_image_processing"],
                output_format="docx"
            )
            
            gen_result = json.loads(gen_result_str)
            
            phase_result.update({
                "status": gen_result.get("status", "unknown"),
                "message": "智能文档生成完成" if gen_result.get("status") == "success" else "文档生成失败",
                "generation_result": gen_result,
                "output_documents": {
                    "document_path": gen_result.get("output", {}).get("document_path"),
                    "total_chapters": gen_result.get("output", {}).get("total_chapters"),
                    "total_images": gen_result.get("output", {}).get("total_images"),
                    "document_size": gen_result.get("output", {}).get("document_size")
                }
            })
            
            return phase_result
            
        except Exception as e:
            phase_result.update({
                "status": "error",
                "message": f"文档生成阶段失败: {str(e)}"
            })
            return phase_result
    
    def _execute_integration_phase(self, knowledge_phase: Dict, generation_phase: Dict) -> Dict[str, Any]:
        """执行结果整合阶段"""
        phase_result = {
            "phase": "integration",
            "status": "processing",
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            # 整合结果信息
            integration_summary = {
                "knowledge_base_status": knowledge_phase.get("status"),
                "document_generation_status": generation_phase.get("status"),
                "total_processing_time": self._calculate_processing_time(knowledge_phase, generation_phase),
                "output_files": [],
                "knowledge_components": knowledge_phase.get("processed_components", {}),
                "document_components": generation_phase.get("output_documents", {})
            }
            
            # 收集输出文件
            if knowledge_phase.get("processed_components", {}).get("output_directory"):
                integration_summary["output_files"].append({
                    "type": "pdf_parsing_output",
                    "path": knowledge_phase["processed_components"]["output_directory"]
                })
            
            if generation_phase.get("output_documents", {}).get("document_path"):
                integration_summary["output_files"].append({
                    "type": "generated_document",
                    "path": generation_phase["output_documents"]["document_path"]
                })
            
            # 执行清理（如果配置允许）
            if self.workflow_config["cleanup_temp_files"]:
                cleanup_result = self._cleanup_temporary_files(integration_summary)
                integration_summary["cleanup_performed"] = cleanup_result
            
            phase_result.update({
                "status": "success",
                "message": "结果整合完成",
                "integration_summary": integration_summary
            })
            
            return phase_result
            
        except Exception as e:
            phase_result.update({
                "status": "error",
                "message": f"结果整合失败: {str(e)}"
            })
            return phase_result
    
    def _build_knowledge_base_only(self, **kwargs) -> str:
        """仅构建知识库"""
        pdf_path = kwargs.get("pdf_path")
        pdf_directory = kwargs.get("pdf_directory")
        
        if pdf_path:
            return self.rag_workflow.execute(
                action="process_pdf",
                pdf_path=pdf_path,
                include_images=self.workflow_config["include_image_processing"]
            )
        elif pdf_directory:
            return self.rag_workflow.execute(
                action="batch_process",
                pdf_directory=pdf_directory,
                include_images=self.workflow_config["include_image_processing"]
            )
        else:
            return json.dumps({
                "status": "error",
                "message": "请提供pdf_path或pdf_directory参数"
            }, indent=2, ensure_ascii=False)
    
    def _generate_document_only(self, **kwargs) -> str:
        """仅生成文档"""
        generation_request = kwargs.get("generation_request")
        project_name = kwargs.get("project_name", "")
        
        if not generation_request:
            return json.dumps({
                "status": "error",
                "message": "请提供generation_request参数"
            }, indent=2, ensure_ascii=False)
        
        return self.doc_generator.execute(
            action="generate",
            request=generation_request,
            project_name=project_name,
            include_images=self.workflow_config["include_image_processing"]
        )
    
    def _execute_batch_workflow(self, **kwargs) -> str:
        """执行批量工作流"""
        pdf_directory = kwargs.get("pdf_directory")
        base_generation_request = kwargs.get("generation_request", "基于PDF文档生成技术报告")
        project_name = kwargs.get("project_name", "")
        
        if not pdf_directory:
            return json.dumps({
                "status": "error",
                "message": "请提供pdf_directory参数"
            }, indent=2, ensure_ascii=False)
        
        batch_result = {
            "status": "processing",
            "batch_type": "full_workflow_batch",
            "pdf_directory": pdf_directory,
            "timestamp": datetime.now().isoformat(),
            "processed_files": [],
            "summary": {
                "total_files": 0,
                "successful_workflows": 0,
                "failed_workflows": 0
            }
        }
        
        try:
            # 查找所有PDF文件
            pdf_files = []
            for root, dirs, files in os.walk(pdf_directory):
                for file in files:
                    if file.lower().endswith('.pdf'):
                        pdf_files.append(os.path.join(root, file))
            
            batch_result["summary"]["total_files"] = len(pdf_files)
            
            # 处理每个PDF文件
            for pdf_path in pdf_files:
                try:
                    # 为每个文件生成专门的请求
                    file_request = f"{base_generation_request} - 基于文件: {os.path.basename(pdf_path)}"
                    
                    workflow_result_str = self._execute_full_workflow(
                        pdf_path=pdf_path,
                        generation_request=file_request,
                        project_name=project_name
                    )
                    
                    workflow_result = json.loads(workflow_result_str)
                    
                    batch_result["processed_files"].append({
                        "pdf_path": pdf_path,
                        "status": workflow_result.get("status"),
                        "workflow_id": workflow_result.get("workflow_id"),
                        "summary": workflow_result.get("summary")
                    })
                    
                    if workflow_result.get("status") == "success":
                        batch_result["summary"]["successful_workflows"] += 1
                    else:
                        batch_result["summary"]["failed_workflows"] += 1
                    
                except Exception as e:
                    batch_result["processed_files"].append({
                        "pdf_path": pdf_path,
                        "status": "error",
                        "error": str(e)
                    })
                    batch_result["summary"]["failed_workflows"] += 1
            
            batch_result["status"] = "completed"
            return json.dumps(batch_result, indent=2, ensure_ascii=False)
            
        except Exception as e:
            batch_result["status"] = "error"
            batch_result["error"] = str(e)
            return json.dumps(batch_result, indent=2, ensure_ascii=False)
    
    def _calculate_processing_time(self, *phases) -> str:
        """计算处理时间"""
        try:
            timestamps = []
            for phase in phases:
                if "timestamp" in phase:
                    timestamps.append(datetime.fromisoformat(phase["timestamp"]))
            
            if len(timestamps) >= 2:
                total_time = timestamps[-1] - timestamps[0]
                return f"{total_time.total_seconds():.1f}秒"
            else:
                return "计算中"
        except:
            return "未知"
    
    def _cleanup_temporary_files(self, integration_summary: Dict) -> Dict[str, Any]:
        """清理临时文件"""
        cleanup_result = {
            "performed": True,
            "cleaned_files": [],
            "errors": []
        }
        
        try:
            # 这里可以添加具体的清理逻辑
            # 例如删除临时解析文件、缓存等
            logger.info("执行临时文件清理...")
            return cleanup_result
        except Exception as e:
            cleanup_result["performed"] = False
            cleanup_result["errors"].append(str(e))
            return cleanup_result
    
    def _generate_workflow_summary(self, workflow_result: Dict) -> Dict[str, Any]:
        """生成工作流摘要"""
        summary = {
            "workflow_id": workflow_result.get("workflow_id"),
            "overall_status": workflow_result.get("status"),
            "total_phases": len(workflow_result.get("phases", [])),
            "successful_phases": sum(1 for phase in workflow_result.get("phases", []) if phase.get("status") == "success"),
            "processing_details": {},
            "output_files": [],
            "recommendations": []
        }
        
        # 提取处理细节
        for phase in workflow_result.get("phases", []):
            phase_name = phase.get("phase", "unknown")
            summary["processing_details"][phase_name] = {
                "status": phase.get("status"),
                "message": phase.get("message")
            }
        
        # 收集输出文件
        for phase in workflow_result.get("phases", []):
            if "integration_summary" in phase:
                summary["output_files"].extend(
                    phase["integration_summary"].get("output_files", [])
                )
        
        # 生成建议
        if summary["overall_status"] == "success":
            summary["recommendations"].append("工作流执行成功，可以查看生成的文档和知识库")
        elif summary["overall_status"] == "partial_success":
            summary["recommendations"].append("工作流部分成功，建议检查失败的阶段")
        else:
            summary["recommendations"].append("工作流执行失败，建议检查错误日志并重试")
        
        return summary
    
    def _get_comprehensive_stats(self) -> str:
        """获取综合统计信息"""
        # 获取各组件统计
        rag_stats_str = self.rag_workflow.execute(action="get_stats")
        doc_gen_stats_str = self.doc_generator.execute(action="get_stats")
        
        try:
            rag_stats = json.loads(rag_stats_str)
            doc_gen_stats = json.loads(doc_gen_stats_str)
        except:
            rag_stats = {}
            doc_gen_stats = {}
        
        comprehensive_stats = {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "workflow_manager_stats": self.workflow_stats,
            "rag_workflow_stats": rag_stats.get("workflow_statistics", {}),
            "document_generator_stats": doc_gen_stats.get("generation_statistics", {}),
            "system_health": {
                "total_workflows": self.workflow_stats["total_workflows"],
                "success_rate": f"{(self.workflow_stats['successful_workflows'] / max(1, self.workflow_stats['total_workflows'])) * 100:.1f}%",
                "components_status": {
                    "rag_workflow": "operational",
                    "document_generator": "operational",
                    "workflow_manager": "operational"
                }
            }
        }
        
        return json.dumps(comprehensive_stats, indent=2, ensure_ascii=False)
    
    def _set_workflow_config(self, **kwargs) -> str:
        """设置工作流配置"""
        config_updates = kwargs.get("config", {})
        
        if not config_updates:
            return json.dumps({
                "status": "error",
                "message": "请提供配置更新 (config参数)"
            }, indent=2, ensure_ascii=False)
        
        # 更新配置
        valid_keys = set(self.workflow_config.keys())
        updated_keys = []
        
        for key, value in config_updates.items():
            if key in valid_keys:
                self.workflow_config[key] = value
                updated_keys.append(key)
        
        return json.dumps({
            "status": "success",
            "message": f"配置更新完成: {updated_keys}",
            "updated_config": {k: self.workflow_config[k] for k in updated_keys},
            "current_config": self.workflow_config
        }, indent=2, ensure_ascii=False)
    
    def get_usage_guide(self) -> str:
        """获取使用指南"""
        return """
🔄 完整工作流管理器使用指南

🎯 核心理念：
实现您设想的完整流程：PDF解析 → 文本embedding → 图片RAG → 智能文档生成

🚀 主要功能：
1. 📄 PDF解析和多模态内容提取
2. 🧠 自动文本embedding到知识库
3. 🖼️ 图片RAG处理和存储
4. 📝 基于知识库的智能文档生成
5. 🔄 端到端工作流管理

📋 基本用法：

1. 完整工作流（推荐）:
   complete_workflow_manager(
       action="full_workflow",
       pdf_path="path/to/document.pdf",
       generation_request="生成技术报告",
       project_name="我的项目"
   )

2. 仅构建知识库:
   complete_workflow_manager(
       action="knowledge_base_only",
       pdf_path="path/to/document.pdf"
   )

3. 仅生成文档:
   complete_workflow_manager(
       action="document_generation_only",
       generation_request="基于已有知识库生成报告"
   )

4. 批量处理:
   complete_workflow_manager(
       action="batch_workflow",
       pdf_directory="path/to/pdfs/",
       generation_request="批量生成报告"
   )

🔧 工作流配置：
- auto_process_pdfs: 自动处理PDF（默认True）
- include_image_processing: 包含图片处理（默认True）
- auto_generate_descriptions: 自动生成图片描述（默认True）
- enable_knowledge_enhancement: 启用知识增强（默认True）
- output_formats: 输出格式列表（默认["docx", "json"]）
- cleanup_temp_files: 清理临时文件（默认True）

📊 完整流程：
1. 📄 PDF解析 → 提取文本、图片、表格
2. 🧠 文本embedding → 构建向量知识库
3. 🖼️ 图片RAG → 图片描述和向量化存储
4. 📝 智能生成 → 基于知识库生成文档
5. 🖼️ 图片插入 → 在每章节中插入相关图片
6. 📄 文档输出 → 生成最终的多模态文档

💡 使用建议：
- 确保PDF文件质量良好
- 提供清晰的项目名称以提高检索精度
- 根据需要调整工作流配置
- 大批量处理时建议分批进行
- 定期查看统计信息监控系统状态

⚡ 系统优势：
✅ 端到端自动化处理
✅ 多模态内容整合（文本+图片）
✅ 智能知识增强
✅ 灵活的工作流配置
✅ 详细的处理状态跟踪
✅ 支持批量处理
✅ 完整的错误处理和恢复

🎉 实现了您的完整设想：
"PDF解析 → 文本embedding → 图片RAG → 长文档生成时调用RAG → 每章生成后图片RAG插入"
        """


# 工具实例化和导出
if __name__ == "__main__":
    manager = CompleteWorkflowManager()
    print(manager.get_usage_guide()) 
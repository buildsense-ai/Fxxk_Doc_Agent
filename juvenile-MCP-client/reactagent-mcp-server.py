#!/usr/bin/env python3
"""
ReactAgent MCP Server
将ReactAgent系统的所有工具封装为MCP (Model Context Protocol) 服务器
"""

import sys
import os
import json
import asyncio
from pathlib import Path
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# 添加ReactAgent的src目录和根目录到Python路径
current_dir = Path(__file__).parent
reactagent_root = current_dir.parent  # ReactAgent根目录
reactagent_src = reactagent_root / "src"  # src目录

# 添加根目录到路径（使src模块可以被导入）
if str(reactagent_root) not in sys.path:
    sys.path.insert(0, str(reactagent_root))
    
# 添加src目录到路径（使src内的模块可以被直接导入）
if str(reactagent_src) not in sys.path:
    sys.path.insert(0, str(reactagent_src))

# 导入ReactAgent的工具
try:
    from tools import create_core_tool_registry
    from deepseek_client import DeepSeekClient
    from enhanced_react_agent import EnhancedReActAgent
    print("✅ 成功导入ReactAgent组件")
except ImportError as e:
    print(f"❌ 导入ReactAgent组件失败: {e}")
    sys.exit(1)

app = FastAPI(
    title="ReactAgent MCP Server",
    description="ReactAgent系统的MCP服务器封装",
    version="1.0.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局变量
tool_registry = None
react_agent = None
deepseek_client = None

@app.on_event("startup")
async def startup_event():
    """启动时初始化ReactAgent系统"""
    global tool_registry, react_agent, deepseek_client
    
    try:
        print("🚀 初始化ReactAgent MCP服务器...")
        
        # 初始化DeepSeek客户端
        deepseek_client = DeepSeekClient()
        print("✅ DeepSeek客户端初始化成功")
        
        # 创建工具注册表
        tool_registry = create_core_tool_registry(deepseek_client)
        print(f"✅ 工具注册表初始化成功，共{len(tool_registry.tools)}个工具")
        
        # 初始化ReAct Agent
        react_agent = EnhancedReActAgent(
            deepseek_client=deepseek_client,
            tool_registry=tool_registry,
            verbose=True,
            enable_memory=True
        )
        print("✅ ReAct Agent初始化成功")
        
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        raise

@app.get("/tools")
async def list_tools():
    """列出所有可用工具 - MCP标准端点"""
    if not tool_registry:
        raise HTTPException(status_code=500, detail="工具注册表未初始化")
    
    tools = []
    for tool_name, tool in tool_registry.tools.items():
        # 转换为MCP工具格式
        mcp_tool = {
            "name": tool_name,
            "description": tool.description,
            "inputSchema": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
        
        # 根据工具类型添加参数
        if tool_name == "rag_tool":
            mcp_tool["inputSchema"]["properties"] = {
                "operation": {
                    "type": "string",
                    "enum": ["add_document", "search", "list_documents", "delete_document"],
                    "description": "操作类型"
                },
                "file_path": {"type": "string", "description": "文档文件路径"},
                "query": {"type": "string", "description": "搜索查询"},
                "top_k": {"type": "integer", "default": 5, "description": "返回结果数量"}
            }
            mcp_tool["inputSchema"]["required"] = ["operation"]
            
        elif tool_name == "professional_document_tool":
            mcp_tool["inputSchema"]["properties"] = {
                "file_path": {"type": "string", "description": "输入文档文件路径"},
                "user_request": {"type": "string", "description": "用户需求描述"},
                "context": {"type": "string", "description": "项目背景信息"},
                "processing_mode": {
                    "type": "string",
                    "enum": ["auto", "professional_agent", "template_insertion", "content_merge"],
                    "default": "auto",
                    "description": "处理模式"
                }
            }
            mcp_tool["inputSchema"]["required"] = ["file_path", "user_request"]
            
        elif tool_name == "template_classifier":
            mcp_tool["inputSchema"]["properties"] = {
                "file_path": {"type": "string", "description": "上传文档的文件路径"},
                "action": {
                    "type": "string",
                    "enum": ["classify"],
                    "default": "classify",
                    "description": "操作类型"
                }
            }
            mcp_tool["inputSchema"]["required"] = ["file_path"]
            
        elif tool_name == "image_rag_tool":
            mcp_tool["inputSchema"]["properties"] = {
                "action": {
                    "type": "string",
                    "enum": ["upload", "search", "list"],
                    "description": "操作类型"
                },
                "image_path": {"type": "string", "description": "图片文件路径"},
                "description": {"type": "string", "description": "图片描述"},
                "query": {"type": "string", "description": "搜索查询"},
                "top_k": {"type": "integer", "default": 5, "description": "返回结果数量"}
            }
            mcp_tool["inputSchema"]["required"] = ["action"]
            
        elif tool_name == "image_document_generator":
            mcp_tool["inputSchema"]["properties"] = {
                "action": {
                    "type": "string",
                    "enum": ["generate", "status", "list"],
                    "description": "操作类型 (generate: 生成文档, status: 查询状态, list: 列出任务)"
                },
                "source_data_path": {
                    "type": "string",
                    "description": "【generate操作必需】由pdf_parser输出的源数据文件夹路径"
                },
                "task_id": {
                    "type": "string",
                    "description": "【status操作必需】要查询状态的任务ID"
                }
            }
            mcp_tool["inputSchema"]["required"] = ["action"]
            
        elif tool_name == "pdf_parser":
            mcp_tool["inputSchema"]["properties"] = {
                "action": {
                    "type": "string",
                    "enum": ["parse", "list_models"],
                    "default": "parse",
                    "description": "操作类型"
                },
                "pdf_path": {
                    "type": "string", 
                    "description": "【parse操作必需】要解析的PDF文件路径"
                },
                "output_dir": {"type": "string", "description": "【可选】指定输出目录"},
                "model_name": {"type": "string", "default": "gpt-4o", "description": "【可选】指定AI模型"}
            }
            mcp_tool["inputSchema"]["required"] = ["action"]
            
        elif tool_name == "optimized_workflow_agent":
            mcp_tool["inputSchema"]["properties"] = {
                "action": {
                    "type": "string",
                    "enum": ["complete_workflow", "parse_only", "embedding_only", "generate_only"],
                    "default": "complete_workflow",
                    "description": "操作类型：complete_workflow(完整流程), parse_only(仅解析), embedding_only(仅embedding), generate_only(仅生成)"
                },
                "pdf_path": {
                    "type": "string",
                    "description": "PDF文件路径（complete_workflow和parse_only时需要）"
                },
                "folder_path": {
                    "type": "string",
                    "description": "解析文件夹路径（embedding_only时需要）"
                },
                "request": {
                    "type": "string",
                    "description": "文档生成请求（complete_workflow和generate_only时需要）"
                },
                "project_name": {
                    "type": "string",
                    "description": "项目名称（可选）"
                }
            }
            mcp_tool["inputSchema"]["required"] = ["action"]
        
        tools.append(mcp_tool)
    
    return {"tools": tools}

@app.post("/call_tool")
async def call_tool(request: Dict[str, Any]):
    """调用工具 - MCP标准端点"""
    if not tool_registry or not react_agent:
        raise HTTPException(status_code=500, detail="系统未初始化")
    
    tool_name = request.get("name")
    arguments = request.get("arguments", {})
    
    if not tool_name:
        raise HTTPException(status_code=400, detail="缺少工具名称")
    
    try:
        # 使用工具注册表执行工具
        result = tool_registry.execute_tool(tool_name, **arguments)
        
        return {
            "content": [
                {
                    "type": "text",
                    "text": str(result)
                }
            ],
            "isError": False
        }
        
    except Exception as e:
        return {
            "content": [
                {
                    "type": "text", 
                    "text": f"工具执行失败: {str(e)}"
                }
            ],
            "isError": True
        }

@app.post("/react_solve")
async def react_solve(request: Dict[str, Any]):
    """使用ReAct Agent解决复杂问题"""
    if not react_agent:
        raise HTTPException(status_code=500, detail="ReAct Agent未初始化")
    
    problem = request.get("problem", "")
    files = request.get("files", [])  # 新增：接收文件信息
    
    print(f"🔍 收到问题: {problem}")
    print(f"📎 收到文件信息: {files}")
    
    if not problem:
        raise HTTPException(status_code=400, detail="缺少问题描述")
    
    try:
        # 如果有文件信息，将其添加到问题描述中，并确保路径正确
        if files:
            file_info = "\n\n已上传的文件:\n"
            for file in files:
                # 优先使用reactAgentPath，然后是path
                file_path = file.get('reactAgentPath') or file.get('path') or file.get('localPath')
                file_name = file.get('name') or file.get('originalName', 'Unknown')
                
                if file_path:
                    # 确保路径是绝对路径
                    import os
                    if not os.path.isabs(file_path):
                        # 如果是相对路径，转换为绝对路径
                        base_dir = os.path.dirname(os.path.abspath(__file__))
                        uploads_dir = os.path.join(base_dir, 'uploads')
                        file_path = os.path.join(uploads_dir, os.path.basename(file_path))
                    
                    # 验证文件是否存在
                    if os.path.exists(file_path):
                        file_info += f"- {file_name}: {file_path}\n"
                        print(f"✅ 文件路径验证成功: {file_path}")
                    else:
                        file_info += f"- {file_name}: {file_path} (文件不存在)\n"
                        print(f"❌ 文件不存在: {file_path}")
                else:
                    file_info += f"- {file_name}: 路径未知\n"
                    print(f"⚠️ 文件路径未知: {file_name}")
            
            problem += file_info
            print(f"📄 添加文件信息后的完整问题: {problem}")
        
        result = react_agent.solve(problem)
        return {
            "content": [
                {
                    "type": "text",
                    "text": result
                }
            ],
            "isError": False
        }
    except Exception as e:
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"ReAct求解失败: {str(e)}"
                }
            ],
            "isError": True
        }

@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "tools_count": len(tool_registry.tools) if tool_registry else 0,
        "react_agent_ready": react_agent is not None,
        "deepseek_client_ready": deepseek_client is not None
    }

@app.get("/")
async def root():
    """根端点信息"""
    return {
        "name": "ReactAgent MCP Server",
        "version": "1.0.0",
        "description": "ReactAgent系统的MCP服务器封装",
        "endpoints": {
            "/tools": "列出所有可用工具",
            "/call_tool": "调用指定工具",
            "/react_solve": "使用ReAct Agent解决问题",
            "/health": "健康检查"
        }
    }

if __name__ == "__main__":
    print("🚀 启动ReactAgent MCP服务器...")
    uvicorn.run(
        "reactagent-mcp-server:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    ) 
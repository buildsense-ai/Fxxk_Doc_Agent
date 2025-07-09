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
from fastapi.responses import StreamingResponse
from fastapi.concurrency import run_in_threadpool
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
    from src.tools import create_core_tool_registry
    from src.deepseek_client import DeepSeekClient
    from src.enhanced_react_agent import EnhancedReActAgent
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

class StreamingReActAgent:
    """支持流式输出的ReAct Agent"""
    
    def __init__(self, deepseek_client, tool_registry, max_iterations=10, verbose=True, enable_memory=True):
        self.client = deepseek_client
        self.tool_registry = tool_registry
        self.max_iterations = max_iterations
        self.verbose = verbose
        self.enable_memory = enable_memory
        
        # 构建系统提示词
        self.system_prompt = self._build_system_prompt()
    
    def _build_system_prompt(self):
        """构建系统提示词"""
        tools_description = "\n".join([
            f"- {tool['name']}: {tool['description']}"
            for tool in self.tool_registry.list_tools()
        ])
        
        return f"""你是一个ReAct (Reasoning and Acting) 智能代理。你需要通过交替进行推理(Thought)和行动(Action)来解决问题。

⚠️ **重要：简单问题可以直接回答，复杂问题才需要使用工具！**

可用工具:
{tools_description}

🚨 **严格的响应格式要求:**

**每次响应必须严格按照以下格式：**

```
Thought: [你的推理过程]
Action: [工具名称，只能是以下之一: rag_tool, image_rag_tool, pdf_parser, pdf_embedding]
Action Input: [{{"action": "操作类型", "其他参数": "参数值"}}]
```

**或者直接给出最终答案：**

```
Thought: [你的推理过程]
Final Answer: [你的回答]
```

🎯 **工具调用格式说明:**
- **pdf_parser**: {{"action": "parse", "pdf_path": "文件路径"}}
- **rag_tool**: {{"action": "search", "query": "搜索内容", "top_k": 5}}
- **image_rag_tool**: {{"action": "search", "query": "搜索内容", "top_k": 5}}
- **pdf_embedding**: {{"action": "add_document", "file_path": "文件路径"}}

🚨 **关键规则:**
1. 简单问候、聊天等可以直接用Final Answer回答
2. 只有在需要处理文档、搜索信息时才使用工具
3. Action Input必须是有效的JSON格式
4. 每次只调用一个工具
5. 等待Observation结果后再继续

开始解决问题吧！"""
    
    def _parse_response(self, response):
        """解析LLM响应，提取推理、行动和输入"""
        import re
        
        # 查找Thought
        thought_match = re.search(r'Thought:\s*(.*?)(?=\n(?:Action|Final Answer):|$)', response, re.DOTALL)
        thought = thought_match.group(1).strip() if thought_match else ""
        
        # 查找Final Answer
        final_answer_match = re.search(r'Final Answer:\s*(.*)', response, re.DOTALL)
        if final_answer_match:
            final_answer = final_answer_match.group(1).strip()
            return thought, None, final_answer
        
        # 查找Action和Action Input
        action_match = re.search(r'Action:\s*(.*?)(?=\n|$)', response)
        action = action_match.group(1).strip() if action_match else None
        
        # 清理action，移除可能的无效字符和格式
        if action:
            # 移除可能的markdown格式标记
            action = re.sub(r'```.*?```', '', action, flags=re.DOTALL)
            action = re.sub(r'```.*', '', action)
            action = action.strip()
            
            # 验证action是否为有效工具名称
            valid_tools = ['rag_tool', 'image_rag_tool', 'pdf_parser', 'pdf_embedding']
            if action not in valid_tools:
                # 尝试从action中提取有效工具名称
                for tool in valid_tools:
                    if tool in action:
                        action = tool
                        break
                else:
                    action = None  # 无效的action
        
        action_input_match = re.search(r'Action Input:\s*(.*?)(?=\n(?:Thought|Action|Final Answer):|$)', response, re.DOTALL)
        action_input = action_input_match.group(1).strip() if action_input_match else ""
        
        # 清理action_input，移除可能的markdown格式标记
        if action_input:
            action_input = re.sub(r'```json\s*', '', action_input)
            action_input = re.sub(r'```\s*$', '', action_input)
            action_input = action_input.strip()
        
        return thought, action, action_input
    
    async def _execute_action(self, action, action_input):
        """执行工具行动 (异步，使用线程池处理阻塞I/O)"""
        try:
            tool = self.tool_registry.get_tool(action)
            if not tool:
                return f"错误：工具 '{action}' 不存在。可用工具: {', '.join([t['name'] for t in self.tool_registry.list_tools()])}"

            # 处理空的action_input
            if not action_input:
                return "错误：工具调用需要参数。请提供有效的JSON格式参数。"

            # 尝试解析JSON格式的输入
            try:
                if action_input.startswith('{') and action_input.endswith('}'):
                    params = json.loads(action_input)
                    
                    # 提取action参数
                    tool_action = params.pop("action", None)
                    if not tool_action:
                        return f"错误：工具 '{action}' 缺少 'action' 参数。"
                    
                    # 调用工具，第一个参数是action，其余通过kwargs传递
                    return await run_in_threadpool(tool.execute, tool_action, **params)
                else:
                    return f"错误: 工具 '{action}' 需要JSON格式的参数, 但收到了: {action_input}"

            except json.JSONDecodeError:
                return f"错误：Action Input不是有效的JSON格式: {action_input}"
            except Exception as e:
                return f"工具执行失败 ({action}): {e}"

        except Exception as e:
            return f"工具获取失败: {e}"
    
    async def solve_stream(self, problem):
        """流式解决问题"""
        try:
            # 立刻发送一个连接成功消息，防止客户端超时
            print(f"🔗 连接已建立，开始处理问题: {problem}")
            yield f"data: {json.dumps({'type': 'status', 'content': '连接已建立，正在准备生成...'})}\n\n"
            await asyncio.sleep(0.01) # 确保消息有机会被发送

            # 构建对话历史
            conversation = []
            conversation.append({"role": "system", "content": self.system_prompt})
            conversation.append({"role": "user", "content": f"问题: {problem}"})
            
            print(f"🎯 开始处理问题: {problem}")
            
            for iteration in range(self.max_iterations):
                # 发送迭代信息
                iteration_msg = f"第 {iteration + 1} 轮"
                print(f"🔄 {iteration_msg}")
                yield f"data: {json.dumps({'type': 'iteration', 'content': iteration_msg, 'iteration': iteration + 1})}\n\n"
                
                # 获取LLM响应
                print(f"🤖 正在请求LLM响应...")
                response, usage_info = self.client.chat_completion(conversation)
                conversation.append({"role": "assistant", "content": response})
                
                # 解析响应
                thought, action, action_input_or_final = self._parse_response(response)
                
                # 发送推理过程
                if thought:
                    print(f"💭 Thought: {thought}")
                    yield f"data: {json.dumps({'type': 'thought', 'content': thought})}\n\n"
                
                # 检查是否是最终答案
                if action is None and action_input_or_final:
                    print(f"✅ Final Answer: {action_input_or_final}")
                    yield f"data: {json.dumps({'type': 'final_answer', 'content': action_input_or_final})}\n\n"
                    return
                
                # 执行行动
                if action:
                    print(f"🔧 Action: {action}")
                    yield f"data: {json.dumps({'type': 'action', 'content': action})}\n\n"
                    
                    if action_input_or_final:
                        print(f"📝 Action Input: {action_input_or_final}")
                        yield f"data: {json.dumps({'type': 'action_input', 'content': action_input_or_final})}\n\n"
                    
                    # 异步执行工具
                    print(f"⚙️ 正在执行工具: {action}")
                    observation = await self._execute_action(action, action_input_or_final or "")
                    print(f"👀 Observation: {str(observation)}")
                    yield f"data: {json.dumps({'type': 'observation', 'content': str(observation)})}\n\n"
                    
                    # 将观察结果添加到对话
                    conversation.append({"role": "user", "content": f"Observation: {str(observation)}"})
                else:
                    # 如果没有明确的action，可能是格式错误
                    error_msg = "响应格式不正确，请按照 Thought -> Action -> Action Input 的格式"
                    print(f"❌ Error: {error_msg}")
                    yield f"data: {json.dumps({'type': 'error', 'content': error_msg})}\n\n"
                    conversation.append({"role": "user", "content": f"Error: {error_msg}"})
            
            # 达到最大迭代次数
            max_iter_msg = f"达到最大迭代次数 ({self.max_iterations})，未能找到最终答案。"
            print(f"⚠️ Max Iterations: {max_iter_msg}")
            yield f"data: {json.dumps({'type': 'max_iterations', 'content': max_iter_msg})}\n\n"
        except Exception as e:
            error_msg = f"处理流式请求时发生意外错误: {str(e)}"
            print(f"❌ Exception: {error_msg}")
            error_data = {
                "type": "error",
                "content": error_msg
            }
            yield f"data: {json.dumps(error_data)}\n\n"
            import traceback
            traceback.print_exc()

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
                        # 如果是相对路径，相对于项目根目录的 'frontend/uploads' 文件夹
                        # (假设前端上传的文件会放在那里)
                        base_dir = reactagent_root # 使用我们定义的根目录
                        uploads_dir = os.path.join(base_dir, 'frontend', 'uploads')
                        if not os.path.exists(uploads_dir):
                            os.makedirs(uploads_dir)
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

@app.post("/react_solve_stream")
async def react_solve_stream(request: Dict[str, Any]):
    """使用ReAct Agent解决复杂问题 - 流式响应版本"""
    if not react_agent:
        raise HTTPException(status_code=500, detail="ReAct Agent未初始化")
    
    problem = request.get("problem", "")
    files = request.get("files", [])
    
    print(f"🔍 收到流式问题: {problem}")
    print(f"📎 收到文件信息: {files}")
    
    if not problem:
        raise HTTPException(status_code=400, detail="缺少问题描述")
    
    # 处理文件信息
    if files:
        file_info = "\n\n已上传的文件:\n"
        for file in files:
            file_path = file.get('reactAgentPath') or file.get('path') or file.get('localPath')
            file_name = file.get('name') or file.get('originalName', 'Unknown')
            
            if file_path:
                import os
                if not os.path.isabs(file_path):
                    base_dir = reactagent_root
                    uploads_dir = os.path.join(base_dir, 'frontend', 'uploads')
                    if not os.path.exists(uploads_dir):
                        os.makedirs(uploads_dir)
                    file_path = os.path.join(uploads_dir, os.path.basename(file_path))
                
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

    async def generate_stream():
        """生成流式响应"""
        try:
            # 立刻发送一个连接成功消息，防止客户端超时
            yield f"data: {json.dumps({'type': 'status', 'content': '连接已建立，正在准备生成...'})}\n\n"
            await asyncio.sleep(0.01) # 确保消息有机会被发送

            # 创建一个修改过的ReAct Agent实例，用于流式输出
            streaming_agent = StreamingReActAgent(
                deepseek_client=deepseek_client,
                tool_registry=tool_registry,
                max_iterations=10,
                verbose=True,
                enable_memory=True
            )
            
            # 使用异步生成器获取步骤
            async for step_data in streaming_agent.solve_stream(problem):
                yield f"data: {json.dumps(step_data)}\n\n"
                await asyncio.sleep(0.1)  # 小延迟以确保流式效果
                
        except Exception as e:
            error_data = {
                "type": "error",
                "content": f"ReAct求解失败: {str(e)}"
            }
            yield f"data: {json.dumps(error_data)}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control",
            "X-Accel-Buffering": "no"  # 禁用nginx缓冲
        }
    )

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
        "main:app",  # <--- 修改为相对于当前文件
        host="0.0.0.0",
        port=8000,
        reload=True,   # <--- 在开发时建议开启reload
        log_level="info",
        app_dir=os.path.dirname(__file__), # <--- 添加app_dir确保uvicorn找到app
        timeout_keep_alive=0  # 禁用keep-alive超时
    ) 
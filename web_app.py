#!/usr/bin/env python3
"""
Enhanced ReAct Agent Web Application
基于Flask的智能文档处理系统，支持RAG检索、模板处理和文档生成
"""

import os
import sys

# 清除代理设置以避免API连接问题
if 'ALL_PROXY' in os.environ:
    del os.environ['ALL_PROXY']
if 'HTTP_PROXY' in os.environ:
    del os.environ['HTTP_PROXY']
if 'HTTPS_PROXY' in os.environ:
    del os.environ['HTTPS_PROXY']
import json
import uuid
from datetime import datetime
from flask import Flask, request, jsonify, render_template, session, Response
from werkzeug.utils import secure_filename

# 添加src目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

try:
    from src.enhanced_react_agent import EnhancedReActAgent
    from src.deepseek_client import DeepSeekClient
    from src.tools import create_core_tool_registry
except ImportError as e:
    print(f"❌ 导入错误: {e}")
    print("请确保所有必需的模块都在src目录中")
    sys.exit(1)

# Flask应用配置
app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # 在生产环境中使用更安全的密钥

# 文件上传配置
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'docx', 'doc', 'md'}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB

# 确保上传目录存在
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

# 全局变量
agent = None
tool_registry = None

def allowed_file(filename):
    """检查文件扩展名是否允许"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def detect_file_format(file_path):
    """检测文件格式"""
    _, ext = os.path.splitext(file_path)
    ext = ext.lower()
    
    format_mapping = {
        '.txt': 'text',
        '.md': 'markdown', 
        '.pdf': 'pdf',
        '.docx': 'docx',
        '.doc': 'doc'
    }
    
    return format_mapping.get(ext, 'unknown')

def read_file_content(file_path):
    """读取文件内容用于AI分析"""
    try:
        file_format = detect_file_format(file_path)
        
        if file_format == 'text':
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        elif file_format == 'markdown':
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        elif file_format == 'pdf':
            try:
                import PyPDF2
                with open(file_path, 'rb') as f:
                    reader = PyPDF2.PdfReader(f)
                    text = ""
                    for page in reader.pages[:3]:  # 只读前3页用于分析
                        text += page.extract_text() + "\n"
                    return text
            except ImportError:
                return "需要安装PyPDF2库来处理PDF文件"
            except Exception as e:
                return f"PDF文件读取失败: {str(e)}"
        elif file_format in ['docx', 'doc']:
            try:
                from docx import Document
                doc = Document(file_path)
                text = ""
                for paragraph in doc.paragraphs[:10]:  # 只读前10段用于分析
                    text += paragraph.text + "\n"
                return text
            except ImportError:
                return "需要安装python-docx库来处理Word文件"
            except Exception as e:
                return f"Word文件读取失败: {str(e)}"
        else:
            return "不支持的文件格式"
            
    except Exception as e:
        return f"无法读取文件: {str(e)}"

def clean_ansi_codes(text):
    """移除ANSI颜色代码"""
    import re
    # 移除ANSI颜色代码的正则表达式
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)

def stream_chat_response(user_message):
    """增强版ReactAgent流式输出 - 详细显示执行日志和推理过程"""
    import json
    import time
    import logging
    
    try:
        # 发送开始信号
        yield f"data: {json.dumps({'type': 'start', 'content': '🤖 ReactAgent启动中...'})}\n\n"
        
        if not agent:
            yield f"data: {json.dumps({'type': 'error', 'content': 'ReactAgent未初始化'})}\n\n"
            return
        
        # 发送ReactAgent开始信号
        yield f"data: {json.dumps({'type': 'thinking_start', 'content': '🧠 ReactAgent开始推理...'})}\n\n"
        yield f"data: {json.dumps({'type': 'log', 'log_type': 'info', 'content': '📋 系统三大核心功能判断开始'})}\n\n"
        time.sleep(0.2)
        
        # 显示ReactAgent的工作流程
        yield f"data: {json.dumps({'type': 'thinking', 'content': '📝 接收用户请求，进入ReAct循环'})}\n\n"
        yield f"data: {json.dumps({'type': 'log', 'log_type': 'info', 'content': '🔄 ReAct循环: Thought → Action → Observation'})}\n\n"
        time.sleep(0.2)
        
        yield f"data: {json.dumps({'type': 'thinking', 'content': '🛠️ Agent将自主选择合适的工具'})}\n\n"
        yield f"data: {json.dumps({'type': 'log', 'log_type': 'info', 'content': '🎯 开始功能判断: 文件上传/长文档生成/模板文档生成/RAG检索'})}\n\n"
        time.sleep(0.2)
        
        try:
            # 开始处理
            yield f"data: {json.dumps({'type': 'log', 'log_type': 'info', 'content': '🚀 ReactAgent开始处理用户请求'})}\n\n"
            
            # 显示问题分析
            problem_preview = user_message[:50] + "..." if len(user_message) > 50 else user_message
            log_content = f"🤔 开始分析问题: {problem_preview}"
            yield f"data: {json.dumps({'type': 'log', 'log_type': 'info', 'content': log_content})}\n\n"
            
            # 完全通过ReactAgent处理请求
            response = agent.solve(user_message, use_enhanced_framework=False)
            
            # 发送ReactAgent完成信号
            yield f"data: {json.dumps({'type': 'thinking_complete', 'content': '✅ ReactAgent推理完成'})}\n\n"
            yield f"data: {json.dumps({'type': 'log', 'log_type': 'success', 'content': '🎉 任务处理完成，开始输出结果'})}\n\n"
            time.sleep(0.2)
            
            # 开始发送响应内容
            yield f"data: {json.dumps({'type': 'content_start', 'content': '📝 生成最终答案...'})}\n\n"
            time.sleep(0.3)
            
            # 分句发送响应内容，创建打字效果
            if response:
                sentences = []
                current_sentence = ""
                
                for char in response:
                    current_sentence += char
                    if char in '.。!！?？\n':
                        if current_sentence.strip():
                            sentences.append(current_sentence.strip())
                        current_sentence = ""
                
                if current_sentence.strip():
                    sentences.append(current_sentence.strip())
                
                # 流式发送每个句子
                for i, sentence in enumerate(sentences):
                    yield f"data: {json.dumps({'type': 'content', 'content': sentence + (' ' if i < len(sentences) - 1 else '')})}\n\n"
                    time.sleep(0.1)  # 控制打字速度
                
                # 发送完整响应
                yield f"data: {json.dumps({'type': 'content_complete', 'content': response})}\n\n"
            else:
                yield f"data: {json.dumps({'type': 'content', 'content': '抱歉，ReactAgent没有生成有效的回答。'})}\n\n"
                
        except Exception as e:
            error_msg = f"ReactAgent执行过程中出错: {str(e)}"
            yield f"data: {json.dumps({'type': 'error', 'content': error_msg})}\n\n"
        
        # 发送完成信号
        yield f"data: {json.dumps({'type': 'complete', 'content': '🎉 ReactAgent处理完成'})}\n\n"
        
    except Exception as e:
        yield f"data: {json.dumps({'type': 'error', 'content': f'ReactAgent流式处理出错: {str(e)}'})}\n\n"

def create_clean_streaming_agent(user_message):
    """已废弃 - 使用新的简化流式处理"""
    pass

def decide_tool_with_ai(user_message, ai_client):
    """已废弃 - 现在所有工具选择都由ReactAgent内部处理"""
    # 这个函数已经不再使用，因为所有工具选择都由ReactAgent通过ReAct循环处理
    pass

def fallback_tool_decision(user_message):
    """已废弃 - 现在所有工具选择都由ReactAgent内部处理"""
    # 这个函数已经不再使用，因为所有工具选择都由ReactAgent通过ReAct循环处理
    pass

def detect_file_type_with_ai(filename, file_path, agent):
    """智能检测文件类型：模板文档(template) or 资料文档(material)"""
    filename_lower = filename.lower()
    
    # 读取文件内容进行分析
    file_content = read_file_content(file_path)
    
    if "无法读取" in file_content or "不支持" in file_content:
        return 'unknown', file_content
    
    # 🔍 先进行规则预检 - 基于文件名的快速判断
    template_name_keywords = [
        '模板', 'template', '样本', 'sample', 'form', '表单', 
        '申请表', '登记表', '记录表', '审核表', '复核', '检查表',
        '清单', 'checklist', '格式', '空白'
    ]
    
    material_name_keywords = [
        '资料', '数据', 'data', 'material', '会议', 'meeting', 
        '报告', 'report', '纪要', 'minutes', '方案', '计划',
        '总结', '分析', '研究', '文件', '档案'
    ]
    
    # 检查文件名
    for keyword in template_name_keywords:
        if keyword in filename_lower:
            return 'template', f'文件名包含模板关键词: {keyword}'
    
    for keyword in material_name_keywords:
        if keyword in filename_lower:
            return 'material', f'文件名包含资料关键词: {keyword}'
    
    # 🤖 AI深度分析文件内容
    ai_prompt = f"""
请分析以下文件，判断这是"模板文档"还是"资料文档"：

文件名：{filename}

文件内容（前800字符）：
{file_content[:800]}

判断标准：
【模板文档特征】：
- 包含待填写的空白字段或占位符
- 有填写说明或字段标签
- 结构化的表单或表格
- 空白的记录表、申请表、审核表等
- 包含如：_____、【】、（）、{{字段名称}}等占位符

【资料文档特征】：
- 包含具体的信息和数据
- 已填写的内容和完整信息
- 会议记录、报告、方案等实际资料
- 不是用来填写，而是用来阅读的内容

请仔细分析内容特征，优先基于内容而非文件名判断。
请只回答"template"或"material"，不要其他解释。
"""
    
    try:
        if agent and hasattr(agent, 'client') and agent.client:
            # 使用AI客户端进行智能判断
            try:
                ai_response = agent.client.chat([{"role": "user", "content": ai_prompt}])
                ai_result = ai_response.strip().lower()
                
                if 'template' in ai_result:
                    return 'template', 'AI分析文件内容判断为模板文档'
                elif 'material' in ai_result:
                    return 'material', 'AI分析文件内容判断为资料文档'
                else:
                    # AI回答不明确，使用内容规则判断
                    return fallback_content_analysis(file_content)
                    
            except Exception as e:
                print(f"AI分析失败: {e}")
                return fallback_content_analysis(file_content)
        else:
            # Agent未初始化，使用内容规则分析
            return fallback_content_analysis(file_content)
            
    except Exception as e:
        return 'unknown', f'文件类型检测失败：{str(e)}'

def fallback_content_analysis(content):
    """备用内容分析 - 基于关键词和模式的规则判断"""
    content_lower = content.lower()
    
    # 模板文档的内容特征
    template_patterns = [
        '____', '＿＿', '______', '___',  # 下划线填空
        '【】', '（）', '()', '[ ]',      # 括号占位符
        '填写', '填入', '请填', '待填',
        '姓名：', '日期：', '地点：', 
        '签名：', '审核：', '复核：',
        '申请人：', '负责人：'
    ]
    
    # 资料文档的内容特征
    material_patterns = [
        '会议时间', '参会人员', '会议内容',
        '项目名称', '负责部门', '完成情况',
        '分析结果', '建议方案', '总结如下',
        '根据调研', '经过讨论', '决定如下'
    ]
    
    # 统计特征出现次数
    template_score = 0
    material_score = 0
    
    for pattern in template_patterns:
        if pattern in content_lower:
            template_score += content_lower.count(pattern)
    
    for pattern in material_patterns:
        if pattern in content_lower:
            material_score += 1
    
    # 额外检查：空白字段密度
    blank_patterns = ['____', '＿＿', '【】', '（）']
    blank_count = sum(content_lower.count(pattern) for pattern in blank_patterns)
    
    # 判断逻辑
    if template_score > material_score or blank_count >= 3:
        return 'template', f'内容特征判断为模板文档 (模板得分:{template_score}, 空白字段:{blank_count})'
    elif material_score > 0:
        return 'material', f'内容特征判断为资料文档 (资料得分:{material_score})'
    else:
        # 默认判断：如果内容较短且包含结构化字段，倾向于模板
        if len(content) < 500 and any(word in content_lower for word in ['：', ':', '姓名', '日期', '地点']):
            return 'template', '短内容包含结构化字段，推测为模板文档'
        else:
            return 'material', '默认判断为资料文档'

def initialize_agent():
    """初始化Agent"""
    global agent, tool_registry
    
    try:
        # 初始化DeepSeek客户端
        deepseek_client = DeepSeekClient()
        print("✅ DeepSeek AI客户端初始化成功")
        
        # 创建核心工具注册表
        tool_registry = create_core_tool_registry(deepseek_client)
        print("✅ 核心三工具架构初始化成功")
        
        # 初始化增强版ReAct Agent
        agent = EnhancedReActAgent(
            deepseek_client=deepseek_client,
            tool_registry=tool_registry,
            verbose=True
        )
        print("✅ Enhanced ReAct Agent 初始化成功")
        return True
        
    except Exception as e:
        print(f"❌ Agent初始化失败: {e}")
        return False

@app.route('/')
def index():
    """主页 - 对话界面"""
    return render_template('chat.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    """处理对话请求"""
    try:
        data = request.get_json()
        user_message = data.get('message', '').strip()
        stream = data.get('stream', False)  # 是否启用流式输出
        
        if not user_message:
            return jsonify({
                'success': False,
                'error': '请输入有效的消息'
            })
        
        # 检查Agent是否已初始化
        if agent is None:
            return jsonify({
                'success': False,
                'error': 'Agent未初始化，请刷新页面重试'
            })
        
        # 统一使用ReAct Agent处理所有对话
        # Agent会通过Thought → Action的方式自己决定调用哪个工具
        print(f"🤖 ReAct Agent处理: {user_message}")
        
        if stream:
            # 流式响应
            return Response(
                stream_chat_response(user_message),
                mimetype='text/plain',
                headers={
                    'Cache-Control': 'no-cache',
                    'Connection': 'keep-alive',
                    'Access-Control-Allow-Origin': '*'
                }
            )
        else:
            # 非流式响应
            response = agent.solve(user_message, use_enhanced_framework=False)
            
            # 获取会话历史（如果需要）
            if 'chat_history' not in session:
                session['chat_history'] = []
            
            # 添加到会话历史
            session['chat_history'].append({
                'timestamp': datetime.now().isoformat(),
                'user_message': user_message,
                'agent_response': response
            })
            
            return jsonify({
                'success': True,
                'response': response,
                'timestamp': datetime.now().isoformat()
            })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'处理请求时出错: {str(e)}'
        })

@app.route('/api/chat/stream', methods=['POST'])
def chat_stream():
    """专门的流式聊天响应路由"""
    try:
        data = request.get_json()
        user_message = data.get('message', '').strip()
        
        if not user_message:
            return jsonify({
                'success': False,
                'error': '请输入有效的消息'
            }), 400
        
        # 检查Agent是否已初始化
        if agent is None:
            return jsonify({
                'success': False,
                'error': 'Agent未初始化，请刷新页面重试'
            }), 500
        
        print(f"🤖 流式ReAct Agent处理: {user_message}")
        
        # 返回流式响应
        return Response(
            stream_chat_response(user_message),
            content_type='text/event-stream; charset=utf-8',
            headers={
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'POST'
            }
        )
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'流式请求处理失败: {str(e)}'
        }), 500

@app.route('/api/system/status')
def system_status():
    """获取系统状态"""
    try:
        status = {
            'agent_initialized': agent is not None,
            'tools_count': len(tool_registry.tools) if tool_registry else 0,
            'tools': []
        }
        
        if tool_registry:
            status['tools'] = [
                {
                    'name': tool.name,
                    'description': tool.description
                }
                for tool in tool_registry.tools.values()
            ]
        
        return jsonify(status)
        
    except Exception as e:
        return jsonify({
            'error': f'获取系统状态失败: {str(e)}'
        })

@app.route('/api/system/tools')
def get_tools():
    """获取可用工具列表"""
    try:
        if not tool_registry:
            return jsonify({
                'success': False,
                'error': '工具注册表未初始化'
            })
        
        tools = []
        for tool_name, tool in tool_registry.tools.items():
            tools.append({
                'name': tool_name,
                'description': tool.description,
                'parameters': getattr(tool, 'parameters', {})
            })
        
        return jsonify({
            'success': True,
            'tools': tools,
            'count': len(tools)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'获取工具列表失败: {str(e)}'
        })

@app.route('/api/chat/clear', methods=['POST'])
def clear_chat():
    """清空聊天历史"""
    try:
        session.pop('chat_history', None)
        return jsonify({
            'success': True,
            'message': '聊天历史已清空'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'清空聊天历史失败: {str(e)}'
        })

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """智能文件上传处理 - 自动判断文档类型并调用相应工具"""
    try:
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': '未选择文件'
            })
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': '未选择文件'
            })
        
        if not allowed_file(file.filename):
            return jsonify({
                'success': False,
                'error': f'不支持的文件类型。支持的格式: {", ".join(ALLOWED_EXTENSIONS)}'
            })
        
        # 保存文件，保留原始文件名（包括中文）
        original_filename = file.filename or 'unknown_file'
        
        # 只对危险字符进行清理，保留中文和常规字符
        import re
        # 移除路径分隔符和危险字符，但保留中文、数字、字母、点、横线、下划线、括号
        safe_filename = re.sub(r'[<>:"/\\|?*]', '', original_filename)
        safe_filename = safe_filename.strip()
        
        # 如果文件名已存在，添加时间戳后缀
        import time
        if os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], safe_filename)):
            base_name, ext = os.path.splitext(safe_filename)
            timestamp = int(time.time())
            final_filename = f"{base_name}_{timestamp}{ext}"
        else:
            final_filename = safe_filename
        
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], final_filename)
        file.save(file_path)
        
        print(f"✅ 文件保存成功: {final_filename}")
        
        # 🔍 智能文档类型判断
        file_type, detection_reason = detect_file_type_with_ai(original_filename, file_path, agent)
        
        print(f"📋 文档类型判断结果: {file_type} - {detection_reason}")
        
        # 🤖 根据文档类型自动生成处理指令
        if file_type == 'template':
            # 模板文档 - 调用模板转换工具
            processing_message = f"""我刚刚上传了一个模板文档：
📁 文件名：{original_filename}
📂 保存路径：{file_path}
🔍 判断依据：{detection_reason}

请使用ReAct循环处理这个模板文档：
1. Thought：分析这是一个模板文档，需要提取其结构和占位符
2. Action：template_conversion
3. Action Input：{file_path}
4. 根据Observation结果继续推理和行动

请完全按照ReAct循环（Thought → Action → Observation）来处理这个模板文档。"""
            
            processing_type = "模板转换"
            tool_name = "template_conversion"
            
        elif file_type == 'material':
            # 资料文档 - 调用RAG工具
            processing_message = f"""我刚刚上传了一个资料文档：
📁 文件名：{original_filename}
📂 保存路径：{file_path}
🔍 判断依据：{detection_reason}

请使用ReAct循环处理这个资料文档：
1. Thought：分析这是一个资料文档，需要进行embedding处理以便后续检索
2. Action：rag_tool
3. Action Input：{{"action": "upload", "file_path": "{file_path}"}}
4. 根据Observation结果继续推理和行动

请完全按照ReAct循环（Thought → Action → Observation）来处理这个资料文档。"""
            
            processing_type = "RAG处理"
            tool_name = "rag_tool"
            
        else:
            # 未知类型 - 让ReAct Agent自己判断
            processing_message = f"""我刚刚上传了一个文件：
📁 文件名：{original_filename}
📂 保存路径：{file_path}
⚠️ 类型判断：{detection_reason}

请使用ReAct循环分析并处理这个文件：
1. Thought：分析文件内容和结构，判断是模板文档还是资料文档
2. Action：根据判断结果选择合适的工具（template_conversion 或 rag_tool）
3. 根据Observation结果继续推理和行动

请完全按照ReAct循环（Thought → Action → Observation）来处理。"""
            
            processing_type = "智能分析"
            tool_name = "auto_detect"
        
        return jsonify({
            'success': True,
            'message': f'文件 {original_filename} 上传成功',
            'filename': final_filename,
            'original_filename': original_filename,
            'file_path': file_path,
            'file_type': file_type,
            'detection_reason': detection_reason,
            'processing_type': processing_type,
            'suggested_tool': tool_name,
            'trigger_processing': True,
            'processing_message': processing_message
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'文件上传失败: {str(e)}'
        })

@app.errorhandler(404)
def not_found(error):
    """404错误处理"""
    return jsonify({
        'success': False,
        'error': '请求的资源未找到'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """500错误处理"""
    return jsonify({
        'success': False,
        'error': '服务器内部错误'
    }), 500

if __name__ == '__main__':
    print("🚀 启动Enhanced ReAct Agent Web应用...")
    
    # 初始化Agent
    if initialize_agent():
        print("🌐 Web服务器启动中...")
        print("📍 访问地址: http://localhost:5000")
        print("⚠️  按Ctrl+C停止服务器")
        
        # 启动Flask应用
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=False,  # 生产环境中设为False
            threaded=True
        )
    else:
        print("❌ Agent初始化失败，无法启动Web服务器")
        sys.exit(1) 
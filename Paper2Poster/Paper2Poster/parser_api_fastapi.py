import os
import shutil
import tempfile
import json
import traceback
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware

# 导入解析智能体
try:
    from parser_agent_openrouter import OpenRouterParserAgent, list_available_models
    PARSER_AVAILABLE = True
except ImportError as e:
    PARSER_AVAILABLE = False
    print(f"Warning: Cannot import parser agent: {e}")

app = FastAPI(title="PDF Parser API", description="PDF解析智能体Web接口", version="1.0.0")

# 允许跨域，方便本地前端调试
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def main_page():
    return HTMLResponse(
        """
        <!DOCTYPE html>
        <html>
        <head>
            <title>PDF Poster Parser</title>
            <style>
                body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
                .container { background: #f5f5f5; padding: 20px; border-radius: 10px; }
                .form-group { margin: 15px 0; }
                input, select, button { padding: 10px; margin: 5px; border: 1px solid #ddd; border-radius: 5px; }
                button { background: #007bff; color: white; cursor: pointer; }
                button:hover { background: #0056b3; }
                .status { margin: 20px 0; padding: 10px; border-radius: 5px; }
                .success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
                .error { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
                .loading { background: #d1ecf1; color: #0c5460; border: 1px solid #bee5eb; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>📄 PDF Poster Parser</h1>
                <p>上传PDF文件，自动解析为Poster结构化内容</p>
                
                <form id="uploadForm" enctype="multipart/form-data">
                    <div class="form-group">
                        <label><strong>选择PDF文件:</strong></label><br>
                        <input name="file" type="file" accept="application/pdf" required>
                    </div>
                    
                    <div class="form-group">
                        <label><strong>选择模型:</strong></label><br>
                        <select name="model">
                            <option value="gpt-4o">GPT-4o (推荐)</option>
                            <option value="gpt-4o-mini">GPT-4o Mini</option>
                            <option value="claude-3.5-sonnet">Claude 3.5 Sonnet</option>
                            <option value="claude-3-haiku">Claude 3 Haiku</option>
                            <option value="llama-3.1-70b">Llama 3.1 70B</option>
                            <option value="llama-3.1-8b">Llama 3.1 8B</option>
                            <option value="qwen2.5-32b">Qwen2.5 32B</option>
                            <option value="qwen2.5-7b">Qwen2.5 7B</option>
                        </select>
                    </div>
                    
                    <button type="submit">🚀 上传并解析</button>
                </form>
                
                <div id="status"></div>
                <div id="result"></div>
                
                <script>
                document.getElementById('uploadForm').addEventListener('submit', async function(e) {
                    e.preventDefault();
                    
                    const formData = new FormData(this);
                    const statusDiv = document.getElementById('status');
                    const resultDiv = document.getElementById('result');
                    
                    statusDiv.innerHTML = '<div class="loading">📤 正在上传和解析PDF，请耐心等待...</div>';
                    resultDiv.innerHTML = '';
                    
                    try {
                        const response = await fetch('/parse', {
                            method: 'POST',
                            body: formData
                        });
                        
                        const result = await response.json();
                        
                        if (result.success) {
                            statusDiv.innerHTML = '<div class="success">✅ 解析成功！</div>';
                            resultDiv.innerHTML = `
                                <h3>📊 解析结果</h3>
                                <p><strong>模型:</strong> ${result.stats.model_used}</p>
                                <p><strong>Sections:</strong> ${result.stats.sections_count}个</p>
                                <p><strong>图片:</strong> ${result.stats.images_count}个</p>
                                <p><strong>表格:</strong> ${result.stats.tables_count}个</p>
                                <p><strong>总文本长度:</strong> ${result.stats.total_text_length.toLocaleString()}字符</p>
                                
                                <h4>📋 Section标题:</h4>
                                <ul>
                                    ${result.stats.section_titles.map((title, i) => `<li>${i+1}. ${title}</li>`).join('')}
                                </ul>
                                
                                <details>
                                    <summary><strong>📄 完整JSON结果 (点击展开)</strong></summary>
                                    <pre style="background: #f8f9fa; padding: 15px; border-radius: 5px; overflow: auto; max-height: 400px;">${JSON.stringify(result.content, null, 2)}</pre>
                                </details>
                            `;
                        } else {
                            statusDiv.innerHTML = '<div class="error">❌ 解析失败: ' + result.error + '</div>';
                        }
                    } catch (error) {
                        statusDiv.innerHTML = '<div class="error">❌ 网络错误: ' + error.message + '</div>';
                    }
                });
                </script>
                
                <hr style="margin: 30px 0;">
                <p><strong>📚 API接口:</strong></p>
                <ul>
                    <li>POST /parse - 解析PDF文件</li>
                    <li>GET /models - 获取可用模型列表</li>
                    <li>GET /docs - API文档</li>
                </ul>
            </div>
        </body>
        </html>
        """
    )

@app.post("/parse")
async def parse_pdf(file: UploadFile = File(...), model: str = Form("gpt-4o")):
    """解析PDF文件"""
    
    # 检查解析智能体是否可用
    if not PARSER_AVAILABLE:
        raise HTTPException(status_code=500, detail="解析智能体不可用，请检查依赖")
    
    # 检查API密钥
    if not os.getenv('OPENAI_API_KEY'):
        raise HTTPException(status_code=500, detail="未设置OPENAI_API_KEY环境变量")
    
    # 检查文件
    if not file.filename or not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="请上传PDF文件")
    
    try:
        # 1. 保存上传的PDF到临时文件
        with tempfile.TemporaryDirectory() as tmpdir:
            pdf_path = os.path.join(tmpdir, file.filename or "uploaded.pdf")
            with open(pdf_path, "wb") as f:
                shutil.copyfileobj(file.file, f)

            # 2. 构造输出目录
            output_dir = os.path.join(tmpdir, "output")
            os.makedirs(output_dir, exist_ok=True)

            # 3. 创建解析智能体并解析
            parser_agent = OpenRouterParserAgent(model_name=model)
            content_json, images, tables = parser_agent.parse_raw(pdf_path, output_dir)
            
            # 4. 获取统计信息
            stats = parser_agent.get_parsing_stats(content_json, images, tables)

            return JSONResponse(content={
                "success": True,
                "content": content_json,
                "images": images,
                "tables": tables,
                "stats": stats
            })
            
    except Exception as e:
        error_msg = f"解析失败: {str(e)}"
        print(f"Error: {error_msg}")
        traceback.print_exc()
        return JSONResponse(
            content={"success": False, "error": error_msg},
            status_code=500
        )


@app.get("/models")
def get_models():
    """获取可用模型列表"""
    models = {
        "OpenAI模型": ["gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo"],
        "Anthropic模型": ["claude-3.5-sonnet", "claude-3-haiku"],
        "Meta模型": ["llama-3.1-8b", "llama-3.1-70b"],
        "Google模型": ["gemini-pro"],
        "开源模型": ["qwen2.5-7b", "qwen2.5-32b"]
    }
    
    return JSONResponse(content={
        "success": True,
        "models": models,
        "total_models": sum(len(m) for m in models.values())
    })


@app.get("/health")
def health_check():
    """健康检查"""
    return JSONResponse(content={
        "status": "healthy",
        "parser_available": PARSER_AVAILABLE,
        "api_key_set": bool(os.getenv('OPENAI_API_KEY'))
    }) 
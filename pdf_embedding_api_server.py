#!/usr/bin/env python3
"""
PDF Embedding API Server - 为前端测试提供API接口
提供PDF embedding搜索和统计信息的RESTful API
"""

import os
import json
import traceback
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from src.pdf_embedding_tool import PDFEmbeddingTool

# 创建Flask应用
app = Flask(__name__)
CORS(app)  # 启用跨域支持

# 初始化PDF embedding工具
pdf_embedding_tool = None

def init_pdf_embedding_tool():
    """初始化PDF embedding工具"""
    global pdf_embedding_tool
    try:
        pdf_embedding_tool = PDFEmbeddingTool()
        print("✅ PDF Embedding工具初始化成功")
        return True
    except Exception as e:
        print(f"❌ PDF Embedding工具初始化失败: {e}")
        return False

@app.route('/')
def index():
    """返回测试页面"""
    return send_from_directory('.', 'pdf_embedding_test_frontend.html')

@app.route('/api/pdf_embedding_stats', methods=['GET'])
def get_stats():
    """获取PDF embedding统计信息"""
    try:
        if not pdf_embedding_tool:
            return jsonify({
                'success': False,
                'message': 'PDF embedding工具未初始化'
            }), 500
        
        # 调用工具获取统计信息
        result = pdf_embedding_tool.execute(action="stats")
        result_data = json.loads(result)
        
        if result_data.get('status') == 'success':
            return jsonify({
                'success': True,
                'statistics': result_data.get('statistics', {}),
                'message': result_data.get('message', '')
            })
        else:
            return jsonify({
                'success': False,
                'message': result_data.get('message', '获取统计信息失败')
            }), 500
            
    except Exception as e:
        print(f"❌ 获取统计信息出错: {e}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'服务器错误: {str(e)}'
        }), 500

@app.route('/api/pdf_embedding_search', methods=['POST'])
def search_embeddings():
    """搜索PDF embedding内容"""
    try:
        if not pdf_embedding_tool:
            return jsonify({
                'success': False,
                'message': 'PDF embedding工具未初始化'
            }), 500
        
        # 获取请求参数
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': '请求数据格式错误'
            }), 400
        
        query = data.get('query', '').strip()
        if not query:
            return jsonify({
                'success': False,
                'message': '搜索查询不能为空'
            }), 400
        
        content_type = data.get('content_type', 'all')
        top_k = data.get('top_k', 5)
        source_file_filter = data.get('source_file_filter')
        
        # 验证参数
        if content_type not in ['text', 'image', 'all']:
            return jsonify({
                'success': False,
                'message': '无效的内容类型'
            }), 400
        
        if not isinstance(top_k, int) or top_k < 1 or top_k > 50:
            return jsonify({
                'success': False,
                'message': '结果数量必须在1-50之间'
            }), 400
        
        # 构建搜索参数
        search_params = {
            'action': 'search',
            'query': query,
            'content_type': content_type,
            'top_k': top_k
        }
        
        if source_file_filter:
            search_params['source_file_filter'] = source_file_filter
        
        # 执行搜索
        result = pdf_embedding_tool.execute(**search_params)
        result_data = json.loads(result)
        
        if result_data.get('status') == 'success':
            return jsonify({
                'success': True,
                'query': result_data.get('query'),
                'search_scope': result_data.get('search_scope'),
                'total_results': result_data.get('total_results', 0),
                'text_results': result_data.get('text_results', 0),
                'image_results': result_data.get('image_results', 0),
                'results': result_data.get('results', []),
                'message': result_data.get('message', '')
            })
        else:
            return jsonify({
                'success': False,
                'message': result_data.get('message', '搜索失败')
            }), 500
            
    except Exception as e:
        print(f"❌ 搜索出错: {e}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'服务器错误: {str(e)}'
        }), 500

@app.route('/api/pdf_embedding_embed', methods=['POST'])
def embed_pdf():
    """对PDF解析结果进行embedding"""
    try:
        if not pdf_embedding_tool:
            return jsonify({
                'success': False,
                'message': 'PDF embedding工具未初始化'
            }), 500
        
        # 获取请求参数
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': '请求数据格式错误'
            }), 400
        
        parser_output_dir = data.get('parser_output_dir', '').strip()
        if not parser_output_dir:
            return jsonify({
                'success': False,
                'message': '解析器输出目录不能为空'
            }), 400
        
        if not os.path.exists(parser_output_dir):
            return jsonify({
                'success': False,
                'message': f'目录不存在: {parser_output_dir}'
            }), 400
        
        # 执行embedding
        result = pdf_embedding_tool.execute(
            action='embed',
            parser_output_dir=parser_output_dir
        )
        result_data = json.loads(result)
        
        if result_data.get('status') == 'success':
            return jsonify({
                'success': True,
                'statistics': result_data.get('statistics', {}),
                'input_directory': result_data.get('input_directory'),
                'message': result_data.get('message', '')
            })
        else:
            return jsonify({
                'success': False,
                'message': result_data.get('message', 'Embedding失败')
            }), 500
            
    except Exception as e:
        print(f"❌ Embedding出错: {e}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'服务器错误: {str(e)}'
        }), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    return jsonify({
        'success': True,
        'message': 'PDF Embedding API服务器运行正常',
        'tool_status': pdf_embedding_tool is not None
    })

@app.errorhandler(404)
def not_found(error):
    """404错误处理"""
    return jsonify({
        'success': False,
        'message': '接口不存在'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """500错误处理"""
    return jsonify({
        'success': False,
        'message': '服务器内部错误'
    }), 500

def main():
    """主函数"""
    print("🚀 启动PDF Embedding API服务器")
    print("=" * 50)
    
    # 初始化PDF embedding工具
    if not init_pdf_embedding_tool():
        print("❌ 无法启动服务器：PDF embedding工具初始化失败")
        return
    
    # 检查前端文件是否存在
    frontend_file = 'pdf_embedding_test_frontend.html'
    if not os.path.exists(frontend_file):
        print(f"⚠️ 前端文件不存在: {frontend_file}")
        print("请确保前端文件在当前目录中")
    
    print("\n🔧 API接口列表:")
    print("   GET  /                      - 测试页面")
    print("   GET  /api/health            - 健康检查")
    print("   GET  /api/pdf_embedding_stats - 获取统计信息")
    print("   POST /api/pdf_embedding_search - 搜索内容")
    print("   POST /api/pdf_embedding_embed - 执行embedding")
    
    print("\n📊 启动参数:")
    print("   主机: localhost")
    print("   端口: 5000")
    print("   调试模式: 开启")
    
    print("\n🌐 访问地址:")
    print("   前端测试页面: http://localhost:5000")
    print("   API文档: http://localhost:5000/api/health")
    
    print("\n✅ 服务器启动中...")
    print("=" * 50)
    
    # 启动Flask服务器
    try:
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=True,
            threaded=True
        )
    except KeyboardInterrupt:
        print("\n🛑 服务器已停止")
    except Exception as e:
        print(f"❌ 服务器启动失败: {e}")

if __name__ == '__main__':
    main() 
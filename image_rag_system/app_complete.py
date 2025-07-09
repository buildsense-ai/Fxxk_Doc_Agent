#!/usr/bin/env python3
"""
完整的图片RAG系统
- 使用BGE-M3进行高质量文本嵌入
- 集成Gemini 2.5 Pro生成AI图片描述
- 支持基于文本描述的图片检索
- ChromaDB向量数据库存储
"""

import sys
import os
import uuid
import io
import json
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

# 加载环境变量
from dotenv import load_dotenv
load_dotenv()

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

import uvicorn
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
import logging
from PIL import Image
import numpy as np

# 导入服务
from app.services.embedding_service_advanced import AdvancedEmbeddingService
from app.services.embedding_service_simple import EmbeddingService as SimpleEmbeddingService
from app.services.gemini_service import GeminiDescriptionService
from app.services.vector_service import VectorService
from app.services.database_service import DatabaseService
from app.services.minio_service import MinIOService

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title="图片RAG系统",
    description="基于BGE-M3文本嵌入和Gemini描述的图片检索系统",
    version="2.0.0"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局变量存储服务实例
embedding_service = None
vector_service = None
gemini_service = None  # Gemini图片描述服务
database_service = None  # 数据库服务
minio_service = None  # MinIO对象存储服务
image_storage = {}  # 简化的内存存储
search_index = {}   # 简化的搜索索引
is_advanced_embedding = False  # 标记是否使用高级嵌入

def get_text_embedding(text: str) -> np.ndarray:
    """统一的文本嵌入接口"""
    global embedding_service, is_advanced_embedding
    
    if not embedding_service:
        raise ValueError("嵌入服务未初始化")
    
    if is_advanced_embedding:
        # 使用高级嵌入服务API
        return embedding_service.embed_documents([text])[0]
    else:
        # 使用简化嵌入服务API
        return embedding_service.encode_text(text)

def get_query_embedding(query: str) -> np.ndarray:
    """统一的查询嵌入接口"""
    global embedding_service, is_advanced_embedding
    
    if not embedding_service:
        raise ValueError("嵌入服务未初始化")
    
    if is_advanced_embedding:
        # 使用高级嵌入服务API
        return embedding_service.embed_query(query)
    else:
        # 使用简化嵌入服务API
        return embedding_service.encode_text(query)

def compute_similarity_unified(query_embedding: np.ndarray, doc_embedding: np.ndarray) -> float:
    """统一的相似度计算接口"""
    global embedding_service, is_advanced_embedding
    
    if is_advanced_embedding and hasattr(embedding_service, 'compute_similarity'):
        # 使用高级嵌入服务的相似度计算
        return float(embedding_service.compute_similarity(query_embedding, doc_embedding.reshape(1, -1))[0])
    else:
        # 使用简化的余弦相似度计算
        return float(np.dot(query_embedding, doc_embedding) / (np.linalg.norm(query_embedding) * np.linalg.norm(doc_embedding)))

def initialize_services():
    """初始化所有服务"""
    global embedding_service, vector_service, gemini_service, database_service, minio_service, is_advanced_embedding
    
    logger.info("🚀 初始化服务...")
    
    # 1. 初始化嵌入服务
    try:
        logger.info("🔧 尝试初始化高质量嵌入服务...")
        embedding_service = AdvancedEmbeddingService()
        
        if embedding_service.is_available():
            logger.info("✅ 使用高质量嵌入服务 (BGE-M3)")
            is_advanced_embedding = True
        else:
            logger.warning("⚠️ 高质量嵌入服务不可用，使用简化服务")
            embedding_service = SimpleEmbeddingService()
            is_advanced_embedding = False
            
    except Exception as e:
        logger.error(f"❌ 高质量嵌入服务初始化失败: {e}")
        logger.info("🔄 回退到简化嵌入服务")
        embedding_service = SimpleEmbeddingService()
        is_advanced_embedding = False
    
    # 2. 初始化Gemini服务
    try:
        logger.info("🤖 初始化Gemini描述生成服务...")
        gemini_service = GeminiDescriptionService()
        
        if gemini_service.is_available():
            logger.info("✅ Gemini 2.5 Pro服务可用")
        else:
            logger.warning("⚠️ Gemini服务不可用，将使用简化描述")
            
    except Exception as e:
        logger.error(f"❌ Gemini服务初始化失败: {e}")
        gemini_service = None
    
    # 3. 初始化向量服务
    try:
        logger.info("🗄️ 初始化向量数据库服务...")
        vector_service = VectorService()
        logger.info("✅ ChromaDB服务初始化成功")
    except Exception as e:
        logger.error(f"❌ ChromaDB服务初始化失败: {e}")
        vector_service = None
    
    # 4. 初始化数据库服务
    try:
        logger.info("🗃️ 初始化MySQL数据库服务...")
        database_service = DatabaseService()
        logger.info("✅ MySQL数据库服务初始化成功")
    except Exception as e:
        logger.error(f"❌ 数据库服务初始化失败: {e}")
        database_service = None
    
    # 5. 初始化MinIO服务
    try:
        logger.info("📦 初始化MinIO对象存储服务...")
        minio_service = MinIOService()
        
        if minio_service.is_available():
            logger.info("✅ MinIO对象存储服务初始化成功")
        else:
            logger.warning("⚠️ MinIO服务不可用，将使用内存存储")
            
    except Exception as e:
        logger.error(f"❌ MinIO服务初始化失败: {e}")
        minio_service = None

def compute_similarity(vec1, vec2):
    """计算两个向量的余弦相似度"""
    return float(np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2)))

@app.on_event("startup")
async def startup_event():
    """应用启动时初始化服务"""
    initialize_services()

@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "图片RAG系统",
        "version": "2.0.0",
        "description": "基于BGE-M3文本嵌入和Gemini描述的图片检索系统",
        "endpoints": {
            "上传图片": "/upload/image",
            "搜索图片": "/search/images",
            "系统状态": "/stats",
            "API文档": "/docs",
            "演示页面": "/demo"
        }
    }

@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "services": {
            "embedding": "available" if embedding_service else "unavailable",
            "gemini": "available" if (gemini_service and gemini_service.is_available()) else "unavailable",
            "vector_db": "available" if vector_service else "unavailable",
            "database": "available" if (database_service and database_service.is_available()) else "unavailable",
            "minio": "available" if (minio_service and minio_service.is_available()) else "unavailable"
        },
        "stats": {
            "total_images": len(image_storage),
            "search_index_size": len(search_index)
        }
    }

@app.post("/upload/image")
async def upload_image(
    file: UploadFile = File(...),
    description: Optional[str] = Form(None)
):
    """上传图片并生成AI描述"""
    try:
        # 验证文件类型
        if not file.content_type or not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="文件必须是图片格式")
        
        # 读取文件数据
        file_data = await file.read()
        
        # 验证图片
        try:
            pil_image = Image.open(io.BytesIO(file_data))
            width, height = pil_image.size
            format_name = pil_image.format
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"无效的图片文件: {e}")
        
        # 生成唯一ID
        image_id = str(uuid.uuid4())
        
        # 保存图片到临时文件（用于Gemini分析）
        temp_image_path = f"temp_{image_id}.jpg"
        pil_image.save(temp_image_path, format='JPEG', quality=95)
        
        # 准备描述文本
        user_description = description or ""
        ai_description = ""
        
        # # 使用Gemini生成AI描述
        # if gemini_service and gemini_service.is_available():
        #     try:
        #         logger.info(f"🤖 使用Gemini为图片 {image_id} 生成AI描述...")
        #         gemini_result = gemini_service.generate_description(temp_image_path, user_description)
                
        #         if gemini_result["success"]:
        #             ai_description = gemini_result["ai_description"]
        #             logger.info(f"✅ AI描述生成成功: {len(ai_description)} 字符")
        #         else:
        #             logger.warning(f"⚠️ AI描述生成失败: {gemini_result['error']}")
        #             ai_description = gemini_result.get("ai_description", "")
                    
        #     except Exception as e:
        #         logger.error(f"❌ Gemini描述生成异常: {e}")
        #         ai_description = ""
        
        # 清理临时文件
        try:
            os.remove(temp_image_path)
        except:
            pass
        
        # 合并描述文本
        combined_description = ""
        if user_description and ai_description:
            combined_description = f"用户描述: {user_description}\n\nAI描述: {ai_description}"
        elif user_description:
            combined_description = f"用户描述: {user_description}"
        elif ai_description:
            combined_description = f"AI描述: {ai_description}"
        else:
            combined_description = f"图片文件: {file.filename}"
        
        # 生成文本嵌入
        if not embedding_service:
            raise HTTPException(status_code=500, detail="嵌入服务未初始化")
        
        logger.info(f"📝 为图片 {image_id} 生成文本嵌入...")
        
        # 使用统一的文本嵌入接口
        text_embedding = get_text_embedding(combined_description)
        
        # 保存到内存存储（向后兼容）
        image_record = {
            "image_id": image_id,
            "filename": file.filename,
            "user_description": user_description,
            "ai_description": ai_description,
            "combined_description": combined_description,
            "file_size": len(file_data),
            "width": width,
            "height": height,
            "format": format_name,
            "content_type": file.content_type,
            "upload_time": time.time(),
            "text_embedding": text_embedding.tolist(),
            "file_data": file_data
        }
        
        image_storage[image_id] = image_record
        
        # 上传到MinIO
        file_url = None
        if minio_service and minio_service.is_available():
            try:
                upload_result = minio_service.upload_image(
                    image_data=file_data,
                    filename=file.filename or "unknown.jpg",
                    content_type=file.content_type,
                    image_id=image_id
                )
                
                if upload_result and upload_result.get('success'):
                    file_url = upload_result['file_url']
                    logger.info(f"✅ 图片已上传到MinIO: {file_url}")
                else:
                    logger.warning(f"⚠️ MinIO上传失败: {image_id}")
                    
            except Exception as e:
                logger.error(f"❌ MinIO上传异常: {e}")
        
        # 保存到数据库
        if database_service:
            try:
                # 获取AI生成信息
                ai_model_used = None
                ai_generation_time = None
                ai_tokens_used = None
                
                if gemini_service and gemini_service.is_available():
                    ai_model_used = gemini_service.model_name if hasattr(gemini_service, 'model_name') else "gemini-2.5-pro"
                
                # 获取嵌入模型信息
                embedding_model_used = None
                if is_advanced_embedding and hasattr(embedding_service, 'get_model_info'):
                    try:
                        model_info = embedding_service.get_model_info()
                        embedding_model_used = model_info.get('text_model', 'BGE-M3')
                    except:
                        embedding_model_used = "BGE-M3"
                else:
                    embedding_model_used = "simplified"
                
                db_record = database_service.create_image_record(
                    image_id=image_id,
                    filename=file.filename or "unknown.jpg",
                    original_filename=file.filename or "unknown.jpg",
                    user_description=user_description,
                    ai_description=ai_description,
                    file_size=len(file_data),
                    width=width,
                    height=height,
                    format=format_name,
                    mime_type=file.content_type,
                    ai_model_used=ai_model_used,
                    embedding_model_used=embedding_model_used
                )
                
                if db_record:
                    logger.info(f"✅ 图片记录已保存到数据库: {image_id}")
                    # 更新嵌入状态
                    database_service.update_embedding_status(image_id, text_status="completed")
                else:
                    logger.warning(f"⚠️ 数据库保存失败: {image_id}")
                    
            except Exception as e:
                logger.error(f"❌ 数据库保存异常: {e}")
        
        # 更新搜索索引
        search_index[image_id] = {
            "text_embedding": text_embedding,
            "metadata": {
                "filename": file.filename,
                "user_description": user_description,
                "ai_description": ai_description,
                "combined_description": combined_description,
                "upload_time": image_record["upload_time"]
            }
        }
        
        # 尝试保存到ChromaDB
        if vector_service:
            try:
                # 修复：使用正确的维度
                if is_advanced_embedding:
                    # BGE-M3: 文本嵌入1024维，图片嵌入1024维
                    image_embedding_dim = 1024
                else:
                    # 简化嵌入: 文本嵌入512维，图片嵌入512维
                    image_embedding_dim = 512
                
                vector_service.insert_embeddings(
                    image_ids=[image_id],
                    image_embeddings=[np.zeros(image_embedding_dim)],  # 使用正确的维度
                    text_embeddings=[text_embedding]
                )
                logger.info(f"✅ 图片 {image_id} 已保存到ChromaDB")
            except Exception as e:
                logger.warning(f"ChromaDB保存失败: {e}")
                import traceback
                logger.warning(f"详细错误: {traceback.format_exc()}")
        
        logger.info(f"✅ 图片上传成功: {image_id}")
        
        # 确定存储状态
        storage_info = []
        if minio_service and file_url:
            storage_info.append("MinIO对象存储")
        if database_service:
            storage_info.append("MySQL数据库")
        if vector_service:
            storage_info.append("ChromaDB向量库")
        storage_info.append("内存缓存")
        
        return {
            "image_id": image_id,
            "filename": file.filename,
            "file_url": file_url,  # MinIO访问URL
            "user_description": user_description,
            "ai_description": ai_description,
            "combined_description": combined_description,
            "file_size": len(file_data),
            "dimensions": f"{width}x{height}",
            "format": format_name,
            "message": "图片上传并处理成功",
            "embedding_status": "completed",
            "ai_description_status": "completed" if ai_description else "skipped",
            "storage": " + ".join(storage_info),
            "minio_url": file_url
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"上传失败: {e}")
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")

@app.get("/search/images")
async def search_images(
    query: str = Query(..., description="搜索查询文本"),
    top_k: int = Query(10, ge=1, le=50, description="返回结果数量"),
    min_score: float = Query(0.0, ge=0.0, le=1.0, description="最小相似度分数")
):
    """搜索图片 - 直接从ChromaDB查询"""
    try:
        start_time = time.time()
        logger.info(f"搜索图片: query='{query}', top_k={top_k}, min_score={min_score}")
        
        # 检查向量服务是否可用
        if not vector_service:
            raise HTTPException(status_code=500, detail="向量数据库服务不可用")
        
        # 获取查询文本的嵌入向量
        if is_advanced_embedding:
            query_embedding = embedding_service.embed_query(query)
        else:
            query_embedding = embedding_service.encode_text(query)
        
        # 直接从ChromaDB搜索
        search_results = vector_service.search_by_vector(
            query_vector=query_embedding,
            vector_field="text",  # 搜索文本嵌入
            top_k=top_k * 2  # 获取更多结果用于过滤
        )
        
        # 过滤和格式化结果
        results = []
        for result in search_results:
            if result["score"] >= min_score:
                image_id = result["image_id"]
                
                # 从数据库获取图片元数据
                description = ""
                if database_service:
                    db_image = database_service.get_image_by_id(image_id)
                    if db_image:
                        # 优先使用combined_description，如果没有则使用user_description
                        description = db_image.get("combined_description", "") or db_image.get("user_description", "")
                
                # 如果数据库中没有，尝试从内存中获取（向后兼容）
                if not description and image_id in image_storage:
                    memory_data = image_storage[image_id]
                    description = memory_data.get("combined_description", "") or memory_data.get("user_description", "")
                
                # 获取MinIO URL
                file_url = None
                if minio_service and minio_service.is_available():
                    file_url = minio_service.get_image_url(image_id)
                
                # 构建简化的结果
                result_item = {
                    "file_url": file_url,
                    "description": description
                }
                
                results.append(result_item)
        
        # 按相似度排序并限制结果数量
        results = results[:top_k]
        
        search_time = time.time() - start_time
        
        logger.info(f"ChromaDB搜索完成: 找到 {len(results)} 个结果，耗时 {search_time:.3f}s")
        
        return {
            "query": query,
            "results": results
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"搜索失败: {e}")
        raise HTTPException(status_code=500, detail=f"搜索失败: {str(e)}")

@app.get("/images/{image_id}")
async def get_image(image_id: str):
    """获取图片文件"""
    if image_id not in image_storage:
        raise HTTPException(status_code=404, detail="图片不存在")
    
    image_data = image_storage[image_id]
    return Response(
        content=image_data["file_data"],
        media_type=image_data["content_type"]
    )

@app.get("/images/{image_id}/info")
async def get_image_info(image_id: str):
    """获取图片信息"""
    if image_id not in image_storage:
        raise HTTPException(status_code=404, detail="图片不存在")
    
    image_data = image_storage[image_id].copy()
    # 移除二进制数据和嵌入向量
    image_data.pop("file_data", None)
    image_data.pop("text_embedding", None)
    
    return image_data

@app.delete("/images/{image_id}")
async def delete_image(image_id: str):
    """删除图片"""
    if image_id not in image_storage:
        raise HTTPException(status_code=404, detail="图片不存在")
    
    # 从存储中删除
    del image_storage[image_id]
    del search_index[image_id]
    
    # 从ChromaDB删除
    if vector_service:
        try:
            vector_service.delete_by_image_id(image_id)
        except Exception as e:
            logger.warning(f"ChromaDB删除失败: {e}")
    
    return {"message": f"图片 {image_id} 已删除"}

@app.get("/database/images")
async def get_database_images(
    limit: int = Query(20, ge=1, le=100, description="返回记录数量"),
    offset: int = Query(0, ge=0, description="跳过记录数量"),
    order_by: str = Query("created_at", description="排序字段"),
    order_desc: bool = Query(True, description="是否降序排列")
):
    """获取数据库中的图片记录列表"""
    if not database_service:
        raise HTTPException(status_code=503, detail="数据库服务不可用")
    
    try:
        images = database_service.get_images_list(
            limit=limit,
            offset=offset,
            order_by=order_by,
            order_desc=order_desc
        )
        
        result = []
        for img in images:
            result.append({
                "image_id": img.image_id,
                "filename": img.filename,
                "original_filename": img.original_filename,
                "user_description": img.user_description,
                "ai_description": img.ai_description,
                "combined_description": img.combined_description,
                "file_size": img.file_size,
                "width": img.width,
                "height": img.height,
                "format": img.format,
                "mime_type": img.mime_type,
                "ai_model_used": img.ai_model_used,
                "ai_generation_status": img.ai_generation_status,
                "embedding_model_used": img.embedding_model_used,
                "text_embedding_status": img.text_embedding_status,
                "search_count": img.search_count,
                "created_at": img.created_at.isoformat() if hasattr(img, 'created_at') and img.created_at else None,
                "last_accessed": img.last_accessed.isoformat() if hasattr(img, 'last_accessed') and img.last_accessed else None
            })
        
        return {
            "images": result,
            "total_returned": len(result),
            "limit": limit,
            "offset": offset,
            "message": f"返回 {len(result)} 条图片记录"
        }
        
    except Exception as e:
        logger.error(f"获取数据库图片列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取图片列表失败: {str(e)}")

@app.get("/database/stats")
async def get_database_stats():
    """获取数据库统计信息"""
    if not database_service:
        raise HTTPException(status_code=503, detail="数据库服务不可用")
    
    try:
        stats = database_service.get_statistics()
        return {
            "database_stats": stats,
            "message": "数据库统计信息获取成功"
        }
    except Exception as e:
        logger.error(f"获取数据库统计失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取统计信息失败: {str(e)}")

@app.get("/stats")
async def get_stats():
    """获取系统统计信息"""
    embedding_info = "未加载"
    if embedding_service:
        if is_advanced_embedding and hasattr(embedding_service, 'get_model_info'):
            model_info = embedding_service.get_model_info()
            embedding_info = f"{model_info['service']} - {model_info['text_model']}"
        else:
            embedding_info = "简化嵌入服务"
    
    gemini_info = "未加载"
    if gemini_service and gemini_service.is_available():
        if hasattr(gemini_service, 'get_model_info'):
            model_info = gemini_service.get_model_info()
            gemini_info = f"{model_info['service']} - {model_info['model']}"
        else:
            gemini_info = "Gemini服务已加载"
    
    # 获取数据库统计
    db_stats = {}
    if database_service:
        try:
            db_stats = database_service.get_statistics()
        except Exception as e:
            logger.error(f"获取数据库统计失败: {e}")
    
    # 获取向量数据库统计
    vector_db_stats = {}
    if vector_service:
        try:
            vector_db_stats = vector_service.get_collection_stats()
        except Exception as e:
            logger.error(f"获取向量数据库统计失败: {e}")
    
    return {
        "total_images": len(image_storage),
        "database_images": db_stats.get("total_images", 0),
        "storage_type": "SQLite + ChromaDB + 内存" if database_service and vector_service else "ChromaDB + 内存" if vector_service else "纯内存",
        "embedding_service": embedding_info,
        "gemini_service": gemini_info,
        "search_index_size": len(search_index),
        "embedding_type": "高级嵌入 (BGE-M3)" if is_advanced_embedding else "简化嵌入",
        "database_stats": db_stats,
        "vector_db_stats": vector_db_stats,
        "features": [
            "✅ 文本描述嵌入",
            "✅ AI图片描述生成" if (gemini_service and gemini_service.is_available()) else "❌ AI描述生成不可用",
            "✅ 语义搜索",
            "✅ ChromaDB持久化" if vector_service else "❌ ChromaDB不可用",
            "✅ SQLite数据库持久化" if database_service else "❌ 数据库不可用"
        ]
    }

# 引入前端页面
@app.get("/demo", response_class=HTMLResponse)
async def demo_page():
    """演示页面"""
    try:
        # 尝试多个可能的路径
        import os
        possible_paths = [
            "frontend.html",  # 当前目录
            "image_rag_system/frontend.html",  # 从项目根目录
            os.path.join(os.path.dirname(__file__), "frontend.html")  # 相对于此文件
        ]
        
        html_content = None
        for path in possible_paths:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    html_content = f.read()
                break
            except FileNotFoundError:
                continue
        
        if html_content:
            return HTMLResponse(content=html_content)
        else:
            raise FileNotFoundError("frontend.html not found in any expected location")
            
    except FileNotFoundError:
        return HTMLResponse(content="""
        <html><body>
        <h1>前端页面未找到</h1>
        <p>请确保 frontend.html 文件存在</p>
        <p><a href="/docs">查看API文档</a></p>
        </body></html>
        """)

if __name__ == "__main__":
    print("🚀 启动图片RAG系统 v2.0...")
    print("📋 系统信息:")
    print("   - API服务: http://localhost:8080")
    print("   - API文档: http://localhost:8080/docs")
    print("   - 演示页面: http://localhost:8080/demo")
    print("   - 健康检查: http://localhost:8080/health")
    print("   - 系统状态: http://localhost:8080/stats")
    print("\n🔧 新功能:")
    print("   - ✅ BGE-M3高质量文本嵌入")
    print("   - ✅ Gemini 2.5 Pro AI描述生成")
    print("   - ✅ 基于文本描述的图片检索")
    print("   - ✅ 双重描述增强搜索")
    print("   - 🔄 ChromaDB向量数据库")
    print("\n💡 使用 Ctrl+C 停止服务")
    
    uvicorn.run(
        "app_complete:app",
        host="0.0.0.0", 
        port=8080,
        reload=True,
        log_level="info"
    ) 
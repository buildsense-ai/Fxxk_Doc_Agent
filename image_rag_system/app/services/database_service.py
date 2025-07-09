"""
数据库服务 - 处理图片记录的增删改查
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc, func

from ..models.database import Image, get_db, create_tables, Base, engine
from ..models.schemas import ImageUploadRequest, ImageResult

logger = logging.getLogger(__name__)


class DatabaseService:
    """数据库服务类"""
    
    def __init__(self):
        """初始化数据库服务"""
        try:
            # 确保数据表存在，但不删除现有数据
            self.ensure_tables_exist()
            logger.info("✅ 数据库服务初始化成功")
        except Exception as e:
            logger.error(f"❌ 数据库服务初始化失败: {e}")
            raise
    
    def ensure_tables_exist(self):
        """确保数据表存在，但不删除现有数据"""
        try:
            # 只创建表，不删除现有数据
            Base.metadata.create_all(bind=engine)
            logger.info("✅ 数据表检查/创建成功")
        except Exception as e:
            logger.error(f"❌ 数据表创建失败: {e}")
            raise
    
    def recreate_tables(self):
        """重新创建所有数据表（会删除现有数据）"""
        try:
            # 删除所有表
            Base.metadata.drop_all(bind=engine)
            logger.info("✅ 旧表删除成功")
            
            # 创建新表
            Base.metadata.create_all(bind=engine)
            logger.info("✅ 新表创建成功")
        except Exception as e:
            logger.error(f"❌ 重建数据表失败: {e}")
            raise
    
    def create_image_record(self, 
                          image_id: str,
                          filename: str,
                          original_filename: str,
                          user_description: Optional[str] = None,
                          ai_description: Optional[str] = None,
                          file_size: int = 0,
                          width: Optional[int] = None,
                          height: Optional[int] = None,
                          format: Optional[str] = None,
                          mime_type: str = "image/jpeg",
                          ai_model_used: Optional[str] = None,
                          ai_generation_time: Optional[float] = None,
                          ai_tokens_used: Optional[int] = None,
                          embedding_model_used: Optional[str] = None,
                          minio_url: Optional[str] = None,
                          object_name: Optional[str] = None,
                          bucket_name: Optional[str] = None,
                          source_file: Optional[str] = None) -> Optional[Image]:
        """
        创建图片记录
        
        Args:
            image_id: 图片唯一ID
            filename: 文件名
            original_filename: 原始文件名
            user_description: 用户描述
            ai_description: AI生成的描述
            file_size: 文件大小
            width: 图片宽度
            height: 图片高度
            format: 图片格式
            mime_type: MIME类型
            ai_model_used: 使用的AI模型
            ai_generation_time: AI生成耗时
            ai_tokens_used: AI使用的token数
            embedding_model_used: 使用的嵌入模型
            minio_url: MinIO访问URL
            object_name: MinIO对象名称
            bucket_name: MinIO存储桶名称
            source_file: 来源文件路径
            
        Returns:
            创建的图片记录，失败返回None
        """
        try:
            with next(get_db()) as db:
                # 合并描述
                combined_description = self._combine_descriptions(user_description, ai_description)
                
                # 创建图片记录
                image_record = Image(
                    image_id=image_id,
                    filename=filename,
                    original_filename=original_filename,
                    user_description=user_description,
                    ai_description=ai_description,
                    combined_description=combined_description,
                    description=combined_description,  # 向后兼容
                    file_size=file_size,
                    width=width,
                    height=height,
                    format=format,
                    mime_type=mime_type,
                    ai_model_used=ai_model_used,
                    ai_generation_time=ai_generation_time,
                    ai_tokens_used=ai_tokens_used,
                    ai_generation_status="completed" if ai_description else "skipped",
                    embedding_model_used=embedding_model_used,
                    text_embedding_status="pending",
                    image_embedding_status="pending",
                    minio_url=minio_url,
                    object_name=object_name,
                    bucket_name=bucket_name,
                    source_file=source_file
                )
                
                db.add(image_record)
                db.commit()
                db.refresh(image_record)
                
                logger.info(f"✅ 图片记录创建成功: {image_id}")
                return image_record
                
        except Exception as e:
            logger.error(f"❌ 创建图片记录失败: {e}")
            return None
    
    def get_image_by_id(self, image_id: str) -> Optional[Dict[str, Any]]:
        """根据ID获取图片记录"""
        try:
            with next(get_db()) as db:
                image = db.query(Image).filter(Image.image_id == image_id).first()
                if image:
                    # 更新最后访问时间
                    image.last_accessed = datetime.utcnow()
                    db.commit()
                    
                    # 转换为字典
                    return {
                        "image_id": image.image_id,
                        "filename": image.filename,
                        "original_filename": image.original_filename,
                        "user_description": image.user_description,
                        "ai_description": image.ai_description,
                        "combined_description": image.combined_description,
                        "file_size": image.file_size,
                        "width": image.width,
                        "height": image.height,
                        "format": image.format,
                        "mime_type": image.mime_type,
                        "ai_model_used": image.ai_model_used,
                        "ai_generation_status": image.ai_generation_status,
                        "embedding_model_used": image.embedding_model_used,
                        "text_embedding_status": image.text_embedding_status,
                        "minio_url": image.minio_url,
                        "object_name": image.object_name,
                        "bucket_name": image.bucket_name,
                        "search_count": image.search_count,
                        "created_at": image.created_at,
                        "last_accessed": image.last_accessed
                    }
                return None
        except Exception as e:
            logger.error(f"❌ 获取图片记录失败: {e}")
            return None
    
    def update_embedding_status(self, 
                              image_id: str, 
                              text_status: Optional[str] = None,
                              image_status: Optional[str] = None) -> bool:
        """更新嵌入状态"""
        try:
            with next(get_db()) as db:
                image = db.query(Image).filter(Image.image_id == image_id).first()
                if not image:
                    return False
                
                if text_status:
                    image.text_embedding_status = text_status
                if image_status:
                    image.image_embedding_status = image_status
                
                db.commit()
                return True
        except Exception as e:
            logger.error(f"❌ 更新嵌入状态失败: {e}")
            return False
    
    def update_ai_description(self, 
                            image_id: str, 
                            ai_description: str,
                            ai_model_used: Optional[str] = None,
                            ai_generation_time: Optional[float] = None,
                            ai_tokens_used: Optional[int] = None) -> bool:
        """更新AI描述"""
        try:
            with next(get_db()) as db:
                image = db.query(Image).filter(Image.image_id == image_id).first()
                if not image:
                    return False
                
                image.ai_description = ai_description
                image.ai_generation_status = "completed"
                image.combined_description = self._combine_descriptions(
                    image.user_description, ai_description
                )
                image.description = image.combined_description  # 向后兼容
                
                if ai_model_used:
                    image.ai_model_used = ai_model_used
                if ai_generation_time:
                    image.ai_generation_time = ai_generation_time
                if ai_tokens_used:
                    image.ai_tokens_used = ai_tokens_used
                
                db.commit()
                return True
        except Exception as e:
            logger.error(f"❌ 更新AI描述失败: {e}")
            return False
    
    def increment_search_count(self, image_id: str) -> bool:
        """增加搜索计数"""
        try:
            with next(get_db()) as db:
                image = db.query(Image).filter(Image.image_id == image_id).first()
                if not image:
                    return False
                
                image.search_count += 1
                image.last_accessed = datetime.utcnow()
                db.commit()
                return True
        except Exception as e:
            logger.error(f"❌ 更新搜索计数失败: {e}")
            return False
    
    def get_images_list(self, 
                       limit: int = 50, 
                       offset: int = 0,
                       order_by: str = "created_at",
                       order_desc: bool = True) -> List[Image]:
        """获取图片列表"""
        try:
            with next(get_db()) as db:
                query = db.query(Image)
                
                # 排序
                if hasattr(Image, order_by):
                    order_field = getattr(Image, order_by)
                    if order_desc:
                        query = query.order_by(desc(order_field))
                    else:
                        query = query.order_by(asc(order_field))
                
                return query.offset(offset).limit(limit).all()
        except Exception as e:
            logger.error(f"❌ 获取图片列表失败: {e}")
            return []
    
    def search_images_by_description(self, 
                                   query: str, 
                                   limit: int = 20) -> List[Image]:
        """根据描述搜索图片"""
        try:
            with next(get_db()) as db:
                # 使用SQL LIKE进行简单的文本搜索
                search_pattern = f"%{query}%"
                
                images = db.query(Image).filter(
                    (Image.user_description.like(search_pattern)) |
                    (Image.ai_description.like(search_pattern)) |
                    (Image.combined_description.like(search_pattern)) |
                    (Image.filename.like(search_pattern))
                ).limit(limit).all()
                
                # 更新搜索计数
                for image in images:
                    image.search_count += 1
                    image.last_accessed = datetime.utcnow()
                
                db.commit()
                return images
                
        except Exception as e:
            logger.error(f"❌ 搜索图片失败: {e}")
            return []
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取数据库统计信息"""
        try:
            with next(get_db()) as db:
                total_images = db.query(func.count(Image.id)).scalar()
                
                # AI描述统计
                ai_completed = db.query(func.count(Image.id)).filter(
                    Image.ai_generation_status == "completed"
                ).scalar()
                
                ai_failed = db.query(func.count(Image.id)).filter(
                    Image.ai_generation_status == "failed"
                ).scalar()
                
                # 嵌入状态统计
                text_embedding_completed = db.query(func.count(Image.id)).filter(
                    Image.text_embedding_status == "completed"
                ).scalar()
                
                # 最近上传的图片
                recent_images = db.query(Image).order_by(desc(Image.created_at)).limit(5).all()
                
                # 热门图片（搜索次数最多）
                popular_images = db.query(Image).order_by(desc(Image.search_count)).limit(5).all()
                
                return {
                    "total_images": total_images,
                    "ai_descriptions": {
                        "completed": ai_completed,
                        "failed": ai_failed,
                        "success_rate": round(ai_completed / max(total_images, 1) * 100, 2)
                    },
                    "text_embeddings_completed": text_embedding_completed,
                    "recent_images": [
                        {
                            "image_id": img.image_id,
                            "filename": img.filename,
                            "created_at": img.created_at.isoformat() if img.created_at else None
                        }
                        for img in recent_images
                    ],
                    "popular_images": [
                        {
                            "image_id": img.image_id,
                            "filename": img.filename,
                            "search_count": img.search_count
                        }
                        for img in popular_images
                    ]
                }
                
        except Exception as e:
            logger.error(f"❌ 获取统计信息失败: {e}")
            return {}
    
    def delete_image(self, image_id: str) -> bool:
        """删除图片记录"""
        try:
            with next(get_db()) as db:
                image = db.query(Image).filter(Image.image_id == image_id).first()
                if not image:
                    return False
                
                db.delete(image)
                db.commit()
                logger.info(f"✅ 图片记录删除成功: {image_id}")
                return True
                
        except Exception as e:
            logger.error(f"❌ 删除图片记录失败: {e}")
            return False
    
    def _combine_descriptions(self, 
                            user_description: Optional[str], 
                            ai_description: Optional[str]) -> str:
        """合并用户描述和AI描述"""
        if user_description and ai_description:
            return f"用户描述: {user_description}\n\nAI描述: {ai_description}"
        elif user_description:
            return f"用户描述: {user_description}"
        elif ai_description:
            return f"AI描述: {ai_description}"
        else:
            return ""
    
    def is_available(self) -> bool:
        """检查数据库服务是否可用"""
        try:
            with next(get_db()) as db:
                db.query(Image).first()
                return True
        except Exception as e:
            logger.error(f"数据库连接检查失败: {e}")
            return False 
"""
MinIO对象存储服务
"""

import os
import io
import logging
from typing import Optional, Dict, Any, BinaryIO
from minio import Minio
from minio.error import S3Error
from urllib3.exceptions import MaxRetryError
import uuid
from datetime import datetime
from urllib.parse import quote

logger = logging.getLogger(__name__)


class MinIOService:
    """MinIO对象存储服务"""
    
    def __init__(self):
        """初始化MinIO客户端"""
        self.endpoint = os.getenv('MINIO_ENDPOINT', '43.139.19.144:9000')
        self.access_key = os.getenv('MINIO_ACCESS_KEY', 'minioadmin')
        self.secret_key = os.getenv('MINIO_SECRET_KEY', 'minioadmin')
        self.bucket_name = os.getenv('MINIO_BUCKET_NAME', 'ragimages')
        self.secure = os.getenv('MINIO_SECURE', 'false').lower() == 'true'
        
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """初始化MinIO客户端连接"""
        try:
            self.client = Minio(
                self.endpoint,
                access_key=self.access_key,
                secret_key=self.secret_key,
                secure=self.secure
            )
            
            # 检查连接并创建bucket
            self._ensure_bucket_exists()
            logger.info(f"✅ MinIO客户端初始化成功: {self.endpoint}/{self.bucket_name}")
            
        except Exception as e:
            logger.error(f"❌ MinIO客户端初始化失败: {e}")
            self.client = None
    
    def _ensure_bucket_exists(self):
        """确保bucket存在"""
        if not self.client:
            return False
            
        try:
            # 检查bucket是否存在
            if not self.client.bucket_exists(self.bucket_name):
                # 创建bucket
                self.client.make_bucket(self.bucket_name)
                logger.info(f"✅ 创建MinIO bucket: {self.bucket_name}")
            else:
                logger.info(f"✅ MinIO bucket已存在: {self.bucket_name}")
            return True
            
        except S3Error as e:
            logger.error(f"❌ MinIO bucket操作失败: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ MinIO连接异常: {e}")
            return False
    
    def is_available(self) -> bool:
        """检查MinIO服务是否可用"""
        if not self.client:
            return False
            
        try:
            # 尝试列出bucket来测试连接
            self.client.bucket_exists(self.bucket_name)
            return True
        except Exception as e:
            logger.error(f"MinIO服务不可用: {e}")
            return False
    
    def upload_image(self, 
                    image_data: bytes, 
                    filename: str,
                    content_type: str = "image/jpeg",
                    image_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        上传图片到MinIO
        
        Args:
            image_data: 图片二进制数据
            filename: 原始文件名
            content_type: 文件MIME类型
            image_id: 图片ID，如果为None则自动生成
            
        Returns:
            上传结果信息，失败返回None
        """
        if not self.is_available():
            logger.error("MinIO服务不可用")
            return None
        
        try:
            # 生成对象名称
            if not image_id:
                image_id = str(uuid.uuid4())
            
            # 获取文件扩展名
            file_extension = filename.split('.')[-1] if '.' in filename else 'jpg'
            object_name = f"images/{image_id}.{file_extension}"
            
            # 上传文件
            data_stream = io.BytesIO(image_data)
            file_size = len(image_data)
            
            # 对中文文件名进行URL编码
            encoded_filename = quote(filename, safe='')
            
            result = self.client.put_object(
                bucket_name=self.bucket_name,
                object_name=object_name,
                data=data_stream,
                length=file_size,
                content_type=content_type,
                metadata={
                    'original_filename': encoded_filename,
                    'image_id': image_id,
                    'upload_time': datetime.utcnow().isoformat()
                }
            )
            
            # 生成访问URL
            file_url = f"{'https' if self.secure else 'http'}://{self.endpoint}/{self.bucket_name}/{object_name}"
            
            logger.info(f"✅ 图片上传成功: {object_name}")
            
            return {
                'success': True,
                'image_id': image_id,
                'object_name': object_name,
                'file_url': file_url,
                'file_size': file_size,
                'bucket_name': self.bucket_name,
                'etag': result.etag,
                'upload_time': datetime.utcnow().isoformat()
            }
            
        except S3Error as e:
            logger.error(f"❌ MinIO上传失败: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ 图片上传异常: {e}")
            return None
    
    def get_image_url(self, image_id: str, file_extension: str = "jpg") -> Optional[str]:
        """
        获取图片访问URL
        
        Args:
            image_id: 图片ID
            file_extension: 文件扩展名
            
        Returns:
            图片访问URL，失败返回None
        """
        if not self.is_available():
            return None
        
        try:
            object_name = f"images/{image_id}.{file_extension}"
            
            # 检查对象是否存在
            self.client.stat_object(self.bucket_name, object_name)
            
            # 生成访问URL
            file_url = f"{'https' if self.secure else 'http'}://{self.endpoint}/{self.bucket_name}/{object_name}"
            return file_url
            
        except S3Error as e:
            logger.error(f"❌ 获取图片URL失败: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ 获取图片URL异常: {e}")
            return None
    
    def get_image_data(self, image_id: str, file_extension: str = "jpg") -> Optional[bytes]:
        """
        获取图片二进制数据
        
        Args:
            image_id: 图片ID
            file_extension: 文件扩展名
            
        Returns:
            图片二进制数据，失败返回None
        """
        if not self.is_available():
            return None
        
        try:
            object_name = f"images/{image_id}.{file_extension}"
            
            # 获取对象数据
            response = self.client.get_object(self.bucket_name, object_name)
            image_data = response.read()
            response.close()
            response.release_conn()
            
            return image_data
            
        except S3Error as e:
            logger.error(f"❌ 获取图片数据失败: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ 获取图片数据异常: {e}")
            return None
    
    def delete_image(self, image_id: str, file_extension: str = "jpg") -> bool:
        """
        删除图片
        
        Args:
            image_id: 图片ID
            file_extension: 文件扩展名
            
        Returns:
            删除是否成功
        """
        if not self.is_available():
            return False
        
        try:
            object_name = f"images/{image_id}.{file_extension}"
            
            # 删除对象
            self.client.remove_object(self.bucket_name, object_name)
            logger.info(f"✅ 图片删除成功: {object_name}")
            return True
            
        except S3Error as e:
            logger.error(f"❌ 删除图片失败: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ 删除图片异常: {e}")
            return False
    
    def get_image_info(self, image_id: str, file_extension: str = "jpg") -> Optional[Dict[str, Any]]:
        """
        获取图片信息
        
        Args:
            image_id: 图片ID
            file_extension: 文件扩展名
            
        Returns:
            图片信息字典，失败返回None
        """
        if not self.is_available():
            return None
        
        try:
            object_name = f"images/{image_id}.{file_extension}"
            
            # 获取对象信息
            stat = self.client.stat_object(self.bucket_name, object_name)
            
            return {
                'image_id': image_id,
                'object_name': object_name,
                'file_size': stat.size,
                'content_type': stat.content_type,
                'last_modified': stat.last_modified.isoformat() if stat.last_modified else None,
                'etag': stat.etag,
                'metadata': stat.metadata,
                'file_url': self.get_image_url(image_id, file_extension)
            }
            
        except S3Error as e:
            logger.error(f"❌ 获取图片信息失败: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ 获取图片信息异常: {e}")
            return None
    
    def list_images(self, prefix: str = "images/", limit: int = 100) -> list:
        """
        列出图片列表
        
        Args:
            prefix: 对象名前缀
            limit: 返回数量限制
            
        Returns:
            图片信息列表
        """
        if not self.is_available():
            return []
        
        try:
            objects = self.client.list_objects(
                self.bucket_name, 
                prefix=prefix, 
                recursive=True
            )
            
            image_list = []
            count = 0
            
            for obj in objects:
                if count >= limit:
                    break
                
                # 从对象名提取图片ID
                object_name = obj.object_name
                if object_name.startswith("images/"):
                    filename = object_name.split("/")[-1]
                    image_id = filename.split(".")[0]
                    
                    image_list.append({
                        'image_id': image_id,
                        'object_name': object_name,
                        'file_size': obj.size,
                        'last_modified': obj.last_modified.isoformat() if obj.last_modified else None,
                        'etag': obj.etag,
                        'file_url': f"{'https' if self.secure else 'http'}://{self.endpoint}/{self.bucket_name}/{object_name}"
                    })
                    
                count += 1
            
            return image_list
            
        except S3Error as e:
            logger.error(f"❌ 列出图片失败: {e}")
            return []
        except Exception as e:
            logger.error(f"❌ 列出图片异常: {e}")
            return []
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """
        获取存储统计信息
        
        Returns:
            存储统计信息字典
        """
        if not self.is_available():
            return {}
        
        try:
            # 获取图片列表来计算统计信息
            images = self.list_images(limit=1000)  # 限制1000个用于统计
            
            total_count = len(images)
            total_size = sum(img.get('file_size', 0) for img in images)
            
            return {
                'total_images': total_count,
                'total_size_bytes': total_size,
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'bucket_name': self.bucket_name,
                'endpoint': self.endpoint,
                'service_status': 'available'
            }
            
        except Exception as e:
            logger.error(f"❌ 获取存储统计失败: {e}")
            return {
                'service_status': 'error',
                'error': str(e)
            } 
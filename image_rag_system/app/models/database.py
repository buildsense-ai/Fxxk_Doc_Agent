"""
Database models and connection setup.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, create_engine, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.sql import func
from typing import Generator
import os

# Database URL
DATABASE_URL = os.getenv("DATABASE_URL", "mysql+pymysql://root:Aa%40114514@gz-cdb-e0aa423v.sql.tencentcdb.com:20236/gauz_ai_messages")

# SQLAlchemy setup
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Image(Base):
    """Image metadata table (精简版，与MySQL表结构一致)"""
    __tablename__ = "images"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    image_id = Column(String(255), unique=True, index=True, nullable=False)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=True)
    user_description = Column(Text, comment="用户描述")
    ai_description = Column(Text, comment="AI生成的描述")
    combined_description = Column(Text, comment="合并描述")
    description = Column(Text, comment="向后兼容的描述字段")
    file_size = Column(Integer, comment="文件大小(字节)")
    width = Column(Integer, comment="图片宽度")
    height = Column(Integer, comment="图片高度")
    format = Column(String(32), comment="图片格式")
    mime_type = Column(String(128), comment="MIME类型")
    ai_model_used = Column(String(255), comment="使用的AI模型")
    ai_generation_time = Column(Float, comment="AI生成耗时(秒)")
    ai_tokens_used = Column(Integer, comment="AI使用的token数")
    ai_generation_status = Column(String(32), comment="AI生成状态")
    embedding_model_used = Column(String(255), comment="使用的嵌入模型")
    text_embedding_status = Column(String(32), comment="文本嵌入状态")
    image_embedding_status = Column(String(32), comment="图片嵌入状态")
    minio_url = Column(String(500), comment="MinIO访问URL")
    object_name = Column(String(500), comment="MinIO对象名称")
    bucket_name = Column(String(255), comment="MinIO存储桶名称")
    source_file = Column(String(500), comment="来源文件路径（如PDF）")
    search_count = Column(Integer, default=0, comment="搜索次数")
    last_accessed = Column(DateTime(timezone=True), comment="最后访问时间")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<Image(id={self.id}, image_id='{self.image_id}', filename='{self.filename}')>"

def create_tables():
    """Create all database tables."""
    Base.metadata.create_all(bind=engine)

def get_db() -> Generator[Session, None, None]:
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 
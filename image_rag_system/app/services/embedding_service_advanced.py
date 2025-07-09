"""
高质量嵌入服务 (Advanced Embedding Service)
使用BGE-M3模型进行文本嵌入，专注于文本描述的语义理解
"""

import numpy as np
from typing import List, Optional, Dict, Any, Tuple
import logging
from pathlib import Path
import torch
import warnings

# 抑制不必要的警告
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

# 配置日志
logger = logging.getLogger(__name__)

class AdvancedEmbeddingService:
    """
    高质量嵌入服务
    使用BGE-M3模型进行文本嵌入，专注于描述文本的语义理解
    """
    
    def __init__(self):
        """初始化高质量嵌入服务"""
        self.text_model = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.embedding_dim = 1024  # BGE-M3的embedding维度
        
        logger.info(f"🚀 初始化高质量嵌入服务 (设备: {self.device})")
        
        # 初始化文本嵌入模型
        self._init_text_model()
    
    def _init_text_model(self):
        """初始化BGE-M3文本嵌入模型"""
        try:
            from FlagEmbedding import BGEM3FlagModel
            
            logger.info("📦 加载BGE-M3模型...")
            self.text_model = BGEM3FlagModel(
                'BAAI/bge-m3',
                use_fp16=True,  # 使用半精度以节省显存
                device=self.device
            )
            logger.info("✅ BGE-M3文本嵌入模型加载成功")
            
        except ImportError as e:
            logger.error(f"❌ BGE-M3模型依赖未安装: {e}")
            self.text_model = None
        except Exception as e:
            logger.error(f"❌ BGE-M3模型加载失败: {e}")
            self.text_model = None
    
    def is_available(self) -> bool:
        """检查服务是否可用"""
        return self.text_model is not None
    
    def embed_texts(self, texts: List[str], instruction: str = "") -> np.ndarray:
        """
        对文本列表进行嵌入
        
        Args:
            texts: 文本列表
            instruction: 查询指令（可选）
            
        Returns:
            嵌入向量数组 (n_texts, embedding_dim)
        """
        if not self.is_available():
            logger.error("❌ BGE-M3模型不可用")
            # 返回零向量作为fallback
            return np.zeros((len(texts), self.embedding_dim), dtype=np.float32)
        
        if not texts:
            logger.warning("⚠️ 文本列表为空")
            return np.zeros((0, self.embedding_dim), dtype=np.float32)
        
        try:
            # 额外的None检查以满足类型检查器
            if self.text_model is None:
                logger.error("❌ text_model为None")
                return np.zeros((len(texts), self.embedding_dim), dtype=np.float32)
            
            logger.info(f"🔤 嵌入 {len(texts)} 个文本...")
            
            # 如果有查询指令，为每个文本添加指令前缀
            if instruction:
                processed_texts = [f"{instruction} {text}" for text in texts]
            else:
                processed_texts = texts
            
            # 使用BGE-M3进行嵌入
            embeddings = self.text_model.encode(
                processed_texts,
                batch_size=32,
                max_length=8192,  # BGE-M3支持的最大长度
                return_dense=True,  # 只返回dense embedding
                return_sparse=False,
                return_colbert_vecs=False
            )
            
            # 确保返回正确的格式
            if isinstance(embeddings, dict) and 'dense_vecs' in embeddings:
                embeddings = embeddings['dense_vecs']
            
            embeddings = np.array(embeddings, dtype=np.float32)
            
            logger.info(f"✅ 文本嵌入完成: {embeddings.shape}")
            return embeddings
            
        except Exception as e:
            logger.error(f"❌ 文本嵌入失败: {e}")
            # 返回零向量作为fallback
            return np.zeros((len(texts), self.embedding_dim), dtype=np.float32)
    
    def embed_query(self, query: str) -> np.ndarray:
        """
        为查询文本生成嵌入向量
        
        Args:
            query: 查询文本
            
        Returns:
            查询向量 (embedding_dim,)
        """
        if not query.strip():
            logger.warning("⚠️ 查询文本为空")
            return np.zeros(self.embedding_dim, dtype=np.float32)
        
        # 为查询添加特殊指令以提升检索效果
        query_instruction = "为这个句子生成表示以用于检索相关文章："
        
        try:
            embeddings = self.embed_texts([query], instruction=query_instruction)
            return embeddings[0]  # 返回单个向量
        except Exception as e:
            logger.error(f"❌ 查询嵌入失败: {e}")
            return np.zeros(self.embedding_dim, dtype=np.float32)
    
    def embed_documents(self, documents: List[str]) -> np.ndarray:
        """
        为文档列表生成嵌入向量
        
        Args:
            documents: 文档文本列表
            
        Returns:
            文档嵌入矩阵 (n_docs, embedding_dim)
        """
        if not documents:
            logger.warning("⚠️ 文档列表为空")
            return np.zeros((0, self.embedding_dim), dtype=np.float32)
        
        try:
            # 对文档进行嵌入（不添加特殊指令）
            embeddings = self.embed_texts(documents)
            logger.info(f"✅ 文档嵌入完成: {len(documents)} 个文档")
            return embeddings
        except Exception as e:
            logger.error(f"❌ 文档嵌入失败: {e}")
            return np.zeros((len(documents), self.embedding_dim), dtype=np.float32)
    
    def compute_similarity(self, query_embedding: np.ndarray, doc_embeddings: np.ndarray) -> np.ndarray:
        """
        计算查询向量与文档向量的相似度
        
        Args:
            query_embedding: 查询向量 (embedding_dim,)
            doc_embeddings: 文档嵌入矩阵 (n_docs, embedding_dim)
            
        Returns:
            相似度分数数组 (n_docs,)
        """
        try:
            # 归一化向量
            query_norm = query_embedding / (np.linalg.norm(query_embedding) + 1e-8)
            doc_norms = doc_embeddings / (np.linalg.norm(doc_embeddings, axis=1, keepdims=True) + 1e-8)
            
            # 计算余弦相似度
            similarities = np.dot(doc_norms, query_norm)
            
            return similarities
            
        except Exception as e:
            logger.error(f"❌ 相似度计算失败: {e}")
            return np.zeros(len(doc_embeddings), dtype=np.float32)
    
    def get_embedding_dimension(self) -> int:
        """获取嵌入向量维度"""
        return self.embedding_dim
    
    def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        return {
            "service": "Advanced (BGE-M3 only)",
            "text_model": "BAAI/bge-m3" if self.text_model else None,
            "image_model": "None (图片嵌入已移除)",
            "embedding_dim": self.embedding_dim,
            "device": self.device,
            "available": self.is_available(),
            "features": [
                "多语言支持", 
                "长文本处理(8192 tokens)", 
                "高质量中文embedding",
                "仅文本描述嵌入"
            ]
        }
    
    def test_embedding(self) -> Dict[str, Any]:
        """测试嵌入功能"""
        if not self.is_available():
            return {
                "success": False,
                "error": "BGE-M3模型不可用",
                "details": {}
            }
        
        try:
            # 测试文本嵌入
            test_texts = [
                "这是一张美丽的风景照片",
                "古庙标志牌的文物保护标识",
                "咪咪躺在床上休息"
            ]
            
            text_embeddings = self.embed_texts(test_texts)
            query_embedding = self.embed_query("古庙标志牌")
            
            # 计算相似度
            similarities = self.compute_similarity(query_embedding, text_embeddings)
            
            return {
                "success": True,
                "error": None,
                "details": {
                    "text_embedding_shape": text_embeddings.shape,
                    "query_embedding_shape": query_embedding.shape,
                    "similarities": similarities.tolist(),
                    "model_info": self.get_model_info()
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "details": {}
            } 
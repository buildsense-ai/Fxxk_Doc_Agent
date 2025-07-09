"""
简化的嵌入服务，使用基础的随机向量和文本特征。
"""

import numpy as np
from PIL import Image
import io
import hashlib
from typing import List, Optional, Union
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EmbeddingService:
    """简化的嵌入服务，用于演示和测试。"""
    
    def __init__(self, model_name: str = "simplified", device: Optional[str] = None):
        """
        初始化简化的嵌入服务。
        
        Args:
            model_name: 模型名称 (用于兼容性)
            device: 设备 (用于兼容性)
        """
        self.model_name = model_name
        self.device = device or "cpu"
        
        logger.info(f"SimplifiedEmbeddingService initialized with model: {model_name}")
    
    def encode_image(self, image: Union[Image.Image, str, bytes]) -> np.ndarray:
        """
        将图片编码为嵌入向量（简化版本）。
        
        Args:
            image: PIL Image, 图片路径, 或图片字节
            
        Returns:
            标准化的嵌入向量
        """
        try:
            # 处理不同的输入类型
            if isinstance(image, str):
                pil_image = Image.open(image).convert('RGB')
            elif isinstance(image, bytes):
                pil_image = Image.open(io.BytesIO(image)).convert('RGB')
            elif isinstance(image, Image.Image):
                pil_image = image.convert('RGB')
            else:
                raise ValueError(f"不支持的图片类型: {type(image)}")
            
            # 生成基于图片内容的特征向量
            # 1. 使用图片的基本统计信息
            img_array = np.array(pil_image)
            width, height = pil_image.size
            
            # 2. 计算颜色统计
            mean_rgb = np.mean(img_array, axis=(0, 1))  # RGB平均值
            std_rgb = np.std(img_array, axis=(0, 1))    # RGB标准差
            
            # 3. 计算图片哈希作为额外特征
            img_bytes = image if isinstance(image, bytes) else pil_image.tobytes()
            img_hash = hashlib.md5(img_bytes).hexdigest()
            hash_features = [int(img_hash[i:i+2], 16) for i in range(0, 32, 2)][:16]
            
            # 4. 组合特征 (确保精确512维)
            features = np.concatenate([
                mean_rgb,           # 3维: RGB平均值
                std_rgb,            # 3维: RGB标准差  
                [width/1000.0],     # 1维: 归一化宽度
                [height/1000.0],    # 1维: 归一化高度
                hash_features,      # 16维: 哈希特征
                np.random.randn(488) * 0.1  # 488维: 填充向量使总维度为512
            ])
            
            # 确保精确512维
            if len(features) > 512:
                features = features[:512]
            elif len(features) < 512:
                padding = np.zeros(512 - len(features))
                features = np.concatenate([features, padding])
            
            # 标准化向量
            features = features / np.linalg.norm(features)
            
            logger.info(f"生成图片嵌入向量: {features.shape}")
            return features
            
        except Exception as e:
            logger.error(f"图片编码错误: {e}")
            # 返回随机向量作为fallback
            return np.random.randn(512) / 10.0
    
    def encode_text(self, text: str, use_clip: bool = True) -> np.ndarray:
        """
        将文本编码为嵌入向量（简化版本）。
        
        Args:
            text: 要编码的文本
            use_clip: 兼容性参数
            
        Returns:
            标准化的嵌入向量
        """
        try:
            if not text:
                text = "空文本"
            
            # 1. 基础文本特征
            text_lower = text.lower()
            text_length = len(text)
            word_count = len(text.split())
            
            # 2. 字符频率特征
            char_freq = {}
            for char in text_lower:
                char_freq[char] = char_freq.get(char, 0) + 1
            
            # 3. 关键词检测 (大幅扩展关键词库)
            keywords = {
                # 动物类
                '猫': 0.9, '狗': 0.9, '鸟': 0.8, '鱼': 0.8, '动物': 0.7, '宠物': 0.7,
                '可爱': 0.6, '萌': 0.6, '毛茸茸': 0.6,
                
                # 建筑标志类
                '标志': 0.95, '牌': 0.9, '标志牌': 0.95, '指示牌': 0.9, '路牌': 0.9,
                '招牌': 0.8, '广告牌': 0.8, '告示牌': 0.8, '公告牌': 0.8,
                
                # 建筑文物类
                '古庙': 0.9, '寺庙': 0.9, '教堂': 0.8, '建筑': 0.7, '文物': 0.9,
                '古迹': 0.8, '遗址': 0.8, '历史': 0.7, '传统': 0.6,
                
                # 颜色类
                '红色': 0.6, '蓝色': 0.6, '绿色': 0.6, '黄色': 0.6, '橙色': 0.6,
                '黑色': 0.5, '白色': 0.5, '灰色': 0.5, '颜色': 0.4,
                
                # 形状类
                '圆形': 0.5, '方形': 0.5, '三角': 0.5, '长方形': 0.5, '椭圆': 0.5,
                '形状': 0.4, '几何': 0.4,
                
                # 常见物品类
                '汽车': 0.7, '房子': 0.7, '树': 0.6, '花': 0.6, '草': 0.5,
                '天空': 0.5, '云': 0.5, '山': 0.6, '水': 0.5, '石头': 0.5
            }
            
            keyword_scores = []
            for keyword, weight in keywords.items():
                # 支持部分匹配和完整匹配
                if keyword in text_lower:
                    # 完整匹配得满分
                    keyword_scores.append(weight)
                else:
                    # 检查部分匹配 (子字符串)
                    partial_score = 0.0
                    words_in_text = text_lower.split()
                    for word in words_in_text:
                        if keyword in word or word in keyword:
                            partial_score = max(partial_score, weight * 0.7)  # 部分匹配70%权重
                    keyword_scores.append(partial_score)
            
            # 4. 文本哈希特征
            text_hash = hashlib.md5(text.encode('utf-8')).hexdigest()
            hash_features = [int(text_hash[i:i+2], 16) for i in range(0, 32, 2)][:16]
            
            # 5. 生成更多真实特征，减少随机向量
            # 文本统计特征
            vowel_count = sum(1 for c in text_lower if c in 'aeiouàáảãạèéẻẽẹìíỉĩịòóỏõọùúủũụ')
            consonant_count = len([c for c in text_lower if c.isalpha()]) - vowel_count
            
            # 字符类型统计  
            chinese_count = sum(1 for c in text if '\u4e00' <= c <= '\u9fff')
            digit_count = sum(1 for c in text if c.isdigit())
            punct_count = sum(1 for c in text if not c.isalnum() and not c.isspace())
            
            # 扩展统计特征
            stat_features = [
                text_length/100.0,      # 文本长度
                word_count/50.0,        # 词数
                vowel_count/50.0,       # 元音数
                consonant_count/100.0,  # 辅音数
                chinese_count/50.0,     # 中文字符数
                digit_count/20.0,       # 数字字符数
                punct_count/20.0,       # 标点符号数
            ]
            
            # 关键词分数加权处理
            weighted_keyword_scores = [score * 2.0 for score in keyword_scores]  # 增强关键词权重
            
            # 6. 组合特征 (确保精确512维)
            features = np.concatenate([
                stat_features,              # 7维: 统计特征
                weighted_keyword_scores,    # 52维: 加权关键词分数  
                hash_features,              # 16维: 哈希特征
                hash_features,              # 16维: 重复哈希特征增强
                np.random.randn(421) * 0.02  # 421维: 填充向量 (7+52+16+16+421=512)
            ])
            
            # 确保精确512维
            if len(features) > 512:
                features = features[:512]
            elif len(features) < 512:
                padding = np.zeros(512 - len(features))
                features = np.concatenate([features, padding])
            
            # 标准化向量
            features = features / np.linalg.norm(features)
            
            logger.info(f"生成文本嵌入向量: {features.shape}")
            return features
            
        except Exception as e:
            logger.error(f"文本编码错误: {e}")
            # 返回随机向量作为fallback (统一512维)
            return np.random.randn(512) / 10.0
    
    def encode_text_batch(self, texts: List[str], use_clip: bool = True) -> np.ndarray:
        """
        批量编码文本。
        
        Args:
            texts: 文本列表
            use_clip: 兼容性参数
            
        Returns:
            嵌入向量数组
        """
        return np.array([self.encode_text(text, use_clip) for text in texts])
    
    def compute_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        计算两个嵌入向量的余弦相似度。
        
        Args:
            embedding1: 第一个嵌入向量
            embedding2: 第二个嵌入向量
            
        Returns:
            余弦相似度分数
        """
        try:
            # 标准化嵌入向量
            norm1 = np.linalg.norm(embedding1)
            norm2 = np.linalg.norm(embedding2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            embedding1_norm = embedding1 / norm1
            embedding2_norm = embedding2 / norm2
            
            similarity = np.dot(embedding1_norm, embedding2_norm)
            return float(similarity)
            
        except Exception as e:
            logger.error(f"计算相似度错误: {e}")
            return 0.0
    
    def get_embedding_dimension(self, use_clip: bool = True) -> int:
        """
        获取嵌入向量的维度。
        
        Args:
            use_clip: 兼容性参数（已统一使用512维）
            
        Returns:
            嵌入维度 (统一512维)
        """
        return 512  # 统一使用512维嵌入 
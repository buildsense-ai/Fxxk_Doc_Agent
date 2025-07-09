"""
Gemini图片描述生成服务
通过OpenRouter API调用Google Gemini 2.5 Pro模型为图片生成详细描述
"""

import os
import base64
import io
from PIL import Image
from typing import Optional, Dict, Any, List, Union
import logging
from pathlib import Path
import time
from openai import OpenAI

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GeminiDescriptionService:
    """
    Gemini图片描述生成服务
    通过OpenRouter API使用Gemini 2.5 Pro模型分析图片并生成详细描述
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        初始化Gemini服务
        
        Args:
            api_key: OpenRouter API密钥，如果为None则从环境变量获取
        """
        # 获取API密钥
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        self.base_url = os.getenv('OPENROUTER_BASE_URL', 'https://openrouter.ai/api/v1')
        
        if not self.api_key or self.api_key == 'your-openrouter-api-key-here':
            logger.warning("⚠️ OpenRouter API密钥未设置，图片描述生成功能将不可用")
            self.client = None
            return
        
        # 配置OpenRouter客户端
        try:
            self.client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url
            )
            
            # 获取模型配置
            self.model_name = os.getenv('GEMINI_MODEL', 'google/gemini-2.0-flash-exp')
            self.max_tokens = int(os.getenv('GEMINI_MAX_TOKENS', '2048'))
            self.temperature = float(os.getenv('GEMINI_TEMPERATURE', '0.7'))
            
            logger.info(f"✅ OpenRouter Gemini客户端初始化成功: {self.model_name}")
            
        except Exception as e:
            logger.error(f"❌ OpenRouter客户端初始化失败: {e}")
            self.client = None
    
    def is_available(self) -> bool:
        """检查Gemini服务是否可用"""
        return self.client is not None
    
    def _image_to_base64(self, image_path: str) -> str:
        """
        将图片转换为base64编码
        
        Args:
            image_path: 图片文件路径
            
        Returns:
            base64编码的图片数据
        """
        try:
            # 读取并压缩图片
            image = Image.open(image_path).convert('RGB')
            
            # 如果图片太大，进行压缩
            max_size = (1024, 1024)
            if image.size[0] > max_size[0] or image.size[1] > max_size[1]:
                image.thumbnail(max_size, Image.Resampling.LANCZOS)
                logger.info(f"图片已压缩至: {image.size}")
            
            # 转换为base64
            buffer = io.BytesIO()
            image.save(buffer, format='JPEG', quality=85)
            img_data = buffer.getvalue()
            
            base64_string = base64.b64encode(img_data).decode('utf-8')
            return base64_string
            
        except Exception as e:
            logger.error(f"图片转换base64失败: {e}")
            raise
    
    def generate_description(self, image_path: str, user_description: str = "") -> Dict[str, Any]:
        """
        为图片生成AI描述
        
        Args:
            image_path: 图片文件路径
            user_description: 用户提供的描述（可选）
            
        Returns:
            包含AI描述和元数据的字典
        """
        if not self.is_available() or self.client is None:
            return {
                "ai_description": "",
                "success": False,
                "error": "OpenRouter Gemini服务不可用",
                "fallback_used": True
            }
        
        try:
            # 将图片转换为base64
            base64_image = self._image_to_base64(image_path)
            
            # 构建提示词
            prompt = self._build_prompt(user_description)
            
            # 构建消息 - 使用正确的格式
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ]
            
            # 调用OpenRouter API
            logger.info(f"正在调用OpenRouter Gemini API: {self.model_name}")
            start_time = time.time()
            
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,  # type: ignore
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            end_time = time.time()
            
            if response.choices and response.choices[0].message.content:
                ai_description = response.choices[0].message.content.strip()
                
                logger.info(f"✅ Gemini成功生成描述: {len(ai_description)} 字符, 耗时: {end_time-start_time:.2f}s")
                
                return {
                    "ai_description": ai_description,
                    "success": True,
                    "error": None,
                    "fallback_used": False,
                    "model_used": self.model_name,
                    "tokens_used": response.usage.total_tokens if response.usage else 0,
                    "generation_time": round(end_time - start_time, 2)
                }
            else:
                logger.warning("⚠️ OpenRouter返回空描述")
                return self._generate_fallback_description(image_path, user_description)
                
        except Exception as e:
            logger.error(f"❌ OpenRouter Gemini描述生成失败: {e}")
            return self._generate_fallback_description(image_path, user_description, str(e))
    
    def _build_prompt(self, user_description: str = "") -> str:
        """
        构建Gemini提示词
        
        Args:
            user_description: 用户描述
            
        Returns:
            完整的提示词
        """
        base_prompt = """请详细描述这张图片的内容。要求：

1. **主要内容**：详细描述图片中的主要物体、人物、场景、动作
2. **视觉特征**：说明主要的颜色、纹理、光线、风格等视觉特征  
3. **空间布局**：描述物体之间的位置关系和场景的空间结构
4. **细节特色**：注意任何独特、有趣或值得关注的细节
5. **情感氛围**：如果适用，描述图片传达的情感、氛围或感受

请用中文回答，描述要准确、详细但简洁（建议300-600字）。描述应该丰富具体，便于他人根据描述想象出图片内容。"""
        
        if user_description:
            base_prompt += f"\n\n**用户提供的描述供参考**：{user_description}"
            base_prompt += "\n请在此基础上补充更多详细的视觉信息和细节。"
        
        return base_prompt
    
    def _generate_fallback_description(self, image_path: str, user_description: str = "", error: str = "") -> Dict[str, Any]:
        """
        生成fallback描述（当Gemini不可用时）
        
        Args:
            image_path: 图片路径
            user_description: 用户描述
            error: 错误信息
            
        Returns:
            Fallback描述结果
        """
        try:
            # 基于文件名和基本图片信息生成描述
            image = Image.open(image_path)
            filename = Path(image_path).stem
            
            # 获取图片基本信息
            width, height = image.size
            mode = image.mode
            
            fallback_description = f"图片文件：{filename}，尺寸：{width}x{height}，格式：{mode}"
            
            if user_description:
                fallback_description = f"{user_description}。{fallback_description}"
            
            return {
                "ai_description": fallback_description,
                "success": False,
                "error": error or "OpenRouter Gemini服务不可用，使用简化描述",
                "fallback_used": True,
                "model_used": "fallback"
            }
            
        except Exception as e:
            logger.error(f"❌ Fallback描述生成失败: {e}")
            return {
                "ai_description": user_description or "无法生成图片描述",
                "success": False,
                "error": f"所有描述生成方法失败: {e}",
                "fallback_used": True,
                "model_used": "none"
            }
    
    def batch_generate_descriptions(self, image_paths: List[str], user_descriptions: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        批量生成图片描述
        
        Args:
            image_paths: 图片路径列表
            user_descriptions: 用户描述列表（可选）
            
        Returns:
            描述结果列表
        """
        if not self.is_available():
            logger.warning("⚠️ OpenRouter Gemini不可用，跳过批量描述生成")
            return []
        
        user_descriptions = user_descriptions or [""] * len(image_paths)
        results = []
        
        for i, image_path in enumerate(image_paths):
            user_desc = user_descriptions[i] if i < len(user_descriptions) else ""
            result = self.generate_description(image_path, user_desc)
            results.append(result)
            
            # 添加延迟避免API限制
            time.sleep(1.0)  # OpenRouter建议的延迟
        
        return results
    
    def test_connection(self) -> Dict[str, Any]:
        """
        测试OpenRouter API连接
        
        Returns:
            测试结果
        """
        if not self.api_key or self.api_key == 'your-openrouter-api-key-here':
            return {
                "success": False,
                "error": "OpenRouter API密钥未配置",
                "available": False
            }
        
        if self.client is None:
            return {
                "success": False,
                "error": "OpenRouter客户端未初始化",
                "available": False
            }
        
        try:
            # 简单的测试请求
            test_messages = [
                {
                    "role": "user", 
                    "content": "请说'OpenRouter连接测试成功'"
                }
            ]
            
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=test_messages,  # type: ignore
                max_tokens=50,
                temperature=0.1
            )
            
            if response.choices and response.choices[0].message.content:
                return {
                    "success": True,
                    "error": None,
                    "available": True,
                    "model": self.model_name,
                    "base_url": self.base_url,
                    "response": response.choices[0].message.content.strip()
                }
            else:
                return {
                    "success": False,
                    "error": "API返回空响应",
                    "available": False
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "available": False
            }
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        获取模型信息
        
        Returns:
            模型信息字典
        """
        return {
            "service": "OpenRouter",
            "model": self.model_name,
            "base_url": self.base_url,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "available": self.is_available()
        } 
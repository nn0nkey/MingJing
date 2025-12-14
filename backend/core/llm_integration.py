"""
LLM 集成模块

支持:
- 加载训练好的本地模型
- 配置 API 模式
- 模型热切换
"""

import os
import logging
from typing import Optional, Dict, Any
from pathlib import Path

from config import get_settings

logger = logging.getLogger("mingjing.llm")


class LLMManager:
    """
    LLM 管理器
    
    用于管理 LLM 验证器的配置和切换
    
    用法:
        manager = LLMManager()
        
        # 配置本地模型
        manager.configure_local_model("/path/to/model")
        
        # 配置 API
        manager.configure_api(api_key="sk-xxx", model="gpt-3.5-turbo")
        
        # 获取验证器
        verifier = manager.get_verifier()
    """
    
    def __init__(self):
        self.settings = get_settings()
        self._verifier = None
        self._mode = self.settings.llm_verifier.mode
        self._config = {}
    
    def configure_local_model(
        self,
        model_path: str,
        device: str = "auto",
        max_new_tokens: int = 200,
    ) -> bool:
        """
        配置本地模型
        
        :param model_path: 模型路径（可以是HuggingFace模型名或本地路径）
        :param device: 设备（auto/cpu/cuda）
        :param max_new_tokens: 最大生成token数
        :return: 是否成功
        """
        path = Path(model_path)
        
        # 检查是否是本地路径
        if path.exists():
            logger.info(f"使用本地模型: {model_path}")
        else:
            logger.info(f"使用HuggingFace模型: {model_path}")
        
        self._mode = "local"
        self._config = {
            "model_path": model_path,
            "device": device,
            "max_new_tokens": max_new_tokens,
        }
        
        # 更新配置
        self.settings.set("llm_verifier.mode", "local")
        self.settings.set("llm_verifier.local.model_path", model_path)
        self.settings.set("llm_verifier.local.device", device)
        self.settings.set("llm_verifier.local.max_new_tokens", max_new_tokens)
        
        # 重新创建验证器
        self._verifier = None
        
        return True
    
    def configure_api(
        self,
        api_key: str,
        api_base: str = "https://api.openai.com/v1",
        model: str = "gpt-3.5-turbo",
        timeout: int = 30,
    ) -> bool:
        """
        配置 API 模式
        
        :param api_key: API 密钥
        :param api_base: API 基础 URL
        :param model: 模型名称
        :param timeout: 超时时间
        :return: 是否成功
        """
        self._mode = "api"
        self._config = {
            "api_key": api_key,
            "api_base": api_base,
            "model": model,
            "timeout": timeout,
        }
        
        # 更新配置
        self.settings.set("llm_verifier.mode", "api")
        self.settings.set("llm_verifier.api.api_key", api_key)
        self.settings.set("llm_verifier.api.base_url", api_base)
        self.settings.set("llm_verifier.api.model", model)
        self.settings.set("llm_verifier.api.timeout", timeout)
        
        # 重新创建验证器
        self._verifier = None
        
        return True
    
    def configure_mock(self, default_is_sensitive: bool = True, default_confidence: float = 0.8) -> bool:
        """
        配置 Mock 模式（用于测试）
        
        :param default_is_sensitive: 默认是否敏感
        :param default_confidence: 默认置信度
        :return: 是否成功
        """
        self._mode = "mock"
        self._config = {
            "default_is_sensitive": default_is_sensitive,
            "default_confidence": default_confidence,
        }
        
        self.settings.set("llm_verifier.mode", "mock")
        self._verifier = None
        
        return True
    
    def get_verifier(self):
        """获取验证器实例"""
        if self._verifier is not None:
            return self._verifier
        
        from presidio_analyzer.nlp_engine import create_verifier
        
        config = self.settings.llm_verifier
        
        try:
            if self._mode == "api":
                api_key = self._config.get("api_key") or config.api_key
                if not api_key:
                    logger.warning("API模式需要配置api_key，回退到mock模式")
                    self._verifier = create_verifier(mode="mock")
                else:
                    self._verifier = create_verifier(
                        mode="api",
                        api_key=api_key,
                        api_base=self._config.get("api_base") or config.api_base_url,
                        model=self._config.get("model") or config.api_model,
                        timeout=self._config.get("timeout") or config.api_timeout,
                        score_threshold=config.score_threshold,
                        context_window=config.context_window,
                    )
                    logger.info(f"API验证器创建成功: {self._config.get('model') or config.api_model}")
            
            elif self._mode == "local":
                model_path = self._config.get("model_path") or config.local_model_path
                if not model_path:
                    logger.warning("本地模式需要配置model_path，回退到mock模式")
                    self._verifier = create_verifier(mode="mock")
                else:
                    self._verifier = create_verifier(
                        mode="local",
                        model_path=model_path,
                        device=self._config.get("device") or config.local_device,
                        max_new_tokens=self._config.get("max_new_tokens") or config.local_max_new_tokens,
                        score_threshold=config.score_threshold,
                        context_window=config.context_window,
                    )
                    logger.info(f"本地验证器创建成功: {model_path}")
            
            else:
                self._verifier = create_verifier(
                    mode="mock",
                    score_threshold=config.score_threshold,
                    context_window=config.context_window,
                    default_is_sensitive=self._config.get("default_is_sensitive", True),
                    default_confidence=self._config.get("default_confidence", 0.8),
                )
                logger.info("Mock验证器创建成功")
        
        except Exception as e:
            logger.error(f"创建验证器失败: {e}")
            self._verifier = create_verifier(mode="mock")
        
        return self._verifier
    
    def get_status(self) -> Dict[str, Any]:
        """获取当前状态"""
        return {
            "mode": self._mode,
            "enabled": self.settings.llm_verifier.enabled,
            "score_threshold": self.settings.llm_verifier.score_threshold,
            "context_window": self.settings.llm_verifier.context_window,
            "config": {
                k: v if k != "api_key" else "***" 
                for k, v in self._config.items()
            },
        }
    
    def reload(self) -> None:
        """重新加载验证器"""
        self._verifier = None
        self.settings.reload()
        self._mode = self.settings.llm_verifier.mode


# 全局 LLM 管理器
_llm_manager: Optional[LLMManager] = None


def get_llm_manager() -> LLMManager:
    """获取全局 LLM 管理器"""
    global _llm_manager
    if _llm_manager is None:
        _llm_manager = LLMManager()
    return _llm_manager

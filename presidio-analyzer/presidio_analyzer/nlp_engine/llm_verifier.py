"""
LLM Verifier for low-confidence entity verification.

对评分低于阈值的识别结果进行大模型二次验证。
支持两种模式：
1. API模式：调用远程LLM API（OpenAI、通义千问等）
2. 本地模式：加载本地模型（transformers）
"""

import logging
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional, Dict, Any, Tuple

logger = logging.getLogger("presidio-analyzer")


@dataclass
class VerificationResult:
    """LLM验证结果。"""
    entity_text: str           # 实体文本
    entity_type: str           # 实体类型
    original_score: float      # 原始分数
    is_sensitive: bool         # LLM判断是否为敏感信息
    confidence: float          # LLM置信度 (0-1)
    final_score: float         # 最终分数
    reason: str                # LLM给出的理由
    context: str               # 上下文


class BaseLLMVerifier(ABC):
    """LLM验证器基类。"""
    
    # 验证提示词模板
    PROMPT_TEMPLATE = """你是一个敏感信息识别专家。请判断以下文本中标记的内容是否为真正的敏感信息。

【上下文】
{context}

【待验证内容】
- 文本: "{entity_text}"
- 预测类型: {entity_type}

【实体类型说明】
- PERSON: 真实人名（不是称呼、职位、代词）
- LOCATION: 真实地址/地名（不是方位词、泛指）
- ORGANIZATION: 真实组织机构名（不是泛指、行业名）
- CN_ID_CARD: 中国身份证号
- CN_PHONE: 中国手机号/电话号码
- CN_BANK_CARD: 银行卡号
- CN_EMAIL: 电子邮箱地址
- CN_IP_ADDRESS: IP地址（需要是真实IP，不是版本号）
- CN_POSTAL_CODE: 邮政编码（需要是真实邮编，不是普通数字）

请以JSON格式回答：
{{
    "is_sensitive": true/false,
    "confidence": 0.0-1.0,
    "reason": "判断理由"
}}

只输出JSON，不要其他内容。"""

    def __init__(self, score_threshold: float = 0.5, context_window: int = 30):
        """
        初始化验证器。
        
        :param score_threshold: 分数阈值，低于此值的结果需要验证
        :param context_window: 上下文窗口大小（前后各多少字符）
        """
        self.score_threshold = score_threshold
        self.context_window = context_window

    def extract_context(self, text: str, start: int, end: int) -> str:
        """
        提取实体周围的上下文。
        
        :param text: 完整文本
        :param start: 实体起始位置
        :param end: 实体结束位置
        :return: 上下文文本，实体用【】标记
        """
        context_start = max(0, start - self.context_window)
        context_end = min(len(text), end + self.context_window)
        
        # 构建上下文，用【】标记实体
        before = text[context_start:start]
        entity = text[start:end]
        after = text[end:context_end]
        
        # 添加省略号
        prefix = "..." if context_start > 0 else ""
        suffix = "..." if context_end < len(text) else ""
        
        return f"{prefix}{before}【{entity}】{after}{suffix}"

    def build_prompt(self, entity_text: str, entity_type: str, context: str) -> str:
        """构建验证提示词。"""
        return self.PROMPT_TEMPLATE.format(
            context=context,
            entity_text=entity_text,
            entity_type=entity_type
        )

    def parse_response(self, response: str) -> Tuple[bool, float, str]:
        """
        解析LLM响应。
        
        :param response: LLM原始响应
        :return: (is_sensitive, confidence, reason)
        """
        try:
            # 尝试提取JSON
            response = response.strip()
            if response.startswith("```"):
                # 移除markdown代码块
                lines = response.split("\n")
                response = "\n".join(lines[1:-1])
            
            data = json.loads(response)
            is_sensitive = data.get("is_sensitive", False)
            confidence = float(data.get("confidence", 0.5))
            reason = data.get("reason", "")
            return is_sensitive, confidence, reason
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.warning(f"解析LLM响应失败: {e}, 响应: {response}")
            # 解析失败，保守处理，认为是敏感信息
            return True, 0.5, "解析失败，保守判断为敏感信息"

    @abstractmethod
    def _call_llm(self, prompt: str) -> str:
        """
        调用LLM获取响应（子类实现）。
        
        :param prompt: 提示词
        :return: LLM响应文本
        """
        pass

    def verify_single(
        self, 
        text: str, 
        entity_text: str, 
        entity_type: str, 
        start: int, 
        end: int,
        original_score: float
    ) -> VerificationResult:
        """
        验证单个实体。
        
        :param text: 完整文本
        :param entity_text: 实体文本
        :param entity_type: 实体类型
        :param start: 起始位置
        :param end: 结束位置
        :param original_score: 原始分数
        :return: 验证结果
        """
        context = self.extract_context(text, start, end)
        prompt = self.build_prompt(entity_text, entity_type, context)
        
        try:
            response = self._call_llm(prompt)
            is_sensitive, confidence, reason = self.parse_response(response)
        except Exception as e:
            logger.error(f"LLM调用失败: {e}")
            # 调用失败，保守处理
            is_sensitive, confidence, reason = True, 0.5, f"LLM调用失败: {e}"
        
        # 计算最终分数
        if is_sensitive:
            final_score = max(original_score, confidence)
        else:
            final_score = 0.0  # 确认不是敏感信息
        
        return VerificationResult(
            entity_text=entity_text,
            entity_type=entity_type,
            original_score=original_score,
            is_sensitive=is_sensitive,
            confidence=confidence,
            final_score=final_score,
            reason=reason,
            context=context
        )

    def verify_results(
        self, 
        text: str, 
        results: List[Any]
    ) -> List[Tuple[Any, Optional[VerificationResult]]]:
        """
        验证识别结果列表。
        
        :param text: 完整文本
        :param results: RecognizerResult列表
        :return: [(原结果, 验证结果或None)]，分数>=阈值的验证结果为None
        """
        verified = []
        
        for result in results:
            if result.score < self.score_threshold:
                # 需要验证
                entity_text = text[result.start:result.end]
                verification = self.verify_single(
                    text=text,
                    entity_text=entity_text,
                    entity_type=result.entity_type,
                    start=result.start,
                    end=result.end,
                    original_score=result.score
                )
                verified.append((result, verification))
            else:
                # 不需要验证
                verified.append((result, None))
        
        return verified


class APILLMVerifier(BaseLLMVerifier):
    """
    API模式LLM验证器。
    
    支持OpenAI兼容的API（OpenAI、通义千问、智谱等）。
    """
    
    def __init__(
        self,
        api_key: str,
        api_base: str = "https://api.openai.com/v1",
        model: str = "gpt-3.5-turbo",
        score_threshold: float = 0.5,
        context_window: int = 30,
        timeout: int = 30,
    ):
        """
        初始化API验证器。
        
        :param api_key: API密钥
        :param api_base: API基础URL
        :param model: 模型名称
        :param score_threshold: 分数阈值
        :param context_window: 上下文窗口
        :param timeout: 请求超时时间（秒）
        """
        super().__init__(score_threshold, context_window)
        self.api_key = api_key
        self.api_base = api_base.rstrip("/")
        self.model = model
        self.timeout = timeout
        
        # 延迟导入
        self._client = None

    def _get_client(self):
        """获取或创建API客户端。"""
        if self._client is None:
            try:
                from openai import OpenAI
                self._client = OpenAI(
                    api_key=self.api_key,
                    base_url=self.api_base,
                    timeout=self.timeout
                )
            except ImportError:
                raise ImportError("请安装openai库: pip install openai")
        return self._client

    def _call_llm(self, prompt: str) -> str:
        """调用API。"""
        client = self._get_client()
        response = client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "你是一个敏感信息识别专家，只输出JSON格式的判断结果。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=200
        )
        return response.choices[0].message.content


class LocalLLMVerifier(BaseLLMVerifier):
    """
    本地模型LLM验证器。
    
    使用transformers加载本地模型。
    """
    
    def __init__(
        self,
        model_path: str,
        score_threshold: float = 0.5,
        context_window: int = 30,
        device: str = "auto",
        torch_dtype: str = "auto",
        max_new_tokens: int = 200,
    ):
        """
        初始化本地模型验证器。
        
        :param model_path: 模型路径或HuggingFace模型ID
        :param score_threshold: 分数阈值
        :param context_window: 上下文窗口
        :param device: 设备（auto/cpu/cuda）
        :param torch_dtype: 数据类型
        :param max_new_tokens: 最大生成token数
        """
        super().__init__(score_threshold, context_window)
        self.model_path = model_path
        self.device = device
        self.torch_dtype = torch_dtype
        self.max_new_tokens = max_new_tokens
        
        self._model = None
        self._tokenizer = None

    def _load_model(self):
        """加载模型。"""
        if self._model is None:
            try:
                from transformers import AutoModelForCausalLM, AutoTokenizer
                import torch
                
                logger.info(f"加载本地模型: {self.model_path}")
                
                # 确定数据类型
                if self.torch_dtype == "auto":
                    dtype = torch.float16 if torch.cuda.is_available() else torch.float32
                elif self.torch_dtype == "float16":
                    dtype = torch.float16
                elif self.torch_dtype == "bfloat16":
                    dtype = torch.bfloat16
                else:
                    dtype = torch.float32
                
                # 加载tokenizer
                self._tokenizer = AutoTokenizer.from_pretrained(
                    self.model_path,
                    trust_remote_code=True
                )
                
                # 加载模型
                self._model = AutoModelForCausalLM.from_pretrained(
                    self.model_path,
                    torch_dtype=dtype,
                    device_map=self.device,
                    trust_remote_code=True
                )
                
                logger.info("模型加载完成")
                
            except ImportError:
                raise ImportError("请安装transformers库: pip install transformers torch")
        
        return self._model, self._tokenizer

    def _call_llm(self, prompt: str) -> str:
        """调用本地模型。"""
        model, tokenizer = self._load_model()
        
        # 构建输入
        messages = [
            {"role": "system", "content": "你是一个敏感信息识别专家，只输出JSON格式的判断结果。"},
            {"role": "user", "content": prompt}
        ]
        
        # 尝试使用chat模板
        if hasattr(tokenizer, "apply_chat_template"):
            input_text = tokenizer.apply_chat_template(
                messages, 
                tokenize=False, 
                add_generation_prompt=True
            )
        else:
            input_text = f"System: {messages[0]['content']}\nUser: {messages[1]['content']}\nAssistant:"
        
        inputs = tokenizer(input_text, return_tensors="pt").to(model.device)
        
        # 生成
        outputs = model.generate(
            **inputs,
            max_new_tokens=self.max_new_tokens,
            temperature=0.1,
            do_sample=True,
            pad_token_id=tokenizer.eos_token_id
        )
        
        # 解码
        response = tokenizer.decode(outputs[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True)
        return response.strip()


class MockLLMVerifier(BaseLLMVerifier):
    """
    模拟LLM验证器（用于测试）。
    """
    
    def __init__(
        self,
        score_threshold: float = 0.5,
        context_window: int = 30,
        default_is_sensitive: bool = True,
        default_confidence: float = 0.8,
    ):
        super().__init__(score_threshold, context_window)
        self.default_is_sensitive = default_is_sensitive
        self.default_confidence = default_confidence

    def _call_llm(self, prompt: str) -> str:
        """模拟LLM响应。"""
        return json.dumps({
            "is_sensitive": self.default_is_sensitive,
            "confidence": self.default_confidence,
            "reason": "模拟验证结果"
        })


def create_verifier(
    mode: str = "api",
    **kwargs
) -> BaseLLMVerifier:
    """
    创建LLM验证器的工厂函数。
    
    :param mode: 模式（api/local/mock）
    :param kwargs: 其他参数
    :return: LLM验证器实例
    
    示例:
        # API模式
        verifier = create_verifier(
            mode="api",
            api_key="sk-xxx",
            api_base="https://api.openai.com/v1",
            model="gpt-3.5-turbo"
        )
        
        # 本地模型模式
        verifier = create_verifier(
            mode="local",
            model_path="/path/to/model"
        )
        
        # 测试模式
        verifier = create_verifier(mode="mock")
    """
    if mode == "api":
        return APILLMVerifier(**kwargs)
    elif mode == "local":
        return LocalLLMVerifier(**kwargs)
    elif mode == "mock":
        return MockLLMVerifier(**kwargs)
    else:
        raise ValueError(f"不支持的模式: {mode}，可选: api/local/mock")

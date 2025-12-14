"""
工厂模式 Provider

提供统一的组件创建接口，支持:
- 基于配置文件创建
- 运行时动态配置
- 自定义扩展
"""

import os
import sys
import logging
from typing import Any, Dict, List, Optional, Type

# 添加 presidio-analyzer 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "presidio-analyzer"))

from presidio_analyzer import AnalyzerEngine, RecognizerRegistry, PatternRecognizer, Pattern
from presidio_analyzer.nlp_engine import (
    SpacyNlpEngine,
    NerModelConfiguration,
    NlpEngine,
    create_verifier,
    BaseLLMVerifier,
)

from config import Settings, get_settings
from config.rules_manager import RulesManager, get_rules_manager, Rule

logger = logging.getLogger("mingjing.providers")


class NlpEngineProvider:
    """
    NLP引擎提供者
    
    根据配置创建NLP引擎实例
    """
    
    def __init__(self, settings: Optional[Settings] = None):
        """
        初始化
        
        :param settings: 配置对象，为空则使用全局配置
        """
        self.settings = settings or get_settings()
    
    def create(self) -> Optional[NlpEngine]:
        """
        创建NLP引擎
        
        :return: NlpEngine实例，失败返回None
        """
        config = self.settings.nlp_engine
        
        if config.type == "spacy":
            return self._create_spacy_engine(config)
        elif config.type == "stanza":
            return self._create_stanza_engine(config)
        elif config.type == "transformers":
            return self._create_transformers_engine(config)
        else:
            logger.error(f"不支持的NLP引擎类型: {config.type}")
            return None
    
    def _create_spacy_engine(self, config) -> Optional[SpacyNlpEngine]:
        """创建spaCy引擎"""
        try:
            ner_config = NerModelConfiguration(
                model_to_presidio_entity_mapping=config.entity_mapping,
                labels_to_ignore=config.labels_to_ignore,
                default_score=config.default_score,
            )
            
            engine = SpacyNlpEngine(
                models=[{
                    "lang_code": self.settings.language,
                    "model_name": config.model,
                }],
                ner_model_configuration=ner_config,
            )
            engine.load()
            logger.info(f"spaCy引擎加载成功: {config.model}")
            return engine
        except Exception as e:
            logger.error(f"spaCy引擎加载失败: {e}")
            return None
    
    def _create_stanza_engine(self, config) -> Optional[NlpEngine]:
        """创建Stanza引擎"""
        try:
            from presidio_analyzer.nlp_engine import StanzaNlpEngine
            
            ner_config = NerModelConfiguration(
                model_to_presidio_entity_mapping=config.entity_mapping,
                labels_to_ignore=config.labels_to_ignore,
                default_score=config.default_score,
            )
            
            engine = StanzaNlpEngine(
                models=[{
                    "lang_code": self.settings.language,
                    "model_name": config.model,
                }],
                ner_model_configuration=ner_config,
            )
            engine.load()
            logger.info(f"Stanza引擎加载成功: {config.model}")
            return engine
        except Exception as e:
            logger.error(f"Stanza引擎加载失败: {e}")
            return None
    
    def _create_transformers_engine(self, config) -> Optional[NlpEngine]:
        """创建Transformers引擎"""
        try:
            from presidio_analyzer.nlp_engine import TransformersNlpEngine
            
            engine = TransformersNlpEngine(
                models=[{
                    "lang_code": self.settings.language,
                    "model_name": config.model,
                }],
            )
            engine.load()
            logger.info(f"Transformers引擎加载成功: {config.model}")
            return engine
        except Exception as e:
            logger.error(f"Transformers引擎加载失败: {e}")
            return None


class RecognizerRegistryProvider:
    """
    识别器注册表提供者
    
    根据配置创建识别器注册表，包括:
    - 内置中文识别器
    - 自定义规则识别器
    - NLP识别器
    """
    
    def __init__(self, settings: Optional[Settings] = None, rules_manager: Optional[RulesManager] = None):
        """
        初始化
        
        :param settings: 配置对象
        :param rules_manager: 规则管理器
        """
        self.settings = settings or get_settings()
        self.rules_manager = rules_manager or get_rules_manager()
    
    def create(self, include_nlp: bool = True) -> RecognizerRegistry:
        """
        创建识别器注册表
        
        :param include_nlp: 是否包含NLP识别器
        :return: RecognizerRegistry实例
        """
        registry = RecognizerRegistry()
        registry.supported_languages = [self.settings.language]
        
        # 添加内置识别器（Python 类，有校验逻辑）
        self._add_builtin_recognizers(registry)
        
        # 添加自定义规则识别器（从配置文件加载）
        self._add_custom_recognizers(registry)
        
        # 添加NLP识别器
        if include_nlp:
            self._add_nlp_recognizers(registry)
        
        return registry
    
    def _add_builtin_recognizers(self, registry: RecognizerRegistry) -> None:
        """添加内置中文识别器（Python 类，有校验逻辑）"""
        from presidio_analyzer.predefined_recognizers.country_specific.china import (
            CnIdCardRecognizer,
            CnPhoneRecognizer,
            CnBankCardRecognizer,
            CnEmailRecognizer,
            CnIpAddressRecognizer,
            CnPostalCodeRecognizer,
            CnVehiclePlateRecognizer,
            CnPassportRecognizer,
            CnDriverLicenseRecognizer,
            CnMilitaryIdRecognizer,
            CnSocialCreditCodeRecognizer,
            CnMedicalLicenseRecognizer,
            CnMacAddressRecognizer,
            CnJdbcRecognizer,
            CnJwtRecognizer,
            CnCloudKeyRecognizer,
            CnWechatRecognizer,
            CnSensitiveFieldRecognizer,
        )
        
        # 识别器映射
        recognizer_classes = {
            "CN_ID_CARD": CnIdCardRecognizer,
            "CN_PHONE": CnPhoneRecognizer,
            "CN_BANK_CARD": CnBankCardRecognizer,
            "CN_EMAIL": CnEmailRecognizer,
            "CN_IP_ADDRESS": CnIpAddressRecognizer,
            "CN_POSTAL_CODE": CnPostalCodeRecognizer,
            "CN_VEHICLE_PLATE": CnVehiclePlateRecognizer,
            "CN_PASSPORT": CnPassportRecognizer,
            "CN_DRIVER_LICENSE": CnDriverLicenseRecognizer,
            "CN_MILITARY_ID": CnMilitaryIdRecognizer,
            "CN_SOCIAL_CREDIT_CODE": CnSocialCreditCodeRecognizer,
            "CN_MEDICAL_LICENSE": CnMedicalLicenseRecognizer,
            "CN_MAC_ADDRESS": CnMacAddressRecognizer,
            "CN_JDBC": CnJdbcRecognizer,
            "CN_JWT": CnJwtRecognizer,
            "CN_CLOUD_KEY": CnCloudKeyRecognizer,
            "CN_WECHAT": CnWechatRecognizer,
            "CN_SENSITIVE_FIELD": CnSensitiveFieldRecognizer,
        }
        
        added_count = 0
        for name, recognizer_class in recognizer_classes.items():
            if self.settings.is_recognizer_enabled(name):
                try:
                    recognizer = recognizer_class()
                    registry.add_recognizer(recognizer)
                    added_count += 1
                except Exception as e:
                    logger.warning(f"添加识别器 {name} 失败: {e}")
        
        logger.info(f"添加了 {added_count} 个内置识别器")
    
    def _add_custom_recognizers(self, registry: RecognizerRegistry) -> None:
        """添加自定义规则识别器（从配置文件加载）"""
        rules = self.rules_manager.get_custom_rules()
        enabled_rules = [r for r in rules if r.enabled]
        
        for rule in enabled_rules:
            try:
                recognizer = self._create_recognizer_from_rule(rule)
                registry.add_recognizer(recognizer)
                logger.debug(f"添加自定义识别器: {rule.name}")
            except Exception as e:
                logger.warning(f"添加自定义识别器 {rule.name} 失败: {e}")
        
        if enabled_rules:
            logger.info(f"添加了 {len(enabled_rules)} 个自定义识别器")
    
    def _create_recognizer_from_rule(self, rule: Rule) -> PatternRecognizer:
        """从规则创建识别器"""
        patterns = [
            Pattern(
                name=p.name,
                regex=p.regex,
                score=p.score,
            )
            for p in rule.patterns
        ]
        
        # 根据来源设置识别器名称
        recognizer_name = f"{'Builtin' if rule.is_builtin() else 'Custom'}Recognizer_{rule.name}"
        
        return PatternRecognizer(
            supported_entity=rule.entity_type,
            name=recognizer_name,
            patterns=patterns,
            context=rule.context,
            supported_language=self.settings.language,
        )
    
    def _add_nlp_recognizers(self, registry: RecognizerRegistry) -> None:
        """添加NLP识别器"""
        try:
            from presidio_analyzer.predefined_recognizers.country_specific.china import CnNlpRecognizer
            
            if self.settings.is_recognizer_enabled("PERSON"):
                recognizer = CnNlpRecognizer()
                registry.add_recognizer(recognizer)
                logger.info("添加了NLP识别器")
        except Exception as e:
            logger.warning(f"添加NLP识别器失败: {e}")


class LlmVerifierProvider:
    """
    LLM验证器提供者
    
    根据配置创建LLM验证器实例
    """
    
    def __init__(self, settings: Optional[Settings] = None):
        """
        初始化
        
        :param settings: 配置对象
        """
        self.settings = settings or get_settings()
    
    def create(self) -> Optional[BaseLLMVerifier]:
        """
        创建LLM验证器
        
        :return: BaseLLMVerifier实例
        """
        config = self.settings.llm_verifier
        
        if not config.enabled:
            logger.info("LLM验证器已禁用")
            return None
        
        try:
            if config.mode == "api":
                if not config.api_key:
                    logger.warning("API模式需要配置api_key，回退到mock模式")
                    return self._create_mock_verifier(config)
                return self._create_api_verifier(config)
            elif config.mode == "local":
                if not config.local_model_path:
                    logger.warning("本地模式需要配置model_path，回退到mock模式")
                    return self._create_mock_verifier(config)
                return self._create_local_verifier(config)
            else:
                return self._create_mock_verifier(config)
        except Exception as e:
            logger.error(f"创建LLM验证器失败: {e}")
            return self._create_mock_verifier(config)
    
    def _create_api_verifier(self, config) -> BaseLLMVerifier:
        """创建API验证器"""
        verifier = create_verifier(
            mode="api",
            api_key=config.api_key,
            api_base=config.api_base_url,
            model=config.api_model,
            score_threshold=config.score_threshold,
            context_window=config.context_window,
            timeout=config.api_timeout,
        )
        logger.info(f"API验证器创建成功: {config.api_model}")
        return verifier
    
    def _create_local_verifier(self, config) -> BaseLLMVerifier:
        """创建本地模型验证器"""
        verifier = create_verifier(
            mode="local",
            model_path=config.local_model_path,
            score_threshold=config.score_threshold,
            context_window=config.context_window,
            device=config.local_device,
            max_new_tokens=config.local_max_new_tokens,
        )
        logger.info(f"本地验证器创建成功: {config.local_model_path}")
        return verifier
    
    def _create_mock_verifier(self, config) -> BaseLLMVerifier:
        """创建Mock验证器"""
        verifier = create_verifier(
            mode="mock",
            score_threshold=config.score_threshold,
            context_window=config.context_window,
        )
        logger.info("Mock验证器创建成功")
        return verifier


class AnalyzerEngineProvider:
    """
    分析引擎提供者
    
    整合所有组件，创建完整的分析引擎
    """
    
    def __init__(self, settings: Optional[Settings] = None):
        """
        初始化
        
        :param settings: 配置对象
        """
        self.settings = settings or get_settings()
        self._nlp_engine: Optional[NlpEngine] = None
        self._registry: Optional[RecognizerRegistry] = None
        self._verifier: Optional[BaseLLMVerifier] = None
        self._analyzer: Optional[AnalyzerEngine] = None
    
    def create(self) -> AnalyzerEngine:
        """
        创建分析引擎
        
        :return: AnalyzerEngine实例
        """
        # 创建NLP引擎
        nlp_provider = NlpEngineProvider(self.settings)
        self._nlp_engine = nlp_provider.create()
        
        # 创建识别器注册表
        registry_provider = RecognizerRegistryProvider(self.settings)
        self._registry = registry_provider.create(include_nlp=self._nlp_engine is not None)
        
        # 创建LLM验证器
        verifier_provider = LlmVerifierProvider(self.settings)
        self._verifier = verifier_provider.create()
        
        # 创建分析引擎
        self._analyzer = AnalyzerEngine(
            registry=self._registry,
            nlp_engine=self._nlp_engine,
            supported_languages=[self.settings.language],
        )
        
        logger.info("分析引擎创建成功")
        return self._analyzer
    
    @property
    def nlp_engine(self) -> Optional[NlpEngine]:
        """获取NLP引擎"""
        return self._nlp_engine
    
    @property
    def registry(self) -> Optional[RecognizerRegistry]:
        """获取识别器注册表"""
        return self._registry
    
    @property
    def verifier(self) -> Optional[BaseLLMVerifier]:
        """获取LLM验证器"""
        return self._verifier
    
    @property
    def analyzer(self) -> Optional[AnalyzerEngine]:
        """获取分析引擎"""
        return self._analyzer
    
    def get_supported_entities(self) -> List[str]:
        """获取支持的实体类型列表"""
        if self._registry:
            recognizers = self._registry.get_recognizers(
                language=self.settings.language,
                all_fields=True,
            )
            entities = set()
            for r in recognizers:
                entities.update(r.supported_entities)
            return sorted(list(entities))
        return []
    
    def reload(self) -> AnalyzerEngine:
        """重新加载分析引擎"""
        self.settings.reload()
        return self.create()

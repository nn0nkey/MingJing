"""
MingJing 配置管理模块

提供统一的配置加载、验证和访问接口。
"""

import os
import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, field
from functools import lru_cache


# 配置文件路径
CONFIG_DIR = Path(__file__).parent
DEFAULT_CONFIG_FILE = CONFIG_DIR / "settings.yaml"
CONTEXT_WORDS_FILE = CONFIG_DIR / "context_words.yaml"


@dataclass
class NlpEngineConfig:
    """NLP引擎配置"""
    type: str = "spacy"
    model: str = "zh_core_web_md"
    default_score: float = 0.4
    entity_mapping: Dict[str, str] = field(default_factory=dict)
    labels_to_ignore: List[str] = field(default_factory=list)


@dataclass
class LlmVerifierConfig:
    """LLM验证器配置"""
    enabled: bool = True
    mode: str = "mock"
    score_threshold: float = 0.5
    context_window: int = 30
    api_base_url: str = "https://api.openai.com/v1"
    api_model: str = "gpt-3.5-turbo"
    api_timeout: int = 30
    api_key: Optional[str] = None
    local_model_path: str = ""
    local_device: str = "auto"
    local_max_new_tokens: int = 200


@dataclass
class ScoringConfig:
    """评分配置"""
    high_confidence: float = 0.5
    low_confidence: float = 0.0
    type_scores: Dict[str, float] = field(default_factory=dict)


@dataclass
class RecognizerSettings:
    """单个识别器配置"""
    enabled: bool = True
    base_score: float = 0.4
    description: Optional[str] = None


@dataclass
class RecognizersConfig:
    """识别器配置"""
    enabled: List[str] = field(default_factory=list)
    disabled: List[str] = field(default_factory=list)
    settings: Dict[str, RecognizerSettings] = field(default_factory=dict)


@dataclass
class FileProcessingConfig:
    """文件处理配置"""
    supported_formats: List[str] = field(default_factory=list)
    archive_formats: List[str] = field(default_factory=list)
    max_file_size: int = 100  # MB
    chunk_size: int = 10  # MB
    temp_dir: str = "/tmp/mingjing"
    recursive_extract: bool = True


@dataclass
class PerformanceConfig:
    """性能配置"""
    batch_size: int = 100
    max_workers: int = 4
    cache_enabled: bool = True
    cache_ttl: int = 3600
    cache_max_size: int = 1000


@dataclass
class RiskLevel:
    """风险等级定义"""
    min_count: int
    types: List[str]


@dataclass
class ReportConfig:
    """报告配置"""
    output_dir: str = "./reports"
    formats: List[str] = field(default_factory=list)
    risk_levels: Dict[str, RiskLevel] = field(default_factory=dict)


class Settings:
    """
    系统配置管理类
    
    支持:
    - YAML配置文件加载
    - 环境变量覆盖
    - 运行时动态修改
    - 配置验证
    """
    
    def __init__(self, config_file: Optional[Union[str, Path]] = None):
        """
        初始化配置
        
        :param config_file: 配置文件路径，为空则使用默认配置
        """
        self._config: Dict[str, Any] = {}
        self._config_file = Path(config_file) if config_file else DEFAULT_CONFIG_FILE
        self._load_config()
        self._apply_env_overrides()
        self._parse_config()
    
    def _load_config(self) -> None:
        """加载配置文件"""
        if self._config_file.exists():
            with open(self._config_file, 'r', encoding='utf-8') as f:
                self._config = yaml.safe_load(f) or {}
        else:
            self._config = {}
        
        # 加载上下文词配置（如果存在）
        if CONTEXT_WORDS_FILE.exists():
            with open(CONTEXT_WORDS_FILE, 'r', encoding='utf-8') as f:
                context_data = yaml.safe_load(f) or {}
                # 合并上下文词配置，context_words.yaml 优先
                if "context_words" in context_data:
                    existing = self._config.get("context_words", {})
                    # 用 context_words.yaml 覆盖 settings.yaml 中的配置
                    self._config["context_words"] = {**existing, **context_data["context_words"]}
    
    def _apply_env_overrides(self) -> None:
        """应用环境变量覆盖"""
        # LLM API Key
        api_key = os.environ.get("MINGJING_LLM_API_KEY")
        if api_key:
            if "llm_verifier" not in self._config:
                self._config["llm_verifier"] = {}
            if "api" not in self._config["llm_verifier"]:
                self._config["llm_verifier"]["api"] = {}
            self._config["llm_verifier"]["api"]["api_key"] = api_key
        
        # Debug模式
        debug = os.environ.get("MINGJING_DEBUG")
        if debug:
            if "system" not in self._config:
                self._config["system"] = {}
            self._config["system"]["debug"] = debug.lower() in ("true", "1", "yes")
    
    def _parse_config(self) -> None:
        """解析配置到数据类"""
        # 系统配置
        system = self._config.get("system", {})
        self.name = system.get("name", "MingJing")
        self.version = system.get("version", "1.0.0")
        self.language = system.get("language", "zh")
        self.debug = system.get("debug", False)
        self.log_level = system.get("log_level", "INFO")
        
        # NLP引擎配置
        nlp = self._config.get("nlp_engine", {})
        self.nlp_engine = NlpEngineConfig(
            type=nlp.get("type", "spacy"),
            model=nlp.get("model", "zh_core_web_md"),
            default_score=nlp.get("default_score", 0.4),
            entity_mapping=nlp.get("entity_mapping", {}),
            labels_to_ignore=nlp.get("labels_to_ignore", []),
        )
        
        # LLM验证器配置
        llm = self._config.get("llm_verifier", {})
        api = llm.get("api", {})
        local = llm.get("local", {})
        self.llm_verifier = LlmVerifierConfig(
            enabled=llm.get("enabled", True),
            mode=llm.get("mode", "mock"),
            score_threshold=llm.get("score_threshold", 0.5),
            context_window=llm.get("context_window", 30),
            api_base_url=api.get("base_url", "https://api.openai.com/v1"),
            api_model=api.get("model", "gpt-3.5-turbo"),
            api_timeout=api.get("timeout", 30),
            api_key=api.get("api_key"),
            local_model_path=local.get("model_path", ""),
            local_device=local.get("device", "auto"),
            local_max_new_tokens=local.get("max_new_tokens", 200),
        )
        
        # 评分配置
        scoring = self._config.get("scoring", {})
        self.scoring = ScoringConfig(
            high_confidence=scoring.get("high_confidence", 0.5),
            low_confidence=scoring.get("low_confidence", 0.0),
            type_scores=scoring.get("type_scores", {}),
        )
        
        # 识别器配置
        recognizers = self._config.get("recognizers", {})
        settings = {}
        for name, cfg in recognizers.get("settings", {}).items():
            settings[name] = RecognizerSettings(
                enabled=cfg.get("enabled", True),
                base_score=cfg.get("base_score", 0.4),
                description=cfg.get("description"),
            )
        self.recognizers = RecognizersConfig(
            enabled=recognizers.get("enabled", []),
            disabled=recognizers.get("disabled", []),
            settings=settings,
        )
        
        # 上下文词配置
        self.context_words: Dict[str, List[str]] = self._config.get("context_words", {})
        
        # 文件处理配置
        file_proc = self._config.get("file_processing", {})
        self.file_processing = FileProcessingConfig(
            supported_formats=file_proc.get("supported_formats", []),
            archive_formats=file_proc.get("archive_formats", []),
            max_file_size=file_proc.get("max_file_size", 100),
            chunk_size=file_proc.get("chunk_size", 10),
            temp_dir=file_proc.get("temp_dir", "/tmp/mingjing"),
            recursive_extract=file_proc.get("recursive_extract", True),
        )
        
        # 性能配置
        perf = self._config.get("performance", {})
        cache = perf.get("cache", {})
        self.performance = PerformanceConfig(
            batch_size=perf.get("batch_size", 100),
            max_workers=perf.get("max_workers", 4),
            cache_enabled=cache.get("enabled", True),
            cache_ttl=cache.get("ttl", 3600),
            cache_max_size=cache.get("max_size", 1000),
        )
        
        # 报告配置
        report = self._config.get("report", {})
        risk_levels = {}
        for level, cfg in report.get("risk_levels", {}).items():
            risk_levels[level] = RiskLevel(
                min_count=cfg.get("min_count", 1),
                types=cfg.get("types", []),
            )
        self.report = ReportConfig(
            output_dir=report.get("output_dir", "./reports"),
            formats=report.get("formats", ["json"]),
            risk_levels=risk_levels,
        )
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取原始配置值"""
        keys = key.split(".")
        value = self._config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
            if value is None:
                return default
        return value
    
    def set(self, key: str, value: Any) -> None:
        """设置配置值（运行时）"""
        keys = key.split(".")
        config = self._config
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value
        # 重新解析配置
        self._parse_config()

    def update_recognizer(self, name: str, *, enabled: Optional[bool] = None, base_score: Optional[float] = None, description: Optional[str] = None) -> None:
        """更新识别器配置并保存"""
        recognizers_cfg = self._config.setdefault("recognizers", {})
        settings_cfg = recognizers_cfg.setdefault("settings", {})
        recognizer_cfg = settings_cfg.setdefault(name, {})

        if enabled is not None:
            recognizer_cfg["enabled"] = enabled
        if base_score is not None:
            recognizer_cfg["base_score"] = base_score
        if description is not None:
            recognizer_cfg["description"] = description

        self._parse_config()
        self.save()

    def update_context_words(self, entity_type: str, words: List[str]) -> None:
        """更新上下文词并保存"""
        context_cfg = self._config.setdefault("context_words", {})
        context_cfg[entity_type] = words
        self._save_context_words_file()
        self._parse_config()
        self.save()

    def _save_context_words_file(self) -> None:
        """把上下文词保存到独立文件"""
        data = {"context_words": self._config.get("context_words", {})}
        CONTEXT_WORDS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(CONTEXT_WORDS_FILE, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, allow_unicode=True, default_flow_style=False)

    def save(self, path: Optional[Union[str, Path]] = None) -> None:
        """保存配置到文件"""
        save_path = Path(path) if path else self._config_file
        save_path.parent.mkdir(parents=True, exist_ok=True)
        with open(save_path, 'w', encoding='utf-8') as f:
            yaml.dump(self._config, f, allow_unicode=True, default_flow_style=False)
    
    def reload(self) -> None:
        """重新加载配置"""
        self._load_config()
        self._apply_env_overrides()
        self._parse_config()
    
    def to_dict(self) -> Dict[str, Any]:
        """导出为字典"""
        return self._config.copy()
    
    def is_recognizer_enabled(self, name: str) -> bool:
        """检查识别器是否启用"""
        # 如果在禁用列表中
        if name in self.recognizers.disabled:
            return False
        # 如果启用列表为空，则默认全部启用
        if not self.recognizers.enabled:
            return True
        # 检查是否在启用列表中
        return name in self.recognizers.enabled
    
    def get_recognizer_score(self, name: str) -> float:
        """获取识别器基础分数"""
        if name in self.recognizers.settings:
            return self.recognizers.settings[name].base_score
        return self.scoring.type_scores.get("regex_match", 0.4)
    
    def get_context_words(self, entity_type: str) -> List[str]:
        """获取实体类型的上下文词"""
        return self.context_words.get(entity_type, [])


# 全局配置实例
_settings: Optional[Settings] = None


def get_settings(config_file: Optional[str] = None, reload: bool = False) -> Settings:
    """
    获取全局配置实例
    
    :param config_file: 配置文件路径
    :param reload: 是否强制重新加载
    :return: Settings实例
    """
    global _settings
    if _settings is None or reload:
        _settings = Settings(config_file)
    return _settings


def reset_settings() -> None:
    """重置全局配置"""
    global _settings
    _settings = None

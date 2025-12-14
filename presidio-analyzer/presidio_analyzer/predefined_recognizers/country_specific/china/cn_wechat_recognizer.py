"""
WeChat/WeCom ID Recognizer.

Recognizes WeChat and WeCom (企业微信) related identifiers:
- WeChat OpenID: User identifier within a single app
- WeChat UnionID: User identifier across apps under same account
- WeCom CorpID: Enterprise identifier
- WeCom AgentID: Application identifier
"""

from typing import List, Optional

from presidio_analyzer import Pattern, PatternRecognizer


class CnWechatRecognizer(PatternRecognizer):
    """
    Recognize WeChat and WeCom identifiers.

    Supports:
    - WeChat OpenID (o + 27 chars)
    - WeChat UnionID (o + 27 chars, same format)
    - WeCom CorpID (ww + 16 hex chars or wx + 16 hex chars)
    - WeCom Secret (32 chars alphanumeric)
    """

    PATTERNS = [
        # WeChat OpenID/UnionID: starts with 'o' followed by 27 alphanumeric/underscore/hyphen
        Pattern(
            "WeChat OpenID",
            r"(?<![A-Za-z0-9_-])o[A-Za-z0-9_-]{27}(?![A-Za-z0-9_-])",
            0.7,
        ),
        # WeCom CorpID: ww + 16 hex chars
        Pattern(
            "WeCom CorpID WW",
            r"(?<![A-Za-z0-9])ww[a-f0-9]{16}(?![A-Za-z0-9])",
            0.8,
        ),
        # WeCom CorpID: wx + 16 hex chars (older format)
        Pattern(
            "WeCom CorpID WX",
            r"(?<![A-Za-z0-9])wx[a-f0-9]{16}(?![A-Za-z0-9])",
            0.8,
        ),
        # WeCom Secret: 32 alphanumeric chars
        Pattern(
            "WeCom Secret",
            r"(?<![A-Za-z0-9])[A-Za-z0-9_-]{32}(?![A-Za-z0-9_-])",
            0.2,
        ),
        # WeChat AppID: wx + 16 hex chars
        Pattern(
            "WeChat AppID",
            r"(?<![A-Za-z0-9])wx[a-f0-9]{16}(?![A-Za-z0-9])",
            0.7,
        ),
        # WeChat AppSecret: 32 hex chars
        Pattern(
            "WeChat AppSecret",
            r"(?<![A-Fa-f0-9])[a-f0-9]{32}(?![A-Fa-f0-9])",
            0.2,
        ),
    ]

    CONTEXT = [
        # 中文 - 微信相关
        "微信", "微信号", "微信ID", "微信用户",
        "OpenID", "openid", "UnionID", "unionid",
        "公众号", "小程序", "服务号", "订阅号",
        "AppID", "appid", "AppSecret", "appsecret",
        # 中文 - 企业微信
        "企业微信", "企微", "WeCom", "wecom",
        "CorpID", "corpid", "CorpSecret", "corpsecret",
        "AgentID", "agentid", "AgentSecret",
        # 中文 - 配置相关
        "配置", "密钥", "秘钥", "凭证", "Token", "token",
        "回调", "回调地址", "Webhook", "webhook",
        # 英文
        "wechat", "weixin", "mini program", "official account",
        "open id", "union id", "app id", "app secret",
        "corp id", "corp secret", "agent id",
        "access token", "refresh token",
    ]

    def __init__(
        self,
        patterns: Optional[List[Pattern]] = None,
        context: Optional[List[str]] = None,
        supported_language: str = "zh",
        supported_entity: str = "CN_WECHAT_ID",
    ):
        patterns = patterns if patterns else self.PATTERNS
        context = context if context else self.CONTEXT
        super().__init__(
            supported_entity=supported_entity,
            patterns=patterns,
            context=context,
            supported_language=supported_language,
        )

    def validate_result(self, pattern_text: str) -> bool:
        """Validate the detected WeChat/WeCom ID."""
        text = pattern_text.strip()
        
        # OpenID starts with 'o'
        if text.startswith('o') and len(text) == 28:
            return True
        
        # CorpID/AppID starts with 'ww' or 'wx'
        if (text.startswith('ww') or text.startswith('wx')) and len(text) == 18:
            return True
        
        # Secret is 32 chars
        if len(text) == 32:
            return True
        
        return False

    def invalidate_result(self, pattern_text: str) -> bool:
        """Check if the pattern is obviously not a valid WeChat ID."""
        text = pattern_text.strip()
        
        # All same characters
        if len(set(text)) <= 2:
            return True
        
        # All zeros or all ones
        if text in ['0' * len(text), '1' * len(text), 'a' * len(text)]:
            return True
        
        return False

"""
Sensitive Field Recognizer.

Recognizes sensitive field names and their values in various formats:
- JSON: "password": "value"
- Query string: password=value
- Assignment: password = value
- XML: <password>value</password>
"""

from typing import List, Optional

from presidio_analyzer import Pattern, PatternRecognizer


class CnSensitiveFieldRecognizer(PatternRecognizer):
    """
    Recognize sensitive fields like password, secret, token, etc.

    Detects field names that typically contain sensitive information
    along with their values.
    """

    PATTERNS = [
        # Password field in JSON/JS format
        Pattern(
            "Password Field JSON",
            r"""(?i)['"]?(?:password|passwd|pwd|pass)['"]?\s*[:=]\s*['"]([^'"]{1,100})['"]""",
            0.8,
        ),
        # Secret/Token field in JSON/JS format
        Pattern(
            "Secret Field JSON",
            r"""(?i)['"]?(?:secret|token|api[_-]?key|app[_-]?key|access[_-]?key)['"]?\s*[:=]\s*['"]([^'"]{1,100})['"]""",
            0.7,
        ),
        # Auth field in JSON/JS format
        Pattern(
            "Auth Field JSON",
            r"""(?i)['"]?(?:auth|authorization|credential|private[_-]?key)['"]?\s*[:=]\s*['"]([^'"]{1,100})['"]""",
            0.7,
        ),
        # Password in query string
        Pattern(
            "Password Query String",
            r"(?i)(?:password|passwd|pwd|pass)=([^&\s]{1,100})",
            0.6,
        ),
        # Username field
        Pattern(
            "Username Field",
            r"""(?i)['"]?(?:username|user[_-]?name|user[_-]?id|account|login)['"]?\s*[:=]\s*['"]([^'"]{1,100})['"]""",
            0.5,
        ),
        # Private key content
        Pattern(
            "Private Key",
            r"-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----",
            0.9,
        ),
        # API Key pattern
        Pattern(
            "API Key Pattern",
            r"(?i)(?:api[_-]?key|apikey)\s*[:=]\s*['\"]?([A-Za-z0-9_\-]{16,64})['\"]?",
            0.7,
        ),
    ]

    CONTEXT = [
        # 中文 - 密码相关
        "密码", "口令", "密钥", "秘钥", "凭证", "凭据",
        "登录密码", "支付密码", "交易密码", "初始密码",
        # 中文 - 账号相关
        "账号", "用户名", "登录名", "账户", "用户",
        # 中文 - 认证相关
        "认证", "授权", "鉴权", "令牌", "Token",
        "私钥", "公钥", "证书", "签名",
        # 中文 - 配置相关
        "配置", "配置文件", "环境变量", "敏感信息",
        # 英文
        "password", "passwd", "pwd", "pass", "secret",
        "token", "api key", "app key", "access key",
        "auth", "authorization", "credential", "private key",
        "username", "user", "account", "login",
        "config", "configuration", "env", "environment",
    ]

    def __init__(
        self,
        patterns: Optional[List[Pattern]] = None,
        context: Optional[List[str]] = None,
        supported_language: str = "zh",
        supported_entity: str = "CN_SENSITIVE_FIELD",
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
        """Validate the detected sensitive field."""
        text = pattern_text.strip()
        
        # Private key header is always valid
        if 'PRIVATE KEY' in text:
            return True
        
        # Check for common sensitive field names
        sensitive_names = [
            'password', 'passwd', 'pwd', 'pass', 'secret',
            'token', 'key', 'auth', 'credential', 'private',
        ]
        
        text_lower = text.lower()
        for name in sensitive_names:
            if name in text_lower:
                return True
        
        return False

    def invalidate_result(self, pattern_text: str) -> bool:
        """Check if the pattern is obviously not sensitive."""
        text = pattern_text.strip().lower()
        
        # Placeholder values
        placeholders = [
            'xxx', 'your_', 'example', 'placeholder', 'null', 'none',
            'undefined', 'empty', 'test', 'demo', 'sample',
        ]
        
        for placeholder in placeholders:
            if placeholder in text:
                return True
        
        return False

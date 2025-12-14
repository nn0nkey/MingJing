"""
China Cloud Service Key Recognizer.

Recognizes cloud service access keys from major Chinese and international providers:
- Alibaba Cloud (阿里云): LTAI prefix
- Tencent Cloud (腾讯云): AKID prefix
- Huawei Cloud (华为云): AK format
- AWS: AKIA prefix
- Azure: various formats
"""

from typing import List, Optional

from presidio_analyzer import Pattern, PatternRecognizer


class CnCloudKeyRecognizer(PatternRecognizer):
    """
    Recognize cloud service access keys.

    Supports:
    - Alibaba Cloud AccessKey ID (LTAI...)
    - Tencent Cloud SecretId (AKID...)
    - Huawei Cloud AK
    - AWS Access Key ID (AKIA...)
    - Generic access key patterns
    """

    PATTERNS = [
        # Alibaba Cloud AccessKey ID: LTAI + 12-20 alphanumeric
        Pattern(
            "Alibaba Cloud AccessKey",
            r"(?<![A-Za-z0-9])LTAI[A-Za-z0-9]{12,20}(?![A-Za-z0-9])",
            0.85,
        ),
        # Tencent Cloud SecretId: AKID + 32 alphanumeric
        Pattern(
            "Tencent Cloud SecretId",
            r"(?<![A-Za-z0-9])AKID[A-Za-z0-9]{32}(?![A-Za-z0-9])",
            0.85,
        ),
        # AWS Access Key ID: AKIA + 16 uppercase alphanumeric
        Pattern(
            "AWS AccessKey",
            r"(?<![A-Za-z0-9])AKIA[0-9A-Z]{16}(?![A-Za-z0-9])",
            0.85,
        ),
        # AWS Secret Access Key pattern (40 chars)
        Pattern(
            "AWS SecretKey",
            r"(?<![A-Za-z0-9])[A-Za-z0-9/+=]{40}(?![A-Za-z0-9/+=])",
            0.3,
        ),
        # Generic AccessKey pattern
        Pattern(
            "Generic AccessKey",
            r"(?i)(?:access[_-]?key[_-]?(?:id|secret)?|secret[_-]?key|api[_-]?key|app[_-]?key|app[_-]?secret)\s*[=:]\s*['\"]?([A-Za-z0-9_\-]{16,64})['\"]?",
            0.6,
        ),
        # Huawei Cloud AK (20 uppercase alphanumeric)
        Pattern(
            "Huawei Cloud AK",
            r"(?<![A-Za-z0-9])[A-Z0-9]{20}(?![A-Za-z0-9])",
            0.2,
        ),
    ]

    CONTEXT = [
        # 中文 - 云服务
        "阿里云", "腾讯云", "华为云", "百度云", "金山云", "青云", "UCloud",
        "云服务", "云平台", "云账号", "云密钥",
        # 中文 - 密钥相关
        "密钥", "秘钥", "访问密钥", "API密钥", "接口密钥",
        "AccessKey", "SecretKey", "AppKey", "AppSecret",
        "AK", "SK", "API Key", "App Key",
        # 中文 - 配置相关
        "配置", "配置文件", "环境变量", "凭证", "凭据", "认证",
        # 英文
        "access key", "secret key", "api key", "app key", "app secret",
        "credential", "credentials", "authentication", "auth",
        "alibaba cloud", "aliyun", "tencent cloud", "qcloud",
        "huawei cloud", "aws", "amazon", "azure", "gcp", "google cloud",
        # 缩写
        "ak", "sk", "aksk", "accesskeyid", "accesskeysecret",
    ]

    def __init__(
        self,
        patterns: Optional[List[Pattern]] = None,
        context: Optional[List[str]] = None,
        supported_language: str = "zh",
        supported_entity: str = "CN_CLOUD_KEY",
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
        """Validate the detected cloud key."""
        key = pattern_text.strip()
        
        # Known valid prefixes
        valid_prefixes = ['LTAI', 'AKID', 'AKIA', 'ASIA', 'ABIA', 'ACCA']
        for prefix in valid_prefixes:
            if key.startswith(prefix):
                return True
        
        # Check for reasonable key format
        if len(key) >= 16 and any(c.isalpha() for c in key) and any(c.isdigit() for c in key):
            return True
        
        return False

    def invalidate_result(self, pattern_text: str) -> bool:
        """Check if the pattern is obviously not a valid cloud key."""
        key = pattern_text.strip()
        
        # All same characters
        if len(set(key)) <= 2:
            return True
        
        # Common false positives
        false_positives = [
            'AAAAAAAAAAAAAAAA', 'BBBBBBBBBBBBBBBB',
            '0000000000000000', '1111111111111111',
        ]
        if key in false_positives:
            return True
        
        return False

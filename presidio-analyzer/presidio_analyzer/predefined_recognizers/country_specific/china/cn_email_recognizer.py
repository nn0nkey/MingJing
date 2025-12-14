"""
Email Address Recognizer (China Enhanced).

Recognizes email addresses with enhanced support for Chinese context
and common Chinese email providers.
"""

from typing import List, Optional

from presidio_analyzer import Pattern, PatternRecognizer


class CnEmailRecognizer(PatternRecognizer):
    """
    Recognize email addresses with Chinese context.

    Enhanced support for:
    - Common Chinese email providers (QQ, 163, 126, sina, etc.)
    - Chinese context words
    - Filtering out false positives (image files, etc.)
    """

    PATTERNS = [
        # 通用邮箱格式 - 低置信度，需LLM验证
        Pattern(
            "Email Standard",
            r"(?<![A-Za-z0-9._%+-])[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}(?![A-Za-z0-9._%+-])",
            0.4,  # 通用格式，容易误报，需LLM验证
        ),
        # 高置信度: QQ邮箱 (数字@qq.com)
        Pattern(
            "Email QQ",
            r"(?<![A-Za-z0-9])[0-9]{5,11}@qq\.com(?![A-Za-z0-9])",
            0.7,  # QQ邮箱格式明确
        ),
        # 163/126邮箱
        Pattern(
            "Email 163",
            r"(?<![A-Za-z0-9._%+-])[A-Za-z0-9._%+-]+@(?:163|126)\.com(?![A-Za-z0-9])",
            0.65,  # 常用邮箱服务商
        ),
        # 新浪邮箱
        Pattern(
            "Email Sina",
            r"(?<![A-Za-z0-9._%+-])[A-Za-z0-9._%+-]+@(?:sina|vip\.sina)\.(?:com|cn)(?![A-Za-z0-9])",
            0.6,  # 常用邮箱服务商
        ),
        # 阿里邮箱
        Pattern(
            "Email Alibaba",
            r"(?<![A-Za-z0-9._%+-])[A-Za-z0-9._%+-]+@(?:aliyun|alibaba|taobao)\.com(?![A-Za-z0-9])",
            0.65,  # 常用邮箱服务商
        ),
        # 腾讯邮箱
        Pattern(
            "Email Tencent",
            r"(?<![A-Za-z0-9._%+-])[A-Za-z0-9._%+-]+@(?:tencent|qq)\.com(?![A-Za-z0-9])",
            0.65,  # 常用邮箱服务商
        ),
        # 企业邮箱
        Pattern(
            "Email Corporate",
            r"(?<![A-Za-z0-9._%+-])[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+\.(?:com\.cn|cn|com|net|org)(?![A-Za-z0-9])",
            0.45,  # 通用格式，需验证
        ),
    ]

    CONTEXT = [
        # 中文 - 邮箱相关
        "邮箱", "邮件", "电子邮箱", "电子邮件", "邮箱地址",
        "收件人", "发件人", "抄送", "密送",
        "注册邮箱", "绑定邮箱", "联系邮箱", "工作邮箱", "个人邮箱",
        # 中文 - 联系方式
        "联系方式", "联系人", "通讯录", "地址簿",
        # 中文 - 操作相关
        "发送", "接收", "回复", "转发", "订阅", "退订",
        # 英文
        "email", "e-mail", "mail", "mailbox",
        "sender", "recipient", "cc", "bcc",
        "contact", "address", "inbox", "outbox",
        "subscribe", "unsubscribe", "newsletter",
        # 邮箱服务商
        "qq", "163", "126", "sina", "sohu", "aliyun",
        "gmail", "outlook", "hotmail", "yahoo",
    ]

    # File extensions to filter out (not emails)
    INVALID_EXTENSIONS = [
        '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg',
        '.tiff', '.ico', '.heic', '.heif',
        '.mp3', '.mp4', '.avi', '.mov', '.wmv',
        '.pdf', '.doc', '.docx', '.xls', '.xlsx',
    ]

    def __init__(
        self,
        patterns: Optional[List[Pattern]] = None,
        context: Optional[List[str]] = None,
        supported_language: str = "zh",
        supported_entity: str = "CN_EMAIL",
    ):
        patterns = patterns if patterns else self.PATTERNS
        context = context if context else self.CONTEXT
        super().__init__(
            supported_entity=supported_entity,
            patterns=patterns,
            context=context,
            supported_language=supported_language,
        )

    def validate_result(self, pattern_text: str) -> Optional[bool]:
        """Validate the detected email address.
        
        :return:
            - True: 已知邮箱服务商，分数设为1.0
            - False: 明确无效，分数设为0，结果被丢弃
            - None: 不确定，保持基础分数，需LLM验证
        """
        email = pattern_text.strip().lower()
        
        # Must contain @ and at least one dot after @
        if '@' not in email:
            return False  # 明确无效
        
        local, domain = email.rsplit('@', 1)
        
        # Local part should not be empty
        if not local:
            return False  # 明确无效
        
        # Domain should have at least one dot
        if '.' not in domain:
            return False  # 明确无效
        
        # Domain should not start or end with dot
        if domain.startswith('.') or domain.endswith('.'):
            return False  # 明确无效
        
        # Known Chinese email providers - high confidence
        known_providers = ['qq.com', '163.com', '126.com', 'sina.com', 'sina.cn',
                          'aliyun.com', 'alibaba.com', 'taobao.com', 'tencent.com',
                          'sohu.com', 'foxmail.com', '139.com', '189.cn']
        for provider in known_providers:
            if domain.endswith(provider):
                return True  # 已知服务商，确认有效
        
        # Known international providers
        intl_providers = ['gmail.com', 'outlook.com', 'hotmail.com', 'yahoo.com', 'icloud.com']
        for provider in intl_providers:
            if domain.endswith(provider):
                return True  # 已知服务商，确认有效
        
        return None  # 未知域名，需LLM验证

    def invalidate_result(self, pattern_text: str) -> bool:
        """Check if the pattern is obviously not a valid email."""
        email = pattern_text.strip().lower()
        
        # Filter out file paths that look like emails
        for ext in self.INVALID_EXTENSIONS:
            if email.endswith(ext):
                return True
        
        # Filter out version numbers like 1.2.3@4.5
        if email.count('.') > 4:
            return True
        
        # Filter out obviously fake emails
        fake_patterns = ['test@test', 'example@example', 'xxx@xxx']
        for fake in fake_patterns:
            if fake in email:
                return True
        
        return False

"""
China Unified Social Credit Code Recognizer.

Recognizes Chinese Unified Social Credit Code (统一社会信用代码).
Format: 18 characters (digits and uppercase letters, excluding I, O, S, V, Z)

Structure:
- 1 digit: Registration authority (登记管理部门代码)
- 1 digit: Organization type (机构类别代码)
- 6 digits: Region code (登记管理机关行政区划码)
- 9 characters: Organization code (主体标识码/组织机构代码)
- 1 character: Check digit (校验码)

Reference: GB 32100-2015
"""

from typing import List, Optional, Tuple

from presidio_analyzer import Pattern, PatternRecognizer


class CnSocialCreditCodeRecognizer(PatternRecognizer):
    """
    Recognize Chinese Unified Social Credit Code (统一社会信用代码).

    The 18-character code consists of:
    - 2 characters: Registration authority + Organization type
    - 6 digits: Region code
    - 9 characters: Organization code
    - 1 character: Check digit

    Valid characters: 0-9, A-H, J-N, P-R, T-U, W-Y (excluding I, O, S, V, Z)

    :param patterns: List of patterns to be used by this recognizer
    :param context: List of context words to increase confidence in detection
    :param supported_language: Language this recognizer supports
    :param supported_entity: The entity this recognizer can detect
    """

    # Valid characters for social credit code (excluding I, O, S, V, Z)
    VALID_CHARS = "0123456789ABCDEFGHJKLMNPQRTUWXY"
    
    # Character weights for checksum calculation
    WEIGHTS = [1, 3, 9, 27, 19, 26, 16, 17, 20, 29, 25, 13, 8, 24, 10, 30, 28]
    
    PATTERNS = [
        # Standard format: 2 chars + 6 digits + 9 chars + 1 check
        Pattern(
            "CN Social Credit Code (High)",
            r"(?<![0-9A-Za-z])[1-9A-GY][1-9A-HJ-NP-RT-UW-Y][0-9]{6}[0-9A-HJ-NP-RT-UW-Y]{9}[0-9A-HJ-NP-RT-UW-Y](?![0-9A-Za-z])",
            0.6,
        ),
        # Relaxed format: 18 alphanumeric characters
        Pattern(
            "CN Social Credit Code (Medium)",
            r"(?<![0-9A-Za-z])[0-9A-HJ-NP-RT-UW-Y]{18}(?![0-9A-Za-z])",
            0.4,
        ),
        # With separators
        Pattern(
            "CN Social Credit Code (Separated)",
            r"(?<![0-9A-Za-z])[0-9A-HJ-NP-RT-UW-Y]{2}[-\s]?[0-9]{6}[-\s]?[0-9A-HJ-NP-RT-UW-Y]{10}(?![0-9A-Za-z])",
            0.5,
        ),
    ]

    # Comprehensive context words
    CONTEXT = [
        # 中文 - 正式称谓
        "统一社会信用代码", "社会信用代码", "信用代码", "统一代码",
        "社会信用", "信用号", "信用编号",
        # 中文 - 相关证件
        "营业执照", "工商注册", "工商登记", "企业注册",
        "组织机构代码", "机构代码", "组织代码",
        "税务登记", "税务登记号", "纳税人识别号",
        # 中文 - 企业相关
        "企业", "公司", "法人", "法定代表人",
        "注册号", "登记号", "许可证号",
        # 中文 - 场景相关
        "开票", "发票", "合同", "签约",
        # 英文
        "unified social credit code", "social credit code",
        "uscc", "credit code",
        "business license", "registration number",
        "organization code", "tax id",
        "company registration", "corporate id",
    ]

    def __init__(
        self,
        patterns: Optional[List[Pattern]] = None,
        context: Optional[List[str]] = None,
        supported_language: str = "zh",
        supported_entity: str = "CN_SOCIAL_CREDIT_CODE",
        replacement_pairs: Optional[List[Tuple[str, str]]] = None,
    ):
        self.replacement_pairs = (
            replacement_pairs if replacement_pairs else [("-", ""), (" ", "")]
        )
        patterns = patterns if patterns else self.PATTERNS
        context = context if context else self.CONTEXT
        super().__init__(
            supported_entity=supported_entity,
            patterns=patterns,
            context=context,
            supported_language=supported_language,
        )

    def validate_result(self, pattern_text: str) -> bool:
        """
        Validate the social credit code using checksum algorithm.

        :param pattern_text: The detected social credit code
        :return: True if valid, False otherwise
        """
        code = pattern_text.replace("-", "").replace(" ", "").upper()
        
        if len(code) != 18:
            return False
        
        # Check all characters are valid
        for c in code:
            if c not in self.VALID_CHARS:
                return False
        
        # Validate checksum
        try:
            total = 0
            for i in range(17):
                char_value = self.VALID_CHARS.index(code[i])
                total += char_value * self.WEIGHTS[i]
            
            remainder = total % 31
            expected_check = self.VALID_CHARS[(31 - remainder) % 31]
            
            return code[17] == expected_check
            
        except (ValueError, IndexError):
            return False

    def invalidate_result(self, pattern_text: str) -> bool:
        """
        Check if the pattern is obviously not a valid social credit code.

        :param pattern_text: Text detected as pattern by regex
        :return: True if invalidated (should be rejected)
        """
        code = pattern_text.replace("-", "").replace(" ", "").upper()
        
        # Check for all same characters
        if len(set(code)) == 1:
            return True
        
        # Check for invalid characters (I, O, S, V, Z)
        invalid_chars = set('IOSVZ')
        if any(c in invalid_chars for c in code):
            return True
        
        return False

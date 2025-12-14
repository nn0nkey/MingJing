"""
China Driver License Number Recognizer.

Recognizes Chinese driver license numbers.
Format: Same as ID card number (18 digits) or old format (15 digits)

The driver license number in China is typically the same as the ID card number.

Reference: 中华人民共和国机动车驾驶证管理办法
"""

from typing import List, Optional, Tuple

from presidio_analyzer import Pattern, PatternRecognizer


class CnDriverLicenseRecognizer(PatternRecognizer):
    """
    Recognize Chinese driver license numbers.

    In China, the driver license number is typically:
    - Same as the 18-digit ID card number
    - Old format: 15 digits (before 2004)
    - Some regions use different formats

    :param patterns: List of patterns to be used by this recognizer
    :param context: List of context words to increase confidence in detection
    :param supported_language: Language this recognizer supports
    :param supported_entity: The entity this recognizer can detect
    """

    PATTERNS = [
        # 18-digit format (same as ID card)
        Pattern(
            "CN Driver License 18",
            r"(?<![0-9])[1-6]\d{5}(?:19|20)\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])\d{3}[\dXx](?![0-9])",
            0.4,  # Lower than ID card because needs context
        ),
        # 15-digit old format
        Pattern(
            "CN Driver License 15",
            r"(?<![0-9])[1-6]\d{5}\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])\d{3}(?![0-9])",
            0.3,
        ),
        # Archive number format (档案编号): 12 digits
        Pattern(
            "CN Driver License Archive",
            r"(?<![0-9])\d{12}(?![0-9])",
            0.2,  # Very low, needs strong context
        ),
    ]

    # Comprehensive context words for driver license
    CONTEXT = [
        # 中文 - 驾驶证相关
        "驾驶证", "驾驶证号", "驾驶证号码", "驾驶证编号",
        "驾照", "驾照号", "驾照号码",
        "机动车驾驶证", "驾驶执照",
        # 中文 - 档案相关
        "档案编号", "驾驶档案", "驾驶证档案",
        # 中文 - 准驾车型
        "准驾车型", "驾驶资格", "驾驶类型",
        "A1", "A2", "A3", "B1", "B2", "C1", "C2", "C3", "C4", "D", "E", "F", "M", "N", "P",
        # 中文 - 场景相关
        "驾驶人", "驾驶员", "司机",
        "初次领证", "有效期", "换证", "补证",
        # 英文
        "driver license", "driver's license", "driving license",
        "driver licence", "driving licence",
        "license number", "licence number",
        "dl", "dl no", "dl number",
    ]

    # Weights for checksum calculation (same as ID card)
    WEIGHTS = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]
    CHECKSUM_MAP = ['1', '0', 'X', '9', '8', '7', '6', '5', '4', '3', '2']

    def __init__(
        self,
        patterns: Optional[List[Pattern]] = None,
        context: Optional[List[str]] = None,
        supported_language: str = "zh",
        supported_entity: str = "CN_DRIVER_LICENSE",
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
        Validate the driver license number.

        :param pattern_text: The detected driver license number
        :return: True if valid, False otherwise
        """
        license_num = pattern_text.replace("-", "").replace(" ", "").upper()
        
        # 18-digit format validation (same as ID card)
        if len(license_num) == 18:
            try:
                total = sum(int(license_num[i]) * self.WEIGHTS[i] for i in range(17))
                expected = self.CHECKSUM_MAP[total % 11]
                return license_num[17] == expected
            except (ValueError, IndexError):
                return False
        
        # 15-digit format
        if len(license_num) == 15:
            return license_num.isdigit()
        
        # 12-digit archive number
        if len(license_num) == 12:
            return license_num.isdigit()
        
        return False

    def invalidate_result(self, pattern_text: str) -> bool:
        """
        Check if the pattern is obviously not a valid driver license.

        :param pattern_text: Text detected as pattern by regex
        :return: True if invalidated (should be rejected)
        """
        license_num = pattern_text.replace("-", "").replace(" ", "").upper()
        
        # Check for all same digits
        digits = ''.join(c for c in license_num if c.isdigit())
        if len(set(digits)) == 1:
            return True
        
        return False

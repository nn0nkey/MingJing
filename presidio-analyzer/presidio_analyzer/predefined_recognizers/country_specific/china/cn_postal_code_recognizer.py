"""
China Postal Code Recognizer.

Recognizes Chinese postal codes (邮政编码).
Format: 6 digits

Structure:
- First 2 digits: Province/Region (省/自治区/直辖市)
- 3rd digit: Postal zone (邮区)
- 4th digit: County/City (县/市)
- Last 2 digits: Delivery office (投递局)

Reference: GB/T 2260
"""

from typing import List, Optional, Tuple

from presidio_analyzer import Pattern, PatternRecognizer


class CnPostalCodeRecognizer(PatternRecognizer):
    """
    Recognize Chinese postal codes (邮政编码).

    The 6-digit postal code structure:
    - Digits 1-2: Province/Region code (01-82)
    - Digit 3: Postal zone
    - Digit 4: County/City
    - Digits 5-6: Delivery office

    :param patterns: List of patterns to be used by this recognizer
    :param context: List of context words to increase confidence in detection
    :param supported_language: Language this recognizer supports
    :param supported_entity: The entity this recognizer can detect
    """

    PATTERNS = [
        # Standard 6-digit postal code with valid province prefix
        Pattern(
            "CN Postal Code (High)",
            r"(?<![0-9])(?:0[1-9]|[1-7][0-9]|8[0-2])\d{4}(?![0-9])",
            0.4,  # Lower confidence, needs context
        ),
        # Any 6-digit number (very low confidence)
        Pattern(
            "CN Postal Code (Low)",
            r"(?<![0-9])\d{6}(?![0-9])",
            0.1,  # Very low, needs strong context
        ),
    ]

    # Comprehensive context words
    CONTEXT = [
        # 中文 - 邮编相关
        "邮编", "邮政编码", "邮政区码", "邮区编号",
        "邮递区号", "邮码",
        # 中文 - 地址相关
        "地址", "住址", "通讯地址", "联系地址", "收货地址",
        "寄件地址", "收件地址", "邮寄地址",
        # 中文 - 邮政相关
        "邮政", "邮局", "邮寄", "快递", "包裹",
        "信件", "挂号信", "平信",
        # 英文
        "postal code", "postcode", "post code",
        "zip code", "zip", "zipcode",
        "mailing code", "area code",
    ]

    # Valid province prefixes (first 2 digits)
    VALID_PROVINCE_PREFIXES = {
        # 华北
        "01", "02", "03", "04", "05", "06", "07", "08", "09", "10",
        # 东北
        "11", "12", "13", "14", "15", "16",
        # 华东
        "20", "21", "22", "23", "24", "25", "26", "27",
        "30", "31", "32", "33", "34", "35", "36", "37",
        # 中南
        "40", "41", "42", "43", "44", "45", "46", "47",
        "50", "51", "52", "53", "54", "55", "56",
        # 西南
        "60", "61", "62", "63", "64", "65", "66", "67",
        # 西北
        "70", "71", "72", "73", "74", "75", "76", "77", "78", "79",
        # 港澳台
        "80", "81", "82",
    }

    def __init__(
        self,
        patterns: Optional[List[Pattern]] = None,
        context: Optional[List[str]] = None,
        supported_language: str = "zh",
        supported_entity: str = "CN_POSTAL_CODE",
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

    def validate_result(self, pattern_text: str) -> Optional[bool]:
        """
        Validate the postal code.

        :param pattern_text: The detected postal code
        :return: 
            - True: 不使用（邮编太容易误报，始终需要上下文验证）
            - False: 明确无效（长度/格式错误），分数设为0，结果被丢弃
            - None: 不确定，保持基础分数，需LLM验证
        """
        code = pattern_text.replace("-", "").replace(" ", "")
        
        if len(code) != 6:
            return False  # 长度不对
        
        if not code.isdigit():
            return False  # 包含非数字
        
        # Check province prefix
        prefix = code[:2]
        if prefix not in self.VALID_PROVINCE_PREFIXES:
            return False  # 无效省份前缀
        
        # 邮编太容易误报（6位数字很常见），始终需要LLM验证
        return None

    def invalidate_result(self, pattern_text: str) -> bool:
        """
        Check if the pattern is obviously not a valid postal code.

        :param pattern_text: Text detected as pattern by regex
        :return: True if invalidated (should be rejected)
        """
        code = pattern_text.replace("-", "").replace(" ", "")
        
        # Check for all same digits
        if len(set(code)) == 1:
            return True
        
        # Check for sequential patterns
        if code in ['123456', '654321', '000000', '111111', '999999']:
            return True
        
        # Check for obviously invalid prefixes
        if code.startswith('00') or code.startswith('99'):
            return True
        
        return False

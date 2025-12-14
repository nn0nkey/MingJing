"""
China Passport Number Recognizer.

Recognizes Chinese passport numbers.
- Ordinary passport (普通护照): E + 8 digits or EA/EB/EC/ED/EE + 7 digits
- Diplomatic passport (外交护照): D + 8 digits
- Service passport (公务护照): S + 8 digits or SE + 7 digits
- HK/Macau Travel Permit (港澳通行证): C + 8 digits or W + 8 digits

Reference: 中华人民共和国护照法
"""

from typing import List, Optional, Tuple

from presidio_analyzer import Pattern, PatternRecognizer


class CnPassportRecognizer(PatternRecognizer):
    """
    Recognize Chinese passport numbers.

    Passport types:
    - E: Ordinary passport (普通护照) - E + 8 digits
    - D: Diplomatic passport (外交护照) - D + 8 digits
    - S: Service passport (公务护照) - S + 8 digits
    - P: Public affairs passport (公务普通护照) - P + 8 digits
    - G: Old format passport - G + 8 digits
    - 14/15: Old format - 14/15 + 7 digits

    :param patterns: List of patterns to be used by this recognizer
    :param context: List of context words to increase confidence in detection
    :param supported_language: Language this recognizer supports
    :param supported_entity: The entity this recognizer can detect
    """

    PATTERNS = [
        # New format ordinary passport: E + 8 digits
        Pattern(
            "CN Passport Ordinary (High)",
            r"(?<![A-Za-z0-9])E[0-9]{8}(?![0-9])",
            0.6,
        ),
        # New format with prefix: EA/EB/EC/ED/EE + 7 digits
        Pattern(
            "CN Passport Ordinary Prefix",
            r"(?<![A-Za-z0-9])E[A-E][0-9]{7}(?![0-9])",
            0.55,
        ),
        # Diplomatic passport: D + 8 digits
        Pattern(
            "CN Passport Diplomatic",
            r"(?<![A-Za-z0-9])D[0-9]{8}(?![0-9])",
            0.6,
        ),
        # Service passport: S/SE + 7-8 digits
        Pattern(
            "CN Passport Service",
            r"(?<![A-Za-z0-9])S[E]?[0-9]{7,8}(?![0-9])",
            0.6,
        ),
        # Public affairs passport: P + 8 digits
        Pattern(
            "CN Passport Public",
            r"(?<![A-Za-z0-9])P[0-9]{8}(?![0-9])",
            0.6,
        ),
        # Old format: G + 8 digits
        Pattern(
            "CN Passport Old G",
            r"(?<![A-Za-z0-9])G[0-9]{8}(?![0-9])",
            0.5,
        ),
        # Old format: 14/15 + 7 digits
        Pattern(
            "CN Passport Old Numeric",
            r"(?<![0-9])1[45][0-9]{7}(?![0-9])",
            0.45,
        ),
        # HK/Macau Travel Permit: C/W + 8 digits
        Pattern(
            "CN Travel Permit HK Macau",
            r"(?<![A-Za-z0-9])[CW][0-9]{8}(?![0-9])",
            0.6,
        ),
        # Taiwan Travel Permit: L/T + 8 digits
        Pattern(
            "CN Travel Permit Taiwan",
            r"(?<![A-Za-z0-9])[LT][0-9]{8}(?![0-9])",
            0.6,
        ),
    ]

    # Comprehensive context words
    CONTEXT = [
        # 中文 - 护照相关
        "护照", "护照号", "护照号码", "护照编号",
        "普通护照", "外交护照", "公务护照", "公务普通护照",
        "因私护照", "因公护照",
        # 中文 - 通行证相关
        "通行证", "港澳通行证", "台湾通行证", "往来港澳通行证", "往来台湾通行证",
        "港澳台通行证", "出入境证件",
        # 中文 - 场景相关
        "出境", "入境", "出入境", "签证", "签注",
        "护照有效期", "护照签发", "护照申请",
        # 英文
        "passport", "passport number", "passport no",
        "travel document", "travel permit",
        "entry permit", "exit permit",
        # 缩写
        "pp", "pp.", "ppt",
    ]

    def __init__(
        self,
        patterns: Optional[List[Pattern]] = None,
        context: Optional[List[str]] = None,
        supported_language: str = "zh",
        supported_entity: str = "CN_PASSPORT",
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
        Validate the passport number format.

        :param pattern_text: The detected passport number
        :return: 
            - True: 有效前缀，分数设为1.0
            - False: 明确无效（长度错误），分数设为0，结果被丢弃
            - None: 不确定，保持基础分数，需LLM验证
        """
        passport = pattern_text.replace("-", "").replace(" ", "").upper()
        
        # Check length
        if len(passport) < 8 or len(passport) > 9:
            return False  # 长度不对，明确无效
        
        # High confidence prefixes (明确的护照前缀)
        high_confidence_prefixes = ['E', 'D', 'S', 'P', 'G', 'C', 'W', 'L', 'T']
        for prefix in high_confidence_prefixes:
            if passport.startswith(prefix):
                return True  # 有效前缀，确认有效
        
        # Medium confidence prefixes (扩展前缀)
        medium_confidence_prefixes = ['EA', 'EB', 'EC', 'ED', 'EE', 'SE', '14', '15']
        for prefix in medium_confidence_prefixes:
            if passport.startswith(prefix):
                return True  # 有效前缀，确认有效
        
        return None  # 未知前缀，需LLM验证

    def invalidate_result(self, pattern_text: str) -> bool:
        """
        Check if the pattern is obviously not a valid passport.

        :param pattern_text: Text detected as pattern by regex
        :return: True if invalidated (should be rejected)
        """
        passport = pattern_text.replace("-", "").replace(" ", "").upper()
        
        # Check for all same digits
        digits = ''.join(c for c in passport if c.isdigit())
        if len(set(digits)) == 1 and len(digits) > 5:
            return True
        
        # Check for obviously fake patterns (all zeros or all ones)
        if digits in ['00000000', '11111111', '99999999']:
            return True
        
        return False

"""
China ID Card (身份证) Recognizer.

18-digit ID card number with checksum validation.
Format: RRRRRRYYYYMMDDSSSC
- RRRRRR: Region code (6 digits)
- YYYYMMDD: Birth date (8 digits)
- SSS: Sequence code (3 digits)
- C: Checksum digit (1 digit, can be 0-9 or X)

Reference: GB 11643-1999
"""

from typing import List, Optional, Tuple

from presidio_analyzer import Pattern, PatternRecognizer


class CnIdCardRecognizer(PatternRecognizer):
    """
    Recognize Chinese ID Card numbers (居民身份证号码).

    The 18-digit ID card number consists of:
    - 6 digits: Region code (行政区划代码)
    - 8 digits: Birth date YYYYMMDD (出生日期)
    - 3 digits: Sequence number (顺序码，奇数男性，偶数女性)
    - 1 digit: Checksum (校验码，0-9 或 X)

    :param patterns: List of patterns to be used by this recognizer
    :param context: List of context words to increase confidence in detection
    :param supported_language: Language this recognizer supports
    :param supported_entity: The entity this recognizer can detect
    """

    PATTERNS = [
        # High confidence: Full format with valid region prefix (1-6)
        # 完整格式 + 有效省份前缀，基础分数0.5，校验通过→1.0
        Pattern(
            "CN ID Card (High)",
            r"(?<![0-9])[1-6]\d{5}(?:19|20)\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])\d{3}[\dXx](?![0-9])",
            0.5,
        ),
        # Medium confidence: 18 digits with valid date structure
        # 日期格式正确但省份不确定，基础分数0.4，需LLM验证
        Pattern(
            "CN ID Card (Medium)",
            r"(?<![0-9])[1-9]\d{5}(?:19|20)\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])\d{3}[\dXx](?![0-9])",
            0.4,
        ),
        # Low confidence: Any 18 character pattern ending with digit or X
        # 宽松匹配，基础分数0.25，必须LLM验证
        Pattern(
            "CN ID Card (Low)",
            r"(?<![0-9])\d{17}[\dXx](?![0-9])",
            0.25,
        ),
    ]

    # Comprehensive Chinese context words for ID card
    CONTEXT = [
        # 中文 - 正式称谓
        "身份证", "身份证号", "身份证号码", "居民身份证", "公民身份号码",
        "证件号", "证件号码", "证件编号", "身份号码", "身份编号",
        # 中文 - 口语/简称
        "身份", "证号", "证件", "号码",
        # 中文 - 相关场景
        "持证人", "证件持有人", "本人身份", "实名认证", "实名制",
        "身份验证", "身份核验", "身份信息", "个人身份",
        # 英文
        "id card", "id number", "id no", "id code",
        "identification", "identification number", "identity",
        "identity card", "identity number", "citizen id",
        "national id", "personal id", "resident id",
        # 拼音缩写
        "sfz", "sfzh", "zjh", "zjhm",
    ]

    # Weights for checksum calculation (GB 11643-1999)
    WEIGHTS = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]
    
    # Checksum mapping table: remainder -> checksum digit
    CHECKSUM_MAP = ['1', '0', 'X', '9', '8', '7', '6', '5', '4', '3', '2']

    # Valid province codes (first 2 digits)
    VALID_PROVINCE_CODES = {
        "11", "12", "13", "14", "15",  # 华北：北京、天津、河北、山西、内蒙古
        "21", "22", "23",              # 东北：辽宁、吉林、黑龙江
        "31", "32", "33", "34", "35", "36", "37",  # 华东：上海、江苏、浙江、安徽、福建、江西、山东
        "41", "42", "43", "44", "45", "46",        # 中南：河南、湖北、湖南、广东、广西、海南
        "50", "51", "52", "53", "54",              # 西南：重庆、四川、贵州、云南、西藏
        "61", "62", "63", "64", "65",              # 西北：陕西、甘肃、青海、宁夏、新疆
        "71",  # 台湾
        "81", "82",  # 港澳：香港、澳门
    }

    def __init__(
        self,
        patterns: Optional[List[Pattern]] = None,
        context: Optional[List[str]] = None,
        supported_language: str = "zh",
        supported_entity: str = "CN_ID_CARD",
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
        Validate the ID card number using checksum algorithm.

        :param pattern_text: The detected ID card number
        :return: 
            - True: 校验码验证通过，分数设为1.0
            - False: 明确无效（格式错误），分数设为0，结果被丢弃
            - None: 不确定（校验码不匹配但格式正确），保持基础分数，需LLM验证
        """
        # Remove any separators and convert to uppercase
        id_number = pattern_text.replace("-", "").replace(" ", "").upper()
        
        if len(id_number) != 18:
            return False  # 长度不对，明确无效
        
        # Validate province code
        province_code = id_number[:2]
        if province_code not in self.VALID_PROVINCE_CODES:
            return None  # 省份码不在已知列表，可能是新增的，需LLM验证
        
        # Validate checksum using GB 11643-1999 algorithm
        try:
            # Calculate weighted sum of first 17 digits
            total = 0
            for i in range(17):
                total += int(id_number[i]) * self.WEIGHTS[i]
            
            # Get expected checksum from mapping table
            expected_checksum = self.CHECKSUM_MAP[total % 11]
            
            # Compare with actual checksum (last digit)
            actual_checksum = id_number[17].upper()
            
            if actual_checksum == expected_checksum:
                return True  # 校验码正确，100%确认
            else:
                return None  # 校验码不匹配，可能是脱敏数据，需LLM验证
            
        except (ValueError, IndexError):
            return None  # 解析失败，需LLM验证

    def invalidate_result(self, pattern_text: str) -> bool:
        """
        Check if the pattern text is obviously not a valid ID card.

        :param pattern_text: Text detected as pattern by regex
        :return: True if invalidated (should be rejected)
        """
        id_number = pattern_text.replace("-", "").replace(" ", "").upper()
        
        if len(id_number) != 18:
            return True
        
        # Check if all digits are the same (except last which can be X)
        if len(set(id_number[:17])) == 1:
            return True
        
        # Check for sequential patterns
        sequential_patterns = [
            "123456789012345678",
            "012345678901234567",
            "111111111111111111",
            "000000000000000000",
        ]
        for pattern in sequential_patterns:
            if id_number[:17] == pattern[:17]:
                return True
        
        # Validate birth date
        try:
            year = int(id_number[6:10])
            month = int(id_number[10:12])
            day = int(id_number[12:14])
            
            # Year validation (reasonable range)
            if year < 1900 or year > 2100:
                return True
            
            # Month validation
            if month < 1 or month > 12:
                return True
            
            # Day validation (basic)
            if day < 1 or day > 31:
                return True
            
            # More precise day validation based on month
            days_in_month = [0, 31, 29, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
            if day > days_in_month[month]:
                return True
                
        except ValueError:
            return True
        
        return False

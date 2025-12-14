"""
China Vehicle License Plate Recognizer.

Recognizes Chinese vehicle license plate numbers.

Formats:
- Regular plates: 省份简称 + 字母 + 5位字母数字 (e.g., 京A12345)
- New energy plates: 省份简称 + 字母 + 6位字母数字 (e.g., 京AD12345)
- Special plates: Various formats for military, police, etc.

Reference: GA 36-2018
"""

from typing import List, Optional, Tuple

from presidio_analyzer import Pattern, PatternRecognizer


class CnVehiclePlateRecognizer(PatternRecognizer):
    """
    Recognize Chinese vehicle license plate numbers.

    Plate types:
    - Regular (普通号牌): 7 characters
    - New energy (新能源): 8 characters
    - Military (军用): Special format
    - Police (警用): Special format
    - Embassy (使馆): Special format

    :param patterns: List of patterns to be used by this recognizer
    :param context: List of context words to increase confidence in detection
    :param supported_language: Language this recognizer supports
    :param supported_entity: The entity this recognizer can detect
    """

    # Province abbreviations (省份简称)
    PROVINCES = "京津沪渝冀豫云辽黑湘皖鲁新苏浙赣鄂桂甘晋蒙陕吉闽贵粤青藏川宁琼"
    
    PATTERNS = [
        # Regular plate: 省 + 字母 + 5位 (e.g., 京A12345, 粤B·12345)
        Pattern(
            "CN Vehicle Plate Regular",
            r"(?<![" + PROVINCES + r"A-Za-z0-9])[" + PROVINCES + r"][A-HJ-NP-Z][A-HJ-NP-Z0-9]{4}[A-HJ-NP-Z0-9挂学警港澳](?![A-Za-z0-9])",
            0.6,
        ),
        # New energy plate: 省 + 字母 + 6位 (e.g., 京AD12345)
        Pattern(
            "CN Vehicle Plate New Energy",
            r"(?<![" + PROVINCES + r"A-Za-z0-9])[" + PROVINCES + r"][A-HJ-NP-Z][A-HJ-NP-Z0-9]{5}[A-HJ-NP-Z0-9](?![A-Za-z0-9])",
            0.6,
        ),
        # With separator: 京A·12345 or 京A-12345
        Pattern(
            "CN Vehicle Plate Separated",
            r"(?<![" + PROVINCES + r"A-Za-z0-9])[" + PROVINCES + r"][A-HJ-NP-Z][·\-]?[A-HJ-NP-Z0-9]{5,6}(?![A-Za-z0-9])",
            0.5,
        ),
        # Military plate: 军/空/海/北/沈/兰/济/南/广/成 + 字母 + 5位
        Pattern(
            "CN Vehicle Plate Military",
            r"(?<![A-Za-z0-9])[军空海北沈兰济南广成][A-Z][A-Z0-9]{5}(?![A-Za-z0-9])",
            0.65,
        ),
        # Police plate: 省 + 字母 + 4位 + 警
        Pattern(
            "CN Vehicle Plate Police",
            r"(?<![" + PROVINCES + r"A-Za-z0-9])[" + PROVINCES + r"][A-HJ-NP-Z][A-Z0-9]{4}警(?![A-Za-z0-9])",
            0.6,
        ),
        # Embassy plate: 使 + 3位数字 + 2位数字
        Pattern(
            "CN Vehicle Plate Embassy",
            r"(?<![A-Za-z0-9])使[0-9]{3}[0-9]{2}(?![0-9])",
            0.6,
        ),
        # Hong Kong/Macau plate: 粤Z + 4位 + 港/澳
        Pattern(
            "CN Vehicle Plate HK Macau",
            r"(?<![" + PROVINCES + r"A-Za-z0-9])粤Z[A-Z0-9]{4}[港澳](?![A-Za-z0-9])",
            0.6,
        ),
    ]

    # Comprehensive context words
    CONTEXT = [
        # 中文 - 车牌相关
        "车牌", "车牌号", "车牌号码", "牌照", "牌照号",
        "号牌", "机动车号牌", "汽车牌照",
        # 中文 - 车辆相关
        "车辆", "机动车", "汽车", "轿车", "货车", "客车",
        "私家车", "公务车", "出租车", "网约车",
        # 中文 - 登记相关
        "行驶证", "车辆登记", "机动车登记",
        "车主", "车辆所有人",
        # 中文 - 场景相关
        "停车", "违章", "违停", "交通违法",
        "年检", "年审", "过户", "上牌",
        # 英文
        "license plate", "plate number", "vehicle plate",
        "car plate", "registration plate",
        "vehicle registration", "car registration",
    ]

    def __init__(
        self,
        patterns: Optional[List[Pattern]] = None,
        context: Optional[List[str]] = None,
        supported_language: str = "zh",
        supported_entity: str = "CN_VEHICLE_PLATE",
        replacement_pairs: Optional[List[Tuple[str, str]]] = None,
    ):
        self.replacement_pairs = (
            replacement_pairs if replacement_pairs else [("·", ""), ("-", ""), (" ", "")]
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
        Validate the vehicle plate number.

        :param pattern_text: The detected plate number
        :return: 
            - True: 有效省份/特殊前缀，分数设为1.0
            - False: 明确无效（长度错误），分数设为0，结果被丢弃
            - None: 不确定，保持基础分数，需LLM验证
        """
        plate = pattern_text.replace("·", "").replace("-", "").replace(" ", "")
        
        # Check length
        if len(plate) < 7 or len(plate) > 8:
            return False  # 长度不对，明确无效
        
        # Check first character is a valid province
        if plate[0] in self.PROVINCES:
            return True  # 有效省份，确认有效
        
        # Check for special plates
        special_prefixes = "军空海北沈兰济南广成使"
        if plate[0] in special_prefixes:
            return True  # 特殊车牌，确认有效
        
        return None  # 未知前缀，需LLM验证

    def invalidate_result(self, pattern_text: str) -> bool:
        """
        Check if the pattern is obviously not a valid plate.

        :param pattern_text: Text detected as pattern by regex
        :return: True if invalidated (should be rejected)
        """
        plate = pattern_text.replace("·", "").replace("-", "").replace(" ", "")
        
        # Check for all same characters (excluding first two: province + letter)
        if len(plate) > 2 and len(set(plate[2:])) == 1:
            return True
        
        # Check for obviously fake patterns (all zeros or all ones)
        suffix = plate[2:] if len(plate) > 2 else ""
        if suffix in ['00000', '11111', '99999', '000000', '111111', '999999']:
            return True
        
        return False

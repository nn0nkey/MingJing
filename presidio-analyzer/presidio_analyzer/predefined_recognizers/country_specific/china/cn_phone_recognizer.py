"""
China Mobile Phone Number Recognizer.

Recognizes Chinese mobile phone numbers (11 digits starting with 1).
Supports all major carriers: China Mobile, China Unicom, China Telecom, and MVNOs.

Also recognizes landline numbers with area codes.
"""

from typing import List, Optional, Tuple

from presidio_analyzer import Pattern, PatternRecognizer


class CnPhoneRecognizer(PatternRecognizer):
    """
    Recognize Chinese phone numbers (mobile and landline).

    Mobile numbers are 11 digits starting with 1:
    - China Mobile (中国移动): 134-139, 147, 148, 150-152, 157-159, 172, 178, 182-184, 187-188, 195, 198
    - China Unicom (中国联通): 130-132, 145, 146, 155-156, 166, 167, 171, 175-176, 185-186, 196
    - China Telecom (中国电信): 133, 149, 153, 173, 174, 177, 180-181, 189, 190, 191, 193, 199
    - China Broadnet (中国广电): 192
    - MVNOs (虚拟运营商): 162, 165, 167, 170, 171

    Landline numbers: Area code (3-4 digits) + Local number (7-8 digits)

    :param patterns: List of patterns to be used by this recognizer
    :param context: List of context words to increase confidence in detection
    :param supported_language: Language this recognizer supports
    :param supported_entity: The entity this recognizer can detect
    """

    PATTERNS = [
        # 高置信度: +86前缀，明确是中国手机号
        Pattern(
            "CN Mobile (Country Code)",
            r"(?:(?:\+|00)86[-\s]?)1[3-9]\d{9}(?![0-9])",
            0.75,  # 有国家码，高度可信
        ),
        # 高置信度: 有效运营商号段
        Pattern(
            "CN Mobile (High)",
            r"(?<![0-9])1(?:3[0-9]|4[5-9]|5[0-35-9]|6[2567]|7[0-8]|8[0-9]|9[0-35-9])\d{8}(?![0-9])",
            0.55,  # 有效号段，较可信
        ),
        # 中置信度: 带分隔符的手机号
        Pattern(
            "CN Mobile (Separated)",
            r"(?<![0-9])1[3-9]\d[-\s]\d{4}[-\s]\d{4}(?![0-9])",
            0.5,  # 格式明确
        ),
        # 中置信度: 固话带区号
        Pattern(
            "CN Landline (High)",
            r"(?<![0-9])0(?:10|2[0-9]|[3-9]\d{2})[-\s]?\d{7,8}(?![0-9])",
            0.5,  # 有区号，较可信
        ),
        # 中置信度: 固话带括号
        Pattern(
            "CN Landline (Parentheses)",
            r"\(0(?:10|2[0-9]|[3-9]\d{2})\)[-\s]?\d{7,8}(?![0-9])",
            0.55,  # 格式明确
        ),
        # 中置信度: 400/800服务号
        Pattern(
            "CN Service Number",
            r"(?<![0-9])(?:400|800)[-\s]?\d{3}[-\s]?\d{4}(?![0-9])",
            0.6,  # 服务号格式明确
        ),
        # 低置信度: 任意1[3-9]开头11位，需LLM验证
        Pattern(
            "CN Mobile (Medium)",
            r"(?<![0-9])1[3-9]\d{9}(?![0-9])",
            0.4,  # 宽松匹配，需验证
        ),
    ]

    # Comprehensive Chinese context words for phone
    CONTEXT = [
        # 中文 - 手机相关
        "手机", "手机号", "手机号码", "移动电话", "移动号码",
        "手机联系", "本机号码", "联系手机",
        # 中文 - 电话相关
        "电话", "电话号码", "联系电话", "联系方式", "通讯方式",
        "座机", "固话", "固定电话", "办公电话", "家庭电话",
        "传真", "传真号", "传真号码",
        # 中文 - 场景相关
        "联系人", "紧急联系", "紧急电话", "客服电话", "服务电话",
        "咨询电话", "投诉电话", "热线", "热线电话",
        "来电", "去电", "通话", "拨打", "致电",
        # 英文
        "phone", "phone number", "mobile", "mobile phone", "mobile number",
        "cell", "cellphone", "cell phone", "cellular",
        "tel", "telephone", "telephone number",
        "contact", "contact number", "call",
        "fax", "fax number",
        "landline", "hotline",
        # 缩写
        "tel.", "mob.", "ph.", "fax.",
    ]

    # Valid mobile prefixes (updated 2024)
    VALID_MOBILE_PREFIXES = {
        # China Mobile (中国移动)
        "134", "135", "136", "137", "138", "139",
        "147", "148",
        "150", "151", "152", "157", "158", "159",
        "172", "178",
        "182", "183", "184", "187", "188",
        "195", "197", "198",
        # China Unicom (中国联通)
        "130", "131", "132",
        "145", "146",
        "155", "156",
        "166", "167",
        "171", "175", "176",
        "185", "186",
        "196",
        # China Telecom (中国电信)
        "133", "149",
        "153",
        "173", "174", "177",
        "180", "181", "189",
        "190", "191", "193", "199",
        # China Broadnet (中国广电)
        "192",
        # MVNOs (虚拟运营商)
        "162", "165", "167", "170", "171",
    }

    # Valid area codes for landlines
    VALID_AREA_CODES = {
        # 直辖市 (3位区号)
        "010",  # 北京
        "021",  # 上海
        "022",  # 天津
        "023",  # 重庆
        # 省会/主要城市 (4位区号) - 部分示例
        "020",  # 广州
        "025",  # 南京
        "027",  # 武汉
        "028",  # 成都
        "029",  # 西安
        "0755", # 深圳
        "0571", # 杭州
        "0512", # 苏州
    }

    def __init__(
        self,
        patterns: Optional[List[Pattern]] = None,
        context: Optional[List[str]] = None,
        supported_language: str = "zh",
        supported_entity: str = "CN_PHONE",
        replacement_pairs: Optional[List[Tuple[str, str]]] = None,
    ):
        self.replacement_pairs = (
            replacement_pairs if replacement_pairs else [("-", ""), (" ", ""), ("(", ""), (")", "")]
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
        Validate the phone number.

        :param pattern_text: The detected phone number
        :return: 
            - True: 确认有效（有效运营商号段/有效区号），分数设为1.0
            - False: 明确无效，分数设为0，结果被丢弃
            - None: 不确定，保持基础分数，需LLM验证
        """
        # Remove separators and country code
        phone = pattern_text.replace("-", "").replace(" ", "").replace("(", "").replace(")", "")
        phone = phone.replace("+86", "").replace("0086", "")
        
        # Mobile number validation
        if len(phone) == 11 and phone.startswith("1"):
            prefix = phone[:3]
            if prefix in self.VALID_MOBILE_PREFIXES:
                return True  # 有效运营商号段，确认有效
            else:
                return None  # 未知号段，可能是新号段，需LLM验证
        
        # Landline validation (area code + local number)
        if phone.startswith("0"):
            # 3-digit area code (010, 02X) + 8-digit local
            if len(phone) == 11 and (phone.startswith("010") or phone[1] == "2"):
                return True  # 有效区号格式
            # 4-digit area code (0XXX) + 7-8 digit local
            if len(phone) in [11, 12] and phone[1] != "0":
                return True  # 有效区号格式
            return None  # 格式不太对，需LLM验证
        
        # 400/800 service numbers
        if phone.startswith(("400", "800")) and len(phone) == 10:
            return True  # 服务号格式正确
        
        return None  # 无法确定，需LLM验证

    def invalidate_result(self, pattern_text: str) -> bool:
        """
        Check if the pattern text is obviously not a valid phone number.

        :param pattern_text: Text detected as pattern by regex
        :return: True if invalidated (should be rejected)
        """
        phone = pattern_text.replace("-", "").replace(" ", "").replace("(", "").replace(")", "")
        phone = phone.replace("+86", "").replace("0086", "")
        
        # Check if all digits are the same
        if len(set(phone)) == 1:
            return True
        
        # Check for sequential patterns
        sequential_patterns = [
            "12345678901",
            "10987654321",
            "11111111111",
            "00000000000",
            "10000000000",
        ]
        if phone in sequential_patterns:
            return True
        
        # Check for obviously fake patterns
        if phone.startswith("100") or phone.startswith("110") or phone.startswith("120"):
            # These are emergency/service numbers, not personal phones
            if len(phone) == 11:
                return True
        
        return False

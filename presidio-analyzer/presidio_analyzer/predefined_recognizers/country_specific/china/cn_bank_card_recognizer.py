"""
China Bank Card Number Recognizer.

Recognizes Chinese bank card numbers (16-19 digits) with Luhn checksum validation.
Supports UnionPay (银联) and international cards (Visa, MasterCard, etc.).

Reference: ISO/IEC 7812
"""

from typing import List, Optional, Tuple

from presidio_analyzer import Pattern, PatternRecognizer


class CnBankCardRecognizer(PatternRecognizer):
    """
    Recognize Chinese bank card numbers.

    Card number structure:
    - BIN (Bank Identification Number): First 6 digits
    - Account Number: Middle digits
    - Check Digit: Last digit (Luhn algorithm)

    Card lengths:
    - Debit cards: Usually 16 or 19 digits
    - Credit cards: Usually 16 digits
    - UnionPay cards: Start with 62

    :param patterns: List of patterns to be used by this recognizer
    :param context: List of context words to increase confidence in detection
    :param supported_language: Language this recognizer supports
    :param supported_entity: The entity this recognizer can detect
    """

    PATTERNS = [
        # 高置信度: 银联卡 (62开头)，Luhn校验通过→1.0
        Pattern(
            "CN Bank Card UnionPay 16",
            r"(?<![0-9])62[0-9]{14}(?![0-9])",
            0.5,  # 银联前缀，较可信
        ),
        Pattern(
            "CN Bank Card UnionPay 19",
            r"(?<![0-9])62[0-9]{17}(?![0-9])",
            0.5,  # 银联前缀，较可信
        ),
        # 中置信度: Visa卡 (4开头)
        Pattern(
            "CN Bank Card Visa",
            r"(?<![0-9])4[0-9]{15}(?![0-9])",
            0.45,  # 国际卡，需Luhn验证
        ),
        # 中置信度: MasterCard (5[1-5]或2[2-7]开头)
        Pattern(
            "CN Bank Card MasterCard",
            r"(?<![0-9])(?:5[1-5][0-9]{14}|2(?:2[2-9][0-9]{12}|[3-6][0-9]{13}|7[01][0-9]{12}|720[0-9]{12}))(?![0-9])",
            0.45,  # 国际卡，需Luhn验证
        ),
        # 中置信度: JCB卡 (35开头)
        Pattern(
            "CN Bank Card JCB",
            r"(?<![0-9])35[0-9]{14}(?![0-9])",
            0.45,  # 国际卡，需Luhn验证
        ),
        # 中置信度: American Express (34/37开头, 15位)
        Pattern(
            "CN Bank Card Amex",
            r"(?<![0-9])3[47][0-9]{13}(?![0-9])",
            0.45,  # 国际卡，需Luhn验证
        ),
        # 中置信度: 带分隔符的卡号
        Pattern(
            "CN Bank Card Separated 16",
            r"(?<![0-9])[3-6][0-9]{3}[-\s][0-9]{4}[-\s][0-9]{4}[-\s][0-9]{4}(?![0-9])",
            0.45,  # 格式明确
        ),
        Pattern(
            "CN Bank Card Separated 19",
            r"(?<![0-9])[3-6][0-9]{3}[-\s][0-9]{4}[-\s][0-9]{4}[-\s][0-9]{4}[-\s][0-9]{3}(?![0-9])",
            0.45,  # 格式明确
        ),
        # 低置信度: 通用16-19位，需LLM验证
        Pattern(
            "CN Bank Card Generic",
            r"(?<![0-9])[3-6][0-9]{15,18}(?![0-9])",
            0.3,  # 宽松匹配，必须验证
        ),
    ]

    # Comprehensive Chinese context words for bank card
    CONTEXT = [
        # 中文 - 卡片类型
        "银行卡", "银行卡号", "卡号", "卡片号", "卡片号码",
        "储蓄卡", "借记卡", "信用卡", "贷记卡", "预付卡",
        "银联卡", "银联", "金融卡",
        # 中文 - 账户相关
        "账号", "账户", "账户号", "账户号码", "开户账号",
        "收款账号", "付款账号", "转账账号", "汇款账号",
        # 中文 - 银行名称
        "工商银行", "建设银行", "农业银行", "中国银行", "交通银行",
        "招商银行", "浦发银行", "民生银行", "中信银行", "光大银行",
        "华夏银行", "广发银行", "平安银行", "兴业银行", "邮储银行",
        "工行", "建行", "农行", "中行", "交行", "招行", "浦发", "民生",
        # 中文 - 操作相关
        "转账", "汇款", "收款", "付款", "支付", "结算",
        "绑定银行卡", "添加银行卡", "银行卡绑定",
        # 英文
        "bank card", "card number", "card no", "card num",
        "account", "account number", "account no",
        "debit card", "credit card", "prepaid card",
        "unionpay", "visa", "mastercard", "amex", "jcb",
        "bank account", "payment card",
        # 缩写
        "acct", "acct.", "a/c",
    ]

    # Common bank BIN prefixes (first 6 digits) - 主要银行
    BANK_BINS = {
        # 工商银行 (ICBC)
        "622202", "622203", "621226", "621227", "621281", "621282",
        "621283", "621284", "621285", "621286", "621287", "621288",
        # 建设银行 (CCB)
        "621700", "622280", "622700", "436742", "436745", "622966",
        "621284", "621467", "621598", "621621", "621670",
        # 农业银行 (ABC)
        "622848", "622849", "621282", "621336", "621619", "621670",
        "622836", "622837", "622838", "622839", "622840",
        # 中国银行 (BOC)
        "621660", "621661", "622760", "622761", "622762", "622763",
        "621256", "621212", "621283", "621485", "621486",
        # 招商银行 (CMB)
        "621836", "622580", "622588", "621286", "621488", "621588",
        "622575", "622576", "622577", "622578", "622579",
        # 交通银行 (BOCOM)
        "621069", "622260", "622261", "621436", "621335", "621326",
        "622258", "622259", "622252", "622253",
        # 邮储银行 (PSBC)
        "621096", "622188", "621098", "621095", "621285", "621798",
        "622199", "621799", "621899",
        # 中信银行 (CITIC)
        "622690", "622691", "622692", "622696", "621768", "621767",
        # 民生银行 (CMBC)
        "622622", "622623", "621691", "621692", "621693", "622600",
        # 浦发银行 (SPDB)
        "622520", "622521", "622522", "621289", "621290", "621291",
        # 兴业银行 (CIB)
        "622909", "622908", "621395", "621396", "621397", "621398",
        # 光大银行 (CEB)
        "622660", "622661", "622662", "622663", "621489", "621490",
        # 平安银行 (PAB)
        "622155", "622156", "622157", "622158", "621626", "621627",
        # 华夏银行 (HXB)
        "622630", "622631", "622632", "622633", "621222", "621223",
        # 广发银行 (CGB)
        "622555", "622556", "622557", "622558", "621462", "621463",
    }

    def __init__(
        self,
        patterns: Optional[List[Pattern]] = None,
        context: Optional[List[str]] = None,
        supported_language: str = "zh",
        supported_entity: str = "CN_BANK_CARD",
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
        Validate the bank card number using Luhn algorithm.

        :param pattern_text: The detected bank card number
        :return: 
            - True: Luhn校验通过，分数设为1.0
            - False: 明确无效（长度/格式错误），分数设为0，结果被丢弃
            - None: 不确定（Luhn校验失败但格式正确，可能是脱敏数据），保持基础分数
        """
        # Remove separators
        card_number = pattern_text.replace("-", "").replace(" ", "")
        
        # Check length (15 for Amex, 16-19 for others)
        if len(card_number) < 15 or len(card_number) > 19:
            return False  # 长度不对，明确无效
        
        # Check if all characters are digits
        if not card_number.isdigit():
            return False  # 包含非数字，明确无效
        
        # Luhn algorithm validation
        if self._luhn_checksum(card_number):
            return True  # Luhn校验通过，100%确认
        else:
            return None  # Luhn校验失败，可能是脱敏数据，需LLM验证

    def _luhn_checksum(self, card_number: str) -> bool:
        """
        Validate card number using Luhn algorithm (ISO/IEC 7812).

        :param card_number: The card number to validate
        :return: True if valid, False otherwise
        """
        def digits_of(n: str) -> List[int]:
            return [int(d) for d in n]
        
        digits = digits_of(card_number)
        # Reverse the digits
        digits = digits[::-1]
        
        checksum = 0
        for i, d in enumerate(digits):
            if i % 2 == 1:  # Double every second digit
                d = d * 2
                if d > 9:
                    d = d - 9
            checksum += d
        
        return checksum % 10 == 0

    def invalidate_result(self, pattern_text: str) -> bool:
        """
        Check if the pattern text is obviously not a valid bank card.

        :param pattern_text: Text detected as pattern by regex
        :return: True if invalidated (should be rejected)
        """
        card_number = pattern_text.replace("-", "").replace(" ", "")
        
        # Check if all digits are the same
        if len(set(card_number)) == 1:
            return True
        
        # Check for sequential patterns
        sequential_patterns = [
            "1234567890123456",
            "0123456789012345",
            "0000000000000000",
            "1111111111111111",
            "9999999999999999",
        ]
        for pattern in sequential_patterns:
            if card_number == pattern[:len(card_number)]:
                return True
        
        # Check for obviously invalid prefixes
        invalid_prefixes = ["0000", "1111", "9999", "0123"]
        for prefix in invalid_prefixes:
            if card_number.startswith(prefix):
                return True
        
        return False

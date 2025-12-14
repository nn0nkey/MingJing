"""
China Military ID Recognizer.

Recognizes Chinese military-related ID numbers:
- Military Officer ID (军官证): 军字第XXXXXXXX号
- Soldier ID (士兵证): 士字第XXXXXXXX号
- Civilian Staff ID (文职干部证): 文字第XXXXXXXX号
- Retired Military ID (退役军人证): Various formats

Reference: 中国人民解放军军人证件管理规定
"""

from typing import List, Optional, Tuple

from presidio_analyzer import Pattern, PatternRecognizer


class CnMilitaryIdRecognizer(PatternRecognizer):
    """
    Recognize Chinese military ID numbers.

    Types:
    - 军官证 (Military Officer ID)
    - 士兵证 (Soldier ID)
    - 文职干部证 (Civilian Staff ID)
    - 退役军人证 (Retired Military ID)
    - 军人保障卡 (Military Security Card)

    :param patterns: List of patterns to be used by this recognizer
    :param context: List of context words to increase confidence in detection
    :param supported_language: Language this recognizer supports
    :param supported_entity: The entity this recognizer can detect
    """

    PATTERNS = [
        # Military ID with prefix: 军/士/文/参/学 + 字第 + 6-10 digits + 号
        Pattern(
            "CN Military ID Full",
            r"[军士文参学]字第[0-9]{6,10}号",
            0.85,
        ),
        # Military ID with prefix without 号: 军/士/文/参/学 + 字第 + 6-10 digits
        Pattern(
            "CN Military ID Prefix",
            r"[军士文参学]字第[0-9]{6,10}(?![0-9])",
            0.75,
        ),
        # Retired military ID: Various formats
        Pattern(
            "CN Retired Military ID",
            r"退[役伍]?[军兵]?[人员]?[证号]?[：:]\s*[A-Z0-9]{8,18}",
            0.7,
        ),
    ]

    # Comprehensive context words
    CONTEXT = [
        # 中文 - 军人证件
        "军官证", "军人证", "士兵证", "士官证",
        "文职干部证", "文职证", "军队文职",
        "军人保障卡", "保障卡",
        # 中文 - 退役相关
        "退役军人证", "退役证", "退伍证", "复员证",
        "退役军人", "退伍军人", "复员军人",
        # 中文 - 军队相关
        "军队", "部队", "军人", "军官", "士兵", "士官",
        "现役", "服役", "入伍", "退伍",
        # 中文 - 证件相关
        "军字第", "士字第", "文字第", "参字第", "学字第",
        "证件号", "证号",
        # 英文
        "military id", "military card",
        "soldier id", "officer id",
        "military service", "armed forces",
    ]

    def __init__(
        self,
        patterns: Optional[List[Pattern]] = None,
        context: Optional[List[str]] = None,
        supported_language: str = "zh",
        supported_entity: str = "CN_MILITARY_ID",
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
        Validate the military ID.

        :param pattern_text: The detected military ID
        :return: True if valid format, False otherwise
        """
        # Extract digits
        digits = ''.join(c for c in pattern_text if c.isdigit())
        
        # Check length
        if len(digits) < 6 or len(digits) > 18:
            return False
        
        return True

    def invalidate_result(self, pattern_text: str) -> bool:
        """
        Check if the pattern is obviously not a valid military ID.

        :param pattern_text: Text detected as pattern by regex
        :return: True if invalidated (should be rejected)
        """
        digits = ''.join(c for c in pattern_text if c.isdigit())
        
        # Check for all same digits
        if len(set(digits)) == 1 and len(digits) > 3:
            return True
        
        return False

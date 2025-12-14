"""
China Medical License Recognizer.

Recognizes Chinese medical-related license numbers:
- Medical Practitioner License (医师执业证书)
- Nurse License (护士执业证书)
- Medical Institution License (医疗机构执业许可证)
- Pharmacist License (药师执业证书)

Reference: 中华人民共和国执业医师法
"""

from typing import List, Optional, Tuple

from presidio_analyzer import Pattern, PatternRecognizer


class CnMedicalLicenseRecognizer(PatternRecognizer):
    """
    Recognize Chinese medical license numbers.

    Types:
    - 医师执业证书 (Medical Practitioner License): 15 digits
    - 护士执业证书 (Nurse License): 15 digits
    - 医疗机构执业许可证 (Medical Institution License): Various formats
    - 药师执业证书 (Pharmacist License): 15 digits

    :param patterns: List of patterns to be used by this recognizer
    :param context: List of context words to increase confidence in detection
    :param supported_language: Language this recognizer supports
    :param supported_entity: The entity this recognizer can detect
    """

    PATTERNS = [
        # Medical practitioner license: 15 digits
        Pattern(
            "CN Medical License 15",
            r"(?<![0-9])\d{15}(?![0-9])",
            0.2,  # Low confidence, needs context
        ),
        # Medical institution license: Province code + year + number
        Pattern(
            "CN Medical Institution License",
            r"(?<![0-9A-Za-z])[A-Z]{2,4}[0-9]{8,12}(?![0-9A-Za-z])",
            0.3,
        ),
        # With prefix: 医师/护士 + 执业证书编号 + number
        Pattern(
            "CN Medical License Prefixed",
            r"(?:医师|护士|药师)(?:执业)?(?:证书)?(?:编号)?[：:\s]*[0-9]{10,18}",
            0.6,
        ),
        # Qualification certificate: 资格证书编号
        Pattern(
            "CN Medical Qualification",
            r"资格证书(?:编号)?[：:\s]*[0-9]{10,18}",
            0.6,
        ),
    ]

    # Comprehensive context words
    CONTEXT = [
        # 中文 - 医师相关
        "医师", "医生", "执业医师", "主治医师", "副主任医师", "主任医师",
        "医师执业证", "医师执业证书", "医师资格证", "医师资格证书",
        "执业证书", "执业证", "执业编号",
        # 中文 - 护士相关
        "护士", "护师", "主管护师",
        "护士执业证", "护士执业证书", "护士资格证",
        # 中文 - 药师相关
        "药师", "执业药师", "药剂师",
        "药师执业证", "药师资格证",
        # 中文 - 医疗机构
        "医疗机构", "医院", "诊所", "卫生院",
        "医疗机构执业许可证", "执业许可证",
        # 中文 - 资格相关
        "资格证", "资格证书", "资格编号",
        "注册号", "注册编号", "执业注册",
        # 英文
        "medical license", "medical practitioner",
        "nurse license", "nursing license",
        "pharmacist license", "pharmacy license",
        "medical certificate", "healthcare license",
    ]

    def __init__(
        self,
        patterns: Optional[List[Pattern]] = None,
        context: Optional[List[str]] = None,
        supported_language: str = "zh",
        supported_entity: str = "CN_MEDICAL_LICENSE",
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
        Validate the medical license number.

        :param pattern_text: The detected license number
        :return: True if valid format, False otherwise
        """
        # Extract digits
        digits = ''.join(c for c in pattern_text if c.isdigit())
        
        # Check length
        if len(digits) < 10 or len(digits) > 18:
            return False
        
        return True

    def invalidate_result(self, pattern_text: str) -> bool:
        """
        Check if the pattern is obviously not a valid license.

        :param pattern_text: Text detected as pattern by regex
        :return: True if invalidated (should be rejected)
        """
        digits = ''.join(c for c in pattern_text if c.isdigit())
        
        # Check for all same digits
        if len(set(digits)) == 1 and len(digits) > 3:
            return True
        
        return False

"""
MAC Address Recognizer.

Recognizes MAC (Media Access Control) addresses in various formats:
- Colon-separated: AA:BB:CC:DD:EE:FF
- Hyphen-separated: AA-BB-CC-DD-EE-FF
- Dot-separated (Cisco): AABB.CCDD.EEFF
- No separator: AABBCCDDEEFF
"""

from typing import List, Optional

from presidio_analyzer import Pattern, PatternRecognizer


class CnMacAddressRecognizer(PatternRecognizer):
    """
    Recognize MAC addresses.

    MAC addresses are 48-bit identifiers assigned to network interfaces.
    They can reveal device information and are considered sensitive.
    """

    PATTERNS = [
        # Colon-separated: AA:BB:CC:DD:EE:FF
        Pattern(
            "MAC Colon",
            r"(?<![A-Fa-f0-9:])(?:[A-Fa-f0-9]{2}:){5}[A-Fa-f0-9]{2}(?![A-Fa-f0-9:])",
            0.7,
        ),
        # Hyphen-separated: AA-BB-CC-DD-EE-FF
        Pattern(
            "MAC Hyphen",
            r"(?<![A-Fa-f0-9-])(?:[A-Fa-f0-9]{2}-){5}[A-Fa-f0-9]{2}(?![A-Fa-f0-9-])",
            0.7,
        ),
        # Dot-separated (Cisco format): AABB.CCDD.EEFF
        Pattern(
            "MAC Dot",
            r"(?<![A-Fa-f0-9.])[A-Fa-f0-9]{4}\.[A-Fa-f0-9]{4}\.[A-Fa-f0-9]{4}(?![A-Fa-f0-9.])",
            0.7,
        ),
        # No separator: AABBCCDDEEFF (12 hex chars)
        Pattern(
            "MAC NoSep",
            r"(?<![A-Fa-f0-9])[A-Fa-f0-9]{12}(?![A-Fa-f0-9])",
            0.3,
        ),
    ]

    CONTEXT = [
        # 中文 - MAC相关
        "MAC", "MAC地址", "物理地址", "硬件地址", "网卡地址",
        "设备地址", "设备标识", "设备ID",
        # 中文 - 网络相关
        "网卡", "网络适配器", "网络接口", "以太网",
        "无线网卡", "WiFi", "蓝牙", "Bluetooth",
        # 中文 - 设备相关
        "设备", "终端", "主机", "服务器", "路由器", "交换机",
        "手机", "电脑", "笔记本", "平板",
        # 英文
        "mac", "mac address", "physical address", "hardware address",
        "network interface", "ethernet", "wifi", "wireless",
        "nic", "network adapter", "device id", "device address",
        "router", "switch", "access point", "ap",
    ]

    def __init__(
        self,
        patterns: Optional[List[Pattern]] = None,
        context: Optional[List[str]] = None,
        supported_language: str = "zh",
        supported_entity: str = "CN_MAC_ADDRESS",
    ):
        patterns = patterns if patterns else self.PATTERNS
        context = context if context else self.CONTEXT
        super().__init__(
            supported_entity=supported_entity,
            patterns=patterns,
            context=context,
            supported_language=supported_language,
        )

    def validate_result(self, pattern_text: str) -> bool:
        """Validate the detected MAC address."""
        mac = pattern_text.strip().upper()
        
        # Remove separators
        mac_clean = mac.replace(':', '').replace('-', '').replace('.', '')
        
        # Should be 12 hex characters
        if len(mac_clean) != 12:
            return False
        
        # Should be valid hex
        try:
            int(mac_clean, 16)
            return True
        except ValueError:
            return False

    def invalidate_result(self, pattern_text: str) -> bool:
        """Check if the pattern is obviously not a valid MAC address."""
        mac = pattern_text.strip().upper()
        mac_clean = mac.replace(':', '').replace('-', '').replace('.', '')
        
        # All zeros or all ones
        if mac_clean in ['000000000000', 'FFFFFFFFFFFF']:
            return True
        
        # Broadcast address
        if mac_clean == 'FFFFFFFFFFFF':
            return True
        
        # All same characters
        if len(set(mac_clean)) == 1:
            return True
        
        return False

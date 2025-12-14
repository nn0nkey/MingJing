"""
China IP Address Recognizer.

Recognizes IP addresses with focus on internal/private IP ranges:
- 10.0.0.0/8 (Class A private)
- 172.16.0.0/12 (Class B private)
- 192.168.0.0/16 (Class C private)
- 127.0.0.0/8 (Loopback)
- IPv6 addresses
"""

from typing import List, Optional

from presidio_analyzer import Pattern, PatternRecognizer


class CnIpAddressRecognizer(PatternRecognizer):
    """
    Recognize IP addresses, especially internal/private IPs.

    Internal IP addresses are often sensitive as they reveal network topology.
    """

    PATTERNS = [
        # Loopback address
        Pattern(
            "IP Loopback",
            r"(?<![0-9])127\.0\.0\.1(?![0-9])",
            0.7,
        ),
        # Class A private: 10.x.x.x
        Pattern(
            "IP Private Class A",
            r"(?<![0-9])10\.(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)(?![0-9])",
            0.7,
        ),
        # Class B private: 172.16-31.x.x
        Pattern(
            "IP Private Class B",
            r"(?<![0-9])172\.(?:1[6-9]|2[0-9]|3[01])\.(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)(?![0-9])",
            0.7,
        ),
        # Class C private: 192.168.x.x
        Pattern(
            "IP Private Class C",
            r"(?<![0-9])192\.168\.(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)(?![0-9])",
            0.7,
        ),
        # Any valid IPv4 address
        Pattern(
            "IPv4 Address",
            r"(?<![0-9])(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)(?![0-9])",
            0.4,
        ),
        # IPv6 address (simplified pattern)
        Pattern(
            "IPv6 Address",
            r"(?<![A-Fa-f0-9:])(?:[A-Fa-f0-9]{1,4}:){7}[A-Fa-f0-9]{1,4}(?![A-Fa-f0-9:])",
            0.5,
        ),
        # IPv6 compressed format
        Pattern(
            "IPv6 Compressed",
            r"(?<![A-Fa-f0-9:])(?:[A-Fa-f0-9]{1,4}:){1,7}:(?![A-Fa-f0-9:])",
            0.4,
        ),
        # IP with port
        Pattern(
            "IP With Port",
            r"(?<![0-9])(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?):(?:[0-9]{1,5})(?![0-9])",
            0.5,
        ),
    ]

    CONTEXT = [
        # 中文 - IP相关
        "IP", "IP地址", "地址", "服务器地址", "主机地址",
        "内网IP", "内网地址", "私有IP", "私网地址",
        "公网IP", "外网IP", "公网地址", "外网地址",
        # 中文 - 网络相关
        "网络", "网段", "子网", "网关", "路由",
        "服务器", "主机", "节点", "集群",
        "数据库", "缓存", "Redis", "MySQL", "MongoDB",
        # 中文 - 配置相关
        "配置", "连接", "访问", "端口", "监听",
        # 英文
        "ip", "ip address", "address", "host", "server",
        "internal ip", "private ip", "public ip", "external ip",
        "network", "subnet", "gateway", "router",
        "database", "cache", "redis", "mysql", "mongodb", "postgresql",
        "connection", "connect", "port", "listen", "bind",
        "localhost", "loopback",
    ]

    def __init__(
        self,
        patterns: Optional[List[Pattern]] = None,
        context: Optional[List[str]] = None,
        supported_language: str = "zh",
        supported_entity: str = "CN_IP_ADDRESS",
    ):
        patterns = patterns if patterns else self.PATTERNS
        context = context if context else self.CONTEXT
        super().__init__(
            supported_entity=supported_entity,
            patterns=patterns,
            context=context,
            supported_language=supported_language,
        )

    def validate_result(self, pattern_text: str) -> Optional[bool]:
        """Validate the detected IP address.
        
        :return:
            - True: 内网IP/回环地址，分数设为1.0
            - False: 明确无效，分数设为0，结果被丢弃
            - None: 不确定（公网IP），保持基础分数，需LLM验证
        """
        ip = pattern_text.split(':')[0]  # Remove port if present
        parts = ip.split('.')
        
        if len(parts) != 4:
            return False  # 不是IPv4格式
        
        try:
            nums = [int(part) for part in parts]
            for num in nums:
                if num < 0 or num > 255:
                    return False  # 数值超出范围
        except ValueError:
            return False  # 包含非数字
        
        # 内网IP - 高置信度
        if nums[0] == 10:  # 10.x.x.x
            return True
        if nums[0] == 172 and 16 <= nums[1] <= 31:  # 172.16-31.x.x
            return True
        if nums[0] == 192 and nums[1] == 168:  # 192.168.x.x
            return True
        if nums[0] == 127:  # 127.x.x.x (loopback)
            return True
        
        # 公网IP - 需要上下文验证，可能是版本号等
        return None

    def invalidate_result(self, pattern_text: str) -> bool:
        """Check if the pattern is obviously not a valid IP."""
        ip = pattern_text.split(':')[0]
        
        # Version numbers like 1.2.3.4
        if ip.count('.') == 3:
            parts = ip.split('.')
            # All zeros except first
            if parts[1:] == ['0', '0', '0']:
                return True
        
        return False

"""
JDBC Connection String Recognizer.

Recognizes JDBC connection strings that may contain sensitive information:
- Database host/IP
- Port
- Database name
- Username/Password (if embedded)
"""

from typing import List, Optional

from presidio_analyzer import Pattern, PatternRecognizer


class CnJdbcRecognizer(PatternRecognizer):
    """
    Recognize JDBC connection strings.

    JDBC URLs contain database connection information which is sensitive.
    Format: jdbc:<subprotocol>://<host>:<port>/<database>?<params>
    """

    PATTERNS = [
        # MySQL JDBC
        Pattern(
            "JDBC MySQL",
            r"jdbc:mysql://[A-Za-z0-9.\-_:;=/@?,&]+",
            0.8,
        ),
        # PostgreSQL JDBC
        Pattern(
            "JDBC PostgreSQL",
            r"jdbc:postgresql://[A-Za-z0-9.\-_:;=/@?,&]+",
            0.8,
        ),
        # Oracle JDBC
        Pattern(
            "JDBC Oracle",
            r"jdbc:oracle:[a-z]+:@[A-Za-z0-9.\-_:;=/@?,&]+",
            0.8,
        ),
        # SQL Server JDBC
        Pattern(
            "JDBC SQLServer",
            r"jdbc:sqlserver://[A-Za-z0-9.\-_:;=/@?,&]+",
            0.8,
        ),
        # MongoDB JDBC
        Pattern(
            "JDBC MongoDB",
            r"mongodb(?:\+srv)?://[A-Za-z0-9.\-_:;=/@?,&]+",
            0.8,
        ),
        # Redis connection
        Pattern(
            "Redis Connection",
            r"redis://[A-Za-z0-9.\-_:;=/@?,&]+",
            0.7,
        ),
        # Generic JDBC
        Pattern(
            "JDBC Generic",
            r"jdbc:[a-z0-9]+://[A-Za-z0-9.\-_:;=/@?,&]+",
            0.6,
        ),
        # Connection string with password
        Pattern(
            "Connection With Password",
            r"(?i)(?:password|pwd|passwd)\s*[=:]\s*['\"]?[A-Za-z0-9!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>\/?]+['\"]?",
            0.7,
        ),
    ]

    CONTEXT = [
        # 中文 - 数据库相关
        "数据库", "数据库连接", "连接字符串", "连接配置",
        "MySQL", "PostgreSQL", "Oracle", "SQLServer", "MongoDB", "Redis",
        "主库", "从库", "读库", "写库", "备库",
        # 中文 - 配置相关
        "配置", "配置文件", "连接池", "数据源",
        "JDBC", "jdbc", "URL", "url", "URI", "uri",
        # 中文 - 认证相关
        "用户名", "密码", "账号", "口令",
        "username", "password", "user", "pass", "pwd",
        # 英文
        "database", "db", "connection", "connection string",
        "datasource", "data source", "connection pool",
        "host", "port", "schema", "catalog",
        "driver", "jdbc driver", "connection url",
    ]

    def __init__(
        self,
        patterns: Optional[List[Pattern]] = None,
        context: Optional[List[str]] = None,
        supported_language: str = "zh",
        supported_entity: str = "CN_JDBC_CONNECTION",
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
        """Validate the detected JDBC connection string."""
        conn = pattern_text.strip().lower()
        
        # Valid JDBC prefixes
        valid_prefixes = [
            'jdbc:mysql', 'jdbc:postgresql', 'jdbc:oracle',
            'jdbc:sqlserver', 'jdbc:mariadb', 'jdbc:h2',
            'jdbc:sqlite', 'jdbc:db2', 'jdbc:derby',
            'mongodb', 'redis',
        ]
        
        for prefix in valid_prefixes:
            if conn.startswith(prefix):
                return True
        
        # Password field pattern
        if 'password' in conn or 'passwd' in conn or 'pwd' in conn:
            return True
        
        return False

    def invalidate_result(self, pattern_text: str) -> bool:
        """Check if the pattern is obviously not a valid JDBC connection."""
        conn = pattern_text.strip()
        
        # Too short
        if len(conn) < 15:
            return True
        
        # Example/placeholder values
        placeholders = ['localhost', 'example.com', 'xxx', 'your-']
        for placeholder in placeholders:
            if placeholder in conn.lower():
                # Still valid but might be example
                pass
        
        return False

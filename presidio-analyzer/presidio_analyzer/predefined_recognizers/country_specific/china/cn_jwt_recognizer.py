"""
JWT (JSON Web Token) Recognizer.

Recognizes JWT tokens in the format: header.payload.signature
Each part is Base64URL encoded.
"""

import base64
import json
from typing import List, Optional

from presidio_analyzer import Pattern, PatternRecognizer


class CnJwtRecognizer(PatternRecognizer):
    """
    Recognize JSON Web Tokens (JWT).

    JWT format: xxxxx.yyyyy.zzzzz
    - Header: Base64URL encoded JSON with alg and typ
    - Payload: Base64URL encoded JSON with claims
    - Signature: Base64URL encoded signature
    """

    PATTERNS = [
        # Standard JWT: eyJ (base64 of {"...) followed by two more parts
        Pattern(
            "JWT Standard",
            r"(?<![A-Za-z0-9_-])eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}(?![A-Za-z0-9_-])",
            0.85,
        ),
        # JWT without signature (unsecured JWT)
        Pattern(
            "JWT Unsecured",
            r"(?<![A-Za-z0-9_-])eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.(?![A-Za-z0-9_-])",
            0.7,
        ),
        # JWT with URL-safe base64 (+ and / replaced with - and _)
        Pattern(
            "JWT URL Safe",
            r"(?<![A-Za-z0-9_\-/+])eyJ[A-Za-z0-9_\-/+]{10,}\.[A-Za-z0-9_\-/+.]{10,}(?![A-Za-z0-9_\-/+])",
            0.6,
        ),
    ]

    CONTEXT = [
        # 中文 - Token相关
        "令牌", "访问令牌", "刷新令牌", "认证令牌", "授权令牌",
        "Token", "token", "JWT", "jwt",
        # 中文 - 认证相关
        "认证", "授权", "鉴权", "身份验证", "登录凭证",
        "会话", "Session", "session",
        # 中文 - 请求相关
        "请求头", "响应头", "Header", "header",
        "Authorization", "Bearer",
        # 英文
        "json web token", "access token", "refresh token",
        "id token", "auth token", "bearer token",
        "authentication", "authorization", "oauth",
        "login", "session", "credential",
    ]

    def __init__(
        self,
        patterns: Optional[List[Pattern]] = None,
        context: Optional[List[str]] = None,
        supported_language: str = "zh",
        supported_entity: str = "CN_JWT",
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
        """Validate the detected JWT by checking if header is valid JSON."""
        token = pattern_text.strip()
        parts = token.split('.')
        
        if len(parts) < 2:
            return False
        
        try:
            # Try to decode and parse the header
            header = parts[0]
            # Add padding if needed
            padding = 4 - len(header) % 4
            if padding != 4:
                header += '=' * padding
            # Replace URL-safe characters
            header = header.replace('-', '+').replace('_', '/')
            decoded = base64.b64decode(header)
            header_json = json.loads(decoded)
            
            # Check for typical JWT header fields
            if 'alg' in header_json or 'typ' in header_json:
                return True
            
        except Exception:
            pass
        
        # Even if we can't decode, if it starts with eyJ it's likely a JWT
        if token.startswith('eyJ'):
            return True
        
        return False

    def invalidate_result(self, pattern_text: str) -> bool:
        """Check if the pattern is obviously not a valid JWT."""
        token = pattern_text.strip()
        
        # Too short
        if len(token) < 30:
            return True
        
        # Must start with eyJ (base64 of '{"')
        if not token.startswith('eyJ'):
            return True
        
        return False

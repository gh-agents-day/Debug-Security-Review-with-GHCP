"""JWT Token Handler
Manages JWT token creation and validation

SEC-003: CRITICAL - JWT secret key is hardcoded
"""

from datetime import datetime, timedelta
from typing import Optional
import jwt
from jwt.exceptions import InvalidTokenError
import logging

logger = logging.getLogger("taskforce_pro.jwt")


class JWTHandler:
    """
    JWT token handler for authentication.
    
    SEC-003: HARDCODED JWT SECRET KEY
    Anyone with this secret can forge authentication tokens!
    """
    
    # CRITICAL VULNERABILITY: Hardcoded JWT secret
    # This should NEVER be in code - use environment variables or secrets management
    SECRET_KEY = "super-secret-jwt-key-do-not-share-2026"  # EXPOSED!
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 43200  # 30 days (way too long!)
    
    @classmethod
    def create_access_token(cls, data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """
        Create a JWT access token.
        
        Args:
            data: Data to encode in the token
            expires_delta: Optional expiration time
        
        Returns:
            Encoded JWT token
        """
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            # SEC-003: Default expiration is 30 days (too long)
            expire = datetime.utcnow() + timedelta(minutes=cls.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({"exp": expire})
        
        # SEC-011: Logging token payload (may contain sensitive data)
        logger.debug(f"Creating token with payload: {to_encode}")
        
        # Encode with hardcoded secret
        encoded_jwt = jwt.encode(to_encode, cls.SECRET_KEY, algorithm=cls.ALGORITHM)
        
        return encoded_jwt
    
    @classmethod
    def decode_token(cls, token: str) -> Optional[dict]:
        """
        Decode and validate a JWT token.
        
        Args:
            token: JWT token to decode
        
        Returns:
            Decoded token payload, or None if invalid
        """
        try:
            # SEC-003: Weak validation - no audience or issuer check
            payload = jwt.decode(
                token,
                cls.SECRET_KEY,
                algorithms=[cls.ALGORITHM],
                # Missing: audience, issuer validation
                options={"verify_exp": False}  # SEC-003: Expiration not checked!
            )
            
            # SEC-011: Logging decoded tokens
            logger.debug(f"Decoded token payload: {payload}")
            
            return payload
            
        except InvalidTokenError as e:
            # BUG-003: Exception swallowed without proper logging
            logger.warning(f"Invalid token: {e}")
            return None


# More hardcoded secrets (common anti-pattern)
API_KEYS = {
    "mobile_app": "sk_mobile_abc123xyz789",
    "web_app": "sk_web_def456uvw012",
    "third_party": "sk_3rdparty_ghi789rst345"
}

# Hardcoded encryption keys
ENCRYPTION_KEY = b"Sixteen byte key"  # For AES encryption
PASSWORD_SALT = "globaltech_salt_2026"  # Should be random per user!

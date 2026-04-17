"""Authentication and Authorization"""
import logging
from fastapi import HTTPException, Security, Request
from fastapi.responses import JSONResponse
from fastapi.security import APIKeyHeader
from functools import lru_cache
import hashlib
import hmac
import json
import time
from datetime import datetime, timedelta, timezone
import jwt
from typing import Optional

logger = logging.getLogger(__name__)

# API Key header
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(api_key: Optional[str] = Security(api_key_header), configured_key: str = None) -> bool:
    """
    Verify API key from header

    Returns:
        True if valid

    Raises:
        HTTPException 401 if missing or invalid
    """
    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="Missing API Key — include header X-API-Key",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    if api_key != configured_key:
        logger.warning("Invalid API key attempt")
        raise HTTPException(
            status_code=401,
            detail="Invalid API Key",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    logger.debug("API Key verified")
    return True


def create_jwt_token(
    user_id: str,
    secret: str,
    expires_minutes: int = 60
) -> str:
    """
    Create JWT token
    
    Args:
        user_id: User identifier
        secret: JWT secret key
        expires_minutes: Token expiration time
        
    Returns:
        JWT token string
    """
    try:
        payload = {
            "user_id": user_id,
            "exp": datetime.now(timezone.utc) + timedelta(minutes=expires_minutes),
            "iat": datetime.now(timezone.utc),
        }
        
        token = jwt.encode(payload, secret, algorithm="HS256")
        logger.info(f"✅ JWT token created for user: {user_id}")
        return token
    
    except Exception as e:
        logger.error(f"Error creating JWT: {e}")
        raise


def verify_jwt_token(token: str, secret: str) -> dict:
    """
    Verify and decode JWT token
    
    Args:
        token: JWT token
        secret: JWT secret key
        
    Returns:
        Decoded payload
        
    Raises:
        HTTPException if invalid
    """
    try:
        payload = jwt.decode(token, secret, algorithms=["HS256"])
        logger.debug(f"✅ JWT verified for user: {payload.get('user_id')}")
        return payload
    
    except jwt.ExpiredSignatureError:
        logger.warning("❌ JWT token expired")
        raise HTTPException(status_code=401, detail="Token expired")
    
    except jwt.InvalidTokenError:
        logger.warning("❌ Invalid JWT token")
        raise HTTPException(status_code=401, detail="Invalid token")


def hash_password(password: str, salt: Optional[str] = None) -> str:
    """
    Hash password using SHA-256
    
    Args:
        password: Plain password
        salt: Optional salt
        
    Returns:
        Hashed password
    """
    if salt is None:
        salt = hashlib.sha256().hexdigest()[:16]
    
    hashed = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        100000
    )
    
    return f"{salt}${hashed.hex()}"


def verify_password(password: str, hashed: str) -> bool:
    """
    Verify password against hash
    
    Args:
        password: Plain password
        hashed: Hashed password
        
    Returns:
        True if matches
    """
    try:
        salt, _ = hashed.split('$')
        return hash_password(password, salt) == hashed
    except Exception as e:
        logger.error(f"Error verifying password: {e}")
        return False


def sign_webhook(payload: dict, secret: str) -> str:
    """
    Sign webhook payload
    
    Args:
        payload: Payload to sign
        secret: Secret key
        
    Returns:
        HMAC signature
    """
    message = json.dumps(payload, sort_keys=True)
    signature = hmac.new(
        secret.encode(),
        message.encode(),
        hashlib.sha256
    ).hexdigest()
    return signature


def verify_webhook_signature(payload: dict, signature: str, secret: str) -> bool:
    """
    Verify webhook signature
    
    Args:
        payload: Payload
        signature: Provided signature
        secret: Secret key
        
    Returns:
        True if valid
    """
    expected = sign_webhook(payload, secret)
    return hmac.compare_digest(signature, expected)

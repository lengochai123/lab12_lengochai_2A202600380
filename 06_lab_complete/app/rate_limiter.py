"""Rate Limiting — Protect API from abuse"""
import logging
import time
from typing import Optional
from collections import defaultdict, deque
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)


class RateLimiter:
    """In-memory rate limiter (use Redis for distributed)"""
    
    def __init__(self, requests_per_minute: int = 30):
        """
        Args:
            requests_per_minute: Max requests per minute per user
        """
        self.requests_per_minute = requests_per_minute
        self.window = 60  # seconds
        self.users = defaultdict(deque)  # {user_id: deque of timestamps}
    
    def is_allowed(self, user_id: str) -> bool:
        """
        Check if user has exceeded rate limit
        
        Args:
            user_id: User identifier (API key, IP, etc.)
            
        Returns:
            True if request is allowed
        """
        now = time.time()
        requests = self.users[user_id]
        
        # Remove old requests outside window
        while requests and requests[0] < now - self.window:
            requests.popleft()
        
        # Check limit
        if len(requests) < self.requests_per_minute:
            requests.append(now)
            logger.debug(f"✅ Request allowed for {user_id} ({len(requests)}/{self.requests_per_minute})")
            return True
        else:
            logger.warning(f"❌ Rate limit exceeded for {user_id}")
            return False
    
    def get_remaining(self, user_id: str) -> int:
        """Get remaining requests in current window"""
        now = time.time()
        requests = self.users[user_id]
        
        # Remove old requests
        while requests and requests[0] < now - self.window:
            requests.popleft()
        
        return max(0, self.requests_per_minute - len(requests))
    
    def get_reset_time(self, user_id: str) -> int:
        """Get Unix timestamp when rate limit resets"""
        requests = self.users.get(user_id, deque())
        
        if not requests:
            return int(time.time())
        
        oldest = requests[0]
        reset = int(oldest + self.window)
        return reset


class RedisRateLimiter:
    """Redis-based rate limiter for distributed systems"""
    
    def __init__(self, redis_client, requests_per_minute: int = 30):
        """
        Args:
            redis_client: Redis client instance
            requests_per_minute: Max requests per minute per user
        """
        self.redis = redis_client
        self.requests_per_minute = requests_per_minute
        self.window = 60  # seconds
    
    def is_allowed(self, user_id: str) -> bool:
        """
        Check if user has exceeded rate limit using Redis
        
        Args:
            user_id: User identifier
            
        Returns:
            True if request is allowed
        """
        try:
            key = f"rate_limit:{user_id}"
            current = self.redis.incr(key)
            
            # Set expiration on first request
            if current == 1:
                self.redis.expire(key, self.window)
            
            if current <= self.requests_per_minute:
                logger.debug(f"✅ Request allowed for {user_id} ({current}/{self.requests_per_minute})")
                return True
            else:
                logger.warning(f"❌ Rate limit exceeded for {user_id}")
                return False
        
        except Exception as e:
            logger.error(f"Error checking rate limit: {e}")
            # Fail open in case of Redis error
            return True
    
    def get_remaining(self, user_id: str) -> int:
        """Get remaining requests in current window"""
        try:
            key = f"rate_limit:{user_id}"
            current = int(self.redis.get(key) or 0)
            return max(0, self.requests_per_minute - current)
        except Exception as e:
            logger.error(f"Error getting remaining: {e}")
            return self.requests_per_minute
    
    def get_reset_time(self, user_id: str) -> int:
        """Get Unix timestamp when rate limit resets"""
        try:
            key = f"rate_limit:{user_id}"
            ttl = self.redis.ttl(key)
            
            if ttl <= 0:
                return int(time.time())
            
            return int(time.time()) + ttl
        except Exception as e:
            logger.error(f"Error getting reset time: {e}")
            return int(time.time())


# Middleware for FastAPI
async def rate_limit_middleware(request, call_next, limiter: RateLimiter, api_key: str):
    """
    Rate limiting middleware for FastAPI
    
    Usage in main.py:
    ```
    @app.middleware("http")
    async def rate_limit_middleware(request, call_next):
        await rate_limit_middleware(request, call_next, limiter, request.headers.get("X-API-Key", "unknown"))
    ```
    """
    if not limiter.is_allowed(api_key):
        from fastapi import HTTPException
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded ({limiter.requests_per_minute} requests/min)",
            headers={
                "X-RateLimit-Limit": str(limiter.requests_per_minute),
                "X-RateLimit-Remaining": str(limiter.get_remaining(api_key)),
                "X-RateLimit-Reset": str(limiter.get_reset_time(api_key)),
            }
        )
    
    response = await call_next(request)
    response.headers["X-RateLimit-Limit"] = str(limiter.requests_per_minute)
    response.headers["X-RateLimit-Remaining"] = str(limiter.get_remaining(api_key))
    response.headers["X-RateLimit-Reset"] = str(limiter.get_reset_time(api_key))
    
    return response

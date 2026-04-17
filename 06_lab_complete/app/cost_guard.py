"""Cost Guard — LLM Budget Protection"""
import logging
import time
import json
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict
import hashlib

logger = logging.getLogger(__name__)


class CostGuard:
    """Track LLM costs and enforce budget limits"""
    
    # OpenAI pricing per 1K tokens (as of 2024)
    PRICING = {
        "gpt-4-vision": {
            "input_tokens": 0.01,      # $0.01 per 1K input tokens
            "output_tokens": 0.03,     # $0.03 per 1K output tokens
        },
        "gpt-4-turbo-vision": {
            "input_tokens": 0.01,
            "output_tokens": 0.03,
        },
        "gpt-4o": {
            "input_tokens": 0.005,
            "output_tokens": 0.015,
        },
    }
    
    def __init__(self, monthly_budget_usd: float = 50.0, redis_client=None):
        """
        Args:
            monthly_budget_usd: Monthly budget in USD
            redis_client: Optional Redis client for distributed tracking
        """
        self.monthly_budget = monthly_budget_usd
        self.redis = redis_client
        self.in_memory_costs = {}  # Fallback if no Redis
    
    def record_usage(
        self,
        model: str,
        input_tokens: int,
        output_tokens: int,
        user_id: str = "default"
    ) -> Dict[str, float]:
        """
        Record LLM usage and calculate cost
        
        Args:
            model: Model name
            input_tokens: Input tokens used
            output_tokens: Output tokens generated
            user_id: User identifier for cost tracking
            
        Returns:
            {
                "input_cost": cost of input,
                "output_cost": cost of output,
                "total_cost": total cost,
                "monthly_spent": total monthly spending,
                "remaining_budget": budget left,
                "percent_used": percentage of budget used,
            }
        """
        try:
            # Get pricing
            pricing = self.PRICING.get(model, self.PRICING["gpt-4o"])
            
            # Calculate costs
            input_cost = (input_tokens / 1000) * pricing["input_tokens"]
            output_cost = (output_tokens / 1000) * pricing["output_tokens"]
            total_cost = input_cost + output_cost
            
            # Store usage
            monthly_spent = self._add_cost(user_id, total_cost)
            remaining_budget = max(0, self.monthly_budget - monthly_spent)
            percent_used = (monthly_spent / self.monthly_budget * 100) if self.monthly_budget > 0 else 0
            
            result = {
                "input_cost": round(input_cost, 6),
                "output_cost": round(output_cost, 6),
                "total_cost": round(total_cost, 6),
                "monthly_spent": round(monthly_spent, 2),
                "remaining_budget": round(remaining_budget, 2),
                "percent_used": round(percent_used, 2),
                "user_id": user_id,
            }
            
            logger.info(f"💰 Cost tracked: ${total_cost:.6f} (Monthly: ${monthly_spent:.2f}/{self.monthly_budget})")
            
            # Check if approaching budget limit
            if percent_used > 80:
                logger.warning(f"⚠️ Budget warning: {percent_used:.1f}% used!")
            if monthly_spent >= self.monthly_budget:
                logger.error(f"❌ BUDGET EXCEEDED! ${monthly_spent:.2f} / ${self.monthly_budget}")
            
            return result
        
        except Exception as e:
            logger.error(f"Error recording usage: {e}")
            return {
                "error": str(e),
                "input_cost": 0,
                "output_cost": 0,
                "total_cost": 0,
            }
    
    def is_budget_available(self, user_id: str = "default", required_cost: float = 0.01) -> bool:
        """
        Check if budget is available before making API call
        
        Args:
            user_id: User identifier
            required_cost: Estimated cost of the operation
            
        Returns:
            True if budget available
        """
        try:
            monthly_spent = self._get_monthly_spent(user_id)
            remaining = self.monthly_budget - monthly_spent
            
            if remaining < required_cost:
                logger.error(f"❌ Insufficient budget for {user_id}: ${remaining:.2f} < ${required_cost:.2f}")
                return False
            
            logger.debug(f"✅ Budget available: ${remaining:.2f}")
            return True
        
        except Exception as e:
            logger.error(f"Error checking budget: {e}")
            return True  # Fail open
    
    def get_monthly_limit_info(self, user_id: str = "default") -> Dict:
        """Get monthly budget info for user"""
        try:
            monthly_spent = self._get_monthly_spent(user_id)
            remaining = max(0, self.monthly_budget - monthly_spent)
            percent_used = (monthly_spent / self.monthly_budget * 100) if self.monthly_budget > 0 else 0
            
            # Calculate reset date (first of next month)
            now = datetime.now(timezone.utc)
            if now.month == 12:
                reset_date = datetime(now.year + 1, 1, 1, tzinfo=timezone.utc)
            else:
                reset_date = datetime(now.year, now.month + 1, 1, tzinfo=timezone.utc)
            
            return {
                "monthly_budget": self.monthly_budget,
                "monthly_spent": round(monthly_spent, 2),
                "remaining_budget": round(remaining, 2),
                "percent_used": round(percent_used, 2),
                "reset_date": reset_date.isoformat(),
                "user_id": user_id,
            }
        
        except Exception as e:
            logger.error(f"Error getting limit info: {e}")
            return {"error": str(e)}
    
    def _add_cost(self, user_id: str, cost: float) -> float:
        """Add cost and return monthly total"""
        if self.redis:
            return self._redis_add_cost(user_id, cost)
        else:
            return self._memory_add_cost(user_id, cost)
    
    def _get_monthly_spent(self, user_id: str) -> float:
        """Get monthly total spent"""
        if self.redis:
            return self._redis_get_monthly_spent(user_id)
        else:
            return self._memory_get_monthly_spent(user_id)
    
    def _memory_add_cost(self, user_id: str, cost: float) -> float:
        """Add cost using in-memory storage"""
        key = self._get_month_key(user_id)
        self.in_memory_costs[key] = self.in_memory_costs.get(key, 0) + cost
        return self.in_memory_costs[key]
    
    def _memory_get_monthly_spent(self, user_id: str) -> float:
        """Get monthly total from memory"""
        key = self._get_month_key(user_id)
        return self.in_memory_costs.get(key, 0)
    
    def _redis_add_cost(self, user_id: str, cost: float) -> float:
        """Add cost using Redis"""
        try:
            key = f"cost:{self._get_month_key(user_id)}"
            # Use Redis INCRBYFLOAT but convert to int (Redis limitation)
            # Store in cents to avoid float precision issues
            cents = int(cost * 100)
            self.redis.incrby(key, cents)
            self.redis.expire(key, 86400 * 35)  # Reset after month
            return float(self.redis.get(key) or 0) / 100
        except Exception as e:
            logger.error(f"Redis cost error: {e}")
            return 0
    
    def _redis_get_monthly_spent(self, user_id: str) -> float:
        """Get monthly total from Redis"""
        try:
            key = f"cost:{self._get_month_key(user_id)}"
            value = self.redis.get(key)
            return float(value or 0) / 100
        except Exception as e:
            logger.error(f"Redis get cost error: {e}")
            return 0
    
    @staticmethod
    def _get_month_key(user_id: str) -> str:
        """Get consistent month key for storage"""
        now = datetime.now(timezone.utc)
        year_month = now.strftime("%Y-%m")
        return f"{user_id}:{year_month}"

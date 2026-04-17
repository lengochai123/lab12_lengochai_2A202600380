"""Fire Detection Production Config — 12-Factor: tất cả từ environment variables."""
import os
import logging
from dataclasses import dataclass, field


@dataclass
class Settings:
    # ──── Server ────
    host: str = field(default_factory=lambda: os.getenv("HOST", "0.0.0.0"))
    port: int = field(default_factory=lambda: int(os.getenv("PORT", "8000")))
    environment: str = field(default_factory=lambda: os.getenv("ENVIRONMENT", "development"))
    debug: bool = field(default_factory=lambda: os.getenv("DEBUG", "false").lower() == "true")

    # ──── App Info ────
    app_name: str = field(default_factory=lambda: os.getenv("APP_NAME", "Fire Detection LLM Agent"))
    app_version: str = field(default_factory=lambda: os.getenv("APP_VERSION", "1.0.0"))

    # ──── LLM (OpenAI) ────
    openai_api_key: str = field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    llm_model: str = field(default_factory=lambda: os.getenv("LLM_MODEL", "gpt-4-vision"))
    llm_max_tokens: int = field(default_factory=lambda: int(os.getenv("LLM_MAX_TOKENS", "200")))

    # ──── Fire Detection (YOLO) ────
    yolo_model_name: str = field(default_factory=lambda: os.getenv("YOLO_MODEL_NAME", "yolov8m.pt"))
    yolo_confidence_threshold: float = field(
        default_factory=lambda: float(os.getenv("YOLO_CONFIDENCE_THRESHOLD", "0.5"))
    )
    yolo_nms_threshold: float = field(
        default_factory=lambda: float(os.getenv("YOLO_NMS_THRESHOLD", "0.45"))
    )

    # ──── Firebase (Sensor Data) ────
    firebase_db_url: str = field(default_factory=lambda: os.getenv("FIREBASE_DB_URL", ""))
    firebase_key_path: str = field(default_factory=lambda: os.getenv("FIREBASE_KEY_PATH", ""))

    # ──── Security ────
    agent_api_key: str = field(default_factory=lambda: os.getenv("AGENT_API_KEY", "dev-key-change-me"))
    jwt_secret: str = field(default_factory=lambda: os.getenv("JWT_SECRET", "dev-jwt-secret"))
    allowed_origins: list = field(
        default_factory=lambda: os.getenv("ALLOWED_ORIGINS", "*").split(",")
    )

    # ──── Rate Limiting ────
    rate_limit_per_minute: int = field(
        default_factory=lambda: int(os.getenv("RATE_LIMIT_PER_MINUTE", "30"))
    )

    # ──── Cost Guard (LLM Budget) ────
    monthly_budget_usd: float = field(
        default_factory=lambda: float(os.getenv("MONTHLY_BUDGET_USD", "50.0"))
    )
    alert_budget_percent: float = field(
        default_factory=lambda: float(os.getenv("ALERT_BUDGET_PERCENT", "0.8"))
    )

    # ──── Storage (Redis) ────
    redis_url: str = field(default_factory=lambda: os.getenv("REDIS_URL", "redis://localhost:6379"))
    redis_ttl: int = field(default_factory=lambda: int(os.getenv("REDIS_TTL", "86400")))

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    def validate(self):
        logger = logging.getLogger(__name__)
        if self.environment == "production":
            if self.agent_api_key == "dev-key-change-me":
                raise ValueError("❌ AGENT_API_KEY must be set in production!")
            if self.jwt_secret == "dev-jwt-secret":
                raise ValueError("❌ JWT_SECRET must be set in production!")
            if not self.openai_api_key:
                raise ValueError("❌ OPENAI_API_KEY required in production!")
        else:
            if not self.openai_api_key:
                logger.warning("⚠️ OPENAI_API_KEY not set — using mock LLM")
        return self


settings = Settings().validate()

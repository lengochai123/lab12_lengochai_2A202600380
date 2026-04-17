"""
Fire Detection Production API — Production-ready fire detection with LLM analysis

Checklist:
  ✅ Config từ environment (12-factor)
  ✅ Structured JSON logging
  ✅ API Key authentication
  ✅ Rate limiting
  ✅ Cost guard (LLM budget)
  ✅ Input validation (Pydantic)
  ✅ Health check + Readiness probe
  ✅ Graceful shutdown
  ✅ Security headers
  ✅ CORS
  ✅ Error handling
  ✅ Fire detection with YOLO
  ✅ LLM analysis
  ✅ Multi-stage production build
  ✅ Python 3.13 compatible
"""
import os
import time
import signal
import logging
import json
import base64
from datetime import datetime, timezone
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, Security, Depends, Request, Response, UploadFile, File
from fastapi.security.api_key import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn
import numpy as np

from app.config import settings
from app.auth import verify_api_key, api_key_header
from app.rate_limiter import RateLimiter
from app.cost_guard import CostGuard
from app.fire_detector import FireDetector
from app.llm_analyzer import LLMAnalyzer


# ─────────────────────────────────────────────────────────
# Logging — JSON structured
# ─────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format='{"ts":"%(asctime)s","lvl":"%(levelname)s","msg":"%(message)s"}',
)
logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────
# Global State
# ─────────────────────────────────────────────────────────
START_TIME = time.time()
_is_ready = False
_request_count = 0
_error_count = 0

# Services
rate_limiter: Optional[RateLimiter] = None
cost_guard: Optional[CostGuard] = None
fire_detector: Optional[FireDetector] = None
llm_analyzer: Optional[LLMAnalyzer] = None

# ─────────────────────────────────────────────────────────
# Lifespan
# ─────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    global _is_ready, rate_limiter, cost_guard, fire_detector, llm_analyzer, alert_manager
    
    logger.info(json.dumps({
        "event": "startup",
        "app": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
    }))
    
    try:
        # Initialize services
        rate_limiter = RateLimiter(requests_per_minute=settings.rate_limit_per_minute)
        cost_guard = CostGuard(monthly_budget_usd=settings.monthly_budget_usd)
        
        # Load YOLO model
        logger.info("Loading YOLO model...")
        model_path = settings.yolo_model_name
        if not Path(model_path).exists():
            logger.warning(f"Model {model_path} not found, downloading...")
        fire_detector = FireDetector(
            model_path=model_path,
            conf_threshold=settings.yolo_confidence_threshold
        )
        
        # Initialize LLM analyzer
        llm_analyzer = LLMAnalyzer(
            api_key=settings.openai_api_key if settings.openai_api_key else None,
            model=settings.llm_model
        )
        
        _is_ready = True
        logger.info(json.dumps({"event": "ready", "services": "all_initialized"}))
    
    except Exception as e:
        logger.error(f"Startup error: {e}")
        raise
    
    yield
    
    _is_ready = False
    logger.info(json.dumps({"event": "shutdown"}))

# ─────────────────────────────────────────────────────────
# FastAPI App
# ─────────────────────────────────────────────────────────
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="🔥 Production Fire Detection with LLM Analysis and Telegram Alerts",
    lifespan=lifespan,
    docs_url="/docs" if not settings.is_production else None,
    redoc_url=None,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type", "X-API-Key"],
)

@app.middleware("http")
async def request_middleware(request: Request, call_next):
    """Request logging and security headers"""
    global _request_count, _error_count
    start = time.time()
    _request_count += 1
    
    try:
        # Check rate limit only on requests that carry an API key
        api_key = request.headers.get("X-API-Key")
        if api_key and api_key == settings.agent_api_key and rate_limiter:
            if not rate_limiter.is_allowed(api_key[:8]):
                raise HTTPException(
                    status_code=429,
                    detail=f"Rate limit exceeded ({settings.rate_limit_per_minute} req/min)"
                )
        
        response: Response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        try:
            del response.headers["server"]
        except KeyError:
            pass
        
        duration = round((time.time() - start) * 1000, 1)
        if response.status_code >= 400:
            logger.warning(json.dumps({
                "event": "request",
                "method": request.method,
                "path": request.url.path,
                "status": response.status_code,
                "ms": duration,
            }))
        else:
            logger.info(json.dumps({
                "event": "request",
                "method": request.method,
                "path": request.url.path,
                "status": response.status_code,
                "ms": duration,
            }))
        
        return response
    
    except HTTPException:
        _error_count += 1
        raise
    except Exception as e:
        _error_count += 1
        logger.error(f"Middleware error: {e}")
        raise

# ─────────────────────────────────────────────────────────
# Request/Response Models
# ─────────────────────────────────────────────────────────
class FireAnalysisRequest(BaseModel):
    """Fire detection analysis request"""
    image_base64: str = Field(..., description="Base64 encoded image")
    user_id: str = Field(default="default", description="User identifier for cost tracking")

class DetectionInfo(BaseModel):
    """Detection information"""
    fire_detected: bool
    total_detections: int
    confidence_scores: list[float]

class FireAnalysisResponse(BaseModel):
    """Fire analysis response"""
    fire_detected: bool
    detections: dict
    llm_analysis: str
    cost_info: dict
    timestamp: str

class BudgetInfo(BaseModel):
    """Budget information"""
    monthly_budget: float
    monthly_spent: float
    remaining_budget: float
    percent_used: float
    reset_date: str

class AskRequest(BaseModel):
    """Text Q&A request — used by the /ask endpoint"""
    user_id: str = Field(default="default", description="User identifier")
    question: str = Field(..., description="Question to ask the AI agent")

class AskResponse(BaseModel):
    """Text Q&A response"""
    answer: str
    user_id: str
    cost_info: dict
    timestamp: str

# ─────────────────────────────────────────────────────────
# Endpoints → Info
# ─────────────────────────────────────────────────────────

@app.get("/", tags=["Info"])
def root():
    """API root information"""
    return {
        "app": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "endpoints": {
            "ask": "POST /ask (requires X-API-Key, text Q&A)",
            "analyze": "POST /analyze (requires X-API-Key, base64 image)",
            "health": "GET /health (no auth)",
            "ready": "GET /ready (no auth)",
            "budget": "GET /budget (requires X-API-Key)",
            "metrics": "GET /metrics (requires X-API-Key)",
        },
    }

# ─────────────────────────────────────────────────────────
# Endpoints → Ask (Text Q&A)
# ─────────────────────────────────────────────────────────

@app.post("/ask", response_model=AskResponse, tags=["Agent"])
async def ask(
    body: AskRequest,
    api_key: str = Depends(verify_api_key),
):
    """
    Ask the AI agent a text question.

    **Authentication:** Include header `X-API-Key: <your-key>`

    **Request body:**
    - user_id: Optional user identifier
    - question: The question to ask

    **Returns:**
    - answer: AI-generated answer
    - cost_info: Cost tracking information
    """
    try:
        if not llm_analyzer:
            raise HTTPException(500, "LLM service not ready. Try again.")

        logger.info(json.dumps({"event": "ask", "user_id": body.user_id, "q_len": len(body.question)}))

        # Use LLM to answer — fall back to mock if no API key
        if settings.openai_api_key:
            from openai import OpenAI
            client = OpenAI(api_key=settings.openai_api_key)
            completion = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful fire-safety AI assistant."},
                    {"role": "user", "content": body.question},
                ],
                max_tokens=settings.llm_max_tokens,
            )
            answer = completion.choices[0].message.content.strip()
            in_tok = completion.usage.prompt_tokens
            out_tok = completion.usage.completion_tokens
        else:
            # Mock response (no API key set)
            answer = f"[Mock] Received question: '{body.question}'. Set OPENAI_API_KEY for real answers."
            in_tok, out_tok = 10, 20

        # Cost tracking
        cost_info = cost_guard.record_usage(
            model="gpt-3.5-turbo",
            input_tokens=in_tok,
            output_tokens=out_tok,
            user_id=body.user_id,
        ) if cost_guard else {"status": "cost_guard_disabled"}

        return AskResponse(
            answer=answer,
            user_id=body.user_id,
            cost_info=cost_info,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in /ask: {e}", exc_info=True)
        raise HTTPException(500, f"Ask failed: {str(e)}")

# ─────────────────────────────────────────────────────────
# Endpoints → Fire Detection
# ─────────────────────────────────────────────────────────

@app.post("/analyze", response_model=FireAnalysisResponse, tags=["Fire Detection"])
async def analyze_fire(
    body: FireAnalysisRequest,
    request: Request,
    api_key: str = Depends(verify_api_key),
):
    """
    Analyze image for fire detection and get LLM-powered analysis.
    
    **Authentication:** Include header `X-API-Key: <your-key>`
    
    **Request body:**
    - image_base64: Base64 encoded image (JPEG or PNG)
    - user_id: Optional user identifier for cost tracking
    
    **Returns:**
    - fire_detected: Boolean indicating if fire was detected
    - detections: Detailed detection information
    - llm_analysis: Intelligent analysis from LLM
    - cost_info: Cost tracking information
    """
    try:
        if not fire_detector or not llm_analyzer:
            raise HTTPException(500, "Services not ready. Try again.")
        
        user_id = body.user_id
        
        # Decode image
        try:
            image_data = base64.b64decode(body.image_base64)
        except Exception as e:
            logger.error(f"Failed to decode base64: {e}")
            raise HTTPException(400, f"Invalid base64 image: {str(e)}")
        
        # ──── Fire Detection ────
        logger.info(f"Analyzing image ({len(image_data)} bytes) for user: {user_id}")
        fire_detected, detections, annotated_frame = fire_detector.detect_from_image_data(image_data)
        
        if "error" in detections:
            logger.error(f"Detection error: {detections['error']}")
            raise HTTPException(400, f"Detection failed: {detections['error']}")
        
        # ──── LLM Analysis ────
        logger.info(f"Running LLM analysis...")
        llm_response = llm_analyzer.analyze_frame(
            np.frombuffer(image_data, np.uint8),
            detections,
            max_tokens=settings.llm_max_tokens
        )
        
        # ──── Cost Tracking ────
        cost_info = cost_guard.record_usage(
            model=settings.llm_model,
            input_tokens=len(llm_response.split()) * 2,
            output_tokens=len(llm_response.split()) * 2,
            user_id=user_id,
        ) if cost_guard else {"status": "cost_guard_disabled"}
        
        return FireAnalysisResponse(
            fire_detected=fire_detected,
            detections=detections,
            llm_analysis=llm_response,
            cost_info=cost_info,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in analyze_fire: {e}", exc_info=True)
        raise HTTPException(500, f"Analysis failed: {str(e)}")

# ─────────────────────────────────────────────────────────
# Endpoints → Operations
# ─────────────────────────────────────────────────────────

@app.get("/health", tags=["Operations"])
def health():
    """
    Liveness probe.
    Platform restarts container if this fails.
    """
    status = "ok"
    checks = {
        "llm": "openai" if settings.openai_api_key else "mock",
        "fire_detector": "loaded" if fire_detector else "not_loaded",
    }
    return {
        "status": status,
        "version": settings.app_version,
        "environment": settings.environment,
        "uptime_seconds": round(time.time() - START_TIME, 1),
        "total_requests": _request_count,
        "checks": checks,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

@app.get("/ready", tags=["Operations"])
def ready():
    """
    Readiness probe.
    Load balancer stops routing if not ready.
    """
    if not _is_ready:
        raise HTTPException(503, "Not ready")
    if not fire_detector or not llm_analyzer:
        raise HTTPException(503, "Services initializing")
    return {"ready": True, "timestamp": datetime.now(timezone.utc).isoformat()}

@app.get("/metrics", tags=["Operations"])
def metrics(_api_key: str = Depends(verify_api_key)):
    """
    Basic metrics (protected).
    Requires valid API key.
    """
    return {
        "uptime_seconds": round(time.time() - START_TIME, 1),
        "total_requests": _request_count,
        "error_count": _error_count,
        "environment": settings.environment,
        "version": settings.app_version,
    }

@app.get("/budget", response_model=BudgetInfo, tags=["Operations"])
def budget_info(
    user_id: str = "default",
    _api_key: str = Depends(verify_api_key)
):
    """
    Get budget information for cost tracking.
    Requires valid API key.
    """
    if not cost_guard:
        raise HTTPException(503, "Cost guard not initialized")
    
    info = cost_guard.get_monthly_limit_info(user_id)
    if "error" in info:
        raise HTTPException(500, info.get("error"))
    
    return BudgetInfo(**info)

# ─────────────────────────────────────────────────────────
# Graceful Shutdown
# ─────────────────────────────────────────────────────────
def _handle_signal(signum, _frame):
    logger.info(json.dumps({
        "event": "signal",
        "signum": signum,
        "action": "graceful_shutdown_starting"
    }))

signal.signal(signal.SIGTERM, _handle_signal)
signal.signal(signal.SIGINT, _handle_signal)

# ─────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    logger.info(f"🔥 Starting {settings.app_name} on {settings.host}:{settings.port}")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"API Key: {settings.agent_api_key[:8]}****")
    
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        timeout_graceful_shutdown=30,
        log_level="info" if not settings.debug else "debug",
    )

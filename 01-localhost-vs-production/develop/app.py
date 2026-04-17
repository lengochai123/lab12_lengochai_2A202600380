"""
✅ FIXED — Agent "Production-Ready" (Best Practices)

Đã sửa tất cả 5 vấn đề anti-pattern:
  1. Không hardcode secrets — dùng biến môi trường (os.getenv)
  2. Có config management rõ ràng với giá trị mặc định an toàn
  3. Dùng logging module chuẩn thay vì print()
  4. Có /health endpoint để platform biết app còn sống
  5. Host/port đọc từ env var → deploy lên cloud được ngay
"""
import logging
import os

import uvicorn
from fastapi import FastAPI
from utils.mock_llm import ask

# ✅ Fix 3: Cấu hình logging chuẩn — không dùng print()
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

# ✅ Fix 1: Đọc secrets từ biến môi trường — KHÔNG bao giờ hardcode
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
DATABASE_URL: str = os.getenv("DATABASE_URL", "")

if not OPENAI_API_KEY:
    logger.warning("OPENAI_API_KEY chưa được đặt trong environment variables!")
if not DATABASE_URL:
    logger.warning("DATABASE_URL chưa được đặt trong environment variables!")

# ✅ Fix 2: Config management tập trung, có giá trị mặc định hợp lý
DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
MAX_TOKENS: int = int(os.getenv("MAX_TOKENS", "500"))

app = FastAPI(
    title="My Agent",
    debug=DEBUG,
)


@app.get("/")
def home():
    return {"message": "Hello! Agent is running.", "status": "ok"}


# ✅ Fix 4: Health check endpoint — giúp platform (Railway/Render/K8s) tự restart khi crash
@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.post("/ask")
def ask_agent(question: str):
    # ✅ Fix 3: Dùng logger thay vì print() — KHÔNG log secret ra ngoài
    logger.info("Received question (length=%d chars)", len(question))

    response = ask(question)

    logger.info("Response generated successfully")
    return {"answer": response}


# ✅ Fix 5: Đọc host/port từ env var → tương thích với mọi cloud platform
if __name__ == "__main__":
    host: str = os.getenv("HOST", "0.0.0.0")   # 0.0.0.0 → lắng nghe mọi interface
    port: int = int(os.getenv("PORT", "8000"))  # Railway/Render inject PORT tự động
    reload: bool = os.getenv("RELOAD", "false").lower() == "true"  # Tắt reload trong prod

    logger.info("Starting agent on %s:%d (reload=%s)", host, port, reload)
    # Truyền object app trực tiếp (không dùng string "app:app") khi reload=False
    # để tránh xung đột asyncio event loop trên Windows Python 3.12+
    uvicorn.run(
        app,        # ✅ object thay vì string — an toàn trên Windows/Python 3.13
        host=host,
        port=port,
        reload=reload,
    )

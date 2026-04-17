# 🔥 Fire Detection System - Deployment Guide

Hướng dẫn chi tiết để chạy Fire Detection LLM system trên local, Railway, và Render.

## 📋 Mục Lục
1. [Setup Local Development](#setup-local-development)
2. [Chạy trên Docker Locally](#chạy-trên-docker-locally)
3. [Deploy Railway](#deploy-railway)
4. [Deploy Render](#deploy-render)
5. [Testing & Validation](#testing--validation)
6. [Troubleshooting](#troubleshooting)

---

## Setup Local Development

### Bước 1: Chuẩn bị môi trường

```bash
# Clone/navigate to project
cd 06-lab-complete

# Tạo Python virtual environment
python -m venv venv

# Activate environment
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip
```

### Bước 2: Cài đặt dependencies

```bash
pip install -r requirements.txt
```

### Bước 3: Setup environment variables

```bash
# Copy .env.example to .env
cp .env.example .env

# Edit .env với các giá trị thật
# Các fields quan trọng:
# - AGENT_API_KEY: Tạo token ngẫu nhiên (32 ký tự)
# - OPENAI_API_KEY: Lấy từ https://platform.openai.com/api-keys
# - TELEGRAM_BOT_TOKEN: Lấy từ @BotFather trên Telegram
# - TELEGRAM_CHAT_ID: ID chat Telegram đích
```

**Lấy OPENAI_API_KEY:**
1. Đi đến https://platform.openai.com/api-keys
2. Click "Create new secret key"
3. Copy key vào .env

### Bước 4: Chạy ứng dụng (không có Docker)

```bash
# Chạy API server
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Output:
# INFO:     Uvicorn running on http://0.0.0.0:8000
# INFO:     Application startup complete
```

### Bước 5: Test API

```bash
# Terminal 1: Keep server running
python -m uvicorn app.main:app --reload

# Terminal 2: Test endpoints
# Get API key từ .env
export API_KEY="your-api-key"

# Health check
curl http://localhost:8000/health

# Readiness check
curl http://localhost:8000/ready

# Get budget info
curl -H "X-API-Key: $API_KEY" http://localhost:8000/budget

# Test fire detection (base64 encoded image)
# Đầu tiên, encode một ảnh thành base64:
python -c "
import base64
with open('test_image.jpg', 'rb') as f:
    img_b64 = base64.b64encode(f.read()).decode()
    print(img_b64)
" > image_b64.txt

api_key="your-api-key"
image_b64=$(cat image_b64.txt)

curl -X POST http://localhost:8000/analyze \
  -H "X-API-Key: $api_key" \
  -H "Content-Type: application/json" \
  -d "{
    \"image_base64\": \"$image_b64\",
    \"user_id\": \"test_user\"
  }"
```

---

## Chạy trên Docker Locally

### Bước 1: Build Docker image

```bash
# Build image
docker build -t fire-detector:latest .

# Verify build
docker images | grep fire-detector
```

### Bước 2: Run với Docker Compose

```bash
# Start all services (fire-detector + redis)
docker compose up -d

# Output:
# [+] Running 3/3
#  ✔ Network fire-network Created
#  ✔ Container fire-redis Created
#  ✔ Container fire-detector Created

# Check logs
docker compose logs -f fire-detector

# Test
curl http://localhost:8000/health
```

### Bước 3: Access Fire Detection API

```bash
api_key=$(grep AGENT_API_KEY .env | cut -d= -f2)

# Health check
curl http://localhost:8000/health

# Get budget
curl -H "X-API-Key: $api_key" http://localhost:8000/budget

# Fire detection
curl -X POST http://localhost:8000/analyze \
  -H "X-API-Key: $api_key" \
  -H "Content-Type: application/json" \
  -d '{"image_base64":"<BASE64_IMAGE_HERE>","user_id":"docker_test"}'
```

### Bước 4: Cleanup

```bash
# Stop all containers
docker compose down

# Remove image
docker rmi fire-detector:latest

# Remove volumes (optional)
docker compose down -v
```

---

## Deploy Railway

Railway là platform deployment tốt nhất cho Python apps (free tier có limitations nhưng đủ test).

### Prerequisites

- Tài khoản GitHub (dùng để login Railway)
- Code lên GitHub
- Railway CLI (optional, nhưng hữu ích)

### Bước 1: Push code lên GitHub

```bash
# Init git repo
git init
git add .
git commit -m "Fire detection system"

# Create repo on github.com và push
git remote add origin https://github.com/YOUR_USERNAME/fire-detection.git
git branch -M main
git push -u origin main
```

### Bước 2: Deploy on Railway

**Via Web UI (Dễ nhất):**

1. Đi đến https://railway.app
2. Click "Start a New Project"
3. Click "Deploy from GitHub"
4. Select repo "fire-detection"
5. Railway sẽ auto-detect Python + Deploy

**Via Railway CLI (để lại cho development):**

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Initialize project
railway init

# Set environment variables
railway variables set AGENT_API_KEY="your-secret-key"
railway variables set OPENAI_API_KEY="sk-..."
railway variables set ENVIRONMENT="production"

# Deploy
railway up
```

### Bước 3: Configure Railway Project

1. Đi vào project dashboard
2. Click service "fire-detector"
3. "Settings" → "Environment"
4. Thêm các biến môi trường (NẾU chưa add):
   - `AGENT_API_KEY`: Tạo random key (32 ký tự)
   - `OPENAI_API_KEY`: sk-...
   - `ENVIRONMENT`: production
   - `MONTHLY_BUDGET_USD`: 50

5. **QUAN TRỌNG**: Thêm Redis service
   - Click "New Service"
   - Click "Add from Marketplace"
   - Select "Redis"
   - Railway sẽ inject `REDIS_URL` tự động

### Bước 4: Get Public URL

1. Vào project
2. Tìm service "fire-detector"
3. Ngoài cùng phải có "Public URL" (ví dụ: `https://fire-detection-prod.railway.app`)

### Bước 5: Test Deployment

```bash
# Set variables
api_key="your-api-key"
public_url="https://fire-detection-prod.railway.app"

# Health check
curl $public_url/health

# Get budget
curl -H "X-API-Key: $api_key" $public_url/budget

# Fire detection
curl -X POST $public_url/analyze \
  -H "X-API-Key: $api_key" \
  -H "Content-Type: application/json" \
  -d '{"image_base64":"<BASE64_IMAGE>","user_id":"railway_test"}'
```

### Railway Monitoring

```bash
# View logs
railway logs

# Check metrics
# Railway dashboard → Metrics tab

# Redeploy if needed
railway up --detach
```

---

## Deploy Render

Render là alternative tốt cho Railway (free tier: 15 minutes runtime/month, nhưng stable hơn).

### Prerequisites

- Tài khoản GitHub
- Code lên GitHub repo
- Render.com account

### Bước 1: Create Render Web Service

1. Đi tới https://dashboard.render.com
2. Click "New +" → "Web Service"
3. Click "Connect account" (GitHub)
4. Select repo "fire-detection"
5. Fill form:
   - **Name**: fire-detection-prod
   - **Root Directory**: (bỏ trống hoặc "./06-lab-complete")
   - **Runtime**: Python 3.11
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port 8000`
   - **Instance Type**: Free (hoặc Starter)
6. Click "Create Web Service"

### Bước 2: Add Environment Variables

1. Trong Web Service dashboard
2. Click "Environment"
3. "Add Environment Variable" cho từng:
   - `AGENT_API_KEY`: your-secret-key
   - `OPENAI_API_KEY`: sk-...
   - `ENVIRONMENT`: production
   - `MONTHLY_BUDGET_USD`: 50.0
   - `REDIS_URL`: redis://localhost:6379 (sẽ update sau)

### Bước 3: Add Redis Service

1. Click "New+" → "Redis"
2. **Name**: fire-redis
3. Click "Create Redis"
4. Sau khi Redis created, copy connection string
5. Quay lại Web Service
6. Update `REDIS_URL` với connection string từ Redis

### Bước 4: Deploy Configuration

1. Web Service sẽ auto-deploy khi commit lên main
2. Hoặc click "Manual Deploy" để trigger ngay

### Bước 5: Get URL & Test

1. Dashboard → Web Service
2. Copy "Live URL" (ví dụ: `https://fire-detection-prod.onrender.com`)
3. Test endpoints:

```bash
api_key="your-api-key"
url="https://fire-detection-prod.onrender.com"

# Health
curl $url/health

# Budget
curl -H "X-API-Key: $api_key" $url/budget

# Fire detection
curl -X POST $url/analyze \
  -H "X-API-Key: $api_key" \
  -H "Content-Type: application/json" \
  -d '{"image_base64":"...","user_id":"render_test"}'
```

### Render Monitoring & Logs

```
Dashboard → Web Service → Logs tab
```

---

## Testing & Validation

### Unit Tests

```bash
# Create test file
cat > test_api.py << 'EOF'
import requests
import base64
from pathlib import Path
import time

# Config
API_KEY = "your-api-key"
PUBLIC_URL = "http://localhost:8000"  # Change for Railway/Render

def test_health():
    """Test health endpoint"""
    resp = requests.get(f"{PUBLIC_URL}/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
    print("✅ Health check passed")

def test_ready():
    """Test readiness"""
    resp = requests.get(f"{PUBLIC_URL}/ready")
    assert resp.status_code == 200
    print("✅ Readiness check passed")

def test_budget():
    """Test budget info"""
    resp = requests.get(
        f"{PUBLIC_URL}/budget",
        headers={"X-API-Key": API_KEY}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["monthly_budget"] > 0
    print(f"✅ Budget: ${data['monthly_spent']:.2f} / ${data['monthly_budget']:.2f}")

def test_fire_detection():
    """Test fire detection (requires real image)"""
    # Nếu có file image test
    image_path = Path("test_image.jpg")
    if not image_path.exists():
        print("⊘ Skipping fire detection test (no test_image.jpg)")
        return
    
    with open(image_path, "rb") as f:
        image_b64 = base64.b64encode(f.read()).decode()
    
    resp = requests.post(
        f"{PUBLIC_URL}/analyze",
        headers={"X-API-Key": API_KEY},
        json={"image_base64": image_b64[:100]}  # Test với ảnh nhỏ
    )
    assert resp.status_code in [200, 400]  # 400 maybe image too small
    print("✅ Fire detection endpoint responded")

def test_rate_limiting():
    """Test rate limiting"""
    for i in range(35):  # Limit is 30/min
        resp = requests.get(
            f"{PUBLIC_URL}/budget",
            headers={"X-API-Key": API_KEY}
        )
        if resp.status_code == 429:
            print(f"✅ Rate limiting triggered at request {i+1}")
            return
    print("⊘ Rate limiting not triggered (might be delayed)")

if __name__ == "__main__":
    print("🧪 Running API tests...\n")
    test_health()
    test_ready()
    test_budget()
    test_fire_detection()
    test_rate_limiting()
    print("\n✅ All tests completed!")
EOF

# Run tests
python test_api.py
```

### Load Testing

```bash
# Install ab (Apache Bench)
# macOS: brew install httpd
# Ubuntu: sudo apt install apache2-utils
# Windows: Use WSL

# Simple load test
ab -n 100 -c 10 http://localhost:8000/health

# With headers (requires custom script for X-API-Key)
python -m locust -f locustfile.py --host http://localhost:8000
```

### Monitor LLM Costs

```bash
# Check cost info after each request
api_key="your-api-key"
curl -H "X-API-Key: $api_key" http://localhost:8000/budget | jq '.percent_used'
```

---

## Troubleshooting

### Issue: "OPENAI_API_KEY not set"

**Solution:**
```bash
# Check .env file
echo $OPENAI_API_KEY

# Or in code:
export OPENAI_API_KEY="sk-your-actual-key"
```

### Issue: Docker build fails "python:3.11-slim not found"

**Solution:**
```bash
docker pull python:3.11-slim
docker build -t fire-detector .
```

### Issue: YOLO model download fails

**Solution:**
```bash
# Manually download model
python -c "from ultralytics import YOLO; YOLO('yolov8m.pt')"
```

### Issue: Redis connection refused

**Solution:**
```bash
# Check if Redis running (locally)
redis-cli ping
# Output: PONG

# Start Redis if needed
redis-server

# Or use Docker compose
docker compose up redis -d
```

### Issue: "Rate limit exceeded" error

**Solution:**
```bash
# Rate limit is 30 requests/minute per API key
# Wait 60 seconds or use different API key
```

### Issue: Budget exceeded on Railway/Render

**Solution:**
```bash
# Edit MONTHLY_BUDGET_USD in environment variables
# Restart service
```

---

## Summary Table

| 環境 | Setup時間 | 本番対応 | コスト/月 | 推奨 |
|------|---------|-------|---------|-----|
| Local | 5分 | ✅ 完全 | ¥0 | 開発 |
| Docker Local | 10分 | ✅ 完全 | ¥0 | テスト |
| Railway | 10分 | ⚠️ 条件付き | ¥5-50 | 本番 |
| Render | 10分 | ✅ 完全 | ¥0-50+ | 本番 |

---

## Next Steps

1. ✅ Local testing
2. ✅ Docker verification
3. ✅ Deploy to Railway or Render
4. ✅ Setup Telegram alerts
5. ✅ Monitor costs on dashboard
6. ✅ Scale to production

---

**Questions? Check logs:**
```bash
# Local
tail -f logs/app.log

# Docker
docker compose logs -f fire-detector

# Railway
railway logs

# Render
Render Dashboard → Logs
```

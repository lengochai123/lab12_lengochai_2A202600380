# 🔥 Fire Detection System — Production-Ready API

[![Python 3.11](https://img.shields.io/badge/Python-3.11-blue)]()
[![FastAPI](https://img.shields.io/badge/FastAPI-Latest-green)]()
[![Docker](https://img.shields.io/badge/Docker-Multi--Stage-blue)]()
[![License](https://img.shields.io/badge/License-MIT-green)]()

**A production-ready fire detection system with LLM-powered analysis, cost management, and real-time alerts.**

## 🎯 Features

✅ **YOLO Fire Detection** - Real-time fire detection using YOLOv8
✅ **LLM Analysis** - Intelligent analysis with OpenAI GPT-4 Vision
✅ **Cost Guard** - Monthly LLM budget tracking and protection
✅ **Rate Limiting** - 30 req/min per API key
✅ **Authentication** - API Key + JWT support
✅ **Health Checks** - Liveness & readiness probes
✅ **Graceful Shutdown** - SIGTERM handler
✅ **Structured Logging** - JSON-formatted logs
✅ **Production Docker** - Multi-stage build < 1GB
✅ **Redis Integration** - Caching & distributed rate limiting
✅ **Railway/Render Ready** - Deploy in < 5 minutes

## 🚀 Quick Start

### Local (5 minutes)

```bash
# Setup
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Copy & edit .env
cp .env.example .env
# Update: AGENT_API_KEY, OPENAI_API_KEY, TELEGRAM credentials

# Run
python -m uvicorn app.main:app --reload

# Test
curl http://localhost:8000/health
```

### Docker (10 minutes)

```bash
# Build & run
docker compose up -d

# Test
curl http://localhost:8000/health

# Cleanup
docker compose down
```

### Railway (5 minutes)

```bash
# Push to GitHub, then:
# 1. https://railway.app → New Project → Deploy from GitHub
# 2. Add environment variables
# 3. Add Redis service
# Done! Get public URL from dashboard
```

👉 **[Full Deployment Guide](./DEPLOYMENT.md)**

## 📚 Project Structure

```
06-lab-complete/
├── app/
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration (12-factor)
│   ├── auth.py              # Authentication & security
│   ├── rate_limiter.py      # Rate limiting (in-memory & Redis)
│   ├── cost_guard.py        # LLM budget tracking
│   ├── fire_detector.py     # YOLO-based fire detection
│   ├── alert_manager.py     # Telegram alert management
│   └── llm_analyzer.py      # LLM-powered analysis
├── utils/
│   └── mock_llm.py          # Mock LLM for development
├── Dockerfile               # Multi-stage production build
├── docker-compose.yml       # Local development stack
├── requirements.txt         # Python dependencies
├── .env.example             # Environment template
├── .env.local               # Local secrets (git-ignored)
├── railway.toml             # Railway deployment config
├── render.yaml              # Render deployment config
├── DEPLOYMENT.md            # Detailed deployment guide
└── README.md                # This file
```

## 🔧 API Endpoints

### Info
- `GET /` - API information

### Fire Detection
- `POST /analyze` - Analyze image for fire (requires API key)
  - Request: `{ "image_base64": "...", "user_id": "..." }`
  - Response: `{ "fire_detected": bool, "detections": {...}, "llm_analysis": "...", "cost_info": {...} }`

### Operations (Monitoring)
- `GET /health` - Liveness probe
- `GET /ready` - Readiness probe
- `GET /metrics` - Metrics (requires API key)
- `GET /budget` - Budget info (requires API key)

## 🔐 Authentication

All endpoints except `/health` and `/ready` require:

```bash
# Include header:
curl -H "X-API-Key: your-api-key" http://localhost:8000/...
```

Get API key from `.env` file:
```bash
export API_KEY=$(grep AGENT_API_KEY .env | cut -d= -f2)
```

## 💰 Cost Management

Monthly budget tracking for LLM calls:

```bash
# Check budget
curl -H "X-API-Key: $API_KEY" http://localhost:8000/budget
```

Response:
```json
{
  "monthly_budget": 50.0,
  "monthly_spent": 2.45,
  "remaining_budget": 47.55,
  "percent_used": 4.9,
  "reset_date": "2024-05-01"
}
```

**Configuration:**
- Set `MONTHLY_BUDGET_USD` in `.env`
- Alert at 80% usage (configurable)
- Requests rejected when budget exceeded

## 📊 Example Usage

### 1. Test with cURL

```bash
# Health check (no auth needed)
curl http://localhost:8000/health

# Get budget info
api_key="dev-key-change-me-in-production"
curl -H "X-API-Key: $api_key" http://localhost:8000/budget

# Analyze image for fire
image_b64=$(cat test_image.jpg | base64 | tr -d '\n')
curl -X POST http://localhost:8000/analyze \
  -H "X-API-Key: $api_key" \
  -H "Content-Type: application/json" \
  -d "{
    \"image_base64\": \"$image_b64\",
    \"user_id\": \"test_user\"
  }"
```

### 2. Python Client

```python
import requests
import base64

API_KEY = "dev-key-change-me-in-production"
API_URL = "http://localhost:8000"

# Load image
with open("fire_image.jpg", "rb") as f:
    image_b64 = base64.b64encode(f.read()).decode()

# Analyze
response = requests.post(
    f"{API_URL}/analyze",
    headers={"X-API-Key": API_KEY},
    json={
        "image_base64": image_b64,
        "user_id": "python_client"
    }
)

print(response.json())
```

### 3. JavaScript/Node Client

```javascript
const fetch = require('node-fetch');
const fs = require('fs');

const API_KEY = 'dev-key-change-me-in-production';
const API_URL = 'http://localhost:8000';

// Load image
const imageBuffer = fs.readFileSync('fire_image.jpg');
const imageB64 = imageBuffer.toString('base64');

// Analyze
fetch(`${API_URL}/analyze`, {
  method: 'POST',
  headers: {
    'X-API-Key': API_KEY,
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    image_base64: imageB64,
    user_id: 'js_client',
  }),
})
  .then(r => r.json())
  .then(data => console.log(data))
  .catch(e => console.error(e));
```

## ⚙️ Configuration

### Environment Variables (`.env`)

```env
# Server
HOST=0.0.0.0
PORT=8000
ENVIRONMENT=development  # production | staging | development
DEBUG=false

# Security (CHANGE IN PRODUCTION!)
AGENT_API_KEY=dev-key-change-me-in-production
JWT_SECRET=dev-jwt-secret-change-in-production

# LLM
OPENAI_API_KEY=sk-...  # Get from https://platform.openai.com
LLM_MODEL=gpt-4-vision

# Fire Detection (YOLO)
YOLO_MODEL_NAME=yolov8m.pt
YOLO_CONFIDENCE_THRESHOLD=0.5

# Rate Limiting
RATE_LIMIT_PER_MINUTE=30

# Cost Guard
MONTHLY_BUDGET_USD=50.0
ALERT_BUDGET_PERCENT=0.8

# Redis
REDIS_URL=redis://localhost:6379/0

# CORS
ALLOWED_ORIGINS=*
```

## 🧪 Testing

```bash
# Unit tests
python -m pytest tests/ -v

# Load test
ab -n 100 -c 10 http://localhost:8000/health

# Cost tracking test
python test_api.py
```

See [DEPLOYMENT.md](./DEPLOYMENT.md) for more tests.

## 📈 Monitoring

### Health Checks

```bash
# Liveness (restart if fails)
curl http://localhost:8000/health

# Readiness (stop routing if fails)
curl http://localhost:8000/ready
```

### Metrics

```bash
curl -H "X-API-Key: $API_KEY" http://localhost:8000/metrics
```

### Logs

```bash
# Local
python -m uvicorn app.main:app --reload

# Docker
docker compose logs -f fire-detector

# Railway
railway logs

# Render
Dashboard → Logs tab
```

## 🐳 Docker & Deployment

### Build Image

```bash
docker build -t fire-detector:latest .
docker run -p 8000:8000 fire-detector:latest
```

### Multi-stage Build Details

- **Stage 1** (Builder): Compiles Python packages
- **Stage 2** (Runtime): Minimal image with only runtime deps
- Result: ~1GB image (slim Python 3.11 + PyTorch + OpenCV)

### Production Checklist

- ✅ Change `AGENT_API_KEY` & `JWT_SECRET`
- ✅ Set `OPENAI_API_KEY`
- ✅ Configure Telegram credentials
- ✅ Set `ENVIRONMENT=production`
- ✅ Enable Redis
- ✅ Setup monitoring/logging
- ✅ Configure CORS for frontend
- ✅ Use HTTPS in production
- ✅ Setup auto-scaling policies

## 🚢 Deployment Platforms

### Railway ✅

- **Setup**: 5 minutes
- **Free tier**: 5 GB bandwidth
- **Cost**: $5-200+/month
- [Railway Guide →](./DEPLOYMENT.md#deploy-railway)

### Render ✅

- **Setup**: 5 minutes
- **Free tier**: 15 min runtime/month
- **Cost**: $7-100+/mo nth
- [Render Guide →](./DEPLOYMENT.md#deploy-render)

### AWS, Google Cloud, etc. ✅

- Use Dockerfile for any platform
- Supports container registry (ECR, GCR, etc.)

## 📝 Troubleshooting

### "YOLO model not found"

```bash
cd app
python -c "from ultralytics import YOLO; YOLO('yolov8m.pt')"
```

### "OpenAI API rate limited"

```bash
# Reduce requests or increase budget
MONTHLY_BUDGET_USD=100.0
```

### "Telegram not sending alerts"

```bash
# Verify token
curl "https://api.telegram.org/bot<TOKEN>/getMe"
```

### "Rate limit exceeded"

```bash
# Increase limit or wait 60 seconds
RATE_LIMIT_PER_MINUTE=100
```

👉 **[Complete Troubleshooting Guide →](./DEPLOYMENT.md#troubleshooting)**

## 🎓 Lab Concepts

This project implements all "Day 12 Lab" production patterns:

| Concept | Implementation |
|---------|-----------------|
| 12-Factor App | Config from environment variables |
| Authentication | API Key + JWT support |
| Rate Limiting | In-memory + Redis backends |
| Budget Protection | Cost guard with monthly tracking |
| Health Checks | Liveness + readiness probes |
| Graceful Shutdown | SIGTERM handler |
| Structured Logging | JSON-formatted logs |
| Security Headers | X-Content-Type-Options, X-Frame-Options |
| CORS | Configurable allowed origins |
| Multi-stage Docker | Builder + Runtime stages |
| Non-root User | Security in container |
| Production Readiness | All checks passed |

## 📖 Documentation

- [Deployment Guide](./DEPLOYMENT.md) - Detailed setup for local, Railway, Render
- [API Docs](http://localhost:8000/docs) - Swagger UI (development only)
- [Config Reference](./app/config.py) - All environment variables
- [Code Comments](./app/) - Inline documentation

## 🤝 Contributing

1. Create feature branch: `git checkout -b feature/xyz`
2. Write tests for new code
3. Ensure `requirements.txt` updated
4. Commit: `git commit -am 'Add feature'`
5. Push: `git push origin feature/xyz`
6. Create PR

## 📄 License

MIT License — See LICENSE file

## 🆘 Support

- Check [DEPLOYMENT.md](./DEPLOYMENT.md)
- Review app logs
- Create GitHub issue

---

**Made with ❤️ for Day 12 Lab**

🔗 **Quick Links:**
- 📌 [Local Setup](./DEPLOYMENT.md#setup-local-development)
- 🐳 [Docker Setup](./DEPLOYMENT.md#chạy-trên-docker-locally)
- 🚀 [Railway Deploy](./DEPLOYMENT.md#deploy-railway)
- 📦 [Render Deploy](./DEPLOYMENT.md#deploy-render)


---

## Deploy Render

1. Push repo lên GitHub
2. Render Dashboard → New → Blueprint
3. Connect repo → Render đọc `render.yaml`
4. Set secrets: `OPENAI_API_KEY`, `AGENT_API_KEY`
5. Deploy → Nhận URL!

---

## Kiểm Tra Production Readiness

```bash
python check_production_ready.py
```

Script này kiểm tra tất cả items trong checklist và báo cáo những gì còn thiếu.

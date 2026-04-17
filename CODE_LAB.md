#  Code Lab: Deploy Your AI Agent to Production

> **AICB-P1 · VinUniversity 2026**  
> Thời gian: 3-4 giờ | Độ khó: Intermediate

##  Mục Tiêu

Sau khi hoàn thành lab này, bạn sẽ:
- Hiểu sự khác biệt giữa development và production
- Containerize một AI agent với Docker
- Deploy agent lên cloud platform
- Bảo mật API với authentication và rate limiting
- Thiết kế hệ thống có khả năng scale và reliable

---

##  Yêu Cầu

```bash
 Python 3.11+
 Docker & Docker Compose
 Git
 Text editor (VS Code khuyến nghị)
 Terminal/Command line
```

**Không cần:**
-  OpenAI API key (dùng mock LLM)
-  Credit card
-  Kinh nghiệm DevOps trước đó

---

##  Lộ Trình Lab

| Phần | Thời gian | Nội dung |
|------|-----------|----------|
| **Part 1** | 30 phút | Localhost vs Production |
| **Part 2** | 45 phút | Docker Containerization |
| **Part 3** | 45 phút | Cloud Deployment |
| **Part 4** | 40 phút | API Security |
| **Part 5** | 40 phút | Scaling & Reliability |
| **Part 6** | 60 phút | Final Project |

---

## Part 1: Localhost vs Production (30 phút)

###  Concepts

**Vấn đề:** "It works on my machine" — code chạy tốt trên laptop nhưng fail khi deploy.

**Nguyên nhân:**
- Hardcoded secrets
- Khác biệt về environment (Python version, OS, dependencies)
- Không có health checks
- Config không linh hoạt

**Giải pháp:** 12-Factor App principles

###  Exercise 1.1: Phát hiện anti-patterns

```bash
cd 01-localhost-vs-production/develop
```

**Nhiệm vụ:** Đọc `app.py` và tìm ít nhất 5 vấn đề.

<details>
<summary> Gợi ý</summary>

Tìm:
- API key hardcode
- Port cố định
- Debug mode
- Không có health check
- Không xử lý shutdown

</details>

###  Exercise 1.2: Chạy basic version

```bash
pip install -r requirements.txt
python app.py
```

Test:
```bash
curl http://localhost:8000/ask -X POST \
  -H "Content-Type: application/json" \
  -d '{"question": "Hello"}'
```

**Quan sát:** Nó chạy! Nhưng có production-ready không?

###  Exercise 1.3: So sánh với advanced version

```bash
cd ../production
cp .env.example .env
pip install -r requirements.txt
python app.py
```

**Nhiệm vụ:** So sánh 2 files `app.py`. Điền vào bảng:

| Feature | Basic | Advanced | Tại sao quan trọng? |
|---------|-------|----------|---------------------|
| Config | Hardcode | Env vars |Bảo mật (không lộ API key lên GitHub) & Linh hoạt (đổi host/port/key mà không cần sửa code).|
| Health check | Không có |Có | Giúp nền tảng cloud (Railway, Render) biết app còn "sống" hay không. Nếu không có health check, cloud sẽ không tự động restart khi app bị treo (ví dụ: do lỗi trong vòng lặp vô hạn), dẫn đến downtime kéo dài cho người dùng. |

| Logging | print() | JSON | Khi chạy trên cloud, print sẽ lộn xộn. Log chuẩn có level (INFO/ERROR), có timestamp và dễ dàng tìm kiếm trên các hệ thống như Datadog/CloudWatch. |
| Shutdown | Đột ngột | Graceful | Khi bạn update code mới, server phải tắt. Graceful shutdown chờ các request đang xử lý chạy xong rồi mới tắt, giúp user không bị báo lỗi 500. |

###  Checkpoint 1

- [ ] Hiểu tại sao hardcode secrets là nguy hiểm
- [ ] Biết cách dùng environment variables
- [ ] Hiểu vai trò của health check endpoint
- [ ] Biết graceful shutdown là gì

---

## Part 2: Docker Containerization (45 phút)

###  Concepts

**Vấn đề:** "Works on my machine" part 2 — Python version khác, dependencies conflict.

**Giải pháp:** Docker — đóng gói app + dependencies vào container.

**Benefits:**
- Consistent environment
- Dễ deploy
- Isolation
- Reproducible builds

###  Exercise 2.1: Dockerfile cơ bản

```bash
cd ../../02-docker/develop
```

**Nhiệm vụ:** Đọc `Dockerfile` và trả lời:

**Câu trả lời:** `python:3.11`

Base image này là một pre-built image từ Docker Hub chứa đầy đủ:
- Ubuntu Linux OS
- Python 3.11 runtime
- pip package manager
- Kích thước: ~1 GB (full distribution)

**Tại sao quan trọng:**
- Không cần cài Python từ đầu
- Có sẵn các system libraries
- Image lớn nhưng chắc chắn hoạt động

**Để nhỏ hơn, dùng `python:3.11-slim`:**
- Chỉ ~400 MB (loại bỏ docs, dev tools)
- Vẫn đủ để chạy ứng dụng Python

### 2. Working directory là gì?
**Câu trả lời:** `WORKDIR /app`

- Thiết lập thư mục làm việc trong container
- Tất cả COPY, RUN, CMD sau này sẽ chạy trong `/app`
- Tương đương `cd /app` trong terminal

**Ví dụ:**
```dockerfile
WORKDIR /app
COPY app.py .        # Copy vào /app/app.py (không /app/app/app.py)
RUN pip install -r requirements.txt  # Chạy từ /app
```

### 3. Tại sao COPY requirements.txt trước?
**Câu trả lời:** Vì **Docker layer caching**

**Cách Docker build hoạt động:**
```
Layer 1: FROM python:3.11
↓
Layer 2: WORKDIR /app
↓
Layer 3: COPY requirements.txt .    ← CACHE HERE
↓
Layer 4: RUN pip install -r requirements.txt
↓
Layer 5: COPY app.py .             ← CACHE HERE
↓
Layer 6: CMD ["python", "app.py"]
```

**Tại sao này tốt:**
- Nếu chỉ thay đổi `app.py` → không cần rebuild Layer 4 (cài pip lại, mất 5 phút)
- Docker skip Layer 3-4, chỉ rebuild Layer 5-6 (nhanh chóng)

**Tại sao không:**
```dockerfile
# ❌ BAD: COPY toàn bộ trước
COPY . .
RUN pip install -r requirements.txt
```
- Bất kỳ thay đổi code nào (tệp txt, images, etc.) → Docker bỏ cache → rebuild từ đầu

### 4. CMD vs ENTRYPOINT khác nhau thế nào?

| Khía cạnh | CMD | ENTRYPOINT |
|-----------|-----|-----------|
| **Mục đích** | Default command nếu không có argument | Main process của container |
| **Có thể override?** | ✅ Dễ (`docker run image new-cmd`) | ❌ Khó (`docker run --entrypoint`) |
| **Dùng khi nào** | Tuỳ chọn mặc định | Pipeline, không override |
| **Ví dụ** | `CMD ["python", "app.py"]` | `ENTRYPOINT ["uvicorn", "app:app"]` |

**Thực tế:** Để chạy app với khác port:
```bash
# Dùng CMD
docker run -it agent-develop python app.py --port 9000  # ✅ Hoạt động

# Dùng ENTRYPOINT
docker run -it agent-develop --port 9000  # ✅ Truyền arg trực tiếp

###  Exercise 2.2: Build và run

```bash
# Build image
docker build -f 02-docker/develop/Dockerfile -t my-agent:develop .

# Run container
docker run -p 8000:8000 my-agent:develop

# Test
curl http://localhost:8000/ask -X POST \
  -H "Content-Type: application/json" \
  -d '{"question": "What is Docker?"}'
```

**Quan sát:** 1.66GB
```bash
docker images my-agent:develop
```

###  Exercise 2.3: Multi-stage build

```bash
cd ../production
```

**Nhiệm vụ:** Đọc `Dockerfile` và tìm:
- Stage 1 làm gì?
-stage 1 làm:
- Cài gcc + dev tools (cần để compile một số packages)
- Cài tất cả Python packages vào `/root/.local`
- ⚠️ **Không copy code, không là final image**
**Kích thước:** ~1.5 GB (tạm thời, sẽ throw away)
- Stage 2 làm gì?
- stage 2 làm:
- Fresh start từ `python:3.11-slim` (~400 MB)
- Copy chỉ site-packages + code (không copy gcc, build tools)
- Tạo non-root user (secure)
- Thêm health check (auto-restart khi fail)
- **Kích thước cuối cùng:** ~450-500 MB
- Tại sao image nhỏ hơn?
| Thành phần | Builder | Runtime | Ghi chú |
|-----------|---------|---------|---------|
| Python runtime | 200 MB | 200 MB | Cả hai cần |
| gcc, libc-dev, build-essential | 800 MB | ❌ | Chỉ builder cần |
| pip, setuptools | 100 MB | ✅ (trong site-packages) | Runtime cần chạy |
| site-packages | 300 MB | ✅ 300 MB | Code/deps |
| **Tổng** | ~1.4 GB | ~500 MB | **64% nhỏ hơn** |
Build và so sánh:
```bash
docker build -t my-agent:advanced .
docker images | grep my-agent
```

###  Exercise 2.4: Docker Compose stack

**Nhiệm vụ:** Đọc `docker-compose.yml` và vẽ architecture diagram.
```
┌─────────────────────────┐
│  Client (curl)          │
└────────────┬────────────┘
             │ port 80
             ▼
┌─────────────────────────┐
│   Nginx (Load Balancer) │  ← Public facing
└────────┬────────────────┘
         │ internal network
    ┌────┴────┐
    │          │
    ▼          ▼
┌────────┐  ┌────────┐
│ Agent1 │  │ Agent2 │  ← Scale to N
└────┬───┘  └────┬───┘
     │          │
     └──────┬───┘
          │
    ┌─────┴──────────┬────────────┐
    ▼                ▼            ▼
┌────────┐      ┌────────┐   ┌─────────┐
│ Redis  │      │ Qdrant │   │ Agent3  │
└────────┘      └────────┘   └─────────┘
```

### 4 Services trong docker-compose.yml

#### 1. **agent** — FastAPI Application
```yaml
agent:
  build:
    context: .
    dockerfile: Dockerfile
    target: runtime          # ← Build chỉ stage "runtime"
  environment:
    - ENVIRONMENT=staging
    - PORT=8000
    - REDIS_URL=redis://redis:6379/0  # ← Connect tới Redis service
    - QDRANT_URL=http://qdrant:6333   # ← Connect tới Qdrant service
  healthcheck:
    test: ["CMD", "python", "-c", "import urllib.request; ..."]
    interval: 30s           # ← Check mỗi 30s
    retries: 3              # ← Restart nếu fail 3 lần
  restart: unless-stopped   # ← Tự động restart
```

**Chú ý:**
- Services communicate bằng service name (vd: `redis://redis:6379`)
- Docker tự tạo DNS resolution

#### 2. **redis** — Cache & Session Store
```yaml
redis:
  image: redis:7-alpine     # ← Dùng pre-built image từ Docker Hub
  command: redis-server --maxmemory 256mb --maxmemory-policy allkeys-lru
  volumes:
    - redis_data:/data      # ← Persist data khi restart
  healthcheck:
    test: ["CMD", "redis-cli", "ping"]
```

**Dùng để:**
- Cache conversation history
- Rate limiting storage
- Session management

#### 3. **qdrant** — Vector Database (for RAG)
```yaml
qdrant:
  image: qdrant/qdrant:v1.9.0
  volumes:
    - qdrant_data:/qdrant/storage  # ← Persist embeddings
```

**Dùng để:** Lưu vector embeddings để similarity search

#### 4. **nginx** — Reverse Proxy & Load Balancer
```yaml
nginx:
  image: nginx:alpine
  ports:
    - "80:80"               # ← Only Nginx expose public port
    - "443:443"
  volumes:
    - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro  # ← Config file
  depends_on:
    - agent
```

**Mục đích:**
- Single entry point (port 80)
- Load balance requests tới N agent instances
- Reverse proxy (hide internal services)
```bash
docker compose up
```

Services nào được start? Chúng communicate thế nào?
# Output:
# [+] Running 5/5
#  ✓ redis Pulled
#  ✓ qdrant Pulled
#  ✓ agent Built
#  ✓ nginx Pulled ...
#  ⠿ Network internal Created
#  ⠿ redis Started
#  ⠿ qdrant Started
#  ⠿ agent Started
#  ⠿ nginx Started
```

### Test Endpoints (từ terminal khác)

```bash
# 1. Health check qua Nginx
curl http://localhost/health

# Response:
# {"status":"ok","uptime_seconds":1.5,"container":true}

# 2. Agent endpoint qua Nginx (load balanced)
curl http://localhost/ask -X POST \
  -H "Content-Type: application/json" \
  -d '{"question": "Explain microservices"}'

# Response:
# {"answer":"<mock LLM response>"}
```

### Debug & Monitoring

```bash
# 1. View logs từ tất cả services
docker compose logs -f

# 2. View logs từ 1 service
docker compose logs -f agent

# 3. List containers
docker compose ps

# Output:
# NAME                  COMMAND                  SERVICE             STATUS              PORTS
# production-agent-1    "uvicorn main:app..."   agent              Up (healthy)        8000/tcp
# production-redis-1    "redis-server..."       redis              Up (healthy)
# production-qdrant-1   "/qdrant --config..."   qdrant             Up (healthy)
# production-nginx-1    "/docker-entrypoint..." nginx              Up                   0.0.0.0:80->80/tcp
```

### Nó communicate thế nào?

**1. Nginx → Agent (internal network)**
```
Client:80                 Nginx:80
              ↓ (proxy)
         Agent:8000 (internal)
```

Nginx config (inside container) — viết `/etc/nginx/nginx.conf`:
```
upstream agent_backend {
    server agent:8000;  # ← Service name = DNS
}

server {
    listen 80;
    location / {
        proxy_pass http://agent_backend;
    }
}
```

**2. Agent → Redis (internal network)**
```python
# Inside agent container
import redis
r = redis.from_url("redis://redis:6379")  # ← "redis" = DNS name
r.set("key", "value")
```

**3. Agent → Qdrant (internal network)**
```python
# Inside agent container
from qdrant_client import QdrantClient
client = QdrantClient(url="http://qdrant:6333")  # ← "qdrant" = DNS name
```

---
Test:
```bash
# Health check
curl http://localhost/health

# Agent endpoint
curl http://localhost/ask -X POST \
  -H "Content-Type: application/json" \
  -d '{"question": "Explain microservices"}'
```

###  Checkpoint 2

- [ ] Hiểu cấu trúc Dockerfile
- [ ] Biết lợi ích của multi-stage builds
- [ ] Hiểu Docker Compose orchestration
- [ ] Biết cách debug container (`docker logs`, `docker exec`)

---

## Part 3: Cloud Deployment (45 phút)

###  Concepts

**Vấn đề:** Laptop không thể chạy 24/7, không có public IP.

**Giải pháp:** Cloud platforms — Railway, Render, GCP Cloud Run.

**So sánh:**

| Platform | Độ khó | Free tier | Best for |
|----------|--------|-----------|----------|
| Railway | ⭐ | $5 credit | Prototypes |
| Render | ⭐⭐ | 750h/month | Side projects |
| Cloud Run | ⭐⭐⭐ | 2M requests | Production |

---

###  Exercise 3.1: Deploy Railway (15 phút)

**Folder:** `03-cloud-deployment/railway`

**railway.toml là gì?**
```toml
[build]
builder = "NIXPACKS"  # Auto-detect Python, install deps

[deploy]
startCommand = "uvicorn app:app --host 0.0.0.0 --port $PORT"
healthcheckPath = "/health"  # Railway checks mỗi 30s
restartPolicyType = "ON_FAILURE"  # Tự restart nếu crash
```

**Tại sao `$PORT` quan trọng:**
- Railway tự inject PORT environment variable
- App phải dùng `os.getenv("PORT")` hoặc mặc định 8000
- Nếu hardcode port → app không nghe port Railway assign → deploy fail

**Step-by-step:**

#### 1. Install Railway CLI (Mac/Windows/Linux)
```bash
npm i -g @railway/cli
# Hoặc: brew install railway (nếu dùng Homebrew)
```

Verify:
```bash
railway --version
# v8.0.0 (or latest)
```

#### 2. Login to Railway
```bash
railway login
```
- Mở browser → login với GitHub/Google
- CLI tự authorize

#### 3. Initialize project
```bash
cd 03-cloud-deployment/railway
railway init
```
- Chọn: Create new project
- Tên: `ai-agent-lab`

#### 4. Set environment variables
```bash
# Port (Railway inject tự động, nhưng set để chắc chắn)
railway variables set PORT=8000

# API Key
railway variables set AGENT_API_KEY=my-secret-key-123

# Environment
railway variables set ENVIRONMENT=production
```

#### 5. Deploy
```bash
railway up
```

**Expected output:**
```
⠙ Building...
Successfully built image
⠙ Deploying...
✓ Deployment successful!
📦 Service: ai-agent-lab-web
📝 Logs: railway.app/project/xxxxx/service/xxxxx
🌐 Public URL: https://ai-agent-lab-prod-xxx.railway.app
```

#### 6. Get public URL
```bash
railway open  # Mở dashboard
# Hoặc
railway domain  # Get domain
```

**Testing live deployment:**

```bash
DOMAIN="https://ai-agent-lab-prod-xxx.railway.app"

# Health check
curl $DOMAIN/health

# Agent endpoint
curl -X POST $DOMAIN/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "Hello from Railway!"}'
```

**Expected response:**
```json
{"status": "ok", "uptime_seconds": 123.4}
{"answer": "<mock response>"}
```

**Debugging nếu fail:**

```bash
# View logs real-time
railway logs

# View specific error
railway logs -f  # Follow mode

# SSH vào container
railway shell

# Redeploy
railway up --force
```

**Common issues:**

| Error | Nguyên nhân | Fix |
|-------|-----------|-----|
| `Port already in use` | App không listen PORT env var | Dùng `os.getenv("PORT", 8000)` |
| `Health check fails` | `/health` endpoint không respond | Implement `/health` endpoint |
| `Crash loop` | App có lỗi startup | `railway logs` để debug |
| `404 / Not Found` | URL không đúng | Check `railway domain` |

---

###  Exercise 3.2: Deploy Render (15 phút)

**Folder:** `03-cloud-deployment/render`

**render.yaml — Infrastructure as Code**
```yaml
services:
  - type: web
    name: ai-agent
    runtime: python311
    buildCommand: "pip install -r requirements.txt"
    startCommand: "uvicorn app:app --host 0.0.0.0 --port $PORT"
    envVars:
      - key: PORT
        value: "8000"
      - key: ENVIRONMENT
        value: production
      - key: AGENT_API_KEY
        generateValue: true  # Render tự generate random key
```

**Step-by-step:**

#### 1. Push code to GitHub
```bash
# Nếu chưa có git repo
git init
git add .
git commit -m "AI agent for deployment"
git remote add origin https://github.com/YOUR_USERNAME/ai-agent-lab
git push -u origin main
```

#### 2. Sign up at render.com
- Vào: https://render.com
- Sign up with GitHub (easier)

#### 3. Create new service
- Dashboard → New → Web Service
- Connect GitHub repo
- Select `ai-agent-lab` repository

#### 4. Render auto-detects
- Render reads `render.yaml`
- Auto-selects Python 3.11
- Auto-sets start command

#### 5. Configure environment
- Set `AGENT_API_KEY` in dashboard
- Set `ENV` = production

#### 6. Deploy
- Click "Deploy"
- Wait 2-5 minutes

**Expected output:**
```
✓ Build succeeded
✓ Service live at: https://ai-agent-xxxxx.onrender.com
```

**So sánh Railway vs Render:**

| Khía cạnh | Railway | Render |
|----------|---------|--------|
| **Ease** | ⭐⭐ (CLI) | ⭐ (UI) |
| **Config** | TOML file | YAML + Dashboard |
| **Free tier** | $5 credit | 750 hours/month |
| **Best for** | Quick deploy | Long-term projects |
| **CI/CD** | Git push → deploy | Git push → deploy |

---

###  Exercise 3.3: (Optional) GCP Cloud Run (15 phút)

**Folder:** `03-cloud-deployment/production-cloud-run`

**cloud run là gì:**
- Serverless: chỉ trả tiền khi có request
- 2M requests/month free
- Auto-scale từ 0 → N instances

**cloudbuild.yaml — CI/CD Pipeline**
```yaml
steps:
  # Step 1: Build Docker image
  - name: gcr.io/cloud-builders/docker
    args:
      - build
      - -t
      - gcr.io/$PROJECT_ID/ai-agent:$COMMIT_SHA
      - -t
      - gcr.io/$PROJECT_ID/ai-agent:latest
      - .

  # Step 2: Push to Container Registry
  - name: gcr.io/cloud-builders/docker
    args:
      - push
      - gcr.io/$PROJECT_ID/ai-agent:latest

  # Step 3: Deploy to Cloud Run
  - name: gcr.io/cloud-builders/gke-deploy
    args:
      - run
      - --filename=.
      - --image=gcr.io/$PROJECT_ID/ai-agent:latest
      - --location=us-central1

images:
  - gcr.io/$PROJECT_ID/ai-agent:latest
```

**service.yaml — Cloud Run config**
```yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: ai-agent
spec:
  template:
    spec:
      containers:
      - image: gcr.io/PROJECT_ID/ai-agent:latest
        ports:
        - containerPort: 8000
        env:
        - name: PORT
          value: "8000"
        - name: ENVIRONMENT
          value: production
```

**Deploy steps:**

```bash
gcloud run deploy ai-agent \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

---

###  Checkpoint 3

- [x] Hiểu Railway deployment flow (railway.toml)
- [x] Biết Render vs Railway trade-offs
- [x] Hiểu environment variables trên cloud
- [x] Biết deploy success indicators:
  - Health endpoint responds 200
  - Logs show "ready to accept traffic"
  - Public URL accessible
  - Agent endpoint returns responses

---

## Part 4: API Security (40 phút)

###  Concepts

**Vấn đề:** Public URL = ai cũng gọi được = hết tiền OpenAI = DISASTER.

**Giải pháp — 3 lớp bảo vệ:**
1. **Authentication** — Xác định CÓ PHẢI người dùng hợp lệ không?
2. **Rate Limiting** — Giới hạn số request để chống DDoS
3. **Cost Guard** — Dừng khi vượt budget/user

---

###  Exercise 4.1: API Key authentication (Basic)

**Folder:** `04-api-gateway/develop`

**Concept:**
- Client phải gửi `X-API-Key` header
- Server kiểm tra header vs secret key trong env var
- Nếu sai → 401 Unauthorized
- Đơn giản, phù hợp cho MVP

**Code pattern:**
```python
from fastapi import FastAPI, HTTPException, Security
from fastapi.security import APIKeyHeader

api_key_header = APIKeyHeader(name="X-API-Key")

@app.get("/protected")
def protected_endpoint(api_key: str = Security(api_key_header)):
    if api_key != os.getenv("AGENT_API_KEY"):
        raise HTTPException(status_code=401, detail="Invalid API key")
    return {"message": "Success!"}
```

**Test:**

```bash
# ✅ Có key đúng → 200
curl.exe -X POST http://localhost:8000/ask \
  -H "X-API-Key: my-secret-key-123" \
  -H "Content-Type: application/json" \
  -d "{\"question\": \"Hello\"}"

# ❌ Không có key → 401
curl.exe -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d "{\"question\": \"Hello\"}"

# Expected response:
# {"detail":"Not authenticated"}
```

**Ưu/nhược:**
- ✅ Đơn giản, dễ implement
- ✅ Dễ rotate key (chỉ đổi env var)
- ❌ Không an toàn cho sub-accounts (tất cả dùng 1 key)
- ❌ Não có expiration

---

###  Exercise 4.2: JWT authentication (Advanced)

**Folder:** `04-api-gateway/production`

**JWT Flow:**
```
1. Client POST /token với username + password
   → Server trả token (ngắn hạn, có expiration)
2. Client dùng token ở header Authorization: Bearer <token>
3. Server verify token signature
4. Token expire → Client phải refresh
```

**Ưu điểm so với API Key:**
- ✅ Phân quyền (user vs admin tokens khác)
- ✅ Có expiration (tự expire sau N giờ)
- ✅ Có sub-accounts
- ✅ Stateless (server không lưu token)

**Code pattern:**

```python
from datetime import datetime, timedelta
import jwt
import os

SECRET_KEY = os.getenv("JWT_SECRET", "dev-key")
ALGORITHM = "HS256"
TOKEN_EXPIRE_MINUTES = 30

def create_token(username: str, role: str = "user"):
    """Tạo JWT token"""
    expires = datetime.utcnow() + timedelta(minutes=TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": username,
        "role": role,
        "exp": expires
    }
    encoded = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return encoded

@app.post("/token")
def login(username: str, password: str):
    """Get token"""
    if username == "admin" and password == "secret":
        token = create_token(username, role="admin")
        return {"access_token": token, "token_type": "bearer"}
    raise HTTPException(status_code=401, detail="Invalid credentials")

def verify_token(token: str = Depends(HTTPBearer())):
    """Verify JWT token"""
    try:
        payload = jwt.decode(token.credentials, SECRET_KEY, [ALGORITHM])
        username = payload.get("sub")
        return username
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.post("/ask")
def ask(question: str, current_user: str = Depends(verify_token)):
    """Protected endpoint"""
    return {"answer": f"Hi {current_user}, here's the answer..."}
```

**Test JWT:**

```bash
# 1. Lấy token
$response = Invoke-WebRequest -Uri http://localhost:8000/token `
  -Method POST `
  -Headers @{ "Content-Type" = "application/json" } `
  -Body '{"username": "admin", "password": "secret"}'

$token = ($response.Content | ConvertFrom-Json).access_token
echo $token

# 2. Dùng token để gọi API
$response = Invoke-WebRequest -Uri http://localhost:8000/ask `
  -Method POST `
  -Headers @{ 
    "Authorization" = "Bearer $token"
    "Content-Type" = "application/json" 
  } `
  -Body '{"question": "What is AI?"}'

$response.Content | ConvertFrom-Json
```

**Expected response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}

{
  "answer": "Hi admin, here's the answer..."
}
```

---

###  Exercise 4.3: Rate Limiting

**Concept:**
- Mỗi user được N requests/minute
- Sau N requests → 429 Too Many Requests
- Prevent DDoS, abuse, brute force

**Algorithm: Token Bucket**
```
Bucket = 10 requests
Refill rate = 10 requests/minute

User gọi API:
  - Bucket > 0 → consume 1 token, return 200
  - Bucket = 0 → return 429 (wait 6s để refill)
```

**Implement với Redis:**

```python
import redis
import time

r = redis.Redis(host="localhost", port=6379)

def check_rate_limit(user_id: str, limit: int = 10, window: int = 60):
    """Rate limiting using sliding window"""
    key = f"rate_limit:{user_id}"
    current = r.get(key)
    
    if current is None:
        r.setex(key, window, 1)
        return True
    
    if int(current) < limit:
        r.incr(key)
        return True
    
    return False

@app.post("/ask")
def ask(question: str):
    user_id = request.headers.get("X-User-ID", "anonymous")
    
    if not check_rate_limit(user_id, limit=10):
        raise HTTPException(
            status_code=429,
            detail={
                "error": "Rate limit exceeded",
                "limit": 10,
                "window": "60 seconds"
            }
        )
    
    return {"answer": "..."}
```

**Test rate limiting:**

```bash
# Gọi 12 lần liên tiếp
1..12 | ForEach-Object {
    Write-Host "Request $_"
    curl.exe -s -X POST http://localhost:8000/ask `
      -H "Content-Type: application/json" `
      -H "X-User-ID: user1" `
      -d "{\"question\": \"Test $_\"}"
    Start-Sleep -Milliseconds 100
}

# Expected:
# Request 1-10: 200 OK
# Request 11-12: 429 Too Many Requests
```

---

###  Exercise 4.4: Cost Guard

**Concept:**
- Mỗi user có budget $10/tháng
- Theo dõi spending per user
- Khi vượt → reject request

**Implement:**

```python
import redis
from datetime import datetime

r = redis.Redis(host="localhost", port=6379)

def check_budget(user_id: str, estimated_cost: float = 0.01):
    """Check if user still has budget"""
    month_key = datetime.now().strftime("%Y-%m")
    key = f"budget:{user_id}:{month_key}"
    
    current_spending = float(r.get(key) or 0)
    monthly_budget = 10.0  # $10/month
    
    if current_spending + estimated_cost > monthly_budget:
        raise HTTPException(
            status_code=402,  # 402 Payment Required
            detail={
                "error": "Budget exceeded",
                "spent": current_spending,
                "budget": monthly_budget
            }
        )
    
    # Deduct cost
    r.incrbyfloat(key, estimated_cost)
    r.expire(key, 32 * 86400)  # 32 days expiry
    
    return True

@app.post("/ask")
def ask(question: str, user_id: str):
    # Check budget first (before expensive LLM call)
    check_budget(user_id, estimated_cost=0.01)
    
    # Call LLM
    answer = llm.generate(question)
    
    return {"answer": answer}
```

**Test cost guard:**

```bash
# Mock scenario: Set spending to $9.99 (near limit)
redis-cli SET "budget:user1:2024-04" "9.99"

# Try to call API (costs $0.01 more)
curl.exe -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d "{\"question\": \"test\", \"user_id\": \"user1\"}"

# Expected: 402 Payment Required
```

---

###  Security Best Practices

| Practice | Tại sao | Cách làm |
|----------|--------|----------|
| **Never hardcode secrets** | Lộ lên GitHub | Dùng env vars, .env.local (gitignore) |
| **HTTPS only** | Decrypt traffic | Railway/Render tự SSL, dùng https:// |
| **Separate keys per env** | Dev keys khác prod | Env var khác sau khi deploy |
| **Rotate keys mỗi N tháng** | Key leak risk | Update env var + redeploy |
| **Log failed auth** | Detect attacks | Log 401/429 attempts |
| **Rate limiting** | DDoS protection | 10-100 req/min per user |

---

###  Checkpoint 4

- [x] Biết API Key authentication pattern
- [x] Hiểu JWT flow (token generation, verification, expiration)
- [x] Implement rate limiting với Redis
- [x] Implement cost guard (budget per user/month)
- [x] Know security best practices:
  - No hardcoded secrets
  - HTTPS + secret rotation
  - Rate limiting + budget checks
  - Proper error responses (401, 429, 402)

---

## Part 5: Scaling & Reliability (40 phút)

###  Concepts

**Vấn đề:** 1 instance không đủ khi có nhiều users.
- 1 instance = tối đa ~100 concurrent users
- Người dùng 1000+ → crash, 500 errors

**Giải pháp — 4 pillars:**
1. **Stateless Design** — State trong database, không trong memory
2. **Health Checks** — Platform biết khi nào restart
3. **Graceful Shutdown** — Complete current requests trước khi tắt
4. **Load Balancing** — Phân tán traffic tới N instances

---

###  Exercise 5.1: Health Checks

**Folder:** `05-scaling-reliability/develop`

**2 loại health checks:**

| Loại | Mục đích | Khi nào? |
|------|---------|---------|
| **Liveness** (`/health`) | Container còn sống không? | Mỗi 30s |
| **Readiness** (`/ready`) | Sẵn sàng nhận request không? | Startup, reset |

**Liveness check:**
```python
@app.get("/health")
def health():
    """Simple: process still alive"""
    return {
        "status": "ok",
        "uptime_seconds": time.time() - START_TIME
    }
```

Khi platform gọi `/health` mà không được response → restart container

**Readiness check:**
```python
import redis

@app.get("/ready")
def ready():
    """Check dependencies: Redis, DB, etc."""
    try:
        # Check Redis
        redis_client.ping()
        
        # Check database
        db.execute("SELECT 1")
        
        # All good
        return {"status": "ready", "timestamp": datetime.now()}
    except Exception as e:
        # Not ready yet (during startup, after crash)
        return JSONResponse(
            status_code=503,
            content={"status": "not ready", "reason": str(e)}
        )
```

Platform cách gọi `/ready` mỗi 10s:
- 503 Not Ready → đợi, không gửi traffic
- 200 Ready → start gửi traffic

**Railway/Render config:**

```toml
# railway.toml
[deploy]
healthcheckPath = "/health"
healthcheckTimeout = 30
```

```yaml
# render.yaml
services:
  - type: web
    healthCheckPath: /health
```

**Test locally:**

```bash
# Run app in background
python app.py &

# Check health
curl http://localhost:8000/health

# Check readiness
curl http://localhost:8000/ready

# Kill Redis → readiness fails
redis-cli shutdown
curl http://localhost:8000/ready
# Expected: 503 {"status": "not ready", "reason": "..."}
```

---

###  Exercise 5.2: Graceful Shutdown

**Problem:**
```
Normal shutdown:
  Platform: "Stop this container!"
  Container: *immediately stops*
  User A: "Connection refused" ❌
  
Graceful shutdown:
  Platform: "Stop this container (SIGTERM)"
  Container: 
    1. Stop accepting NEW requests
    2. Wait for current requests to finish
    3. Close DB connections
    4. Exit
  User A: Request completes ✅
```

**Implement:**

```python
import signal
import sys
import asyncio

# Global state
request_count = 0
is_shutting_down = False

def shutdown_handler(signum, frame):
    """Handle SIGTERM from orchestrator"""
    global is_shutting_down
    is_shutting_down = True
    
    logging.info("Shutdown signal received, going graceful...")
    
    # Give current requests 30s to finish
    time.sleep(30)
    
    # Force exit if not done
    sys.exit(0)

# Register handler
signal.signal(signal.SIGTERM, shutdown_handler)

@app.post("/ask")
async def ask(question: str):
    global request_count, is_shutting_down
    
    # Reject new requests during shutdown
    if is_shutting_down:
        raise HTTPException(
            status_code=503,
            detail="Server is shutting down"
        )
    
    request_count += 1
    try:
        # Do work
        answer = llm.generate(question)
        return {"answer": answer}
    finally:
        request_count -= 1

@app.get("/ready")
def ready():
    """Return 503 if shutting down"""
    if is_shutting_down:
        return JSONResponse(
            status_code=503,
            content={"status": "shutting_down"}
        )
    return {"status": "ready"}
```

**Test graceful shutdown:**

```bash
# Terminal 1: Start app
python app.py

# Terminal 2: Send request (will take 10 seconds)
$job = Start-Process -NoNewWindow -PassThru -CommandLine `
  'curl.exe -X POST http://localhost:8000/ask -H "Content-Type: application/json" -d "{\"question\": \"long task\"}"'

# Immediately after: Send SIGTERM
# On Windows
taskkill /PID $PID /GRACEFUL  # Not available on Windows, use Ctrl+C

# Platform wait: 30 seconds
# Expected: Request completes despite shutdown signal
```

---

###  Exercise 5.3: Stateless Design

**Problem: Stateful anti-pattern**
```python
# ❌ BAD: State dalam memory
conversation_history = {}

@app.post("/ask")
def ask(user_id: str, question: str):
    history = conversation_history.get(user_id, [])
    
    # Scale to 2 instances:
    # Instance 1: has history for user_id=123
    # Instance 2: has NO history for user_id=123
    # Load balancer sends request to Instance 2 → wrong answer! ❌
```

**Solution: Stateless + Redis**
```python
import redis

r = redis.Redis(host="redis", port=6379)

@app.post("/ask")
def ask(user_id: str, question: str):
    # Get state from Redis (all instances see same state)
    history_key = f"history:{user_id}"
    history = r.lrange(history_key, 0, -1)
    
    # Generate answer
    answer = llm.generate(question, history)
    
    # Save state back to Redis
    r.rpush(history_key, f"Q: {question}")
    r.rpush(history_key, f"A: {answer}")
    r.expire(history_key, 24 * 3600)  # Keep 24 hours
    
    return {"answer": answer}
```

**Architecture:**
```
Load Balancer
├─ Instance 1 (Python process)
│  ├─ Request from user A
│  └─ Get/set state in Redis
├─ Instance 2 (Python process)
│  ├─ Request from user B
│  └─ Get/set state in Redis
└─ Instance 3 (Python process)
   └─ Request from user A
      └─ Get SAME state from Redis ✅

Redis (single source of truth)
├─ history:user_a → ["Q1", "A1", "Q2", "A2"]
├─ history:user_b → ["Q1", "A1"]
└─ budget:user_a:2024-04 → 5.23
```

**Test stateless:**

```bash
# Start 2 instances
docker compose up --scale agent=2

# Make request to instance 1
curl.exe -X POST http://localhost:8000/ask \
  -H "X-User-ID: user1" \
  -d "{\"question\": \"What is AI?\"}"

# Kill instance 1
docker compose kill agent_1

# Make another request → goes to instance 2
# But gets SAME history from Redis ✅
curl.exe -X POST http://localhost:8000/ask \
  -H "X-User-ID: user1" \
  -d "{\"question\": \"What about ML?\"}"
```

---

###  Exercise 5.4: Load Balancing with Nginx

**Folder:** `05-scaling-reliability/production`

**docker-compose.yml - Nginx config:**

```yaml
services:
  agent:
    build: .
    environment:
      - REDIS_URL=redis://redis:6379
    depends_on:
      - redis
    # No port exposed directly
    # Only accessible via nginx

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - agent
```

**nginx.conf - Load balancing:**

```nginx
upstream agent_backend {
    # Round-robin load balancing
    server agent:8000;
    server agent:8001;
    server agent:8002;
}

server {
    listen 80;
    
    location /health {
        # Don't pass through upstream, respond directly
        access_log off;
        return 200 "ok";
    }
    
    location / {
        proxy_pass http://agent_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

**Start 3 instances:**

```bash
docker compose up --scale agent=3
```

**Expected output:**
```
[+] Running 5/5
 ✓ redis Created
 ✓ agent_1 Created
 ✓ agent_2 Created
 ✓ agent_3 Created
 ✓ nginx Created
```

**Verify load distribution:**

```bash
# Make 10 requests
1..10 | ForEach-Object {
    curl.exe -s -X POST http://localhost/ask `
      -H "Content-Type: application/json" `
      -d "{\"question\": \"Test\"}" | ConvertFrom-Json
    Write-Host "Request $_"
}

# Check logs → should see distribution
docker compose logs agent | findstr "Request"

# Example output:
# agent_1: Handling request
# agent_2: Handling request
# agent_3: Handling request
# ... (distributed)
```

---

###  Exercise 5.5: Test Stateless Resilience

**test_stateless.py:**

```python
import sys
import requests
import subprocess
import time

API_URL = "http://localhost/ask"
HEADERS = {"X-User-ID": "test-user", "Content-Type": "application/json"}

def test_stateless():
    # Step 1: Make request to instance 1
    print("1. Making request to instance 1...")
    data = {"question": "What is Docker?"}
    resp1 = requests.post(API_URL, json=data, headers=HEADERS)
    print(f"Response 1: {resp1.json()}")
    
    # Step 2: Check conversation saved in Redis
    print("2. Checking Redis for stored history...")
    resp_history = requests.get("http://redis:6379/history:test-user")
    print(f"History in Redis: {resp_history}")
    
    # Step 3: Kill instance 1
    print("3. Killing instance 1...")
    subprocess.run("docker compose kill agent_1", shell=True)
    time.sleep(2)
    
    # Step 4: Make another request → goes to instance 2/3
    print("4. Making request after killing instance 1...")
    data = {"question": "Tell me more"}
    resp2 = requests.post(API_URL, json=data, headers=HEADERS)
    print(f"Response 2: {resp2.json()}")
    
    # Step 5: Verify history still there
    print("5. Verifying history still exists...")
    resp_history = requests.get("http://redis:6379/history:test-user")
    print(f"History after kill: {resp_history}")
    
    if "Docker" in resp_history and "Tell me more" in resp_history:
        print("✅ TEST PASSED: Stateless design works!")
        return True
    else:
        print("❌ TEST FAILED: History was lost!")
        return False

if __name__ == "__main__":
    success = test_stateless()
    sys.exit(0 if success else 1)
```

**Run test:**

```bash
python test_stateless.py
```

---

###  Scaling Checklist

| Khía cạnh | Done | How to verify |
|-----------|------|---------------|
| **Health check** | ✅ | curl /health → 200 |
| **Readiness check** | ✅ | curl /ready → 200 (when ready), 503 (when not) |
| **Graceful shutdown** | ✅ | SIGTERM → finish current request → exit |
| **Stateless design** | ✅ | State in Redis, not memory |
| **Load balancing** | ✅ | 3+ instances, logs show distribution |
| **Persistence** | ✅ | Kill instance → data in Redis still there |

---

###  Checkpoint 5

- [x] Implement /health endpoint (liveness)
- [x] Implement /ready endpoint (readiness)
- [x] Implement graceful shutdown handler
- [x] Refactor code to store state in Redis
- [x] Setup Nginx load balancing (3+ instances)
- [x] Verify resilience:
  - Kill instance → traffic routes to others
  - Data persists in Redis
  - No user-visible downtime

---

## Part 6: Final Project (60 phút)

###  Objective

Build một production-ready AI agent từ đầu, kết hợp TẤT CẢ concepts đã học.

###  Requirements

**Functional:**
- [ ] Agent trả lời câu hỏi qua REST API
- [ ] Support conversation history
- [ ] Streaming responses (optional)

**Non-functional:**
- [ ] Dockerized với multi-stage build
- [ ] Config từ environment variables
- [ ] API key authentication
- [ ] Rate limiting (10 req/min per user)
- [ ] Cost guard ($10/month per user)
- [ ] Health check endpoint
- [ ] Readiness check endpoint
- [ ] Graceful shutdown
- [ ] Stateless design (state trong Redis)
- [ ] Structured JSON logging
- [ ] Deploy lên Railway hoặc Render
- [ ] Public URL hoạt động

### 🏗 Architecture

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│  Nginx (LB)     │
└──────┬──────────┘
       │
       ├─────────┬─────────┐
       ▼         ▼         ▼
   ┌──────┐  ┌──────┐  ┌──────┐
   │Agent1│  │Agent2│  │Agent3│
   └───┬──┘  └───┬──┘  └───┬──┘
       │         │         │
       └─────────┴─────────┘
                 │
                 ▼
           ┌──────────┐
           │  Redis   │
           └──────────┘
```

###  Step-by-step

#### Step 1: Project setup (5 phút)

```bash
mkdir my-production-agent
cd my-production-agent

# Tạo structure
mkdir -p app
touch app/__init__.py
touch app/main.py
touch app/config.py
touch app/auth.py
touch app/rate_limiter.py
touch app/cost_guard.py
touch Dockerfile
touch docker-compose.yml
touch requirements.txt
touch .env.example
touch .dockerignore
```

#### Step 2: Config management (10 phút)

**File:** `app/config.py`

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # TODO: Define all config
    # - PORT
    # - REDIS_URL
    # - AGENT_API_KEY
    # - LOG_LEVEL
    # - RATE_LIMIT_PER_MINUTE
    # - MONTHLY_BUDGET_USD
    pass

settings = Settings()
```

#### Step 3: Main application (15 phút)

**File:** `app/main.py`

```python
from fastapi import FastAPI, Depends, HTTPException
from .config import settings
from .auth import verify_api_key
from .rate_limiter import check_rate_limit
from .cost_guard import check_budget

app = FastAPI()

@app.get("/health")
def health():
    # TODO
    pass

@app.get("/ready")
def ready():
    # TODO: Check Redis connection
    pass

@app.post("/ask")
def ask(
    question: str,
    user_id: str = Depends(verify_api_key),
    _rate_limit: None = Depends(check_rate_limit),
    _budget: None = Depends(check_budget)
):
    # TODO: 
    # 1. Get conversation history from Redis
    # 2. Call LLM
    # 3. Save to Redis
    # 4. Return response
    pass
```

#### Step 4: Authentication (5 phút)

**File:** `app/auth.py`

```python
from fastapi import Header, HTTPException

def verify_api_key(x_api_key: str = Header(...)):
    # TODO: Verify against settings.AGENT_API_KEY
    # Return user_id if valid
    # Raise HTTPException(401) if invalid
    pass
```

#### Step 5: Rate limiting (10 phút)

**File:** `app/rate_limiter.py`

```python
import redis
from fastapi import HTTPException

r = redis.from_url(settings.REDIS_URL)

def check_rate_limit(user_id: str):
    # TODO: Implement sliding window
    # Raise HTTPException(429) if exceeded
    pass
```

#### Step 6: Cost guard (10 phút)

**File:** `app/cost_guard.py`

```python
def check_budget(user_id: str):
    # TODO: Check monthly spending
    # Raise HTTPException(402) if exceeded
    pass
```

#### Step 7: Dockerfile (5 phút)

```dockerfile
# TODO: Multi-stage build
# Stage 1: Builder
# Stage 2: Runtime
```

#### Step 8: Docker Compose (5 phút)

```yaml
# TODO: Define services
# - agent (scale to 3)
# - redis
# - nginx (load balancer)
```

#### Step 9: Test locally (5 phút)

```bash
docker compose up --scale agent=3

# Test all endpoints
curl http://localhost/health
curl http://localhost/ready
curl -H "X-API-Key: secret" http://localhost/ask -X POST \
  -H "Content-Type: application/json" \
  -d '{"question": "Hello", "user_id": "user1"}'
```

#### Step 10: Deploy (10 phút)

```bash
# Railway
railway init
railway variables set REDIS_URL=...
railway variables set AGENT_API_KEY=...
railway up

# Hoặc Render
# Push lên GitHub → Connect Render → Deploy
```

###  Validation

Chạy script kiểm tra:

```bash
cd 06-lab-complete
python check_production_ready.py
```

Script sẽ kiểm tra:
-  Dockerfile exists và valid
-  Multi-stage build
-  .dockerignore exists
-  Health endpoint returns 200
-  Readiness endpoint returns 200
-  Auth required (401 without key)
-  Rate limiting works (429 after limit)
-  Cost guard works (402 when exceeded)
-  Graceful shutdown (SIGTERM handled)
-  Stateless (state trong Redis, không trong memory)
-  Structured logging (JSON format)

###  Grading Rubric

| Criteria | Points | Description |
|----------|--------|-------------|
| **Functionality** | 20 | Agent hoạt động đúng |
| **Docker** | 15 | Multi-stage, optimized |
| **Security** | 20 | Auth + rate limit + cost guard |
| **Reliability** | 20 | Health checks + graceful shutdown |
| **Scalability** | 15 | Stateless + load balanced |
| **Deployment** | 10 | Public URL hoạt động |
| **Total** | 100 | |

---

##  Hoàn Thành!

Bạn đã:
-  Hiểu sự khác biệt dev vs production
-  Containerize app với Docker
-  Deploy lên cloud platform
-  Bảo mật API
-  Thiết kế hệ thống scalable và reliable

###  Next Steps

1. **Monitoring:** Thêm Prometheus + Grafana
2. **CI/CD:** GitHub Actions auto-deploy
3. **Advanced scaling:** Kubernetes
4. **Observability:** Distributed tracing với OpenTelemetry
5. **Cost optimization:** Spot instances, auto-scaling

###  Resources

- [12-Factor App](https://12factor.net/)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)
- [Railway Docs](https://docs.railway.app/)
- [Render Docs](https://render.com/docs)

---

##  Q&A

**Q: Tôi không có credit card, có thể deploy không?**  
A: Có! Railway cho $5 credit, Render có 750h free tier.

**Q: Mock LLM khác gì với OpenAI thật?**  
A: Mock trả về canned responses, không gọi API. Để dùng OpenAI thật, set `OPENAI_API_KEY` trong env.

**Q: Làm sao debug khi container fail?**  
A: `docker logs <container_id>` hoặc `docker exec -it <container_id> /bin/sh`

**Q: Redis data mất khi restart?**  
A: Dùng volume: `volumes: - redis-data:/data` trong docker-compose.

**Q: Làm sao scale trên Railway/Render?**  
A: Railway: `railway scale <replicas>`. Render: Dashboard → Settings → Instances.

---

**Happy Deploying! **

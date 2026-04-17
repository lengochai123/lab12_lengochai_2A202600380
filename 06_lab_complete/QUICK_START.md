# 🔥 Quick Start — Hướng Dẫn Nhanh (Việt Nam)

**Thời gian setup: 5 phút** ⏱️

## 1️⃣ Chạy Local (không Docker)

### Bước 1: Chuẩn bị

```bash
# Vào thư mục project
cd 06-lab-complete

# Tạo virtual environment
python -m venv venv

# Kích hoạt (Windows)
venv\Scripts\activate

# Kích hoạt (macOS/Linux)
source venv/bin/activate
```

### Bước 2: Cài đặt dependencies

```bash
pip install -r requirements.txt
```

### Bước 3: Thiết lập environment

```bash
# Copy template
cp .env.example .env

# Sửa file .env với editor yêu thích (VSCode, Notepad++, etc.)
# Cần sửa các giá trị sau:

# 1. AGENT_API_KEY (tạo giá trị ngẫu nhiên)
#    Ví dụ: abc123def456ghi789jkl012mno345pq

# 2. OPENAI_API_KEY (lấy từ OpenAI)
#    - Vào https://platform.openai.com/api-keys
#    - Click "Create new secret key"
#    - Copy: sk-...
```

### Bước 4: Chạy server

```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Xem output:
# INFO:     Uvicorn running on http://0.0.0.0:8000
# ✅ Server đã sẵn sàng!
```

### Bước 5: Test API (Terminal 2)

```bash
# Lấy API key từ .env
export API_KEY="your-api-key-from-env"

# Health check
curl http://localhost:8000/health

# Xem budget
curl -H "X-API-Key: $API_KEY" http://localhost:8000/budget

# Fire detection (nếu có ảnh)
curl -X POST http://localhost:8000/analyze \
  -H "X-API-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"image_base64":"iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==","user_id":"quicktest"}'
```

---

## 2️⃣ Chạy với Docker

### Bước 1: Setup environment

```bash
cp .env.example .env
# Sửa các giá trị trong .env
```

### Bước 2: Run với Docker Compose

```bash
# Tất cả trong 1 command!
docker compose up -d

# Output:
# [+] Running 3/3
#  ✔ Network fire-network Created
#  ✔ Container fire-redis Created
#  ✔ Container fire-detector Created
```

### Bước 3: Test

```bash
# Chờ ~10 giây để services khởi động
sleep 10

# Health check
curl http://localhost:8000/health

# View logs
docker compose logs -f fire-detector
```

### Bước 4: Dừng

```bash
docker compose down
```

---

## 3️⃣ Deploy Railway (5 phút)

### Bước 1: Push lên GitHub

```bash
git init
git add .
git commit -m "Fire detection system"
git remote add origin https://github.com/YOUR_USERNAME/fire-detection.git
git push -u origin main
```

### Bước 2: Deploy

1. Vào https://railway.app
2. Đăng nhập bằng GitHub
3. Click "New Project" → "Deploy from GitHub"
4. Select repo "fire-detection"
5. Railway sẽ build & deploy automaticly

### Bước 3: Cấu hình

1. Click service "fire-detector"
2. Click "Environment" tab
3. Thêm environment variables:
   - `AGENT_API_KEY`: your-secret-key
   - `OPENAI_API_KEY`: sk-...
   - `ENVIRONMENT`: production

4. Click "New Service" → thêm Redis

### Bước 4: Lấy URL & test

```bash
# Public URL ở phần ngoài cùng bên phải
# Ví dụ: https://fire-detection-prod.railway.app

curl https://fire-detection-prod.railway.app/health
```

---

## 4️⃣ Test Script

Sử dụng script test tự động:

```bash
# Chạy toàn bộ test suite
python test_api.py

# Output sẽ hiển thị:
# ✅ Health check passed
# ✅ Budget check passed
# ✅ Fire detection endpoint is working
# ... etc
```

---

## 🎯 Các câu lệnh hay dùng

### Lấy API Key

```bash
# macOS/Linux
export API_KEY=$(grep AGENT_API_KEY .env | cut -d= -f2)

# Windows PowerShell
$API_KEY = (Select-String -Path ".env" -Pattern "AGENT_API_KEY").ToString().Split("=")[1].Trim()

# Verify
echo $API_KEY
```

### Base64 encode ảnh

```bash
# macOS/Linux
cat image.jpg | base64

# Hoặc dùng Python
python -c "
import base64
with open('image.jpg', 'rb') as f:
    print(base64.b64encode(f.read()).decode())
"
```

### Xem logs

```bash
# Local (không Docker)
tail -f app/logs.log

# Docker
docker compose logs -f fire-detector

# Railway
railway logs

# Render
Render Dashboard → Logs tab
```

---

## ❓ Troubleshooting

| Lỗi | Giải pháp |
|-----|---------|
| `Connection refused` | API chưa chạy. Chạy: `python -m uvicorn app.main:app --reload` |
| `Invalid API key` | Kiểm tra AGENT_API_KEY trong .env |
| `YOLO model not found` | Download: `python -c "from ultralytics import YOLO; YOLO('yolov8m.pt')"` |
| `OpenAI error` | Kiểm tra OPENAI_API_KEY hợp lệ |
| `Rate limit exceeded` | Chờ 60 giây hoặc tăng RATE_LIMIT_PER_MINUTE |
| `Budget exceeded` | Tăng MONTHLY_BUDGET_USD |

---

## 📚 Bước tiếp theo

1. ✅ Chạy test script `python test_api.py`
2. ✅ Đọc [DEPLOYMENT.md](./DEPLOYMENT.md) để deploy production
3. ✅ Review code trong `app/` folder
4. ✅ Tùy chỉnh model YOLO cho case cụ thể
5. ✅ Kết nối với hệ thống của bạn

---

## 🆘 Cần giúp?

- 📖 Đọc [README.md](./README.md)
- 🚀 Xem [DEPLOYMENT.md](./DEPLOYMENT.md)
- 🧪 Chạy `python test_api.py`
- 💬 Xem comments trong code

---

**Chúc bạn thành công! 🎉**

Next: Read [DEPLOYMENT.md](./DEPLOYMENT.md) for production deployment.

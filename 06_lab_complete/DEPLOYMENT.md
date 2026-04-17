# Deployment Information

## Public URL
https://lab12-lengochai-2a202600380-ie87.onrender.com  <!-- Cập nhật URL này sau khi deploy thành công -->

## Platform
Railway / Render / Cloud Run  <!-- Giữ lại platform bạn sử dụng -->

## Test Commands

### Health Check
```bash
curl https://lab12-lengochai-2a202600380-ie87.onrender.com/health
# Expected: {"status": "ok", ...}
```

### API Test (with authentication)
```bash
curl -X POST https://lab12-lengochai-2a202600380-ie87.onrender.com/analyze \
  -H "X-API-Key: YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test", "image_base64": "<base64_string>"}'
```

## Environment Variables Set
- `PORT`
- `REDIS_URL`
- `AGENT_API_KEY`
- `OPENAI_API_KEY`
- `LOG_LEVEL`
- `RATE_LIMIT_PER_MINUTE` (Set to 10)
- `MONTHLY_BUDGET_USD` (Set to 10.0)

## Screenshots
- [ ] Deployment dashboard (Chụp màn hình dashboard Render/Railway khi deploy SUCCESS)
- [ ] Service running (Chụp màn hình logs server đang chạy ổn định)
- [ ] Test results (Chụp màn hình terminal chạy curl hoặc postman kết quả trả về 200 OK)

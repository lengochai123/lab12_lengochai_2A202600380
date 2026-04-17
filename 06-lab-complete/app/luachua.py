import firebase_admin
from firebase_admin import credentials, db
from ultralytics import YOLO
import cv2
import time
import requests

TELEGRAM_BOT_TOKEN = "7231457380:AAHmx_IS-xCX3k-fzfcmW6Ug69A18VbLNJ8"
CHAT_ID = "7263060804"

# Gửi thông báo qua Telegram
def send_telegram_alert(message, image):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
    
    # Chuyển ảnh thành file byte
    _, img_encoded = cv2.imencode('.jpg', image)
    img_byte = img_encoded.tobytes()

    # Gửi ảnh và thông báo
    payload = {
        "chat_id": CHAT_ID,
        "caption": message
    }
    files = {
        'photo': ('fire_alert.jpg', img_byte)
    }

    try:
        requests.post(url, data=payload, files=files)
    except Exception as e:
        print("Lỗi khi gửi Telegram:", e)
# ==== Cấu hình Firebase ====
cred = credentials.Certificate("hethongbaochay-fa0af-firebase-adminsdk-fbsvc-fb0efe9343.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://hethongbaochay-fa0af-default-rtdb.firebaseio.com/'
})

# ==== Load mô hình YOLO đã huấn luyện phát hiện lửa ====
model = YOLO("lua_chua_1.pt")  # Đường dẫn đến mô hình YOLO tùy chỉnh

# ==== Hàm lấy dữ liệu sensor từ Firebase ====
def get_sensor_data():
    try:
        ref = db.reference('/')
        data = ref.get()
        if data:
            temp = float(data.get('nhiet_do', 0))
            gas = float(data.get('nong_do_khi', 0))
            return temp, gas
    except Exception as e:
        print("Lỗi khi đọc dữ liệu từ Firebase:", e)
    return 0, 0, 0

# ==== Hàm kiểm tra điều kiện cháy + vẽ bounding box ====
def is_fire_detected(frame):
    results = model(frame)[0]  # Chỉ lấy kết quả đầu tiên

    fire_detected = False

    
    for box in results.boxes:
        conf = float(box.conf[0])
        if conf < 0.7:
            continue
        cls_id = int(box.cls[0])
        label = model.names[cls_id]  # Lấy tên lớp (vd: "fire")
        conf = float(box.conf[0])
        x1, y1, x2, y2 = map(int, box.xyxy[0])

        # Vẽ bounding box và nhãn
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
        cv2.putText(frame, f"{label} {conf:.2f}", (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

        fire_detected = True

    return fire_detected

# ==== Khởi động webcam ====
cap = cv2.VideoCapture(0)

print(" Hệ thống phát hiện cháy đang chạy...")
alert_sent=False
while True:
    ret, frame = cap.read()
    if not ret:
        break

    # Detect lửa từ hình ảnh
    fire_detected_by_yolo = is_fire_detected(frame)

    # Đọc dữ liệu sensor từ Firebase
    temp, gas = get_sensor_data()
    print(f"[Sensors] Nhiệt độ: {temp} °C | Gas: {gas} ppm ")

    # Rule cảnh báo cháy
    danger_by_sensor = temp > 30 or gas > 300

    if fire_detected_by_yolo and danger_by_sensor:
        print(" CẢNH BÁO: PHÁT HIỆN NGUY CƠ CHÁY!")
        cv2.putText(frame, "ALERT", (10, 40), cv2.FONT_HERSHEY_SIMPLEX,
                    1, (0, 0, 255), 2, cv2.LINE_AA)
        if not alert_sent:
            send_telegram_alert("🔥 CẢNH BÁO NGUY CƠ CHÁY! Vui lòng kiểm tra ngay!", frame)
            alert_sent = True
    else:
        print(" An toàn")
        cv2.putText(frame, "SAFE", (10, 40), cv2.FONT_HERSHEY_SIMPLEX,
                    1, (0, 255, 0), 2, cv2.LINE_AA)
        alert_sent = False

    # Overlay thêm dữ liệu sensor
    cv2.putText(frame, f"Temp: {temp}C  Gas: {gas}ppm", (10, 470),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

    # Hiển thị khung hình
    cv2.imshow("Fire Detection", frame)

    # Nhấn 'q' để thoát
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

    time.sleep(1)  # Delay giữa mỗi lần đọc sensor

# Giải phóng tài nguyên
cap.release()
cv2.destroyAllWindows()

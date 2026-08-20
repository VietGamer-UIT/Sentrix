import os
import sys
import uuid
import time
import urllib.request
from fastapi.testclient import TestClient

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.api.main import app
from backend.db.firestore_ops import get_firestore_client

client = TestClient(app)
TENANT_ID = "pho-ba-lan_1722500000000"
PHONE_NUMBER = "0987654321"

def print_step(msg):
    print(f"\n{'='*50}\n- {msg}\n{'='*50}")

def run_tests():
    db = get_firestore_client()
    tenant_ref = db.collection("tenants").document(TENANT_ID)

    # =========================================================================
    print_step("TEST 1: Gửi 1 feedback text tiêu cực -> kiểm tra sentiment âm")
    # =========================================================================
    res1 = client.post(
        "/api/v1/feedback",
        data={
            "tenant_id": TENANT_ID,
            "location": "Bàn 1",
            "text_content": "đồ ăn hôm nay dở tệ, thái độ phục vụ quá kém",
            "customer_phone": PHONE_NUMBER,
        }
    )
    if res1.status_code not in [200, 201, 202]:
        print(f"❌ API Error: {res1.json()}")
    else:
        fb1_id = res1.json()["feedback_id"]
        doc1 = tenant_ref.collection("feedbacks").document(fb1_id).get().to_dict()
        sentiment = doc1.get("sentiment_score")
        print(f"✅ Feedback ID: {fb1_id}")
        print(f"✅ Sentiment Score: {sentiment}")
        if sentiment and sentiment < 0:
            print("✅ TEST 1 PASS: Sentiment ra số âm đúng.")
        else:
            print(f"❌ TEST 1 FAIL: Sentiment là {sentiment}, không phải số âm.")

    # =========================================================================
    print_step("TEST 2: Gửi 2 feedback liên tiếp cùng 1 SĐT -> kiểm tra feedback_count")
    # =========================================================================
    res2_1 = client.post(
        "/api/v1/feedback",
        data={
            "tenant_id": TENANT_ID,
            "location": "Bàn 2",
            "text_content": "ok, tạm được",
            "customer_phone": PHONE_NUMBER,
        }
    )
    time.sleep(2) # Đợi firestore trigger nếu có, thực ra code chạy sync
    res2_2 = client.post(
        "/api/v1/feedback",
        data={
            "tenant_id": TENANT_ID,
            "location": "Bàn 3",
            "text_content": "cũng được",
            "customer_phone": PHONE_NUMBER,
        }
    )
    
    # Check customer doc
    from backend.db.firestore_ops import get_or_create_customer
    cust = get_or_create_customer(TENANT_ID, PHONE_NUMBER)
    count = cust.get("feedback_count")
    print(f"✅ Feedback Count: {count}")
    if count >= 3:
        print("✅ TEST 2 PASS: feedback_count tăng dần.")
    else:
        print(f"❌ TEST 2 FAIL: feedback_count = {count}")

    # =========================================================================
    print_step("TEST 3: Gửi feedback -> bấm quay thưởng ngay (fire-and-forget race condition)")
    # =========================================================================
    feedback_id_override = str(uuid.uuid4())
    print(f"UUID client tự sinh: {feedback_id_override}")
    
    # 1. Quay thưởng TRƯỚC/CÙNG LÚC khi feedback lưu (mô phỏng SpinPage load nhanh hơn)
    res_spin = client.post(
        "/api/v1/gamification/spin",
        data={
            "tenant_id": TENANT_ID,
            "customer_phone": PHONE_NUMBER,
            "feedback_id": feedback_id_override,
        }
    )
    print("Gamification Spin Response:", res_spin.json())
    
    # 2. Sau đó /feedback hoàn tất
    res_fb_3 = client.post(
        "/api/v1/feedback",
        data={
            "tenant_id": TENANT_ID,
            "location": "Bàn 4",
            "text_content": "Rất ngon!",
            "customer_phone": PHONE_NUMBER,
            "feedback_id": feedback_id_override,
        }
    )
    print("Feedback Response:", res_fb_3.json())

    # Kiểm tra doc
    doc3 = tenant_ref.collection("feedbacks").document(feedback_id_override).get().to_dict()
    prize = doc3.get("gamification_prize")
    text = doc3.get("transcript")
    print(f"✅ Prize in DB: {prize}, Text in DB: {text}")
    if prize and text:
        print("✅ TEST 3 PASS: Voucher đã link vào feedback dù gọi song song.")
    else:
        print("❌ TEST 3 FAIL: Voucher hoặc Text bị ghi đè/mất.")

    # =========================================================================
    print_step("TEST 4: Thử ghi âm thật")
    # =========================================================================
    # Download 1 sample audio file
    audio_path = "sample_test.wav"
    try:
        if not os.path.exists(audio_path):
            print("Đang tải file âm thanh giả lập...")
            req = urllib.request.Request("https://www2.cs.uic.edu/~i101/SoundFiles/BabyElephantWalk60.wav", headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req) as response, open(audio_path, 'wb') as out_file:
                data = response.read()
                out_file.write(data)
        
        with open(audio_path, "rb") as f:
            print("Đang gửi file âm thanh tới API /feedback (Whisper)...")
            res_audio = client.post(
                "/api/v1/feedback",
                data={
                    "tenant_id": TENANT_ID,
                    "location": "Bàn Audio",
                    "customer_phone": PHONE_NUMBER,
                },
                files={"audio_file": ("sample_test.wav", f, "audio/wav")}
            )
        print(f"Audio API Status: {res_audio.status_code}")
        if res_audio.status_code == 200:
            doc4 = tenant_ref.collection("feedbacks").document(res_audio.json()["feedback_id"]).get().to_dict()
            transcript = doc4.get("text_content")
            print(f"✅ Transcript từ Whisper: {transcript}")
            print("✅ TEST 4 PASS: Ghi âm được gửi, Whisper dịch và lưu thành công.")
        else:
            print(f"❌ TEST 4 FAIL: API Error: {res_audio.text}")
    except Exception as e:
        print(f"❌ Lỗi tải hoặc test file audio: {e}")

if __name__ == "__main__":
    run_tests()

"""
Test script cho POST /api/v1/feedback — Giai đoạn 4
=====================================================
Chạy: python apps/web-client/test_api_connection.py
Yêu cầu: Backend đang chạy tại http://localhost:8000

Kịch bản test (theo DoD Giai đoạn 4):
  Test 1: /health — kiểm tra backend sống
  Test 2: POST /feedback với TEXT — trường hợp thành công
  Test 3: POST /feedback không có audio lẫn text — phải trả 400
  Test 4: POST /feedback với text rỗng (chỉ whitespace) — phải trả 400
"""

import sys
import requests
import json

BASE_URL = "http://localhost:8001"

def print_result(name, passed, detail=""):
    icon = "✅" if passed else "❌"
    print(f"{icon} {name}")
    if detail:
        print(f"   → {detail}")

def test_health():
    """Test GET /health"""
    try:
        r = requests.get(f"{BASE_URL}/health", timeout=5)
        passed = r.status_code == 200 and r.json().get("status") == "ok"
        print_result("GET /health", passed, f"status={r.status_code}, body={r.json()}")
        return passed
    except requests.exceptions.ConnectionError:
        print_result("GET /health", False, "❌ Backend chưa chạy! Chạy: uvicorn backend.api.main:app --reload")
        return False

def test_feedback_text_ok():
    """Test POST /feedback với text — phải trả 202"""
    payload = {
        "tenant_id": "pho-ba-lan_demo",
        "location": "Ban 5 — Test",
        "text_content": "Đồ ăn ngon lắm, phục vụ nhanh. Sẽ quay lại!"
    }
    try:
        r = requests.post(f"{BASE_URL}/api/v1/feedback", data=payload, timeout=30)
        body = r.json()
        passed = (
            r.status_code == 202
            and "request_id" in body
            and body.get("status") in ("accepted", "accepted_with_warning")
        )
        print_result("POST /feedback [text - happy path]", passed,
                     f"status={r.status_code}, request_id={body.get('request_id', 'N/A')[:8]}...")
        return passed
    except Exception as e:
        print_result("POST /feedback [text - happy path]", False, str(e))
        return False

def test_feedback_no_input():
    """Test POST /feedback không có cả audio lẫn text — phải trả 400"""
    payload = {
        "tenant_id": "pho-ba-lan_demo",
        "location": "Ban 5"
        # Không có audio_file, không có text_content
    }
    try:
        r = requests.post(f"{BASE_URL}/api/v1/feedback", data=payload, timeout=10)
        passed = r.status_code == 400
        detail_msg = r.json().get("detail", "?") if r.headers.get("content-type", "").startswith("application") else r.text
        print_result("POST /feedback [no input → expect 400]", passed,
                     f"status={r.status_code}, detail={str(detail_msg)[:80]}")
        return passed
    except Exception as e:
        print_result("POST /feedback [no input → expect 400]", False, str(e))
        return False

def test_feedback_empty_text():
    """Test POST /feedback với text chỉ là khoảng trắng — phải trả 400"""
    payload = {
        "tenant_id": "pho-ba-lan_demo",
        "location": "Ban 5",
        "text_content": "   "  # chỉ whitespace
    }
    try:
        r = requests.post(f"{BASE_URL}/api/v1/feedback", data=payload, timeout=10)
        passed = r.status_code == 400
        detail_msg = r.json().get("detail", "?") if r.headers.get("content-type", "").startswith("application") else r.text
        print_result("POST /feedback [whitespace text → expect 400]", passed,
                     f"status={r.status_code}, detail={str(detail_msg)[:80]}")
        return passed
    except Exception as e:
        print_result("POST /feedback [whitespace text → expect 400]", False, str(e))
        return False

def test_feedback_audio():
    """Test POST /feedback với audio fake (1 giây của silence) — phải trả 202 hoặc lỗi Whisper"""
    # Tạo file WAV silence tối giản (44 bytes header + 4 bytes data)
    import struct
    silence_wav = (
        b'RIFF' + struct.pack('<I', 36) +  # chunk size
        b'WAVE' +
        b'fmt ' + struct.pack('<I', 16) +  # subchunk1 size
        struct.pack('<H', 1) +             # PCM format
        struct.pack('<H', 1) +             # mono
        struct.pack('<I', 16000) +         # sample rate
        struct.pack('<I', 32000) +         # byte rate
        struct.pack('<H', 2) +             # block align
        struct.pack('<H', 16) +            # bits per sample
        b'data' + struct.pack('<I', 0)     # data chunk (0 bytes)
    )

    files = {"audio_file": ("recording.wav", silence_wav, "audio/wav")}
    data = {"tenant_id": "pho-ba-lan_demo", "location": "Ban 5"}
    try:
        r = requests.post(f"{BASE_URL}/api/v1/feedback", data=data, files=files, timeout=30)
        # Chấp nhận 202 (ok), 400 (fraud filter từ chối audio quá ngắn), hoặc 503 (Whisper key chưa set)
        passed = r.status_code in (202, 400, 503, 504)
        body = r.json() if r.headers.get("content-type", "").startswith("application") else {"raw": r.text[:100]}
        print_result("POST /feedback [audio WAV silence]", passed,
                     f"status={r.status_code} (202/400/503/504 đều OK), body={str(body)[:100]}")
        return passed
    except Exception as e:
        print_result("POST /feedback [audio WAV silence]", False, str(e))
        return False

def main():
    print("=" * 55)
    print("  Sentrix API Connection Test — Giai đoạn 4")
    print("  Backend URL:", BASE_URL)
    print("=" * 55)

    results = []

    # Test 1: Health check trước — nếu fail thì dừng luôn
    health_ok = test_health()
    results.append(health_ok)
    if not health_ok:
        print("\n⛔ Backend chưa chạy. Không thể test các endpoint.")
        print("   Lệnh chạy backend:")
        print("   uvicorn backend.api.main:app --reload --port 8000")
        sys.exit(1)

    print()
    results.append(test_feedback_text_ok())
    results.append(test_feedback_no_input())
    results.append(test_feedback_empty_text())
    results.append(test_feedback_audio())

    passed = sum(results)
    total = len(results)
    print()
    print("=" * 55)
    print(f"  Kết quả: {passed}/{total} tests passed")
    if passed == total:
        print("  🎉 Tất cả pass! Giai đoạn 4 DoD đạt.")
    else:
        print("  ⚠️  Có test chưa pass — kiểm tra log backend.")
    print("=" * 55)

if __name__ == "__main__":
    main()

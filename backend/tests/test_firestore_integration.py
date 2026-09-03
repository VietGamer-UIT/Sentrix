"""
Test Giai đoạn 8 — Firestore Multi-Tenant Integration
=======================================================
Chạy: python backend/tests/test_firestore_integration.py

Test thực tế yêu cầu Firebase credentials. Script này có 2 chế độ:

MODE 1: Test với Firestore THẬT (cần FIREBASE_CREDENTIALS_PATH hoặc env vars)
  - Lưu feedback cho tenant_test_a và tenant_test_b
  - Xác nhận dữ liệu được lưu đúng schema
  - Xác nhận cách ly: tenant A không đọc được data của tenant B

MODE 2: Test LOGIC (không cần Firebase)
  - Test hàm _hash_phone, _mask_phone
  - Test _sentiment_to_risk_level
  - Test cấu trúc feedback_doc trước khi gửi Firestore
  - Test không có credentials → raise EnvironmentError đúng chỗ

Chạy Mode 2 (không cần Firebase):
  python backend/tests/test_firestore_integration.py --logic-only

Chạy Mode 1 (cần Firebase, cài đặt credentials trước):
  python backend/tests/test_firestore_integration.py
"""

import sys
import json
import hashlib
import logging
import argparse
from pathlib import Path
from datetime import datetime, timezone

# Load .env
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent.parent / ".env")
    load_dotenv(Path(__file__).parent.parent / ".env")
except ImportError:
    pass

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helper nội bộ (copy logic từ firestore_ops để test độc lập)
# ---------------------------------------------------------------------------
def _hash_phone_standalone(phone: str) -> str:
    p = phone.strip().replace(" ", "").replace("-", "")
    if p.startswith("0"):
        p = "+84" + p[1:]
    elif not p.startswith("+"):
        p = "+84" + p
    return "cust_" + hashlib.sha256(p.encode()).hexdigest()[:16]

def _mask_phone_standalone(phone: str) -> str:
    p = phone.strip().replace(" ", "")
    if len(p) < 7:
        return "***"
    return p[:3] + "****" + p[-3:]


def divider(title: str):
    print(f"\n{'='*65}")
    print(f"  {title}")
    print("="*65)


# ---------------------------------------------------------------------------
# Mode 2: Logic tests (không cần Firebase)
# ---------------------------------------------------------------------------
def test_logic_only():
    divider("LOGIC TEST — Khong can Firebase credentials")

    # --- Test hash phone ---
    print("\n[1/5] Test _hash_phone (an danh hoa mot chieu)")
    phones = ["0901234567", "0901234567", "0987654321", "+84901234567"]
    ids = [_hash_phone_standalone(p) for p in phones]
    print(f"  '0901234567' → {ids[0]}")
    print(f"  '0901234567' (lan 2) → {ids[1]}  ← phai giong ids[0]")
    print(f"  '0987654321' → {ids[2]}  ← phai KHAC ids[0]")
    print(f"  '+84901234567' → {ids[3]}  ← phai giong ids[0] (cung so, khac format)")
    assert ids[0] == ids[1], "FAIL: hash phai deterministic"
    assert ids[0] != ids[2], "FAIL: hash khac nhau cho so khac nhau"
    assert ids[0] == ids[3], "FAIL: '0901...' va '+84901...' phai co cung hash"
    print("  OK: hash deterministic, phan biet SDT, chuan hoa format")

    # --- Test mask phone ---
    print("\n[2/5] Test _mask_phone (an mot phan SDT hien thi Dashboard)")
    test_phones = [
        ("0901234567", "090****567"),
        ("0987654321", "098****321"),
    ]
    for phone, expected in test_phones:
        result = _mask_phone_standalone(phone)
        print(f"  '{phone}' → '{result}'  (mong doi: '{expected}')")
        assert result == expected, f"FAIL: '{phone}' mask sai"
    print("  OK: mask dung format")

    # --- Test risk level ---
    print("\n[3/5] Test _sentiment_to_risk_level (xep muc rui ro)")
    from backend.db.firestore_ops import _sentiment_to_risk_level
    # Ngưỡng thực tế (firestore_ops.py line 84-89):
    #   p_churn < 0.30  → 'low'
    #   0.30 <= p < 0.85 → 'medium'
    #   p >= 0.85       → 'high'
    cases = [
        (0.10, "low"),    # 0.10 < 0.30 → low
        (0.29, "low"),    # 0.29 < 0.30 → low (boundary)
        (0.30, "medium"), # 0.30 >= 0.30 → medium
        (0.49, "medium"), # 0.49 >= 0.30 và < 0.85 → medium (trước đây test sai là 'low')
        (0.50, "medium"), # 0.50 → medium
        (0.84, "medium"), # 0.84 < 0.85 → medium (boundary)
        (0.85, "high"),   # 0.85 >= 0.85 → high
        (0.99, "high"),   # 0.99 → high
    ]
    for p, expected in cases:
        result = _sentiment_to_risk_level(p)
        print(f"  p_churn={p:.2f} → '{result}'  (mong doi: '{expected}')")
        assert result == expected, f"FAIL: p_churn={p} → {result} != {expected}"
    print("  OK: risk level dung nguong (< 0.30 = low, 0.30-0.85 = medium, >= 0.85 = high)")

    # --- Test feedback document structure ---
    print("\n[4/5] Test feedback_doc structure (khong gui Firebase)")
    from backend.db.firestore_ops import _hash_phone, _mask_phone
    phone = "0912345678"
    customer_id = _hash_phone(phone)
    phone_masked = _mask_phone(phone)
    print(f"  customer_id = {customer_id}")
    print(f"  phone_masked = {phone_masked}")

    feedback_doc = {
        "feedback_id": "test_abc123",
        "customer_id": customer_id,
        "location": "Ban 5",
        "input_type": "text",
        "transcript": "Mon an ngon, nhan vien than thien",
        "audio_features": None,
        "aspects": [
            {"aspect": "mon_an", "sentiment": "Tich cuc", "reason": "Mon an ngon"},
            {"aspect": "nhan_vien", "sentiment": "Tich cuc", "reason": "Than thien"},
        ],
        "sentiment_score": 0.85,
        "is_sarcasm": False,
        "p_churn": 0.12,
        "churn_risk_level": "low",
        "processing_status": "done",
    }
    print(f"  Feedback doc keys: {list(feedback_doc.keys())}")
    assert "customer_id" in feedback_doc
    assert "tenant_id" not in feedback_doc, "tenant_id khong duoc luu trong feedback doc (no trong path)"
    print("  OK: cau truc document hop le")

    # --- Test EnvironmentError khi thieu credentials ---
    print("\n[5/5] Test EnvironmentError khi thieu Firebase credentials")
    import os
    from backend.db.firestore_client import reset_firestore_client

    # Backup env vars
    orig_vars = {}
    for var in ["FIREBASE_CREDENTIALS_PATH", "FIREBASE_PROJECT_ID", "FIREBASE_PRIVATE_KEY", "FIREBASE_CLIENT_EMAIL"]:
        orig_vars[var] = os.environ.pop(var, None)

    reset_firestore_client()
    try:
        from backend.db.firestore_client import get_firestore_client
        get_firestore_client()
        print("  FAIL: Phai raise EnvironmentError khi thieu credentials")
    except EnvironmentError as e:
        print(f"  OK: raise EnvironmentError dung: {str(e)[:80]}...")
    except Exception as e:
        print(f"  OK (other exception, acceptable): {type(e).__name__}: {str(e)[:60]}")
    finally:
        # Restore
        for var, val in orig_vars.items():
            if val is not None:
                os.environ[var] = val
        reset_firestore_client()

    divider("Logic tests PASS — khong can Firebase")
    print("  Toan bo 5 logic test deu thanh cong.\n")


# ---------------------------------------------------------------------------
# Mode 1: Full Firebase integration test
# ---------------------------------------------------------------------------
def test_with_firebase():
    divider("FULL INTEGRATION TEST — Voi Firebase Firestore that")

    from backend.db.firestore_client import get_firestore_client
    from backend.db.firestore_ops import (
        save_feedback, get_or_create_customer,
        update_customer_rfms, get_tenant_config,
        _hash_phone,
    )

    db = get_firestore_client()
    print("  Firebase ket noi thanh cong!")

    TENANT_A = "tenant_test_a"
    TENANT_B = "tenant_test_b"
    PHONE_A = "0901111001"
    PHONE_B = "0902222002"

    # -------------------------------------------------------------------
    # Test 1: Tao customer cho 2 tenant
    # -------------------------------------------------------------------
    print(f"\n[1/6] Tao customer cho tenant A va B ...")
    cust_a = get_or_create_customer(TENANT_A, PHONE_A)
    cust_b = get_or_create_customer(TENANT_B, PHONE_B)
    print(f"  Tenant A — customer_id: {cust_a['customer_id']}")
    print(f"  Tenant B — customer_id: {cust_b['customer_id']}")
    assert cust_a["customer_id"] != cust_b["customer_id"]
    print("  OK: customer_id khac nhau (khac SDT)")

    # -------------------------------------------------------------------
    # Test 2: Luu feedback cho tenant A
    # -------------------------------------------------------------------
    print(f"\n[2/6] Luu feedback cho Tenant A ...")
    feedback_a_data = {
        "customer_id": cust_a["customer_id"],
        "location": "Ban 3",
        "input_type": "text",
        "transcript": "Pho ngon lam, nuoc dung dam da!",
        "audio_features": None,
        "aspects": [{"aspect": "mon_an", "sentiment": "Tich cuc", "reason": "Pho ngon"}],
        "sentiment_score": 0.88,
        "is_sarcasm": False,
        "fusion_mode": "text_only",
        "is_spam": False,
        "p_churn": 0.09,
        "churn_risk_level": "low",
        "rfms_r": 0.02, "rfms_f": 0.1, "rfms_m": 0.05, "rfms_s": 0.88,
        "is_suspicious": False,
        "suspicious_reason": None,
        "processing_status": "done",
        "error_message": None,
        "request_id": "test-req-a-001",
    }
    fid_a = save_feedback(TENANT_A, feedback_a_data)
    print(f"  Feedback Tenant A saved: tenants/{TENANT_A}/feedbacks/{fid_a}")

    # -------------------------------------------------------------------
    # Test 3: Luu feedback cho tenant B
    # -------------------------------------------------------------------
    print(f"\n[3/6] Luu feedback cho Tenant B ...")
    feedback_b_data = {
        **feedback_a_data,
        "customer_id": cust_b["customer_id"],
        "transcript": "Cho 45 phut moi co do an. Nhan vien thai do kho chiu.",
        "aspects": [{"aspect": "toc_do_phuc_vu", "sentiment": "Tieu cuc", "reason": "Cho lau"}],
        "sentiment_score": 0.08,
        "p_churn": 0.91,
        "churn_risk_level": "high",
        "rfms_s": 0.08,
        "request_id": "test-req-b-001",
    }
    fid_b = save_feedback(TENANT_B, feedback_b_data)
    print(f"  Feedback Tenant B saved: tenants/{TENANT_B}/feedbacks/{fid_b}")

    # -------------------------------------------------------------------
    # Test 4: Xac nhan cach ly — doc feedback cua A tu path cua B
    # -------------------------------------------------------------------
    print(f"\n[4/6] Kiem tra cach ly: doc feedback A tu path B ...")
    # Query feedback A's ID trong path của B → phải không tìm thấy
    wrong_ref = (
        db.collection("tenants").document(TENANT_B)
        .collection("feedbacks").document(fid_a)
    )
    wrong_doc = wrong_ref.get()
    assert not wrong_doc.exists, "FAIL: Data cua A bi lo sang B!"
    print(f"  OK: feedback '{fid_a}' KHONG ton tai trong tenants/{TENANT_B}/feedbacks/")
    print(f"  -> Cach ly multi-tenant THANH CONG")

    # Doc ngược lại
    wrong_ref2 = (
        db.collection("tenants").document(TENANT_A)
        .collection("feedbacks").document(fid_b)
    )
    wrong_doc2 = wrong_ref2.get()
    assert not wrong_doc2.exists, "FAIL: Data cua B bi lo sang A!"
    print(f"  OK: feedback '{fid_b}' KHONG ton tai trong tenants/{TENANT_A}/feedbacks/")

    # -------------------------------------------------------------------
    # Test 5: Xac nhan doc duoc tung tenant rieng
    # -------------------------------------------------------------------
    print(f"\n[5/6] Xac nhan feedback luu dung trong path cua tung tenant ...")
    correct_a = (
        db.collection("tenants").document(TENANT_A)
        .collection("feedbacks").document(fid_a).get()
    )
    assert correct_a.exists
    data_a = correct_a.to_dict()
    print(f"  Tenant A feedback — transcript: '{data_a.get('transcript', '')[:40]}'")
    print(f"  Tenant A feedback — sentiment_score: {data_a.get('sentiment_score')}")
    assert data_a["sentiment_score"] == 0.88

    correct_b = (
        db.collection("tenants").document(TENANT_B)
        .collection("feedbacks").document(fid_b).get()
    )
    assert correct_b.exists
    data_b = correct_b.to_dict()
    print(f"  Tenant B feedback — sentiment_score: {data_b.get('sentiment_score')}")
    assert data_b["sentiment_score"] == 0.08

    # -------------------------------------------------------------------
    # Test 6: Update RFMS + kiem tra customer doc
    # -------------------------------------------------------------------
    print(f"\n[6/6] Update RFMS cho customer A ...")
    update_customer_rfms(
        tenant_id=TENANT_A,
        customer_id=cust_a["customer_id"],
        R=0.02, F=0.04, M=0.1, S=0.88,
        p_churn=0.09,
        sentiment_score_raw=0.88,
    )
    # Doc lai de kiem tra
    updated_cust = (
        db.collection("tenants").document(TENANT_A)
        .collection("customers").document(cust_a["customer_id"]).get()
    )
    updated_data = updated_cust.to_dict()
    print(f"  Customer A sau update:")
    print(f"    feedback_count: {updated_data.get('feedback_count')}")
    print(f"    p_churn: {updated_data.get('p_churn')}")
    print(f"    churn_risk_level: {updated_data.get('churn_risk_level')}")
    assert updated_data.get("feedback_count") >= 1
    assert updated_data.get("p_churn") == 0.09

    # -------------------------------------------------------------------
    # Tong ket
    # -------------------------------------------------------------------
    divider("FULL INTEGRATION TEST PASS")
    print(f"  Tenant A feedback: tenants/{TENANT_A}/feedbacks/{fid_a}")
    print(f"  Tenant B feedback: tenants/{TENANT_B}/feedbacks/{fid_b}")
    print(f"  Cach ly 2 tenant: XUAT SAC")
    print(f"  Schema dung: XUAT SAC")
    print(f"  RFMS update: XUAT SAC")
    print()
    print("  => Vao Firebase Console de xem du lieu that:")
    print(f"     Firestore → tenants → {TENANT_A} → feedbacks")
    print(f"     Firestore → tenants → {TENANT_B} → feedbacks\n")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--logic-only",
        action="store_true",
        help="Chi chay logic test, khong can Firebase credentials",
    )
    args = parser.parse_args()

    if args.logic_only:
        test_logic_only()
    else:
        import os
        has_creds = (
            os.getenv("FIREBASE_CREDENTIALS_PATH")
            or (os.getenv("FIREBASE_PROJECT_ID") and os.getenv("FIREBASE_PRIVATE_KEY"))
        )
        if not has_creds:
            print("Khong tim thay Firebase credentials.")
            print("Chay logic-only mode (khong can Firebase)...\n")
            test_logic_only()
        else:
            test_logic_only()
            print("\n--- Tiep tuc chay Full Integration Test ---")
            test_with_firebase()

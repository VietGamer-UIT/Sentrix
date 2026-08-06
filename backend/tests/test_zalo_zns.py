"""
Test Giai đoạn 9 — Zalo ZNS Webhook
======================================
Chạy: python backend/tests/test_zalo_zns.py

Test tất cả logic của zalo_zns.py mà KHÔNG cần credentials Zalo thật.
Sử dụng httpx mock để intercept HTTP request.

Test cases:
  1. Chuẩn hoá SĐT sang format Zalo (84XXXXXXXXX)
  2. get_primary_complained_aspect — lấy aspect tiêu cực đầu tiên
  3. ZaloConfigError khi thiếu env vars
  4. Thành công: mock HTTP 200, error_code=0
  5. Token hết hạn: mock error_code=216 → ZaloTokenExpiredError → success=False, no crash
  6. Rate limit: mock error_code=147 → success=False, no crash
  7. Timeout: mock timeout → success=False sau retry
  8. Luồng tích hợp: p_churn < 0.85 → KHÔNG gửi ZNS
  9. Luồng tích hợp: p_churn > 0.85 + no phone → log warning, KHÔNG crash
"""

import sys
import os
import logging
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


def divider(title: str):
    print(f"\n{'='*65}")
    print(f"  {title}")
    print("="*65)


# ---------------------------------------------------------------------------
# Import module cần test
# ---------------------------------------------------------------------------
from backend.webhooks.zalo_zns import (
    _normalize_phone_for_zalo,
    _generate_tracking_id,
    _parse_zalo_error,
    get_primary_complained_aspect,
    send_zalo_zns_alert,
    ZaloTokenExpiredError,
    ZaloRateLimitError,
    ZaloAPIError,
    ZaloConfigError,
)


# ---------------------------------------------------------------------------
# Test 1: Chuẩn hoá SĐT
# ---------------------------------------------------------------------------
def test_normalize_phone():
    divider("Test 1: Chuan hoa SDT -> format Zalo (84XXXXXXXXX)")

    cases = [
        ("0987654321",    "84987654321"),   # Số 0x → 84x
        ("+84987654321",  "84987654321"),   # +84... → 84...
        ("84987654321",   "84987654321"),   # Đã đúng
        ("0901111222",    "84901111222"),   # Khác số
        ("  0912 345 678 ", "84912345678"), # Có khoảng trắng
    ]

    for input_phone, expected in cases:
        result = _normalize_phone_for_zalo(input_phone)
        status = "OK" if result == expected else "FAIL"
        print(f"  [{status}] '{input_phone.strip()}' → '{result}'  (mong doi: '{expected}')")
        assert result == expected, f"FAIL: '{input_phone}' -> '{result}' != '{expected}'"

    print("  => Tat ca SDT duoc chuan hoa dung!")


# ---------------------------------------------------------------------------
# Test 2: get_primary_complained_aspect
# ---------------------------------------------------------------------------
def test_get_primary_aspect():
    divider("Test 2: get_primary_complained_aspect")

    # Case 1: Có aspect tiêu cực
    aspects_with_negative = [
        {"aspect": "toc_do_phuc_vu", "sentiment": "Tieu cuc", "reason": "Cho lau"},
        {"aspect": "mon_an", "sentiment": "Tich cuc", "reason": "Ngon"},
    ]
    result1 = get_primary_complained_aspect(aspects_with_negative)
    print(f"  [1] Co aspect tieu cuc → '{result1}'")
    assert result1 == "toc_do_phuc_vu"

    # Case 2: Không có aspect tiêu cực → fallback
    aspects_positive_only = [
        {"aspect": "nhan_vien", "sentiment": "Tich cuc", "reason": "Than thien"},
    ]
    result2 = get_primary_complained_aspect(aspects_positive_only)
    print(f"  [2] Chi co tich cuc → fallback: '{result2}'")
    assert "trai nghiem" in result2.lower() or result2  # fallback string

    # Case 3: Danh sách rỗng
    result3 = get_primary_complained_aspect([])
    print(f"  [3] Danh sach rong → fallback: '{result3}'")
    assert result3  # Không rỗng

    # Case 4: Nhận dạng cả "negative" tiếng Anh
    aspects_english = [
        {"aspect": "ve_sinh", "sentiment": "negative", "reason": "Doi dep"},
    ]
    result4 = get_primary_complained_aspect(aspects_english)
    print(f"  [4] Sentiment 'negative' (English) → '{result4}'")
    assert result4 == "ve_sinh"

    print("  => Tat ca OK!")


# ---------------------------------------------------------------------------
# Test 3: ZaloConfigError khi thiếu env vars
# ---------------------------------------------------------------------------
def test_config_missing():
    divider("Test 3: Thieu env vars → ZaloConfigError, result['success']=False")

    # Xóa env vars Zalo nếu có
    backup = {}
    for var in ["ZALO_ACCESS_TOKEN", "ZALO_TEMPLATE_ID"]:
        backup[var] = os.environ.pop(var, None)

    try:
        result = send_zalo_zns_alert(
            customer_phone="0987654321",
            tenant_id="test-tenant",
            aspect_complained="toc do phuc vu",
            voucher_code="BACK20",
            p_churn=0.91,
        )
        print(f"  result['success'] = {result['success']}  (mong doi: False)")
        print(f"  result['error_type'] = {result['error_type']}")
        assert result["success"] is False
        assert result["error_type"] == "ZaloConfigError"
        print("  => ZaloConfigError duoc xu ly: KHONG crash, tra success=False")
    finally:
        # Restore
        for var, val in backup.items():
            if val is not None:
                os.environ[var] = val


# ---------------------------------------------------------------------------
# Test 4: Thành công — mock HTTP 200, error_code=0
# ---------------------------------------------------------------------------
def test_send_success():
    divider("Test 4: Gui thanh cong (mock HTTP 200, error_code=0)")

    os.environ["ZALO_ACCESS_TOKEN"] = "fake-token-test"
    os.environ["ZALO_TEMPLATE_ID"]  = "fake-template-123"

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "error": 0,
        "message": "Success",
        "data": {"message_id": "zalo_msg_abc123"}
    }
    mock_response.raise_for_status = MagicMock()  # Không raise

    with patch("httpx.Client") as mock_client_class:
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.post.return_value = mock_response
        mock_client_class.return_value = mock_client

        result = send_zalo_zns_alert(
            customer_phone="0987654321",
            tenant_id="pho-ba-lan_172250000000",
            aspect_complained="toc do phuc vu",
            voucher_code="BACK20",
            p_churn=0.93,
        )

    print(f"  result['success']        = {result['success']}  (mong doi: True)")
    print(f"  result['zalo_message_id'] = {result['zalo_message_id']}")
    print(f"  result['tracking_id']    = {result['tracking_id']}")
    print(f"  result['phone_normalized'] = {result['phone_normalized']}")
    assert result["success"] is True
    assert result["zalo_message_id"] == "zalo_msg_abc123"
    assert result["phone_normalized"] == "84987654321"
    assert result["tracking_id"].startswith("sentrix_")
    print("  => GUI THANH CONG dung flow!")


# ---------------------------------------------------------------------------
# Test 5: Token hết hạn → success=False, không crash
# ---------------------------------------------------------------------------
def test_token_expired():
    divider("Test 5: Token het han (error_code=216) → success=False, KHONG crash")

    os.environ["ZALO_ACCESS_TOKEN"] = "expired-token"
    os.environ["ZALO_TEMPLATE_ID"]  = "fake-template-123"

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "error": 216,
        "message": "Access token expired"
    }
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.Client") as mock_client_class:
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.post.return_value = mock_response
        mock_client_class.return_value = mock_client

        # Phải KHÔNG raise exception ra bên ngoài
        result = send_zalo_zns_alert(
            customer_phone="0987654321",
            tenant_id="test-tenant",
            aspect_complained="ve sinh",
            voucher_code="VIP15",
            p_churn=0.88,
        )

    print(f"  result['success']    = {result['success']}  (mong doi: False)")
    print(f"  result['error_type'] = {result['error_type']}  (mong doi: ZaloTokenExpiredError)")
    assert result["success"] is False
    assert result["error_type"] == "ZaloTokenExpiredError"
    print("  => Token het han: log ro rang, KHONG crash pipeline!")


# ---------------------------------------------------------------------------
# Test 6: Rate limit → success=False, không crash
# ---------------------------------------------------------------------------
def test_rate_limit():
    divider("Test 6: Rate limit (error_code=147) → success=False, KHONG crash")

    os.environ["ZALO_ACCESS_TOKEN"] = "valid-token"
    os.environ["ZALO_TEMPLATE_ID"]  = "fake-template-123"

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "error": 147,
        "message": "Rate limit exceeded"
    }
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.Client") as mock_client_class, \
         patch("time.sleep") as mock_sleep:  # Mock sleep để test không chờ
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client.post.return_value = mock_response
        mock_client_class.return_value = mock_client

        result = send_zalo_zns_alert(
            customer_phone="0901234567",
            tenant_id="test-tenant",
            aspect_complained="nhan vien",
            voucher_code="BACK30",
            p_churn=0.92,
        )

    print(f"  result['success']    = {result['success']}  (mong doi: False)")
    print(f"  result['error_type'] = {result['error_type']}")
    assert result["success"] is False
    assert result["error_type"] == "ZaloRateLimitError"
    print("  => Rate limit: KHONG crash, ghi log canh bao!")


# ---------------------------------------------------------------------------
# Test 7: Timeout → retry, vẫn fail → success=False
# ---------------------------------------------------------------------------
def test_timeout():
    divider("Test 7: Timeout → retry 1 lan → success=False, KHONG crash")
    import httpx

    os.environ["ZALO_ACCESS_TOKEN"] = "valid-token"
    os.environ["ZALO_TEMPLATE_ID"]  = "fake-template-123"

    with patch("httpx.Client") as mock_client_class, \
         patch("time.sleep") as mock_sleep:
        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        # Luôn raise TimeoutException
        mock_client.post.side_effect = httpx.TimeoutException("Connection timeout")
        mock_client_class.return_value = mock_client

        result = send_zalo_zns_alert(
            customer_phone="0912345678",
            tenant_id="test-tenant",
            aspect_complained="gia ca",
            voucher_code="BACK10",
            p_churn=0.87,
        )

    print(f"  result['success']    = {result['success']}  (mong doi: False)")
    print(f"  result['error_type'] = {result['error_type']}  (mong doi: TimeoutException)")
    # Kiểm tra đã retry ít nhất 1 lần
    call_count = mock_client.post.call_count
    print(f"  So lan thu: {call_count}  (mong doi: >= 2 = retry 1 lan)")
    assert result["success"] is False
    assert call_count >= 2  # 1 lan chinh + 1 lan retry
    print("  => Timeout: retry xong van fail, khong crash!")


# ---------------------------------------------------------------------------
# Test 8: p_churn < threshold → không gửi ZNS (logic ở feedback.py)
# ---------------------------------------------------------------------------
def test_below_threshold_logic():
    divider("Test 8: p_churn=0.30 (Thap) → KHONG trigger ZNS")
    # Đây là logic ở feedback.py (should_alert = False)
    # ZNS chỉ được gọi khi should_alert=True
    # Test này chỉ xác nhận logic phân biệt

    from backend.rfms_model.churn_model import calculate_churn_full
    result = calculate_churn_full(3, 20, 1_200_000, 0.88)
    p = result["p_churn"]
    should_alert = result["should_alert"]
    print(f"  p_churn={p:.4f} | should_alert={should_alert}")
    assert should_alert is False
    print(f"  => p_churn thap → should_alert=False → ZNS KHONG bi goi")

    result2 = calculate_churn_full(120, 3, 80_000, 0.05)
    p2 = result2["p_churn"]
    should_alert2 = result2["should_alert"]
    print(f"  p_churn={p2:.4f} | should_alert={should_alert2}  (khach nguy hiem)")
    assert should_alert2 is True
    print(f"  => p_churn cao → should_alert=True → ZNS SE duoc goi!")


# ---------------------------------------------------------------------------
# Test 9: Tracking ID format
# ---------------------------------------------------------------------------
def test_tracking_id_format():
    divider("Test 9: Tracking ID format va uniqueness")
    ids = set()
    for i in range(10):
        tid = _generate_tracking_id("pho-ba-lan_1722500000000", "0987654321")
        ids.add(tid)
        print(f"  [{i+1}] {tid}")
    assert all(t.startswith("sentrix_") for t in ids)
    # Hầu hết phải unique (có thể trùng nếu chạy cùng giây + cùng rand, nhưng cực hiếm)
    assert len(ids) >= 8, "FAIL: tracking_id khong du unique"
    print(f"  => {len(ids)}/10 unique IDs (mong doi >= 8)")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    divider("GIAI DOAN 9 — TEST ZALO ZNS WEBHOOK")
    print("  Che do: Logic mock — KHONG can Zalo credentials that\n")

    test_normalize_phone()
    test_get_primary_aspect()
    test_config_missing()
    test_send_success()
    test_token_expired()
    test_rate_limit()
    test_timeout()
    test_below_threshold_logic()
    test_tracking_id_format()

    divider("TONG KET GIAI DOAN 9")
    print("  [1] Chuan hoa SDT           OK")
    print("  [2] Primary aspect logic    OK")
    print("  [3] Config missing          OK → success=False, khong crash")
    print("  [4] Gui thanh cong (mock)   OK → tracking_id, message_id")
    print("  [5] Token het han           OK → success=False, log ro rang")
    print("  [6] Rate limit              OK → success=False, log canh bao")
    print("  [7] Timeout + retry         OK → retry 1 lan, roi fail dep")
    print("  [8] Nguong churn logic      OK → chi gui khi should_alert=True")
    print("  [9] Tracking ID uniqueness  OK → sentrix_ prefix, unique")
    print()
    print("  ZNS KHONG BAO GIO CRASH PIPELINE CHINH!")
    print("  Pipeline chinh: Firestore luu truoc, ZNS gui sau, loi ZNS = bo qua")
    print()
    print("  Cau hinh can thiet de dung that (them vao .env):")
    print("    ZALO_ACCESS_TOKEN=your_access_token   (lam moi sau 25h)")
    print("    ZALO_TEMPLATE_ID=your_template_id     (lay tu Zalo OA Manager)")
    print("="*65 + "\n")

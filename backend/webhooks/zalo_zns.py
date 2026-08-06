"""
Zalo ZNS (ZBS Template Message) — Webhook Alert
=================================================
Author: Nguyễn Thanh Tuyền (AI & Data Architect) — hỗ trợ bởi Đoàn Hoàng Việt
Giai đoạn: 9 — Gửi cảnh báo Zalo khi phát hiện rủi ro rời bỏ cao

API THAM KHẢO (tài liệu chính thức tại thời điểm code — 08/2026):
  Từ 01/01/2026, ZNS đã được hợp nhất vào ZBS Template Message.
  Endpoint: POST https://business.openapi.zalo.me/message/template
  Header:   access_token (OAuth 2.0, thời hạn 25 giờ)
  Tài liệu: https://developers.zalo.me/docs/zalo-notification-service/

CẤU TRÚC REQUEST:
  {
    "phone": "84987654321",          ← SĐT dạng quốc tế, KHÔNG có dấu +
    "template_id": "your_template",  ← ID template đã được Zalo duyệt
    "template_data": {               ← Tham số điền vào template
      "customer_name": "...",
      "aspect": "...",
      "voucher_code": "..."
    },
    "tracking_id": "sentrix_..."     ← ID tracking tuỳ chỉnh của chúng ta
  }

TOKEN MANAGEMENT:
  - Access Token hết hạn sau 25 giờ → cần refresh tự động.
  - Module này KHÔNG tự động refresh token (quá phức tạp cho MVP).
  - Dùng ZALO_ACCESS_TOKEN từ biến môi trường; khi hết hạn, Việt/Tuấn
    cần refresh thủ công hoặc dùng cron job refresh token.
  - Ghi chú mục "Cần phối hợp với Việt/Tuấn" trong backend/README.md.

XỬ LÝ LỖI:
  - Token hết hạn (error_code 216) → log rõ, KHÔNG crash pipeline chính
  - Rate limit (error_code 147/148) → log rõ, KHÔNG crash pipeline chính
  - Lỗi network → retry 1 lần sau 2 giây, vẫn thất bại thì log + bỏ qua
  - Mọi lỗi webhook KHÔNG làm crash luồng lưu Firestore (đã xử lý ở giai đoạn 8)

BIẾN MÔI TRƯỜNG:
  ZALO_ACCESS_TOKEN   — OAuth access token của Official Account (25h)
  ZALO_TEMPLATE_ID    — ID template ZNS đã được Zalo duyệt
  ZALO_OA_ID          — OA ID (tuỳ chọn, để log)
"""

import os
import time
import logging
import hashlib
import secrets
from datetime import datetime, timezone
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Endpoint ZBS Template Message (kế thừa từ ZNS sau 01/01/2026)
ZNS_API_ENDPOINT = "https://business.openapi.zalo.me/message/template"

# Timeout gọi API (giây)
ZNS_REQUEST_TIMEOUT_SECONDS = 10

# Retry config
ZNS_MAX_RETRIES = 1
ZNS_RETRY_DELAY_SECONDS = 2

# Zalo error codes đặc biệt cần xử lý riêng
ZALO_ERROR_TOKEN_EXPIRED = 216      # Access token hết hạn (25h)
ZALO_ERROR_TOKEN_INVALID = 4        # Access token không hợp lệ
ZALO_ERROR_RATE_LIMIT    = 147      # Rate limit: vượt số lượng ZNS/ngày
ZALO_ERROR_RATE_LIMIT_2  = 148      # Rate limit: gửi quá nhanh cho 1 số
ZALO_ERROR_PHONE_INVALID = 1205     # SĐT không hợp lệ hoặc không dùng Zalo


# ---------------------------------------------------------------------------
# Custom Exceptions
# ---------------------------------------------------------------------------

class ZaloZNSError(Exception):
    """Base exception cho mọi lỗi Zalo ZNS."""
    pass

class ZaloTokenExpiredError(ZaloZNSError):
    """Access token đã hết hạn — cần refresh."""
    pass

class ZaloRateLimitError(ZaloZNSError):
    """Vượt giới hạn gửi ZNS."""
    pass

class ZaloConfigError(ZaloZNSError):
    """Thiếu cấu hình biến môi trường."""
    pass

class ZaloAPIError(ZaloZNSError):
    """Lỗi API chung từ Zalo."""
    pass


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _normalize_phone_for_zalo(phone_number: str) -> str:
    """
    Chuẩn hoá SĐT về định dạng Zalo yêu cầu: 84987654321
    (84 = mã quốc gia Việt Nam, KHÔNG có dấu +, KHÔNG có số 0 đầu)

    Ví dụ:
      "0987654321"    → "84987654321"
      "+84987654321"  → "84987654321"
      "84987654321"   → "84987654321" (đã đúng)
    """
    phone = phone_number.strip().replace(" ", "").replace("-", "")
    if phone.startswith("+84"):
        return "84" + phone[3:]
    elif phone.startswith("84") and len(phone) == 11:
        return phone  # Đã đúng format
    elif phone.startswith("0"):
        return "84" + phone[1:]
    else:
        return "84" + phone  # Fallback: thêm 84


def _generate_tracking_id(tenant_id: str, customer_phone: str) -> str:
    """
    Sinh tracking_id duy nhất cho mỗi lần gửi ZNS.
    Format: sentrix_{tenant_short}_{timestamp}_{random4}
    """
    tenant_short = tenant_id[:8].replace("-", "")
    ts = int(datetime.now(timezone.utc).timestamp())
    rand = secrets.token_hex(2)  # 4 ký tự hex ngẫu nhiên
    return f"sentrix_{tenant_short}_{ts}_{rand}"


def _get_zalo_config() -> tuple[str, str]:
    """
    Lấy Zalo credentials từ biến môi trường.

    Returns:
        (access_token, template_id)

    Raises:
        ZaloConfigError: Nếu thiếu biến môi trường bắt buộc.
    """
    access_token = os.getenv("ZALO_ACCESS_TOKEN", "").strip()
    template_id  = os.getenv("ZALO_TEMPLATE_ID", "").strip()

    missing = []
    if not access_token:
        missing.append("ZALO_ACCESS_TOKEN")
    if not template_id:
        missing.append("ZALO_TEMPLATE_ID")

    if missing:
        raise ZaloConfigError(
            f"Thieu cau hinh Zalo ZNS: {', '.join(missing)}. "
            "Them vao file .env: ZALO_ACCESS_TOKEN=... va ZALO_TEMPLATE_ID=..."
        )

    return access_token, template_id


def _parse_zalo_error(response_json: dict) -> None:
    """
    Parse response từ Zalo API và raise exception phù hợp nếu có lỗi.

    Zalo trả error_code = 0 là thành công; khác 0 là lỗi.
    """
    error_code = response_json.get("error") or response_json.get("error_code", 0)
    if error_code == 0:
        return  # Thành công

    message = response_json.get("message", "Khong ro ly do")

    if error_code in (ZALO_ERROR_TOKEN_EXPIRED, ZALO_ERROR_TOKEN_INVALID):
        raise ZaloTokenExpiredError(
            f"Zalo access token het han hoac khong hop le (error_code={error_code}). "
            "Can refresh token tai: https://developers.zalo.me"
        )
    elif error_code in (ZALO_ERROR_RATE_LIMIT, ZALO_ERROR_RATE_LIMIT_2):
        raise ZaloRateLimitError(
            f"Da vuot gioi han gui ZNS (error_code={error_code}): {message}"
        )
    elif error_code == ZALO_ERROR_PHONE_INVALID:
        raise ZaloAPIError(
            f"So dien thoai khong hop le hoac khong dung Zalo (error_code={error_code})"
        )
    else:
        raise ZaloAPIError(
            f"Zalo API loi (error_code={error_code}): {message}"
        )


# ---------------------------------------------------------------------------
# Hàm chính
# ---------------------------------------------------------------------------

def send_zalo_zns_alert(
    customer_phone: str,
    tenant_id: str,
    aspect_complained: str,
    voucher_code: str,
    p_churn: Optional[float] = None,
) -> dict:
    """
    Gửi cảnh báo Zalo ZNS khi phát hiện khách hàng có rủi ro rời bỏ cao.

    Hàm này gọi Zalo ZBS Template Message API (kế thừa ZNS từ 01/01/2026).
    Nếu gọi API thất bại vì bất kỳ lý do nào, hàm LOG lỗi rõ ràng và
    KHÔNG raise exception ra ngoài — để pipeline chính (lưu Firestore) không bị crash.

    Args:
        customer_phone:    SĐT khách hàng (bất kỳ format: 0987..., +84987..., 84987...)
                           Sẽ được chuẩn hoá trước khi gửi.
        tenant_id:         ID tenant (để điền vào template và log).
        aspect_complained: Khía cạnh khách hàng phàn nàn nhiều nhất.
                           Ví dụ: "thai do nhan vien", "toc do phuc vu"
        voucher_code:      Mã voucher cứu vãn đính kèm tin nhắn.
                           Ví dụ: "BACK10", "VIP20"
        p_churn:           Xác suất rời bỏ (để log). Tuỳ chọn.

    Returns:
        dict với:
        {
            "success": bool,
            "tracking_id": str,        # ID để tra cứu lại nếu cần
            "zalo_message_id": str,    # ID tin nhắn từ Zalo (nếu thành công)
            "error_type": str | None,  # Loại lỗi (nếu thất bại)
            "error_detail": str | None,
            "phone_normalized": str,   # SĐT đã chuẩn hoá gửi đi
        }

    Note:
        Hàm KHÔNG raise exception — mọi lỗi được bắt và trả về trong result["success"]=False.
        Caller (feedback.py) nên kiểm tra result["success"] để log thêm nếu cần.
    """
    phone_normalized = _normalize_phone_for_zalo(customer_phone)
    tracking_id = _generate_tracking_id(tenant_id, customer_phone)

    p_churn_str = f"{p_churn:.4f}" if p_churn is not None else "N/A"
    logger.info(
        f"[ZaloZNS] Bat dau gui canh bao | "
        f"phone={phone_normalized} | tenant={tenant_id} | "
        f"aspect='{aspect_complained}' | voucher={voucher_code} | "
        f"p_churn={p_churn_str} | tracking_id={tracking_id}"
    )

    # --- Lấy config ---
    try:
        access_token, template_id = _get_zalo_config()
    except ZaloConfigError as e:
        logger.warning(f"[ZaloZNS] Thieu cau hinh — bo qua gui ZNS: {e}")
        return {
            "success": False,
            "tracking_id": tracking_id,
            "zalo_message_id": None,
            "error_type": "ZaloConfigError",
            "error_detail": str(e),
            "phone_normalized": phone_normalized,
        }

    # --- Chuẩn bị request body ---
    # template_data phải khớp với cấu trúc template đã đăng ký trên Zalo OA.
    # Template mẫu cho Sentrix:
    #   "Xin chào, chúng tôi nhận thấy trải nghiệm {{aspect}} của bạn chưa tốt.
    #    Vui lòng quay lại để chúng tôi phục vụ tốt hơn — tặng bạn voucher {{voucher_code}}!"
    payload = {
        "phone":         phone_normalized,
        "template_id":   template_id,
        "template_data": {
            "aspect":       aspect_complained,
            "voucher_code": voucher_code,
        },
        "tracking_id": tracking_id,
    }

    headers = {
        "Content-Type":  "application/json",
        "access_token":  access_token,
    }

    # --- Gọi API với retry ---
    last_error: Optional[Exception] = None

    for attempt in range(ZNS_MAX_RETRIES + 1):
        if attempt > 0:
            logger.info(f"[ZaloZNS] Retry lan {attempt}/{ZNS_MAX_RETRIES}...")
            time.sleep(ZNS_RETRY_DELAY_SECONDS)

        try:
            with httpx.Client(timeout=ZNS_REQUEST_TIMEOUT_SECONDS) as client:
                response = client.post(
                    ZNS_API_ENDPOINT,
                    json=payload,
                    headers=headers,
                )

            response.raise_for_status()  # Raise cho 4xx/5xx HTTP errors

            resp_json = response.json()
            logger.debug(f"[ZaloZNS] Response JSON: {resp_json}")

            # Parse Zalo-level error (HTTP 200 nhưng error_code != 0)
            _parse_zalo_error(resp_json)

            # --- Thành công ---
            zalo_msg_id = (
                resp_json.get("data", {}).get("message_id")
                or resp_json.get("message_id")
                or "unknown"
            )
            logger.info(
                f"[ZaloZNS] Gui ZNS THANH CONG | "
                f"tracking_id={tracking_id} | zalo_message_id={zalo_msg_id}"
            )
            return {
                "success": True,
                "tracking_id": tracking_id,
                "zalo_message_id": zalo_msg_id,
                "error_type": None,
                "error_detail": None,
                "phone_normalized": phone_normalized,
            }

        except ZaloTokenExpiredError as e:
            logger.error(
                f"[ZaloZNS] TOKEN HET HAN (attempt {attempt+1}): {e}\n"
                "  → Can: Viet/Tuan refresh ZALO_ACCESS_TOKEN trong .env va Render env vars.\n"
                "  → Huong dan: https://developers.zalo.me (OAuth v4 refresh token flow)"
            )
            last_error = e
            break  # Không retry — token hết hạn cần action thủ công

        except ZaloRateLimitError as e:
            logger.warning(
                f"[ZaloZNS] RATE LIMIT (attempt {attempt+1}): {e}\n"
                "  → Se thu lai sau. Neu lien tuc, kiem tra han muc ZNS/ngay tren Zalo OA."
            )
            last_error = e
            # Tiếp tục retry

        except ZaloAPIError as e:
            logger.error(f"[ZaloZNS] Zalo API Error (attempt {attempt+1}): {e}")
            last_error = e
            break  # Lỗi API không phải rate limit → không retry

        except httpx.TimeoutException as e:
            logger.warning(f"[ZaloZNS] Timeout (attempt {attempt+1}): {e}")
            last_error = e
            # Tiếp tục retry

        except httpx.HTTPStatusError as e:
            logger.error(
                f"[ZaloZNS] HTTP Error (attempt {attempt+1}): "
                f"{e.response.status_code} {e.response.text[:200]}"
            )
            last_error = e
            if e.response.status_code < 500:
                break  # 4xx → không retry

        except Exception as e:
            logger.error(f"[ZaloZNS] Loi khong xac dinh (attempt {attempt+1}): {type(e).__name__}: {e}")
            last_error = e

    # --- Thất bại sau tất cả retry ---
    error_type = type(last_error).__name__ if last_error else "UnknownError"
    error_detail = str(last_error) if last_error else "No error details"

    logger.error(
        f"[ZaloZNS] GUI THAT BAI sau {ZNS_MAX_RETRIES + 1} lan thu | "
        f"tracking_id={tracking_id} | error={error_type}: {error_detail[:100]}\n"
        "  → Pipeline chinh (Firestore) van hoat dong binh thuong.\n"
        "  → Kiem tra lai ZALO_ACCESS_TOKEN, ZALO_TEMPLATE_ID trong .env."
    )
    return {
        "success": False,
        "tracking_id": tracking_id,
        "zalo_message_id": None,
        "error_type": error_type,
        "error_detail": error_detail,
        "phone_normalized": phone_normalized,
    }


# ---------------------------------------------------------------------------
# Helper công khai: lấy aspect chính từ danh sách aspects
# ---------------------------------------------------------------------------

def get_primary_complained_aspect(aspects: list[dict]) -> str:
    """
    Lấy khía cạnh bị phàn nàn nhiều nhất từ kết quả ABSA.
    Dùng để điền vào template ZNS.

    Nếu không có aspect tiêu cực → trả về chuỗi mặc định.
    """
    negative_aspects = [
        a for a in aspects
        if str(a.get("sentiment", "")).lower() in ("tiêu cực", "tieu cuc", "negative")
    ]
    if not negative_aspects:
        return "trai nghiem cua ban"

    # Lấy aspect đầu tiên (ABSA đã sắp xếp theo mức độ quan trọng)
    primary = negative_aspects[0]
    return primary.get("aspect", "trai nghiem cua ban")

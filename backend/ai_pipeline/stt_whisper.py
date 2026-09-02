"""
Speech-to-Text (STT) — Groq Whisper API Integration
=====================================================
Author: Nguyễn Thanh Tuyền (AI & Data Architect)
Giai đoạn: 4 — Tích hợp Whisper STT (provider: Groq)

LUỒNG SỬ DỤNG:
  audio_path = "/tmp/sentrix_audio_temp/abc123.webm"
  text = transcribe_audio(audio_path)
  # → "Phục vụ tốt quá ha, đợi có 20 phút mà"

THƯ VIỆN:
  Sử dụng openai Python SDK v1.x (openai>=1.0.0) trỏ sang Groq endpoint.
  Groq tương thích hoàn toàn với OpenAI Audio API — không cần SDK riêng.
  Tài liệu: https://console.groq.com/docs/speech-text
  Endpoint: POST https://api.groq.com/openai/v1/audio/transcriptions
  Model: "whisper-large-v3-turbo" — nhanh hơn whisper-1, miễn phí trên Groq free tier.

CẤU HÌNH:
  Đặt biến môi trường GROQ_API_KEY (dạng gsk_...) trong .env local.
  Fallback: WHISPER_API_KEY → OPENAI_API_KEY (tương thích ngược).
  Xem .env.example để biết format.

GIỚI HẠN FREE TIER GROQ (tại thời điểm 09/2026):
  - File tối đa: 25 MB (kiểm tra trước khi gọi API ở Bước 1)
  - Rate limit: 20 req/phút, 2.000 req/ngày, 7.200 s audio/giờ, 28.800 s audio/ngày
  - HTTP 429 → bắt và trả thông báo thân thiện (xem xử lý lỗi bên dưới)

XỬ LÝ LỖI:
  - File không tồn tại → FileNotFoundError ngay trước khi gọi API (tiết kiệm quota)
  - API Key thiếu/sai → WhisperAuthError với hướng dẫn cụ thể
  - File không đúng định dạng / quá lớn → WhisperFormatError với chi tiết từ API
  - Rate limit (429) → WhisperRateLimitError với thông báo thân thiện cho user
  - Timeout → WhisperTimeoutError (default timeout: 60s cho file 15 giây)
  - Lỗi mạng/hạ tầng khác → WhisperAPIError bọc exception gốc
"""

import os
import logging
from pathlib import Path

from openai import (
    OpenAI,
    AuthenticationError,
    BadRequestError,
    APITimeoutError,
    APIConnectionError,
    RateLimitError,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Hằng số
# ---------------------------------------------------------------------------

# Các MIME type và extension mà Whisper API hỗ trợ
# Nguồn: https://console.groq.com/docs/speech-text (tương thích OpenAI Whisper)
WHISPER_SUPPORTED_EXTENSIONS = {
    ".mp3", ".mp4", ".mpeg", ".mpga", ".m4a",
    ".wav", ".webm", ".ogg", ".flac",
}

# Kích thước tối đa Groq Whisper API chấp nhận: 25 MB
WHISPER_MAX_SIZE_BYTES = 25 * 1024 * 1024

# Timeout (giây) — audio 15 giây nên 60s là thừa đủ, thậm chí khi mạng chậm
WHISPER_TIMEOUT_SECONDS = 60

# Groq API base URL — tương thích OpenAI SDK
_GROQ_BASE_URL = "https://api.groq.com/openai/v1"

# Model Groq Whisper sử dụng (nhanh hơn whisper-1, hỗ trợ tiếng Việt)
_GROQ_MODEL = "whisper-large-v3-turbo"


# ---------------------------------------------------------------------------
# Custom exceptions — để caller (endpoint) bắt và trả lỗi có cấu trúc
# ---------------------------------------------------------------------------

class WhisperError(Exception):
    """Base exception cho mọi lỗi liên quan đến Whisper STT."""
    pass

class WhisperAuthError(WhisperError):
    """API key thiếu hoặc không hợp lệ."""
    pass

class WhisperFormatError(WhisperError):
    """File audio không đúng định dạng hoặc bị hỏng."""
    pass

class WhisperTimeoutError(WhisperError):
    """Request tới Whisper API bị timeout."""
    pass

class WhisperRateLimitError(WhisperError):
    """Vượt rate limit Groq (HTTP 429). Caller nên trả thông báo thân thiện."""
    pass

class WhisperAPIError(WhisperError):
    """Lỗi API chung (mạng, server 5xx, v.v.)."""
    pass


# ---------------------------------------------------------------------------
# Hàm chính
# ---------------------------------------------------------------------------

def transcribe_audio(audio_file_path: str, language: str = "vi") -> str:
    """
    Gọi Groq Whisper API để chuyển đổi file âm thanh thành văn bản tiếng Việt.

    Provider: Groq (https://api.groq.com/openai/v1) — miễn phí cho demo/MVP.
    Model: whisper-large-v3-turbo — nhanh hơn whisper-1, chất lượng tương đương.

    Args:
        audio_file_path: Đường dẫn tuyệt đối hoặc tương đối tới file audio.
                         Hỗ trợ: .webm, .mp3, .mp4, .wav, .ogg, .flac, .m4a
        language:        Mã ngôn ngữ ISO 639-1. Mặc định "vi" (tiếng Việt).
                         Truyền rõ ngôn ngữ giúp Whisper chính xác hơn và giảm latency.

    Returns:
        str: Văn bản đã được transcript, đã strip() khoảng trắng thừa.
             Trả về chuỗi rỗng "" nếu audio không có tiếng nói (im lặng hoàn toàn).

    Raises:
        FileNotFoundError:      File audio không tồn tại tại đường dẫn đã cho.
        WhisperAuthError:       GROQ_API_KEY (hoặc fallback) thiếu hoặc sai.
        WhisperFormatError:     File audio sai định dạng, quá lớn (>25MB), hoặc bị hỏng.
        WhisperRateLimitError:  Vượt rate limit Groq (429). Thử lại sau vài giây.
        WhisperTimeoutError:    Request tới Groq Whisper API timeout sau 60 giây.
        WhisperAPIError:        Lỗi mạng hoặc lỗi không xác định từ API.
    """
    # --- Bước 1: Kiểm tra file tồn tại và đúng định dạng TRƯỚC KHI gọi API ---
    # (Tiết kiệm API quota, phát hiện lỗi sớm với thông báo rõ hơn)
    audio_path = Path(audio_file_path)

    if not audio_path.exists():
        raise FileNotFoundError(
            f"Không tìm thấy file audio: '{audio_file_path}'"
        )

    extension = audio_path.suffix.lower()
    if extension not in WHISPER_SUPPORTED_EXTENSIONS:
        raise WhisperFormatError(
            f"Định dạng file '{extension}' không được Whisper API hỗ trợ. "
            f"Các định dạng hợp lệ: {', '.join(sorted(WHISPER_SUPPORTED_EXTENSIONS))}"
        )

    file_size = audio_path.stat().st_size
    if file_size > WHISPER_MAX_SIZE_BYTES:
        raise WhisperFormatError(
            f"File audio quá lớn: {file_size / 1024 / 1024:.1f}MB. "
            f"Whisper API giới hạn tối đa {WHISPER_MAX_SIZE_BYTES // 1024 // 1024}MB."
        )

    if file_size == 0:
        raise WhisperFormatError("File audio rỗng (0 bytes).")

    # --- Bước 2: Lấy API key ---
    # Ưu tiên GROQ_API_KEY; fallback WHISPER_API_KEY → OPENAI_API_KEY (tương thích ngược)
    api_key = (
        os.getenv("GROQ_API_KEY")
        or os.getenv("WHISPER_API_KEY")
        or os.getenv("OPENAI_API_KEY")
    )
    if not api_key:
        raise WhisperAuthError(
            "Chưa thiết lập API key cho Groq Whisper. "
            "Hãy đặt biến môi trường GROQ_API_KEY (dạng gsk_...) trong file .env."
        )

    # --- Bước 3: Gọi Groq Whisper API qua OpenAI-compatible SDK ---
    try:
        # Dùng OpenAI SDK trỏ sang Groq endpoint — không cần cài thêm groq package
        groq_client = OpenAI(
            api_key=api_key,
            base_url=_GROQ_BASE_URL,
            timeout=WHISPER_TIMEOUT_SECONDS,
        )

        logger.info(
            f"[STT] Gửi file đến Groq Whisper: {audio_path.name} "
            f"({file_size / 1024:.1f}KB, ext={extension}, lang={language}, model={_GROQ_MODEL})"
        )

        with open(audio_path, "rb") as audio_file:
            response = groq_client.audio.transcriptions.create(
                model=_GROQ_MODEL,
                file=audio_file,
                language=language,       # Truyền rõ "vi" giúp model chính xác hơn
                response_format="text",  # Trả về plain text, không phải JSON có timestamps
            )

        # response là str khi response_format="text"
        transcript = response.strip() if isinstance(response, str) else str(response).strip()

        logger.info(
            f"[STT] Transcript thành công (Groq): "
            f"{repr(transcript[:80])}{'...' if len(transcript) > 80 else ''}"
        )
        return transcript

    except RateLimitError as e:
        # HTTP 429 — Groq free tier rate limit. Trả thông báo thân thiện thay vì crash.
        logger.warning(f"[STT] Groq rate limit (429): {e}")
        raise WhisperRateLimitError(
            "Hệ thống đang bận, vui lòng thử lại sau vài giây."
        ) from e

    except AuthenticationError as e:
        logger.error(f"[STT] Lỗi xác thực API key Groq: {e}")
        raise WhisperAuthError(
            f"API key Groq không hợp lệ. Kiểm tra lại GROQ_API_KEY trong .env. "
            f"(Chi tiết: {e})"
        ) from e

    except BadRequestError as e:
        # Xảy ra khi file bị hỏng, codec không hỗ trợ, hoặc audio quá ngắn/quá dài
        logger.error(f"[STT] Groq API từ chối file audio: {e}")
        raise WhisperFormatError(
            f"Whisper API từ chối xử lý file audio: {e}. "
            "Có thể file bị hỏng, codec không hỗ trợ, hoặc audio quá ngắn."
        ) from e

    except APITimeoutError as e:
        logger.error(f"[STT] Timeout sau {WHISPER_TIMEOUT_SECONDS}s khi gọi Groq: {e}")
        raise WhisperTimeoutError(
            f"Groq Whisper API không phản hồi sau {WHISPER_TIMEOUT_SECONDS} giây. "
            "Hãy thử lại sau."
        ) from e

    except APIConnectionError as e:
        logger.error(f"[STT] Lỗi kết nối tới Groq: {e}")
        raise WhisperAPIError(
            f"Không thể kết nối đến Groq Whisper API: {e}. "
            "Kiểm tra kết nối mạng."
        ) from e

    except Exception as e:
        logger.error(f"[STT] Lỗi không xác định khi gọi Groq: {type(e).__name__}: {e}")
        raise WhisperAPIError(
            f"Lỗi không xác định khi gọi Groq Whisper API: {type(e).__name__}: {e}"
        ) from e

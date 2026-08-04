"""
Speech-to-Text (STT) — Whisper API Integration
===============================================
Author: Nguyễn Thanh Tuyền (AI & Data Architect)
Giai đoạn: 4 — Tích hợp Whisper STT

LUỒNG SỬ DỤNG:
  audio_path = "/tmp/sentrix_audio_temp/abc123.webm"
  text = transcribe_audio(audio_path)
  # → "Phục vụ tốt quá ha, đợi có 20 phút mà"

THƯ VIỆN:
  Sử dụng openai Python SDK v1.x (openai>=1.0.0).
  Tài liệu chính thức: https://platform.openai.com/docs/guides/speech-to-text
  Endpoint thực tế: POST https://api.openai.com/v1/audio/transcriptions
  Model: "whisper-1" — model duy nhất OpenAI cung cấp qua API tại thời điểm code.

CẤU HÌNH:
  Đặt biến môi trường WHISPER_API_KEY (hoặc OPENAI_API_KEY) trong .env local.
  Xem .env.example để biết format.

XỬ LÝ LỖI:
  - File không tồn tại → FileNotFoundError ngay trước khi gọi API (tiết kiệm quota)
  - API Key thiếu/sai → WhisperAuthError với hướng dẫn cụ thể
  - File không đúng định dạng / quá lớn → WhisperFormatError với chi tiết từ API
  - Timeout → WhisperTimeoutError (default timeout: 60s cho file 15 giây)
  - Lỗi mạng/hạ tầng khác → WhisperAPIError bọc exception gốc
"""

import os
import logging
from pathlib import Path

from openai import OpenAI, AuthenticationError, BadRequestError, APITimeoutError, APIConnectionError

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Hằng số
# ---------------------------------------------------------------------------

# Các MIME type và extension mà Whisper API hỗ trợ
# Nguồn: https://platform.openai.com/docs/guides/speech-to-text
WHISPER_SUPPORTED_EXTENSIONS = {
    ".mp3", ".mp4", ".mpeg", ".mpga", ".m4a",
    ".wav", ".webm", ".ogg", ".flac",
}

# Kích thước tối đa Whisper API chấp nhận: 25 MB
WHISPER_MAX_SIZE_BYTES = 25 * 1024 * 1024

# Timeout (giây) — audio 15 giây nên 60s là thừa đủ, thậm chí khi mạng chậm
WHISPER_TIMEOUT_SECONDS = 60


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

class WhisperAPIError(WhisperError):
    """Lỗi API chung (mạng, server 5xx, v.v.)."""
    pass


# ---------------------------------------------------------------------------
# Hàm chính
# ---------------------------------------------------------------------------

def transcribe_audio(audio_file_path: str, language: str = "vi") -> str:
    """
    Gọi OpenAI Whisper API để chuyển đổi file âm thanh thành văn bản tiếng Việt.

    Args:
        audio_file_path: Đường dẫn tuyệt đối hoặc tương đối tới file audio.
                         Hỗ trợ: .webm, .mp3, .mp4, .wav, .ogg, .flac, .m4a
        language:        Mã ngôn ngữ ISO 639-1. Mặc định "vi" (tiếng Việt).
                         Truyền rõ ngôn ngữ giúp Whisper chính xác hơn và giảm latency.

    Returns:
        str: Văn bản đã được transcript, đã strip() khoảng trắng thừa.
             Trả về chuỗi rỗng "" nếu audio không có tiếng nói (im lặng hoàn toàn).

    Raises:
        FileNotFoundError:   File audio không tồn tại tại đường dẫn đã cho.
        WhisperAuthError:    WHISPER_API_KEY (hoặc OPENAI_API_KEY) thiếu hoặc sai.
        WhisperFormatError:  File audio sai định dạng, quá lớn (>25MB), hoặc bị hỏng.
        WhisperTimeoutError: Request tới Whisper API timeout sau 60 giây.
        WhisperAPIError:     Lỗi mạng hoặc lỗi không xác định từ API.
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
    # Hỗ trợ cả 2 tên biến để linh hoạt (WHISPER_API_KEY ưu tiên, fallback OPENAI_API_KEY)
    api_key = os.getenv("WHISPER_API_KEY") or os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise WhisperAuthError(
            "Chưa thiết lập API key cho Whisper. "
            "Hãy đặt biến môi trường WHISPER_API_KEY hoặc OPENAI_API_KEY trong file .env."
        )

    # --- Bước 3: Gọi Whisper API ---
    try:
        client = OpenAI(
            api_key=api_key,
            timeout=WHISPER_TIMEOUT_SECONDS,
        )

        logger.info(
            f"[STT] Gửi file đến Whisper: {audio_path.name} "
            f"({file_size / 1024:.1f}KB, ext={extension}, lang={language})"
        )

        with open(audio_path, "rb") as audio_file:
            response = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language=language,       # Truyền rõ "vi" giúp model chính xác hơn
                response_format="text",  # Trả về plain text, không phải JSON có timestamps
            )

        # response là str khi response_format="text"
        transcript = response.strip()

        logger.info(
            f"[STT] Transcript thành công: "
            f"{repr(transcript[:80])}{'...' if len(transcript) > 80 else ''}"
        )
        return transcript

    except AuthenticationError as e:
        logger.error(f"[STT] Lỗi xác thực API key: {e}")
        raise WhisperAuthError(
            f"API key Whisper không hợp lệ. Kiểm tra lại WHISPER_API_KEY trong .env. "
            f"(Chi tiết: {e})"
        ) from e

    except BadRequestError as e:
        # Xảy ra khi file bị hỏng, codec không hỗ trợ, hoặc audio quá ngắn/quá dài
        logger.error(f"[STT] API từ chối file audio: {e}")
        raise WhisperFormatError(
            f"Whisper API từ chối xử lý file audio: {e}. "
            "Có thể file bị hỏng, codec không hỗ trợ, hoặc audio quá ngắn."
        ) from e

    except APITimeoutError as e:
        logger.error(f"[STT] Timeout sau {WHISPER_TIMEOUT_SECONDS}s: {e}")
        raise WhisperTimeoutError(
            f"Whisper API không phản hồi sau {WHISPER_TIMEOUT_SECONDS} giây. "
            "Hãy thử lại sau."
        ) from e

    except APIConnectionError as e:
        logger.error(f"[STT] Lỗi kết nối: {e}")
        raise WhisperAPIError(
            f"Không thể kết nối đến Whisper API: {e}. "
            "Kiểm tra kết nối mạng."
        ) from e

    except Exception as e:
        logger.error(f"[STT] Lỗi không xác định: {type(e).__name__}: {e}")
        raise WhisperAPIError(
            f"Lỗi không xác định khi gọi Whisper API: {type(e).__name__}: {e}"
        ) from e

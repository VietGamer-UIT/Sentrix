"""
Audio Quality Service — Kiểm tra chất lượng âm thanh trước khi gọi Whisper
============================================================================
Author: Nguyễn Thanh Tuyền (AI & Data Architect)
Module 1 — Lớp 2: Tiền xử lý âm thanh (Librosa gate)

MỤC ĐÍCH:
  Lọc các audio rác TRƯỚC KHI gọi Whisper API để tiết kiệm chi phí.
  Nếu audio không đạt chất lượng → reject ngay, không tốn 1 request Whisper nào.

HAI CHỈ SỐ CHÍNH:
  1. Thời lượng (duration):
     - Quá ngắn (< AUDIO_MIN_DURATION_SEC) → "invalid_short_audio"
       Lý do: audio < 3s không thể chứa phản hồi có nội dung thực chất.
     - Quá dài (> AUDIO_MAX_DURATION_SEC) → "invalid_long_audio"
       Lý do: giới hạn UI hiển thị 15s; 20s là biên an toàn để không tốn Whisper
              cho các file lỗi/bị loop.

  2. SNR — Signal-to-Noise Ratio (dB):
     - Quá thấp (< SNR_MIN_THRESHOLD) → "invalid_low_snr"
       Lý do: audio nhiễu nặng → Whisper sẽ cho ra transcript vô nghĩa/trống.
              Tiết kiệm 1 lần gọi Whisper ($0.006/phút).

  ⚠️ NGƯỠNG SNR LÀ GIÁ TRỊ KHỞI ĐIỂM GIẢ ĐỊNH:
     Giá trị SNR_MIN_THRESHOLD = 8.0 dB được đề xuất dựa trên tài liệu ITU-T P.563
     (đánh giá chất lượng giọng nói VoIP). Đây KHÔNG phải giá trị tối ưu cuối cùng.
     Cần điều chỉnh sau khi có dữ liệu pilot thực tế từ môi trường quán ăn/spa Việt Nam
     (tiếng ồn nền thường cao hơn phòng studio).

THIẾT KẾ PURE FUNCTION:
  `analyze_audio_quality(file_bytes)` là pure function:
  - Không có side effect (không đọc/ghi file/DB).
  - Dễ unit test độc lập với phần gọi API.
  - Nhận bytes thô → trả AudioQualityResult.
"""

import io
import logging
import os
from dataclasses import dataclass
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Cấu hình ngưỡng — đọc từ env để dễ điều chỉnh không cần deploy lại
# ---------------------------------------------------------------------------
# Thời lượng tối thiểu (giây).
# Lý do ngưỡng 3s: cần ít nhất 3–4 giây để nói được một câu phản hồi có ý nghĩa.
AUDIO_MIN_DURATION_SEC: float = float(os.getenv("AUDIO_MIN_DURATION_SEC", "3.0"))

# Thời lượng tối đa (giây).
# UI cho phép ghi 15s; 20s là biên an toàn xử lý các file loop/bị lỗi.
AUDIO_MAX_DURATION_SEC: float = float(os.getenv("AUDIO_MAX_DURATION_SEC", "20.0"))

# SNR tối thiểu (dB).
# ⚠️ KHỞI ĐIỂM: 8 dB = "nghe được nhưng có nhiễu đáng kể" (ITU-T P.563).
# Cần hiệu chỉnh sau pilot. Đặt quá cao → false reject, quá thấp → Whisper tốn tiền vô ích.
SNR_MIN_THRESHOLD: float = float(os.getenv("SNR_MIN_THRESHOLD", "8.0"))

# Librosa sample rate chuẩn (Hz) — đủ cho phân tích giọng nói, không cần 44.1kHz
_LIBROSA_SR = 16000


# ---------------------------------------------------------------------------
# Data class kết quả
# ---------------------------------------------------------------------------
@dataclass
class AudioQualityResult:
    """Kết quả kiểm tra chất lượng audio."""
    passed: bool                      # True nếu audio đạt chất lượng
    reject_reason: Optional[str]      # None nếu passed; mã lý do nếu bị reject
    reject_message: Optional[str]     # Thông báo thân thiện để trả frontend
    duration_sec: Optional[float]     # Thời lượng audio (giây)
    snr_db: Optional[float]           # SNR đo được (dB); None nếu không tính được


# ---------------------------------------------------------------------------
# Pure function chính
# ---------------------------------------------------------------------------
def analyze_audio_quality(file_bytes: bytes) -> AudioQualityResult:
    """
    Phân tích chất lượng audio từ bytes thô.

    Pure function — không đọc/ghi file/DB, dễ unit test.

    Args:
        file_bytes: Nội dung file audio dạng bytes (WebM/WAV/MP3/OGG...).

    Returns:
        AudioQualityResult với passed=True nếu audio đạt yêu cầu.

    Raises:
        ImportError: Nếu librosa chưa được cài.
        Exception:   Nếu file bytes không decode được thành audio hợp lệ.
    """
    try:
        import librosa
    except ImportError:
        logger.error("[AudioQuality] librosa chưa được cài. Bỏ qua kiểm tra chất lượng.")
        # Graceful degradation: cho qua nếu librosa không có (không nên xảy ra trong production)
        return AudioQualityResult(
            passed=True,
            reject_reason=None,
            reject_message=None,
            duration_sec=None,
            snr_db=None,
        )

    # Decode audio từ bytes → numpy array
    try:
        audio_buf = io.BytesIO(file_bytes)
        y, sr = librosa.load(audio_buf, sr=_LIBROSA_SR, mono=True)
    except Exception as e:
        logger.warning(f"[AudioQuality] Không decode được audio bytes: {e}. Bỏ qua kiểm tra chất lượng để Whisper xử lý.")
        return AudioQualityResult(
            passed=True,
            reject_reason=None,
            reject_message=None,
            duration_sec=None,
            snr_db=None,
        )

    # ── Kiểm tra 1: Thời lượng ──────────────────────────────────────────────
    duration_sec = float(len(y)) / sr

    if duration_sec < AUDIO_MIN_DURATION_SEC:
        logger.info(
            f"[AudioQuality] REJECT — quá ngắn: {duration_sec:.2f}s "
            f"(min={AUDIO_MIN_DURATION_SEC}s)"
        )
        return AudioQualityResult(
            passed=False,
            reject_reason="invalid_short_audio",
            reject_message=(
                f"Ghi âm quá ngắn ({duration_sec:.1f} giây). "
                f"Vui lòng ghi âm ít nhất {AUDIO_MIN_DURATION_SEC:.0f} giây."
            ),
            duration_sec=round(duration_sec, 2),
            snr_db=None,
        )

    if duration_sec > AUDIO_MAX_DURATION_SEC:
        logger.info(
            f"[AudioQuality] REJECT — quá dài: {duration_sec:.2f}s "
            f"(max={AUDIO_MAX_DURATION_SEC}s)"
        )
        return AudioQualityResult(
            passed=False,
            reject_reason="invalid_long_audio",
            reject_message=(
                f"Ghi âm quá dài ({duration_sec:.1f} giây). "
                f"Vui lòng ghi âm tối đa {AUDIO_MAX_DURATION_SEC:.0f} giây."
            ),
            duration_sec=round(duration_sec, 2),
            snr_db=None,
        )

    # ── Kiểm tra 2: SNR ─────────────────────────────────────────────────────
    snr_db = _estimate_snr(y)

    if snr_db is not None and snr_db < SNR_MIN_THRESHOLD:
        logger.info(
            f"[AudioQuality] REJECT — SNR quá thấp: {snr_db:.1f} dB "
            f"(min={SNR_MIN_THRESHOLD} dB)"
        )
        return AudioQualityResult(
            passed=False,
            reject_reason="invalid_low_snr",
            reject_message=(
                "Chất lượng âm thanh quá kém (nhiều tiếng ồn). "
                "Vui lòng ghi âm ở nơi ít ồn hơn."
            ),
            duration_sec=round(duration_sec, 2),
            snr_db=round(snr_db, 2),
        )

    logger.info(
        f"[AudioQuality] PASS — duration={duration_sec:.2f}s, SNR={snr_db:.1f if snr_db else 'N/A'} dB"
    )
    return AudioQualityResult(
        passed=True,
        reject_reason=None,
        reject_message=None,
        duration_sec=round(duration_sec, 2),
        snr_db=round(snr_db, 2) if snr_db is not None else None,
    )


# ---------------------------------------------------------------------------
# Helper tính SNR
# ---------------------------------------------------------------------------
def _estimate_snr(y: "np.ndarray") -> Optional[float]:
    """
    Ước lượng SNR (dB) bằng phương pháp phân đoạn năng lượng.

    Thuật toán:
      1. Chia audio thành các frame ngắn (25ms, hop 10ms — chuẩn trong speech analysis).
      2. Tính RMS năng lượng từng frame.
      3. Signal power = trung bình năng lượng các frame NHIỀU NĂNG LƯỢNG NHẤT (top 50%).
         Lý do: đây là các frame có giọng nói thật, không phải silence/noise.
      4. Noise power = trung bình năng lượng các frame ÍT NĂNG LƯỢNG NHẤT (bottom 20%).
         Lý do: các frame im lặng ở đầu/cuối thường chứa noise floor.
      5. SNR (dB) = 10 * log10(signal_power / noise_power).

    Phương pháp này đơn giản nhưng đủ tốt cho bài toán phát hiện audio rác.
    Không dùng webrtcvad vì tránh thêm dependency C extension.

    Returns:
        SNR tính bằng dB, hoặc None nếu không tính được (audio quá ngắn/rỗng).
    """
    if len(y) < 100:
        return None

    frame_length = int(_LIBROSA_SR * 0.025)  # 25ms frame
    hop_length   = int(_LIBROSA_SR * 0.010)  # 10ms hop

    # Tính RMS từng frame
    frames = _frame_signal(y, frame_length, hop_length)
    if frames.shape[1] < 5:
        return None

    rms_per_frame = np.sqrt(np.mean(frames ** 2, axis=0))

    # Tránh log(0)
    rms_per_frame = np.where(rms_per_frame < 1e-10, 1e-10, rms_per_frame)

    n_frames = len(rms_per_frame)
    sorted_rms = np.sort(rms_per_frame)

    # Noise: bottom 20% frame (im lặng / noise floor)
    noise_frames = sorted_rms[:max(1, int(n_frames * 0.20))]
    noise_power  = float(np.mean(noise_frames ** 2))

    # Signal: top 50% frame (có giọng nói)
    signal_frames = sorted_rms[int(n_frames * 0.50):]
    signal_power  = float(np.mean(signal_frames ** 2))

    if noise_power <= 0 or signal_power <= 0:
        return None

    snr = 10.0 * np.log10(signal_power / noise_power)
    return float(snr)


def _frame_signal(y: "np.ndarray", frame_length: int, hop_length: int) -> "np.ndarray":
    """Chia tín hiệu thành các frame chồng nhau (vectorized, không dùng librosa.util.frame để tránh version issues)."""
    n_frames = 1 + (len(y) - frame_length) // hop_length
    if n_frames <= 0:
        return np.zeros((frame_length, 1))
    indices = np.arange(frame_length)[:, None] + hop_length * np.arange(n_frames)[None, :]
    # Clip indices để tránh out-of-bounds
    indices = np.clip(indices, 0, len(y) - 1)
    return y[indices]

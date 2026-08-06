"""
Trích xuất đặc trưng âm thanh — Librosa
=========================================
Author: Nguyễn Thanh Tuyền (AI & Data Architect) — hỗ trợ bởi Đoàn Hoàng Việt
Giai đoạn: 5 — Librosa Audio Feature Extraction

MỤC ĐÍCH:
  Trích xuất các đặc trưng âm học từ file audio để định lượng MỨC ĐỘ CĂNG THẲNG /
  CẢM XÚC trong giọng nói, HOÀN TOÀN ĐỘC LẬP với nội dung lời nói.
  Đây là "kênh tín hiệu thứ hai" bên cạnh kết quả ABSA từ văn bản (Giai đoạn 6),
  phục vụ cho thuật toán Dynamic Weighted Fusion để phát hiện mỉa mai / sarcasm.

CÁC ĐẶC TRƯNG ĐƯỢC TRÍCH XUẤT:
  1. MFCC (Mel-Frequency Cepstral Coefficients):
     - Mô tả "màu sắc" phổ tần của giọng nói theo thang Mel (gần với cảm nhận người nghe).
     - 13 hệ số MFCC + delta (tốc độ thay đổi) + delta-delta (gia tốc thay đổi).
     - Giọng căng thẳng/gắt có phân bố MFCC khác biệt so với giọng bình thường.

  2. F0 — Cao độ cơ bản (Fundamental Frequency / Pitch):
     - Tần số rung của dây thanh quản (Hz). Giọng bình thường: 85–255 Hz.
     - Giọng căng thẳng, tức giận thường có F0 CAO HƠN và BIẾN THIÊN NHIỀU HƠN.
     - F0 = 0 nghĩa là đoạn đó không có giọng nói (im lặng, âm vô thanh).

  3. Jitter — Biến thiên tần số:
     - Đo độ không đều đặn của chu kỳ rung dây thanh (cycle-to-cycle variation).
     - Giá trị cao → giọng run rẩy, mất kiểm soát → dấu hiệu căng thẳng/tức giận.
     - Đơn vị: tỷ lệ phần trăm (0.0 = hoàn toàn đều đặn).

  4. Shimmer — Biến thiên biên độ:
     - Đo độ không đều đặn của biên độ (volume) qua từng chu kỳ.
     - Giá trị cao → giọng không ổn định, dao động lớn → dấu hiệu căng thẳng.
     - Đơn vị: tỷ lệ phần trăm (0.0 = hoàn toàn ổn định).

  5. ZCR (Zero-Crossing Rate) — Tỷ lệ qua zero:
     - Số lần tín hiệu đổi dấu (âm → dương hoặc ngược lại) mỗi giây.
     - Giọng gắt/nhanh thường có ZCR cao hơn giọng bình thản.

  6. RMS Energy — Năng lượng hiệu dụng:
     - Đo độ lớn (loudness) trung bình của tín hiệu âm thanh.
     - Giọng tức giận thường có năng lượng cao hơn giọng bình thường.

LUỒNG SỬ DỤNG TRONG PIPELINE (phối hợp với Giai đoạn 6):
  # Giai đoạn 5: song song với Whisper STT
  audio_feats = extract_audio_features(audio_path)

  # Giai đoạn 6: ABSA từ văn bản
  absa_result = analyze_absa(transcript)

  # Giai đoạn 6 (Fusion): kết hợp 2 tín hiệu
  fusion_result = dynamic_weighted_fusion(absa_result, audio_feats)
  # → phát hiện mỉa mai nếu text dương nhưng audio có chỉ số căng thẳng cao

NGƯỠNG CĂNG THẲNG (đề xuất ban đầu, sẽ hiệu chỉnh khi có dữ liệu pilot thật):
  Xem AUDIO_STRESS_THRESHOLDS trong module này.

THƯ VIỆN:
  librosa==0.10.x — tài liệu: https://librosa.org/doc/latest/
  soundfile==0.12.x — backend đọc WAV/FLAC cho librosa
  numpy==1.26.x

CẤU HÌNH:
  Không cần API key — chạy hoàn toàn local, không gọi bên ngoài.
"""

import logging
import warnings
from pathlib import Path
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Hằng số — Ngưỡng căng thẳng đề xuất ban đầu
# ---------------------------------------------------------------------------
# ⚠️ QUAN TRỌNG: Đây là ngưỡng KHỞI TẠO GIẢ ĐỊNH dựa trên nghiên cứu học thuật
# về phân tích cảm xúc giọng nói (Emotional Speech Analysis).
# Các ngưỡng này SẼ CẦN HIỆU CHỈNH khi có dữ liệu pilot thật từ thực tế.
# Tham khảo: Schuller et al. (2013) "Computational Paralinguistics", Wiley.

AUDIO_STRESS_THRESHOLDS = {
    # F0 (pitch) — Hz. Giọng căng thẳng thường > 220 Hz với nam, > 300 Hz với nữ
    # Dùng ngưỡng trung bình 260 Hz (không phân biệt giới tính ở giai đoạn pilot)
    "f0_mean_high": 260.0,

    # Jitter — Ngưỡng bình thường < 1.04% (theo tiêu chuẩn lâm sàng)
    # > 2% là dấu hiệu rõ ràng của căng thẳng / giọng không ổn định
    "jitter_high": 0.02,

    # Shimmer — Ngưỡng bình thường < 3.81% (theo tiêu chuẩn lâm sàng)
    # > 5% là dấu hiệu căng thẳng / giọng dao động bất thường
    "shimmer_high": 0.05,

    # ZCR (Zero-Crossing Rate) — Đơn vị: lần/giây
    # > 0.15 thường thấy ở giọng gắt, nói nhanh
    "zcr_mean_high": 0.15,
}

# ---------------------------------------------------------------------------
# Custom Exceptions
# ---------------------------------------------------------------------------

class AudioFeaturesError(Exception):
    """Base exception cho lỗi trích xuất đặc trưng âm thanh."""
    pass

class AudioFileNotFoundError(AudioFeaturesError):
    """File audio không tồn tại."""
    pass

class AudioLoadError(AudioFeaturesError):
    """Không thể load file audio (định dạng lỗi, file hỏng, v.v.)."""
    pass

class AudioTooShortError(AudioFeaturesError):
    """Audio quá ngắn để trích xuất đặc trưng có ý nghĩa."""
    pass


# ---------------------------------------------------------------------------
# Hàm nội bộ — load audio
# ---------------------------------------------------------------------------

def _load_audio(audio_file_path: str) -> tuple[np.ndarray, int]:
    """
    Load file audio thành mảng numpy.

    Returns:
        (y, sr): mảng tín hiệu float32 và sample rate.

    Raises:
        AudioFileNotFoundError: File không tồn tại.
        AudioLoadError: Không thể đọc file.
        AudioTooShortError: Audio < 0.5 giây.
    """
    # Import ở đây để tránh lỗi import nếu librosa chưa cài
    try:
        import librosa
    except ImportError as e:
        raise ImportError(
            "Thư viện librosa chưa được cài đặt. "
            "Chạy: pip install librosa soundfile"
        ) from e

    audio_path = Path(audio_file_path)
    if not audio_path.exists():
        raise AudioFileNotFoundError(
            f"File audio không tồn tại: '{audio_file_path}'"
        )

    try:
        # mono=True: chuyển về mono channel để thống nhất xử lý
        # sr=None: giữ nguyên sample rate gốc (không resample, bảo toàn tần số cao)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")  # Tắt warning deprecated từ librosa
            y, sr = librosa.load(audio_file_path, sr=None, mono=True)
    except Exception as e:
        raise AudioLoadError(
            f"Không thể đọc file audio '{audio_file_path}': {type(e).__name__}: {e}"
        ) from e

    duration = len(y) / sr
    if duration < 0.5:
        raise AudioTooShortError(
            f"Audio quá ngắn: {duration:.2f} giây (tối thiểu 0.5 giây). "
            "Không thể trích xuất đặc trưng có ý nghĩa thống kê."
        )

    logger.info(
        f"[Librosa] Loaded '{audio_path.name}': "
        f"duration={duration:.2f}s, sr={sr}Hz, samples={len(y)}"
    )
    return y, sr


# ---------------------------------------------------------------------------
# Hàm nội bộ — tính từng nhóm đặc trưng
# ---------------------------------------------------------------------------

def _extract_mfcc(y: np.ndarray, sr: int, n_mfcc: int = 13) -> dict[str, Any]:
    """
    Trích xuất MFCC và các biến thể delta.

    Returns:
        dict với:
        - mfcc_mean: list[float] — giá trị trung bình của n_mfcc hệ số MFCC
        - mfcc_std: list[float] — độ lệch chuẩn (đo sự biến động)
        - mfcc_delta_mean: list[float] — tốc độ thay đổi MFCC theo thời gian
        - mfcc_delta2_mean: list[float] — gia tốc thay đổi (delta của delta)
    """
    import librosa

    # Tính MFCC: shape (n_mfcc, T) với T là số frame thời gian
    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=n_mfcc)

    # Delta — tốc độ thay đổi MFCC (order=1)
    mfcc_delta = librosa.feature.delta(mfcc, order=1)

    # Delta-delta — gia tốc thay đổi MFCC (order=2)
    mfcc_delta2 = librosa.feature.delta(mfcc, order=2)

    return {
        "mfcc_mean": [round(float(v), 4) for v in np.mean(mfcc, axis=1)],
        "mfcc_std": [round(float(v), 4) for v in np.std(mfcc, axis=1)],
        "mfcc_delta_mean": [round(float(v), 4) for v in np.mean(mfcc_delta, axis=1)],
        "mfcc_delta2_mean": [round(float(v), 4) for v in np.mean(mfcc_delta2, axis=1)],
    }


def _extract_f0(y: np.ndarray, sr: int) -> dict[str, float]:
    """
    Trích xuất F0 (cao độ cơ bản / pitch) bằng thuật toán PYIN.

    PYIN (Probabilistic YIN) là thuật toán hiện đại hơn YIN, chính xác hơn
    với giọng nói tự nhiên và ít bị ảnh hưởng bởi nhiễu nền.

    Returns:
        dict với:
        - f0_mean: float — F0 trung bình (Hz), chỉ tính frame có giọng nói (voiced)
        - f0_std: float — độ lệch chuẩn F0 (Hz), thể hiện sự biến động pitch
        - f0_min: float — F0 thấp nhất (Hz)
        - f0_max: float — F0 cao nhất (Hz)
        - voiced_fraction: float — tỷ lệ frame có giọng nói (0.0-1.0)
    """
    import librosa

    try:
        # fmin/fmax: giới hạn tìm kiếm pitch để tăng tốc và giảm lỗi octave
        # Giọng người: 65 Hz (giọng nam thấp) đến 1047 Hz (giọng nữ cao nhất)
        f0, voiced_flag, voiced_probs = librosa.pyin(
            y,
            fmin=librosa.note_to_hz('C2'),   # ~65 Hz
            fmax=librosa.note_to_hz('C7'),   # ~2093 Hz
            sr=sr,
        )
        # f0 chứa NaN cho các frame unvoiced — lọc ra để tính stats
        voiced_f0 = f0[voiced_flag] if voiced_flag is not None else f0[~np.isnan(f0)]
        voiced_f0 = voiced_f0[~np.isnan(voiced_f0)]  # safety filter

        voiced_fraction = float(np.mean(voiced_flag)) if voiced_flag is not None else 0.0

        if len(voiced_f0) == 0:
            # Không phát hiện được giọng nói có pitch (có thể là tiếng ồn/im lặng)
            logger.warning("[Librosa] Không phát hiện được F0 có ý nghĩa — audio có thể toàn im lặng hoặc nhiễu.")
            return {
                "f0_mean": 0.0,
                "f0_std": 0.0,
                "f0_min": 0.0,
                "f0_max": 0.0,
                "voiced_fraction": voiced_fraction,
            }

        return {
            "f0_mean": round(float(np.mean(voiced_f0)), 2),
            "f0_std": round(float(np.std(voiced_f0)), 2),
            "f0_min": round(float(np.min(voiced_f0)), 2),
            "f0_max": round(float(np.max(voiced_f0)), 2),
            "voiced_fraction": round(voiced_fraction, 4),
        }

    except Exception as e:
        logger.warning(f"[Librosa] Lỗi khi tính F0 (PYIN): {e} — trả về zeros")
        return {
            "f0_mean": 0.0,
            "f0_std": 0.0,
            "f0_min": 0.0,
            "f0_max": 0.0,
            "voiced_fraction": 0.0,
        }


def _extract_jitter_shimmer(y: np.ndarray, sr: int) -> dict[str, float]:
    """
    Ước tính Jitter và Shimmer từ tín hiệu âm thanh.

    Jitter và Shimmer thông thường được tính bằng phần mềm chuyên biệt (Praat).
    Ở đây dùng phương pháp xấp xỉ thông qua phân tích các chu kỳ pitch từ PYIN,
    phù hợp cho mục đích phát hiện căng thẳng tương đối (không cần độ chính xác
    lâm sàng tuyệt đối).

    PHƯƠNG PHÁP XẤP XỈ:
      - Jitter: std(chu kỳ) / mean(chu kỳ) — biến thiên tương đối của chu kỳ
      - Shimmer: std(biên độ RMS theo frame) / mean(biên độ) — biến thiên biên độ

    Returns:
        dict với:
        - jitter: float — biến thiên chu kỳ tương đối (0.0 = hoàn toàn đều)
        - shimmer: float — biến thiên biên độ tương đối (0.0 = hoàn toàn ổn định)
    """
    import librosa

    # --- Jitter: xấp xỉ qua nghịch đảo F0 ---
    try:
        f0, voiced_flag, _ = librosa.pyin(
            y,
            fmin=librosa.note_to_hz('C2'),
            fmax=librosa.note_to_hz('C7'),
            sr=sr,
        )
        voiced_f0 = f0[voiced_flag] if voiced_flag is not None else f0[~np.isnan(f0)]
        voiced_f0 = voiced_f0[~np.isnan(voiced_f0)]

        if len(voiced_f0) > 1:
            # Chu kỳ = 1/F0 (giây). Jitter = std(T)/mean(T)
            periods = 1.0 / voiced_f0
            jitter = float(np.std(periods) / np.mean(periods))
        else:
            jitter = 0.0
    except Exception:
        jitter = 0.0

    # --- Shimmer: biến thiên RMS energy theo từng frame ---
    try:
        hop_length = 512
        rms = librosa.feature.rms(y=y, hop_length=hop_length)[0]  # shape (T,)
        # Chỉ lấy frame có năng lượng đáng kể (loại im lặng)
        active_rms = rms[rms > np.percentile(rms, 20)]
        if len(active_rms) > 1 and np.mean(active_rms) > 0:
            shimmer = float(np.std(active_rms) / np.mean(active_rms))
        else:
            shimmer = 0.0
    except Exception:
        shimmer = 0.0

    return {
        "jitter": round(jitter, 6),
        "shimmer": round(shimmer, 6),
    }


def _extract_zcr_and_energy(y: np.ndarray, sr: int) -> dict[str, float]:
    """
    Trích xuất Zero-Crossing Rate (ZCR) và RMS Energy.

    Returns:
        dict với:
        - zcr_mean: float — ZCR trung bình (tỷ lệ crossing/sample)
        - zcr_std: float — độ lệch chuẩn ZCR
        - rms_energy_mean: float — năng lượng RMS trung bình
        - rms_energy_std: float — độ lệch chuẩn năng lượng
    """
    import librosa

    hop_length = 512

    # Zero-Crossing Rate
    zcr = librosa.feature.zero_crossing_rate(y, hop_length=hop_length)[0]

    # RMS Energy
    rms = librosa.feature.rms(y=y, hop_length=hop_length)[0]

    return {
        "zcr_mean": round(float(np.mean(zcr)), 6),
        "zcr_std": round(float(np.std(zcr)), 6),
        "rms_energy_mean": round(float(np.mean(rms)), 6),
        "rms_energy_std": round(float(np.std(rms)), 6),
    }


def _compute_stress_score(features: dict[str, Any]) -> dict[str, Any]:
    """
    Tính điểm căng thẳng tổng hợp (0.0 → 1.0) dựa trên các ngưỡng đề xuất.

    Đây là ĐIỂM ƯỚC TÍNH BAN ĐẦU, chưa qua học máy — dùng simple threshold counting.
    Giai đoạn 6 (Fusion) sẽ dùng điểm này để so sánh với kết quả ABSA từ văn bản.

    ⚠️ Ngưỡng dùng theo AUDIO_STRESS_THRESHOLDS — cần hiệu chỉnh với dữ liệu thật.

    Returns:
        dict với:
        - stress_score: float (0.0-1.0) — điểm căng thẳng tổng hợp
        - stress_indicators: list[str] — các chỉ số vượt ngưỡng
        - is_stressed: bool — True nếu stress_score > 0.5
    """
    indicators = []
    thresholds = AUDIO_STRESS_THRESHOLDS

    # Kiểm tra từng chỉ số
    f0_mean = features.get("f0_mean", 0.0)
    if f0_mean > thresholds["f0_mean_high"]:
        indicators.append(f"f0_mean_high ({f0_mean:.1f}Hz > {thresholds['f0_mean_high']}Hz)")

    jitter = features.get("jitter", 0.0)
    if jitter > thresholds["jitter_high"]:
        indicators.append(f"jitter_high ({jitter:.4f} > {thresholds['jitter_high']})")

    shimmer = features.get("shimmer", 0.0)
    if shimmer > thresholds["shimmer_high"]:
        indicators.append(f"shimmer_high ({shimmer:.4f} > {thresholds['shimmer_high']})")

    zcr_mean = features.get("zcr_mean", 0.0)
    if zcr_mean > thresholds["zcr_mean_high"]:
        indicators.append(f"zcr_mean_high ({zcr_mean:.4f} > {thresholds['zcr_mean_high']})")

    # Điểm = tỷ lệ chỉ số vượt ngưỡng / tổng số chỉ số kiểm tra
    total_checks = 4
    stress_score = len(indicators) / total_checks

    return {
        "stress_score": round(stress_score, 4),
        "stress_indicators": indicators,
        "is_stressed": stress_score > 0.4,  # > 40% chỉ số vượt ngưỡng → coi là căng thẳng
    }


# ---------------------------------------------------------------------------
# Hàm chính — Public API
# ---------------------------------------------------------------------------

def extract_audio_features(audio_file_path: str) -> dict[str, Any]:
    """
    Trích xuất toàn bộ đặc trưng âm thanh từ file audio để phục vụ Giai đoạn 6
    (Dynamic Weighted Fusion — phát hiện mỉa mai / sarcasm trong phản hồi khách hàng).

    Các chỉ số được trích xuất PHẢN ÁNH TRẠNG THÁI CẢM XÚC TRONG GIỌNG NÓI,
    hoàn toàn độc lập với ý nghĩa câu chữ. Đây là yếu tố chủ chốt để phát hiện
    mỉa mai: khi văn bản tích cực ("phục vụ tốt quá ha") nhưng giọng gắt/căng.

    Args:
        audio_file_path: Đường dẫn đến file audio (.wav, .webm, .mp3, .ogg, .flac, .m4a).
                         File được xử lý hoàn toàn local — không gọi API bên ngoài.

    Returns:
        dict với cấu trúc:
        {
            "file_info": {
                "filename": str,          # Tên file
                "duration_seconds": float, # Thời lượng (giây)
                "sample_rate": int,        # Sample rate (Hz)
            },
            "mfcc_mean": list[float],     # 13 hệ số MFCC trung bình
            "mfcc_std": list[float],      # 13 hệ số MFCC độ lệch chuẩn
            "mfcc_delta_mean": list[float], # 13 hệ số MFCC-delta trung bình
            "mfcc_delta2_mean": list[float], # 13 hệ số MFCC-delta2 trung bình
            "f0_mean": float,             # Cao độ trung bình (Hz), 0 = không có giọng
            "f0_std": float,              # Độ biến thiên pitch (Hz)
            "f0_min": float,              # Pitch thấp nhất (Hz)
            "f0_max": float,              # Pitch cao nhất (Hz)
            "voiced_fraction": float,     # Tỷ lệ frame có giọng nói (0.0-1.0)
            "jitter": float,              # Biến thiên chu kỳ (0.0 = ổn định)
            "shimmer": float,             # Biến thiên biên độ (0.0 = ổn định)
            "zcr_mean": float,            # Zero-crossing rate trung bình
            "zcr_std": float,             # Zero-crossing rate độ lệch chuẩn
            "rms_energy_mean": float,     # Năng lượng RMS trung bình
            "rms_energy_std": float,      # Năng lượng RMS độ lệch chuẩn
            "stress_score": float,        # Điểm căng thẳng tổng hợp (0.0-1.0)
            "stress_indicators": list[str], # Chỉ số nào vượt ngưỡng căng thẳng
            "is_stressed": bool,          # True nếu phát hiện giọng căng thẳng
        }

    Raises:
        AudioFileNotFoundError: File không tồn tại.
        AudioLoadError: Không thể đọc file (hỏng, codec không hỗ trợ).
        AudioTooShortError: Audio < 0.5 giây.
        ImportError: librosa hoặc soundfile chưa được cài đặt.
    """
    import librosa

    # --- Bước 1: Load audio ---
    y, sr = _load_audio(audio_file_path)
    duration = len(y) / sr

    logger.info(
        f"[Librosa] Bắt đầu trích xuất đặc trưng: '{Path(audio_file_path).name}' "
        f"({duration:.2f}s, {sr}Hz)"
    )

    # --- Bước 2: Trích xuất từng nhóm đặc trưng ---
    mfcc_features = _extract_mfcc(y, sr, n_mfcc=13)
    f0_features = _extract_f0(y, sr)
    jitter_shimmer = _extract_jitter_shimmer(y, sr)
    zcr_energy = _extract_zcr_and_energy(y, sr)

    # --- Bước 3: Gộp tất cả đặc trưng ---
    all_features: dict[str, Any] = {
        "file_info": {
            "filename": Path(audio_file_path).name,
            "duration_seconds": round(duration, 3),
            "sample_rate": sr,
        },
        **mfcc_features,
        **f0_features,
        **jitter_shimmer,
        **zcr_energy,
    }

    # --- Bước 4: Tính điểm căng thẳng tổng hợp ---
    stress_result = _compute_stress_score(all_features)
    all_features.update(stress_result)

    logger.info(
        f"[Librosa] Hoàn thành trích xuất | "
        f"f0_mean={all_features['f0_mean']}Hz | "
        f"jitter={all_features['jitter']:.4f} | "
        f"shimmer={all_features['shimmer']:.4f} | "
        f"stress_score={all_features['stress_score']} | "
        f"is_stressed={all_features['is_stressed']}"
    )

    return all_features

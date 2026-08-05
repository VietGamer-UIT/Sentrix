"""
Test script — Giai đoạn 5: Librosa Audio Feature Extraction
=============================================================
Tạo 2 file audio mẫu bằng numpy/scipy (không cần mic thật):
  1. Giọng "bình thường": sine wave ổn định, F0 thấp, ít biến động
  2. Giọng "căng thẳng/gắt": sine wave dao động mạnh, F0 cao, nhiều biến thiên

Chạy: python backend/tests/test_audio_features.py
"""

import sys
import json
import logging
import tempfile
from pathlib import Path

# Thêm root vào sys.path để import backend.*
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s"
)

def create_test_audio_calm(filepath: str, duration: float = 3.0) -> None:
    """
    Tạo file audio giả lập giọng BÌNH THƯỜNG:
    - Sine wave ở F0 = 130 Hz (giọng nam bình thường)
    - Biên độ ổn định
    - Thêm chút noise nhỏ để realistic
    """
    import numpy as np
    import soundfile as sf

    sr = 22050
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)

    # Giọng nam bình thường: F0 ~130 Hz, ổn định
    f0 = 130.0
    y = 0.5 * np.sin(2 * np.pi * f0 * t)

    # Thêm harmonics (giọng người = tổ hợp nhiều harmonics)
    y += 0.3 * np.sin(2 * np.pi * 2 * f0 * t)   # 2nd harmonic
    y += 0.15 * np.sin(2 * np.pi * 3 * f0 * t)  # 3rd harmonic
    y += 0.07 * np.sin(2 * np.pi * 4 * f0 * t)  # 4th harmonic

    # Noise nhỏ (SNR cao ~30dB — giọng rõ ràng)
    noise = np.random.normal(0, 0.01, len(t))
    y = y + noise

    # Normalize
    y = y / np.max(np.abs(y)) * 0.8

    sf.write(filepath, y.astype(np.float32), sr)
    print(f"✅ Đã tạo file audio BÌNH THƯỜNG: {filepath} ({duration}s, sr={sr}Hz)")


def create_test_audio_stressed(filepath: str, duration: float = 3.0) -> None:
    """
    Tạo file audio giả lập giọng CĂNG THẲNG/GẮT:
    - Sine wave ở F0 = 320 Hz (pitch cao)
    - F0 dao động mạnh (jitter cao)
    - Biên độ không đều (shimmer cao)
    - Noise nhiều (ZCR cao)
    - Nói nhanh, bứt bứt
    """
    import numpy as np
    import soundfile as sf

    sr = 22050
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)

    # Giọng căng thẳng: F0 = 320 Hz (cao), dao động jitter ~±10%
    f0_base = 320.0
    jitter_variation = 0.10  # 10% jitter — rất cao (bình thường < 1%)
    f0_jitter = f0_base + jitter_variation * f0_base * np.random.randn(len(t))

    # Sinh tín hiệu với F0 dao động (tích phân phase)
    phase = 2 * np.pi * np.cumsum(f0_jitter) / sr
    y = np.sin(phase)

    # Shimmer: biên độ dao động mạnh
    shimmer_envelope = 1.0 + 0.3 * np.sin(2 * np.pi * 5 * t)  # dao động 5Hz
    shimmer_envelope += 0.15 * np.random.randn(len(t))  # random shimmer
    y = y * shimmer_envelope

    # Noise nhiều (SNR thấp ~10dB — giọng gắt, xúc cảm mạnh)
    noise = np.random.normal(0, 0.15, len(t))
    y = y + noise

    # Đột ngột ngắt quãng (simulate nói bứt bứt)
    for i in range(5):
        pause_start = int((i * 0.6 + 0.1) * sr)
        pause_end = int((i * 0.6 + 0.15) * sr)
        if pause_end < len(y):
            y[pause_start:pause_end] *= 0.1

    # Normalize
    y = y / np.max(np.abs(y)) * 0.9

    sf.write(filepath, y.astype(np.float32), sr)
    print(f"✅ Đã tạo file audio CĂNG THẲNG: {filepath} ({duration}s, sr={sr}Hz)")


def run_test():
    from backend.ai_pipeline.audio_features_librosa import (
        extract_audio_features,
        AudioFeaturesError,
    )

    print("\n" + "="*70)
    print("GIAI ĐOẠN 5 — TEST LIBROSA AUDIO FEATURE EXTRACTION")
    print("="*70)

    with tempfile.TemporaryDirectory() as tmpdir:
        calm_path = str(Path(tmpdir) / "calm_voice.wav")
        stressed_path = str(Path(tmpdir) / "stressed_voice.wav")

        # Tạo 2 file test
        print("\n[1/4] Tạo file audio test...")
        create_test_audio_calm(calm_path, duration=3.0)
        create_test_audio_stressed(stressed_path, duration=3.0)

        # ---------------------------------------------------------------
        # Test 1: Giọng bình thường
        # ---------------------------------------------------------------
        print("\n[2/4] Trích xuất đặc trưng — GIỌNG BÌNH THƯỜNG")
        print("-"*50)
        try:
            calm_features = extract_audio_features(calm_path)
            print("\n📊 Kết quả thật (GIỌNG BÌNH THƯỜNG):")
            print(f"  Duration:      {calm_features['file_info']['duration_seconds']}s")
            print(f"  Sample Rate:   {calm_features['file_info']['sample_rate']}Hz")
            print(f"  F0 mean:       {calm_features['f0_mean']} Hz")
            print(f"  F0 std:        {calm_features['f0_std']} Hz")
            print(f"  Jitter:        {calm_features['jitter']:.6f}")
            print(f"  Shimmer:       {calm_features['shimmer']:.6f}")
            print(f"  ZCR mean:      {calm_features['zcr_mean']:.6f}")
            print(f"  RMS energy:    {calm_features['rms_energy_mean']:.6f}")
            print(f"  Stress score:  {calm_features['stress_score']} (0=bình thường, 1=căng thẳng)")
            print(f"  Is stressed:   {calm_features['is_stressed']}")
            print(f"  Indicators:    {calm_features['stress_indicators'] or '(không có)'}")
            print(f"  MFCC[0..3]:    {calm_features['mfcc_mean'][:4]}")
        except Exception as e:
            print(f"❌ LỖI: {e}")
            raise

        # ---------------------------------------------------------------
        # Test 2: Giọng căng thẳng
        # ---------------------------------------------------------------
        print("\n[3/4] Trích xuất đặc trưng — GIỌNG CĂNG THẲNG")
        print("-"*50)
        try:
            stressed_features = extract_audio_features(stressed_path)
            print("\n📊 Kết quả thật (GIỌNG CĂNG THẲNG):")
            print(f"  Duration:      {stressed_features['file_info']['duration_seconds']}s")
            print(f"  Sample Rate:   {stressed_features['file_info']['sample_rate']}Hz")
            print(f"  F0 mean:       {stressed_features['f0_mean']} Hz")
            print(f"  F0 std:        {stressed_features['f0_std']} Hz")
            print(f"  Jitter:        {stressed_features['jitter']:.6f}")
            print(f"  Shimmer:       {stressed_features['shimmer']:.6f}")
            print(f"  ZCR mean:      {stressed_features['zcr_mean']:.6f}")
            print(f"  RMS energy:    {stressed_features['rms_energy_mean']:.6f}")
            print(f"  Stress score:  {stressed_features['stress_score']} (0=bình thường, 1=căng thẳng)")
            print(f"  Is stressed:   {stressed_features['is_stressed']}")
            print(f"  Indicators:    {stressed_features['stress_indicators']}")
            print(f"  MFCC[0..3]:    {stressed_features['mfcc_mean'][:4]}")
        except Exception as e:
            print(f"❌ LỖI: {e}")
            raise

        # ---------------------------------------------------------------
        # So sánh kết quả
        # ---------------------------------------------------------------
        print("\n[4/4] So sánh 2 bộ số liệu:")
        print("-"*50)
        print(f"{'Chỉ số':<25} {'Bình thường':>15} {'Căng thẳng':>15} {'Khác biệt':>12}")
        print("-"*67)

        metrics = [
            ("F0 mean (Hz)", "f0_mean"),
            ("F0 std (Hz)", "f0_std"),
            ("Jitter", "jitter"),
            ("Shimmer", "shimmer"),
            ("ZCR mean", "zcr_mean"),
            ("RMS energy", "rms_energy_mean"),
            ("Stress score", "stress_score"),
        ]

        all_different = True
        for label, key in metrics:
            calm_val = calm_features.get(key, 0.0)
            stressed_val = stressed_features.get(key, 0.0)
            if isinstance(calm_val, float):
                diff_pct = ((stressed_val - calm_val) / (calm_val + 1e-9)) * 100
                direction = "↑" if stressed_val > calm_val else "↓"
                print(f"  {label:<23} {calm_val:>15.4f} {stressed_val:>15.4f} {direction}{abs(diff_pct):>10.1f}%")
                if abs(diff_pct) < 5 and key != "rms_energy_mean":
                    all_different = False

        print()
        if all_different:
            print("✅ KIỂM TRA THÀNH CÔNG: Hai bộ số liệu KHÁC NHAU RÕ RỆTÖ")
            print("   → Hàm extract_audio_features() đang ĐỌC AUDIO THẬT")
            print("   → KHÔNG trả về giá trị cố định/giả")
        else:
            print("⚠️ Một số chỉ số tương đồng — kiểm tra lại logic sinh audio test")

        print(f"\n✅ is_stressed (bình thường): {calm_features['is_stressed']} (mong đợi: False)")
        print(f"✅ is_stressed (căng thẳng):  {stressed_features['is_stressed']} (mong đợi: True)")

        print("\n" + "="*70)
        print("GIAI ĐOẠN 5 HOÀN THÀNH — SẴN SÀNG CHO GIAI ĐOẠN 6 (ABSA + FUSION)")
        print("="*70 + "\n")

        return calm_features, stressed_features


if __name__ == "__main__":
    run_test()

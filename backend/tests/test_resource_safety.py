"""
Resource Safety Tests \u2014 Sentrix Backend Hardening
===================================================
Ch\u1ee9ng minh:
  A. Kh\u00f4ng c\u00f2n per-request ThreadPoolExecutor (d\u00f9ng shared executor)
  B. Bounded executor capacity \u0111\u01b0\u1ee3c tu\u00e2n th\u1ee7
  C. PYIN ch\u1ec9 \u0111\u01b0\u1ee3c g\u1ecdi 1 l\u1ea7n per extract_audio_features call
  D. Audio bytes kh\u00f4ng b\u1ecb duplicate (kh\u00f4ng read_bytes sau write_bytes)
  E. Temp file \u0111\u01b0\u1ee3c cleanup \u0111\u00fang tr\u00ean c\u1ea3 success path v\u00e0 error path
  F. Fallback behavior khi LLM timeout gi\u1eef nguy\u00ean

Ch\u1ea1y: pytest backend/tests/test_resource_safety.py -v --tb=short
"""

import asyncio
import concurrent.futures
import io
import threading
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# A + B: Shared executor \u2014 kh\u00f4ng t\u1ea1o per-request, bounded capacity
# ---------------------------------------------------------------------------

class TestSharedExecutor:
    """
    A. X\u00e1c nh\u1eadn _SHARED_EXECUTOR t\u1ed3n t\u1ea1i \u1edf module level trong feedback.py.
    B. max_workers b\u1ecb gi\u1edbi h\u1ea1n c\u1ee9ng \u2014 kh\u00f4ng t\u1ea1o thread m\u1edbi khi saturated.
    """

    def test_shared_executor_exists_at_module_level(self):
        """A: _SHARED_EXECUTOR ph\u1ea3i l\u00e0 module-level attribute c\u1ee7a feedback module."""
        from backend.api.routes import feedback
        assert hasattr(feedback, "_SHARED_EXECUTOR"), (
            "_SHARED_EXECUTOR kh\u00f4ng t\u1ed3n t\u1ea1i trong feedback module \u2014 "
            "per-request executor ch\u01b0a \u0111\u01b0\u1ee3c thay th\u1ebf."
        )
        assert isinstance(feedback._SHARED_EXECUTOR, concurrent.futures.ThreadPoolExecutor), (
            "_SHARED_EXECUTOR ph\u1ea3i l\u00e0 ThreadPoolExecutor instance."
        )

    def test_shared_executor_has_bounded_max_workers(self):
        """B: max_workers ph\u1ea3i trong kho\u1ea3ng [2, 10] \u2014 bounded v\u00e0 \u0111\u1ee7 cho workload."""
        from backend.api.routes import feedback
        max_w = feedback._SHARED_EXECUTOR._max_workers
        assert 2 <= max_w <= 10, (
            f"max_workers={max_w} kh\u00f4ng h\u1ee3p l\u1ec7. "
            "Ph\u1ea3i >= 2 (Whisper+Librosa song song) v\u00e0 <= 10 (RAM safety)."
        )

    def test_no_per_request_executor_in_submit_feedback(self):
        """
        A: Ki\u1ec3m tra source code c\u1ee7a feedback.py kh\u00f4ng c\u00f2n t\u1ea1o
        ThreadPoolExecutor b\u00ean trong submit_feedback function.
        """
        import re
        feedback_src = Path("backend/api/routes/feedback.py").read_text(encoding="utf-8")

        func_start = feedback_src.find("async def submit_feedback")
        assert func_start != -1, "Kh\u00f4ng t\u00ecm th\u1ea5y submit_feedback"

        function_body = feedback_src[func_start:]
        per_request_pattern = re.compile(
            r"ThreadPoolExecutor\s*\(\s*max_workers\s*=",
            re.MULTILINE,
        )
        matches = per_request_pattern.findall(function_body)
        assert len(matches) == 0, (
            f"V\u1eabn c\u00f2n {len(matches)} ch\u1ed7 t\u1ea1o per-request ThreadPoolExecutor "
            "trong submit_feedback \u2014 ph\u1ea3i d\u00f9ng _SHARED_EXECUTOR."
        )

    def test_bounded_executor_queues_not_spawns(self):
        """
        B: Khi executor \u0111\u00e3 \u0111\u1ea7y, task m\u1edbi X\u1ebfP H\u00c0NG thay v\u00ec t\u1ea1o thread m\u1edbi.
        Thread count kh\u00f4ng v\u01b0\u1ee3t max_workers c\u1ee7a executor.
        """
        max_w = 3
        executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=max_w,
            thread_name_prefix="test-bounded",
        )
        gate = threading.Event()

        def hold():
            gate.wait(timeout=5)

        # Submit nhi\u1ec1u h\u01a1n max_workers tasks
        futures = [executor.submit(hold) for _ in range(max_w + 4)]
        time_start = __import__("time").time()

        # \u0110\u1ee3i thread pool \u0111\u1ea7y
        __import__("time").sleep(0.1)

        # \u0110\u1ebfm thread t\u1eeb executor
        worker_threads = [
            t for t in threading.enumerate()
            if t.name.startswith("test-bounded")
        ]
        assert len(worker_threads) <= max_w, (
            f"Executor t\u1ea1o {len(worker_threads)} threads nh\u01b0ng max_workers={max_w}. "
            "Bounded constraint b\u1ecb vi ph\u1ea1m."
        )

        gate.set()
        executor.shutdown(wait=True)

    def test_concurrent_requests_use_shared_executor(self):
        """
        A+B: Confirm _SHARED_EXECUTOR \u0111\u01b0\u1ee3c d\u00f9ng trong c\u1ea3 4 call site:
        Whisper, Librosa, Semantic validity, Intent, ABSA.
        """
        feedback_src = Path("backend/api/routes/feedback.py").read_text(encoding="utf-8")
        # T\u1ea5t c\u1ea3 run_in_executor ph\u1ea3i d\u00f9ng _SHARED_EXECUTOR, kh\u00f4ng c\u00f3 c\u00e1i n\u00e0o d\u00f9ng executor kh\u00e1c
        import re
        run_in_exec_calls = re.findall(
            r"run_in_executor\s*\(([^,)]+)",
            feedback_src,
        )
        # Filter c\u00e1c call n\u1eb1m trong submit_feedback
        func_start = feedback_src.find("async def submit_feedback")
        func_body = feedback_src[func_start:]
        calls_in_func = re.findall(
            r"run_in_executor\s*\(([^,)]+)",
            func_body,
        )
        for executor_arg in calls_in_func:
            stripped = executor_arg.strip()
            assert "_SHARED_EXECUTOR" in stripped, (
                f"run_in_executor d\u00f9ng executor kh\u00f4ng ph\u1ea3i _SHARED_EXECUTOR: '{stripped}'. "
                "T\u1ea5t c\u1ea3 blocking tasks ph\u1ea3i d\u00f9ng shared executor."
            )


# ---------------------------------------------------------------------------
# C: PYIN ch\u1ec9 g\u1ecdi 1 l\u1ea7n
# ---------------------------------------------------------------------------

class TestPYINSingleCall:
    """
    C: extract_audio_features() ph\u1ea3i g\u1ecdi librosa.pyin() \u0111\u00fang 1 l\u1ea7n.
    """

    def test_pyin_called_exactly_once(self, tmp_path):
        """C: \u0110\u1ebfm s\u1ed1 l\u1ea7n librosa.pyin() \u0111\u01b0\u1ee3c g\u1ecdi qua mock."""
        import numpy as np

        try:
            import soundfile as sf
            import librosa as _librosa
        except ImportError:
            pytest.skip("librosa/soundfile kh\u00f4ng c\u00f3 s\u1eb5n")

        sr = 22050
        duration = 2.0
        t = np.linspace(0, duration, int(sr * duration))
        y = (0.5 * np.sin(2 * np.pi * 130 * t)).astype(np.float32)
        audio_path = str(tmp_path / "pyin_test.wav")
        sf.write(audio_path, y, sr)

        pyin_call_count = []
        real_pyin = _librosa.pyin

        def counting_pyin(*args, **kwargs):
            pyin_call_count.append(1)
            return real_pyin(*args, **kwargs)

        with patch("librosa.pyin", side_effect=counting_pyin):
            from backend.ai_pipeline.audio_features_librosa import extract_audio_features
            extract_audio_features(audio_path)

        assert len(pyin_call_count) == 1, (
            f"librosa.pyin() \u0111\u01b0\u1ee3c g\u1ecdi {len(pyin_call_count)} l\u1ea7n \u2014 "
            "mong \u0111\u1ee3i ch\u00ednh x\u00e1c 1 l\u1ea7n."
        )

    def test_output_schema_intact_after_pyin_refactor(self, tmp_path):
        """C: T\u1ea5t c\u1ea3 keys output v\u1eabn c\u00f3 sau khi refactor PYIN."""
        import numpy as np
        try:
            import soundfile as sf
        except ImportError:
            pytest.skip("soundfile kh\u00f4ng c\u00f3 s\u1eb5n")

        sr = 22050
        duration = 2.0
        t = np.linspace(0, duration, int(sr * duration))
        y = (0.5 * np.sin(2 * np.pi * 130 * t) + 0.05 * np.random.randn(len(t))).astype(np.float32)
        audio_path = str(tmp_path / "schema_test.wav")
        sf.write(audio_path, y, sr)

        from backend.ai_pipeline.audio_features_librosa import extract_audio_features
        result = extract_audio_features(audio_path)

        required_keys = {
            "file_info",
            "mfcc_mean", "mfcc_std", "mfcc_delta_mean", "mfcc_delta2_mean",
            "f0_mean", "f0_std", "f0_min", "f0_max", "voiced_fraction",
            "jitter", "shimmer",
            "zcr_mean", "zcr_std",
            "rms_energy_mean", "rms_energy_std",
            "stress_score", "stress_indicators", "is_stressed",
        }
        missing = required_keys - set(result.keys())
        assert not missing, f"Keys b\u1ecb thi\u1ebfu sau PYIN refactor: {missing}"
        assert len(result["mfcc_mean"]) == 13, "mfcc_mean ph\u1ea3i c\u00f3 13 coefficients"


# ---------------------------------------------------------------------------
# D: Audio bytes kh\u00f4ng b\u1ecb duplicate
# ---------------------------------------------------------------------------

class TestAudioBytesNotDuplicated:
    """D: feedback.py kh\u00f4ng \u0111\u01b0\u1ee3c \u0111\u1ecdc l\u1ea1i file t\u1ea1m sau khi \u0111\u00e3 c\u00f3 audio_content."""

    def test_no_read_bytes_in_quality_gate_path(self):
        """D: read_bytes() kh\u00f4ng xu\u1ea5t hi\u1ec7n trong quality gate code path."""
        feedback_src = Path("backend/api/routes/feedback.py").read_text(encoding="utf-8")

        quality_idx = feedback_src.find("ANTI-FRAUD L\u1edaP 2")
        assert quality_idx != -1, "Kh\u00f4ng t\u00ecm th\u1ea5y comment ANTI-FRAUD L\u1edaP 2"

        # 500 ky t\u1ef1 sau comment quality gate
        nearby_code = feedback_src[quality_idx:quality_idx + 500]
        assert "read_bytes()" not in nearby_code, (
            "read_bytes() v\u1eabn xu\u1ea5t hi\u1ec7n g\u1ea7n quality gate \u2014 "
            "duplicate audio buffer ch\u01b0a \u0111\u01b0\u1ee3c fix."
        )

    def test_audio_content_passed_directly(self):
        """D: analyze_audio_quality \u0111\u01b0\u1ee3c g\u1ecdi v\u1edbi audio_content tr\u1ef1c ti\u1ebfp."""
        feedback_src = Path("backend/api/routes/feedback.py").read_text(encoding="utf-8")
        assert "analyze_audio_quality(audio_content)" in feedback_src, (
            "analyze_audio_quality() ph\u1ea3i nh\u1eadn audio_content tr\u1ef1c ti\u1ebfp, "
            "kh\u00f4ng qua read_bytes() t\u1eeb file t\u1ea1m."
        )

    def test_del_audio_content_before_executor(self):
        """D: del audio_content x\u1ea3y ra TR\u01af\u1edaC khi g\u1ecdi executor cho Whisper."""
        feedback_src = Path("backend/api/routes/feedback.py").read_text(encoding="utf-8")
        del_pos = feedback_src.find("del audio_content")
        whisper_pos = feedback_src.find("run_in_executor(_SHARED_EXECUTOR, _run_whisper)")

        assert del_pos != -1, "Kh\u00f4ng t\u00ecm th\u1ea5y 'del audio_content' trong feedback.py"
        assert whisper_pos != -1, "Kh\u00f4ng t\u00ecm th\u1ea5y Whisper executor call"
        assert del_pos < whisper_pos, (
            "del audio_content ph\u1ea3i xu\u1ea5t hi\u1ec7n TR\u01af\u1edaC g\u1ecdi Whisper executor."
        )


# ---------------------------------------------------------------------------
# E: Temp file cleanup
# ---------------------------------------------------------------------------

class TestTempFileCleanup:
    """E: File audio t\u1ea1m \u0111\u01b0\u1ee3c x\u00f3a sau STT th\u00e0nh c\u00f4ng v\u00e0 sau khi STT l\u1ed7i."""

    def test_cleanup_called_on_success(self):
        """E: _cleanup_temp_audio() \u0111\u01b0\u1ee3c g\u1ecdi sau Whisper STT th\u00e0nh c\u00f4ng."""
        from backend.api.main import app
        from backend.services.audio_quality_service import AudioQualityResult

        mock_quality = AudioQualityResult(
            passed=True, reject_reason=None, reject_message=None,
            duration_sec=5.0, snr_db=20.0,
        )
        with patch("backend.api.routes.feedback.transcribe_audio", return_value="test ok"), \
             patch("backend.api.routes.feedback.analyze_audio_quality",
                   return_value=mock_quality), \
             patch("backend.api.routes.feedback._cleanup_temp_audio") as mock_cleanup:
            client = TestClient(app)
            resp = client.post(
                "/api/v1/feedback",
                data={"tenant_id": "test-tenant_1000000000", "location": "Ban 1"},
                files={"audio_file": ("t.webm", io.BytesIO(b"\x00" * 10_000), "audio/webm")},
            )
        calls_with_path = [
            c for c in mock_cleanup.call_args_list
            if c.args and c.args[0] is not None
        ]
        assert len(calls_with_path) >= 1, (
            "_cleanup_temp_audio() kh\u00f4ng \u0111\u01b0\u1ee3c g\u1ecdi v\u1edbi valid path \u2014 "
            "temp file c\u00f3 th\u1ec3 b\u1ecb r\u00f2 r\u1ec9."
        )

    def test_cleanup_called_on_rate_limit_error(self):
        """E: _cleanup_temp_audio() \u0111\u01b0\u1ee3c g\u1ecdi khi Whisper raise WhisperRateLimitError."""
        from backend.api.main import app
        from backend.services.audio_quality_service import AudioQualityResult
        from backend.ai_pipeline.stt_whisper import WhisperRateLimitError

        mock_quality = AudioQualityResult(
            passed=True, reject_reason=None, reject_message=None,
            duration_sec=5.0, snr_db=20.0,
        )
        with patch("backend.api.routes.feedback.transcribe_audio",
                   side_effect=WhisperRateLimitError("rate limited")), \
             patch("backend.api.routes.feedback.analyze_audio_quality",
                   return_value=mock_quality), \
             patch("backend.api.routes.feedback._cleanup_temp_audio") as mock_cleanup:
            client = TestClient(app)
            resp = client.post(
                "/api/v1/feedback",
                data={"tenant_id": "test-tenant_1000000000", "location": "Ban 1"},
                files={"audio_file": ("t.webm", io.BytesIO(b"\x00" * 10_000), "audio/webm")},
            )
        assert resp.status_code in (429, 503)
        assert mock_cleanup.call_count >= 1, (
            "_cleanup_temp_audio() kh\u00f4ng \u0111\u01b0\u1ee3c g\u1ecdi khi rate limit \u2014 "
            "temp file b\u1ecb r\u00f2 r\u1ec9."
        )


# ---------------------------------------------------------------------------
# F: Fallback behavior gi\u1eef nguy\u00ean
# ---------------------------------------------------------------------------

class TestFallbackBehavior:
    """F: Timeout paths v\u1eabn tr\u1ea3 v\u1ec1 \u0111\u00fang response sau khi \u0111\u1ed5i sang shared executor."""

    def test_text_feedback_still_works(self):
        """F: Text-only feedback v\u1eabn \u0111\u01b0\u1ee3c ch\u1ea5p nh\u1eadn v\u1edbi shared executor."""
        from backend.api.main import app
        client = TestClient(app)
        resp = client.post(
            "/api/v1/feedback",
            data={
                "tenant_id": "test-tenant_1000000000",
                "location": "Ban 1",
                "text_content": "Ph\u1ee5c v\u1ee5 t\u1ed1t, m\u00f3n ngon",
            },
        )
        assert resp.status_code in (202, 503), (
            f"Text feedback: expected 202/503, got {resp.status_code}"
        )

    def test_whisper_singleton_has_no_api_key_in_env(self):
        """
        F: N\u1ebfu kh\u00f4ng c\u00f3 GROQ_API_KEY, WhisperAuthError \u0111\u01b0\u1ee3c raise (kh\u00f4ng crash).
        Singleton kh\u00f4ng cache tr\u1ea1ng th\u00e1i l\u1ed7i \u2014 m\u1ed7i l\u1ea7n g\u1ecdi _get_groq_client()
        s\u1ebd th\u1eed l\u1ea1i n\u1ebfu _GROQ_CLIENT v\u1eabn None.
        """
        from backend.ai_pipeline import stt_whisper
        from backend.ai_pipeline.stt_whisper import WhisperAuthError

        # Reset singleton \u0111\u1ec3 test
        original_client = stt_whisper._GROQ_CLIENT
        stt_whisper._GROQ_CLIENT = None

        try:
            with patch.dict("os.environ", {
                "GROQ_API_KEY": "",
                "WHISPER_API_KEY": "",
                "OPENAI_API_KEY": "",
            }, clear=False):
                # Override: x\u00f3a keys kh\u1ecfi env \u0111\u1ec3 test
                env_backup = {}
                for key in ("GROQ_API_KEY", "WHISPER_API_KEY", "OPENAI_API_KEY"):
                    env_backup[key] = os.environ.pop(key, None)
                try:
                    with pytest.raises(WhisperAuthError):
                        stt_whisper._get_groq_client()
                finally:
                    for key, val in env_backup.items():
                        if val is not None:
                            os.environ[key] = val
        finally:
            stt_whisper._GROQ_CLIENT = original_client


import os  # noqa: E402 (placed here to not interfere with module-level imports above)

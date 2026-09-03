"""
Test Giai đoạn 3 — Feedback Endpoint (integration test với TestClient)
-----------------------------------------------------------------------
Chạy: pytest backend/tests/test_feedback_endpoint.py -v

Bao gồm test:
  - Gửi text hợp lệ → 202 + request_id
  - Gửi audio hợp lệ → 202 + request_id
  - Không gửi gì cả → 400
  - Gửi audio quá lớn → 413
  - Gửi text rỗng → 400
  - Gửi audio rỗng (0 byte) → 400
  - Fraud filter: audio quá ngắn → 400
"""

import io
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from backend.api.main import app
from backend.services.audio_quality_service import AudioQualityResult


def _make_audio_quality_passed(duration_sec: float = 5.0, snr_db: float = 20.0) -> AudioQualityResult:
    """Helper: trả AudioQualityResult passed=True để bypass audio gate trong tests."""
    return AudioQualityResult(
        passed=True,
        reject_reason=None,
        reject_message=None,
        duration_sec=duration_sec,
        snr_db=snr_db,
    )

client = TestClient(app)

# ---------------------------------------------------------------------------
# Helpers tạo fake audio bytes
# ---------------------------------------------------------------------------
def make_fake_audio(size_bytes: int = 10_000) -> bytes:
    """Tạo bytes giả có kích thước cho trước (nội dung không quan trọng ở giai đoạn 3)."""
    return b"\x00" * size_bytes


VALID_FORM_BASE = {
    "tenant_id": "pho-ba-lan_1722500000000",
    "location": "Ban 5",
}


# ---------------------------------------------------------------------------
# Test cases
# ---------------------------------------------------------------------------
class TestTextOnlyFeedback:
    def test_valid_text_returns_202(self):
        """Gửi text hợp lệ → 202 Accepted với request_id."""
        response = client.post(
            "/api/v1/feedback",
            data={**VALID_FORM_BASE, "text_content": "Phục vụ ổn, món ăn ngon"},
        )
        assert response.status_code == 202, response.text
        data = response.json()
        assert data["status"] == "processed"
        assert "request_id" in data
        assert len(data["request_id"]) == 36   # UUID format
        assert data["input_type"] == "text"
        assert data["is_suspicious"] is False

    def test_empty_text_returns_400(self):
        """Gửi text rỗng → 400 Bad Request."""
        response = client.post(
            "/api/v1/feedback",
            data={**VALID_FORM_BASE, "text_content": ""},
        )
        assert response.status_code == 400, response.text

    def test_whitespace_text_returns_400(self):
        """Gửi text toàn khoảng trắng → 400."""
        response = client.post(
            "/api/v1/feedback",
            data={**VALID_FORM_BASE, "text_content": "   "},
        )
        assert response.status_code == 400, response.text

    def test_no_input_at_all_returns_400(self):
        """Không gửi audio lẫn text → 400 với message rõ ràng."""
        response = client.post(
            "/api/v1/feedback",
            data=VALID_FORM_BASE,
        )
        assert response.status_code == 400, response.text
        detail = response.json()["detail"]
        assert "audio" in detail.lower() or "text" in detail.lower()

    def test_repeated_text_flagged_but_accepted(self):
        """Text spam lặp → 202 nhưng is_suspicious=True (không reject)."""
        response = client.post(
            "/api/v1/feedback",
            data={**VALID_FORM_BASE, "text_content": "asdasdasdasd"},
        )
        assert response.status_code == 202, response.text
        data = response.json()
        assert data["is_suspicious"] is True
        assert data["status"] == "processed_with_warning"


class TestAudioOnlyFeedback:
    def test_valid_audio_returns_202(self):
        """Gửi audio webm hợp lệ (10KB) → 202 Accepted.

        Note: Fake bytes (\x00*N) không decode được bởi librosa, vì vậy cần mock
        cả analyze_audio_quality (Lớp 2) lẫn transcribe_audio (Groq Whisper).
        Đây là đúng behavior của integration test — isolate từng dependency.
        """
        audio_content = make_fake_audio(10_000)
        with patch("backend.api.routes.feedback.transcribe_audio", return_value="Phục vụ tốt"), \
             patch("backend.api.routes.feedback.analyze_audio_quality",
                   return_value=_make_audio_quality_passed()):
            response = client.post(
                "/api/v1/feedback",
                data=VALID_FORM_BASE,
                files={"audio_file": ("feedback.webm", io.BytesIO(audio_content), "audio/webm")},
            )
        assert response.status_code == 202, response.text
        data = response.json()
        assert data["status"] == "processed"
        assert data["input_type"] == "audio"
        assert data["transcript"] == "Phục vụ tốt"  # Giai đoạn 4: phải có transcript
        assert len(data["request_id"]) == 36

    def test_audio_too_large_returns_413(self):
        """Gửi audio > 5MB → 413 Request Entity Too Large."""
        big_audio = make_fake_audio(6 * 1024 * 1024)  # 6MB
        response = client.post(
            "/api/v1/feedback",
            data=VALID_FORM_BASE,
            files={"audio_file": ("big.webm", io.BytesIO(big_audio), "audio/webm")},
        )
        assert response.status_code == 413, response.text

    def test_empty_audio_returns_400(self):
        """Gửi audio 0 byte → 400 (fraud filter bắt)."""
        response = client.post(
            "/api/v1/feedback",
            data=VALID_FORM_BASE,
            files={"audio_file": ("empty.webm", io.BytesIO(b""), "audio/webm")},
        )
        assert response.status_code == 400, response.text

    def test_audio_too_short_returns_400(self):
        """Gửi audio 500 bytes (~< 1 giây) → 400 (fraud filter)."""
        short_audio = make_fake_audio(500)
        response = client.post(
            "/api/v1/feedback",
            data=VALID_FORM_BASE,
            files={"audio_file": ("short.webm", io.BytesIO(short_audio), "audio/webm")},
        )
        assert response.status_code == 400, response.text
        detail = response.json()["detail"]
        assert "ngắn" in detail or "short" in detail.lower()

    def test_invalid_mime_type_returns_400(self):
        """Gửi file định dạng không hỗ trợ (image/png) → 400."""
        response = client.post(
            "/api/v1/feedback",
            data=VALID_FORM_BASE,
            files={"audio_file": ("image.png", io.BytesIO(b"fake_png" * 1000), "image/png")},
        )
        assert response.status_code == 400, response.text


class TestAudioAndTextFeedback:
    def test_both_audio_and_text_returns_202(self):
        """Gửi cả audio + text → 202 với input_type='audio_and_text'.

        Note: Mock analyze_audio_quality vì fake bytes không decode được bởi librosa.
        """
        audio_content = make_fake_audio(10_000)
        with patch("backend.api.routes.feedback.transcribe_audio", return_value="Phục vụ tốt"), \
             patch("backend.api.routes.feedback.analyze_audio_quality",
                   return_value=_make_audio_quality_passed()):
            response = client.post(
                "/api/v1/feedback",
                data={**VALID_FORM_BASE, "text_content": "Phục vụ tốt"},
                files={"audio_file": ("feedback.webm", io.BytesIO(audio_content), "audio/webm")},
            )
        assert response.status_code == 202, response.text
        data = response.json()
        assert data["input_type"] == "audio_and_text"
        assert data["tenant_id"] == VALID_FORM_BASE["tenant_id"]
        assert data["location"] == VALID_FORM_BASE["location"]
        assert data["transcript"] == "Phục vụ tốt"  # Whisper transcript có trong response

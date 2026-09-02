"""
Test Giai đoạn 4 — Whisper STT (Unit tests + Integration tests)
----------------------------------------------------------------
Chạy: pytest backend/tests/test_stt_whisper.py -v

Kiến trúc test:
  - Unit test cho stt_whisper.py: mock OpenAI client để test logic xử lý lỗi
    mà KHÔNG gọi API thật (nhanh, không tốn quota).
  - Integration test: được bỏ qua (skip) nếu không có API key thật trong môi trường.
    Khi có key thật, chạy thêm flag --run-integration để test end-to-end.
"""

import os
import io
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from backend.ai_pipeline.stt_whisper import (
    transcribe_audio,
    WhisperAuthError,
    WhisperFormatError,
    WhisperTimeoutError,
    WhisperRateLimitError,
    WhisperAPIError,
    WHISPER_MAX_SIZE_BYTES,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def valid_webm_file(tmp_path: Path) -> Path:
    """Tạo file .webm giả hợp lệ (đủ kích thước, đúng extension)."""
    f = tmp_path / "test_audio.webm"
    f.write_bytes(b"\x00" * 5000)  # 5KB fake content
    return f


@pytest.fixture
def valid_wav_file(tmp_path: Path) -> Path:
    """Tạo file .wav giả hợp lệ."""
    f = tmp_path / "test_audio.wav"
    f.write_bytes(b"\x00" * 10000)
    return f


# ---------------------------------------------------------------------------
# Test: File không tồn tại
# ---------------------------------------------------------------------------

class TestFileValidation:
    def test_file_not_found_raises(self):
        """File không tồn tại → FileNotFoundError ngay, không gọi API."""
        with pytest.raises(FileNotFoundError, match="Không tìm thấy file audio"):
            transcribe_audio("/tmp/sentrix/nonexistent_abc123.webm")

    def test_unsupported_extension_raises(self, tmp_path: Path):
        """File .txt → WhisperFormatError trước khi gọi API."""
        bad_file = tmp_path / "fake.txt"
        bad_file.write_bytes(b"hello world")
        with pytest.raises(WhisperFormatError, match="không được Whisper API hỗ trợ"):
            transcribe_audio(str(bad_file))

    def test_empty_file_raises(self, tmp_path: Path):
        """File rỗng (0 bytes) → WhisperFormatError."""
        empty_file = tmp_path / "empty.webm"
        empty_file.write_bytes(b"")
        with pytest.raises(WhisperFormatError, match="rỗng"):
            transcribe_audio(str(empty_file))

    def test_oversized_file_raises(self, tmp_path: Path):
        """File vượt 25MB → WhisperFormatError trước khi gọi API."""
        big_file = tmp_path / "huge.webm"
        # Ghi 26MB để vượt ngưỡng (dùng sparse file trick cho nhanh)
        big_file.write_bytes(b"\x00" * (WHISPER_MAX_SIZE_BYTES + 1024))
        with pytest.raises(WhisperFormatError, match="quá lớn"):
            transcribe_audio(str(big_file))


# ---------------------------------------------------------------------------
# Test: API key thiếu
# ---------------------------------------------------------------------------

class TestAPIKeyValidation:
    def test_missing_api_key_raises(self, valid_webm_file: Path):
        """Không có GROQ_API_KEY, WHISPER_API_KEY và OPENAI_API_KEY → WhisperAuthError."""
        # Đảm bảo xóa cả 3 biến môi trường
        env_without_keys = {
            k: v for k, v in os.environ.items()
            if k not in ("GROQ_API_KEY", "WHISPER_API_KEY", "OPENAI_API_KEY")
        }
        with patch.dict(os.environ, env_without_keys, clear=True):
            with pytest.raises(WhisperAuthError, match="Chưa thiết lập API key"):
                transcribe_audio(str(valid_webm_file))


# ---------------------------------------------------------------------------
# Test: Logic xử lý lỗi API (mock OpenAI client)
# ---------------------------------------------------------------------------

class TestAPIErrorHandling:
    """Mock OpenAI client để test xử lý lỗi mà không gọi API thật."""

    def _setup_env(self):
        """Trả về dict môi trường có GROQ_API_KEY giả."""
        return {"GROQ_API_KEY": "gsk_fake-key-for-testing"}

    def test_auth_error_from_api_raises_whisper_auth_error(self, valid_webm_file: Path):
        """AuthenticationError từ OpenAI → WhisperAuthError."""
        from openai import AuthenticationError

        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.json.return_value = {"error": {"message": "Incorrect API key"}}

        with patch.dict(os.environ, self._setup_env()):
            with patch("backend.ai_pipeline.stt_whisper.OpenAI") as mock_openai_cls:
                mock_client = MagicMock()
                mock_openai_cls.return_value = mock_client
                mock_client.audio.transcriptions.create.side_effect = AuthenticationError(
                    message="Incorrect API key provided",
                    response=mock_response,
                    body={"error": {"message": "Incorrect API key"}},
                )
                with pytest.raises(WhisperAuthError):
                    transcribe_audio(str(valid_webm_file))

    def test_bad_request_from_api_raises_whisper_format_error(self, valid_webm_file: Path):
        """BadRequestError từ OpenAI → WhisperFormatError (file bị hỏng)."""
        from openai import BadRequestError

        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {"error": {"message": "Invalid file format"}}

        with patch.dict(os.environ, self._setup_env()):
            with patch("backend.ai_pipeline.stt_whisper.OpenAI") as mock_openai_cls:
                mock_client = MagicMock()
                mock_openai_cls.return_value = mock_client
                mock_client.audio.transcriptions.create.side_effect = BadRequestError(
                    message="Invalid file format",
                    response=mock_response,
                    body={"error": {"message": "Invalid file format"}},
                )
                with pytest.raises(WhisperFormatError):
                    transcribe_audio(str(valid_webm_file))

    def test_timeout_raises_whisper_timeout_error(self, valid_webm_file: Path):
        """APITimeoutError → WhisperTimeoutError."""
        from openai import APITimeoutError

        with patch.dict(os.environ, self._setup_env()):
            with patch("backend.ai_pipeline.stt_whisper.OpenAI") as mock_openai_cls:
                mock_client = MagicMock()
                mock_openai_cls.return_value = mock_client
                mock_client.audio.transcriptions.create.side_effect = APITimeoutError(
                    request=MagicMock()
                )
                with pytest.raises(WhisperTimeoutError):
                    transcribe_audio(str(valid_webm_file))

    def test_rate_limit_raises_whisper_rate_limit_error(self, valid_webm_file: Path):
        """RateLimitError (HTTP 429) từ Groq → WhisperRateLimitError với thông báo thân thiện."""
        from openai import RateLimitError

        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.json.return_value = {"error": {"message": "Rate limit exceeded"}}

        with patch.dict(os.environ, self._setup_env()):
            with patch("backend.ai_pipeline.stt_whisper.OpenAI") as mock_openai_cls:
                mock_client = MagicMock()
                mock_openai_cls.return_value = mock_client
                mock_client.audio.transcriptions.create.side_effect = RateLimitError(
                    message="Rate limit exceeded",
                    response=mock_response,
                    body={"error": {"message": "Rate limit exceeded"}},
                )
                with pytest.raises(WhisperRateLimitError, match="Hệ thống đang bận"):
                    transcribe_audio(str(valid_webm_file))

    def test_successful_transcription_returns_text(self, valid_webm_file: Path):
        """Mock API trả về text → hàm trả về đúng chuỗi đó."""
        expected_text = "Phục vụ tốt quá ha, đợi có 20 phút mà"

        with patch.dict(os.environ, self._setup_env()):
            with patch("backend.ai_pipeline.stt_whisper.OpenAI") as mock_openai_cls:
                mock_client = MagicMock()
                mock_openai_cls.return_value = mock_client
                mock_client.audio.transcriptions.create.return_value = expected_text

                result = transcribe_audio(str(valid_webm_file))
                assert result == expected_text

    def test_transcription_strips_whitespace(self, valid_webm_file: Path):
        """Kết quả từ API có khoảng trắng thừa → được strip()."""
        with patch.dict(os.environ, self._setup_env()):
            with patch("backend.ai_pipeline.stt_whisper.OpenAI") as mock_openai_cls:
                mock_client = MagicMock()
                mock_openai_cls.return_value = mock_client
                mock_client.audio.transcriptions.create.return_value = "  Phục vụ tốt  \n"

                result = transcribe_audio(str(valid_webm_file))
                assert result == "Phục vụ tốt"

    def test_fallback_to_openai_api_key(self, valid_webm_file: Path):
        """Ưu tiên GROQ_API_KEY; fallback WHISPER_API_KEY → OPENAI_API_KEY nếu không có."""
        expected = "Món ăn ngon lắm"
        env = {"OPENAI_API_KEY": "sk-fallback-key"}  # Không có GROQ_API_KEY hay WHISPER_API_KEY

        with patch.dict(os.environ, env, clear=True):
            with patch("backend.ai_pipeline.stt_whisper.OpenAI") as mock_openai_cls:
                mock_client = MagicMock()
                mock_openai_cls.return_value = mock_client
                mock_client.audio.transcriptions.create.return_value = expected

                result = transcribe_audio(str(valid_webm_file))
                assert result == expected

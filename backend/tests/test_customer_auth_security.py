"""
test_customer_auth_security.py - Regression Tests for Customer Auth and OTP Security

Test coverage:
  1.  Google token valid + email_verified=True -> 202, voucher_eligible=True.
  2.  Google token invalid/expired -> 401.
  3.  Google email not verified -> 403.
  4.  Email claim from token, not from client data.
  5.  Disposable email blocked (datadudi.com, comzx.com).
  6.  Email OTP: send success, provider failure, cooldown.
  7.  Phone OTP: rejected when no SMS/Zalo provider.
  8.  Anonymous mode: 202, voucher_eligible=False.
  9.  Non-anonymous without OTP/token -> 403.
  10. SUPPORT_REQUEST alert not regressed.
  11. P0: Firestore error -> 503 (fail-closed, NOT bypass).
  12. P0: verified session TTL expired -> 403.
  13. P0: session missing verified_at -> 403 (backward safe).
  14. P0: OTP reuse prevention (second verify fails).
  15. P1: Hourly OTP rate limit (5 sends/hour, 6th blocked 429).
  16. P1: Provider failure rollback (resend allowed without cooldown block).
"""
import os
os.environ.setdefault("ENVIRONMENT", "test")

import uuid
import secrets
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from backend.api.main import app
from backend.services.email_validation_service import (
    is_disposable_email,
    normalize_email,
    extract_domain,
    FRIENDLY_DISPOSABLE_ERROR_MESSAGE,
)
from backend.services.otp_service import (
    check_otp_cooldown,
    check_otp_hourly_rate_limit,
    create_otp_session,
    check_verified_session_valid,
    verify_otp_session,
    OTP_RESEND_COOLDOWN_SECONDS,
    OTP_VERIFIED_SESSION_TTL_MINUTES,
    OTP_HOURLY_SEND_LIMIT,
    _hash_contact_for_otp,
    _hash_otp_code,
    _memory_sessions,
    OtpCooldownError,
    OtpHourlyLimitError,
)

client = TestClient(app)
TENANT_ID = "pho-ba-lan_1722500000000"
LOCATION = "Ban 1"


# ===========================================================================
# 1. Email Validation Service
# ===========================================================================
class TestEmailValidationService:
    def test_normalize_email(self):
        assert normalize_email("  User.Test@Gmail.COM  ") == "user.test@gmail.com"
        assert normalize_email("") == ""
        assert normalize_email(None) == ""

    def test_extract_domain(self):
        assert extract_domain("user@gmail.com") == "gmail.com"
        assert extract_domain("user@SUB.datadudi.com") == "sub.datadudi.com"
        assert extract_domain("invalid-email") is None
        assert extract_domain("user@") is None

    def test_disposable_email_denylist(self):
        assert is_disposable_email("test@datadudi.com") is True
        assert is_disposable_email("admin@comzx.com") is True
        assert is_disposable_email("user@mail.datadudi.com") is True
        assert is_disposable_email("user@sub.temp.comzx.com") is True
        assert is_disposable_email("student@uit.edu.vn") is False
        assert is_disposable_email("customer@gmail.com") is False
        assert is_disposable_email("user@yahoo.com") is False
        assert is_disposable_email("user@notdatadudi.com") is False
        assert is_disposable_email("user@datadudi.com.vn") is False


# ===========================================================================
# 2. Google Sign-In Authentication
# ===========================================================================
class TestGoogleSignInFeedback:
    @patch("firebase_admin.auth.verify_id_token")
    @patch("backend.api.routes.feedback.check_rate_limit")
    @patch("backend.api.routes.feedback.check_semantic_validity")
    @patch("backend.api.routes.feedback.classify_intent")
    def test_google_token_valid_and_verified(self, mock_intent, mock_sem, mock_rate, mock_verify):
        """Valid token + email_verified -> 202, voucher_eligible=True."""
        from backend.services.rate_limit_service import RateLimitResult
        mock_rate.return_value = RateLimitResult(allowed=True, reason=None, next_allowed_at=None)
        mock_sem.return_value = MagicMock(is_valid=True, reason=None)
        mock_intent.return_value = {"intent": "FEEDBACK", "confidence": 0.95}
        mock_verify.return_value = {
            "email": "Student.UIT@gmail.com",
            "email_verified": True,
            "uid": "google-user-123",
        }
        resp = client.post(
            "/api/v1/feedback",
            data={
                "tenant_id": TENANT_ID,
                "location": LOCATION,
                "text_content": "Mon pho rat ngon, nuoc dung dam da",
                "voucher_eligible": "true",
                "firebase_id_token": "valid-firebase-token",
                "customer_phone": "attacker-provided@evil.com",
            },
        )
        assert resp.status_code == 202, resp.text
        data = resp.json()
        assert data["voucher_eligible"] is True
        mock_verify.assert_called_once_with("valid-firebase-token")

    @patch("firebase_admin.auth.verify_id_token")
    def test_google_token_invalid_returns_401(self, mock_verify):
        """Invalid/expired token -> 401."""
        mock_verify.side_effect = Exception("Firebase ID token has expired")
        resp = client.post(
            "/api/v1/feedback",
            data={
                "tenant_id": TENANT_ID,
                "location": LOCATION,
                "text_content": "Mon pho rat ngon",
                "voucher_eligible": "true",
                "firebase_id_token": "expired-token",
                "customer_phone": "0901234567",
            },
        )
        assert resp.status_code == 401
        assert "Token" in resp.json()["detail"]

    @patch("firebase_admin.auth.verify_id_token")
    def test_google_token_email_not_verified_returns_403(self, mock_verify):
        """Google email not verified -> 403 Forbidden."""
        mock_verify.return_value = {
            "email": "unverified@gmail.com",
            "email_verified": False,
            "uid": "google-unverified",
        }
        resp = client.post(
            "/api/v1/feedback",
            data={
                "tenant_id": TENANT_ID,
                "location": LOCATION,
                "text_content": "Mon pho rat ngon",
                "voucher_eligible": "true",
                "firebase_id_token": "token-with-unverified-email",
            },
        )
        assert resp.status_code == 403
        assert "Email Google" in resp.json()["detail"]

    @patch("firebase_admin.auth.verify_id_token")
    def test_google_token_with_disposable_domain_returns_400(self, mock_verify):
        """Disposable email in Google token -> 400 Bad Request."""
        mock_verify.return_value = {
            "email": "tempuser@datadudi.com",
            "email_verified": True,
            "uid": "disposable-user",
        }
        resp = client.post(
            "/api/v1/feedback",
            data={
                "tenant_id": TENANT_ID,
                "location": LOCATION,
                "text_content": "Mon pho rat ngon",
                "voucher_eligible": "true",
                "firebase_id_token": "token-with-disposable-email",
            },
        )
        assert resp.status_code == 400
        assert resp.json()["detail"] == FRIENDLY_DISPOSABLE_ERROR_MESSAGE


# ===========================================================================
# 3. Email OTP Route and Cooldown
# ===========================================================================
class TestEmailOtpFlow:
    @patch("backend.api.routes.otp.get_otp_provider")
    def test_email_otp_send_success(self, mock_get_provider):
        """Send OTP email success."""
        mock_provider = MagicMock()
        mock_provider.send_otp.return_value = MagicMock(success=True, error=None, message="OTP sent.")
        mock_get_provider.return_value = mock_provider

        contact = f"fresh_{uuid.uuid4().hex[:8]}@gmail.com"
        resp = client.post("/api/v1/otp/send", json={"contact": contact, "tenant_id": TENANT_ID})
        assert resp.status_code == 200
        assert resp.json()["success"] is True
        assert resp.json()["contact_type"] == "email"

    def test_email_otp_disposable_blocked(self):
        """Disposable email blocked at /otp/send."""
        contact = f"spammer_{uuid.uuid4().hex[:8]}@comzx.com"
        resp = client.post("/api/v1/otp/send", json={"contact": contact, "tenant_id": TENANT_ID})
        assert resp.status_code == 400
        assert resp.json()["detail"] == FRIENDLY_DISPOSABLE_ERROR_MESSAGE

    @patch("backend.api.routes.otp.get_otp_provider")
    def test_email_otp_cooldown_resend_limit(self, mock_get_provider):
        """Resend within 60s -> 429 Too Many Requests."""
        mock_provider = MagicMock()
        mock_provider.send_otp.return_value = MagicMock(success=True, error=None, message="Sent.")
        mock_get_provider.return_value = mock_provider

        contact = f"cooldown_{uuid.uuid4().hex[:8]}@gmail.com"
        r1 = client.post("/api/v1/otp/send", json={"contact": contact, "tenant_id": TENANT_ID})
        assert r1.status_code == 200

        r2 = client.post("/api/v1/otp/send", json={"contact": contact, "tenant_id": TENANT_ID})
        assert r2.status_code == 429

    @patch("backend.api.routes.otp.get_otp_provider")
    def test_email_otp_provider_failure_returns_503(self, mock_get_provider):
        """Provider failure -> 503, sanitized message, not leaking provider error."""
        mock_provider = MagicMock()
        mock_provider.send_otp.return_value = MagicMock(
            success=False, error="Resend API 403: domain not verified"
        )
        mock_get_provider.return_value = mock_provider

        contact = f"resend_fail_{uuid.uuid4().hex[:8]}@gmail.com"
        resp = client.post("/api/v1/otp/send", json={"contact": contact, "tenant_id": TENANT_ID})
        assert resp.status_code == 503
        assert resp.json()["detail"] == "Không thể gửi mã OTP lúc này. Vui lòng thử lại sau."
        assert "Resend API 403" not in resp.text
        assert "domain not verified" not in resp.text

    @patch("backend.api.routes.otp.get_otp_provider")
    def test_provider_error_does_not_leak_internal_details(self, mock_get_provider):
        """Verify response does not leak SMTP host, provider body, credentials, or internal details."""
        mock_provider = MagicMock()
        mock_provider.send_otp.return_value = MagicMock(
            success=False,
            error="SMTP AuthenticationError 535: password 'secret_pass_123' rejected by smtp.gmail.com:587",
        )
        mock_get_provider.return_value = mock_provider

        contact = f"leakcheck_{uuid.uuid4().hex[:8]}@gmail.com"
        resp = client.post("/api/v1/otp/send", json={"contact": contact, "tenant_id": TENANT_ID})
        assert resp.status_code == 503
        assert "smtp.gmail.com" not in resp.text
        assert "secret_pass_123" not in resp.text
        assert "AuthenticationError" not in resp.text
        assert resp.json()["detail"] == "Không thể gửi mã OTP lúc này. Vui lòng thử lại sau."


# ===========================================================================
# 4. Phone OTP Safe Disabling
# ===========================================================================
class TestPhoneOtpDisabling:
    def test_phone_otp_cannot_send_without_provider(self, monkeypatch):
        """Phone OTP rejected when no SMS/Zalo provider configured."""
        monkeypatch.setenv("OTP_PROVIDER", "disabled")
        phone = f"09{secrets.randbelow(89999999) + 10000000}"
        resp = client.post("/api/v1/otp/send", json={"contact": phone, "tenant_id": TENANT_ID})
        assert resp.status_code == 503


# ===========================================================================
# 5. Anonymous Mode and Non-Anonymous Enforcement
# ===========================================================================
class TestAnonymousAndSecurityEnforcement:
    def test_anonymous_mode_success(self):
        """Anonymous feedback -> 202, voucher_eligible=False."""
        resp = client.post(
            "/api/v1/feedback",
            data={
                "tenant_id": TENANT_ID,
                "location": LOCATION,
                "text_content": "Khong gian quan sach se, thoang mat",
                "voucher_eligible": "false",
            },
        )
        assert resp.status_code == 202
        assert resp.json()["voucher_eligible"] is False

    def test_non_anonymous_without_token_or_otp_rejected(self):
        """Claiming identity without OTP/token -> 403 Forbidden."""
        with patch("backend.db.firestore_client.get_firestore_client") as mock_fs:
            mock_snap = MagicMock()
            mock_snap.exists = False
            mock_fs.return_value.collection.return_value.document.return_value.get.return_value = mock_snap

            contact = f"nootp_{uuid.uuid4().hex[:8]}@gmail.com"
            resp = client.post(
                "/api/v1/feedback",
                data={
                    "tenant_id": TENANT_ID,
                    "location": LOCATION,
                    "text_content": "Do an rat ngon",
                    "customer_phone": contact,
                    "voucher_eligible": "true",
                },
            )
            assert resp.status_code == 403


# ===========================================================================
# 6. Intent Alert Regression
# ===========================================================================
class TestAlertNoRegression:
    @patch("firebase_admin.auth.verify_id_token")
    def test_support_request_alert_still_created(self, mock_verify):
        """SUPPORT_REQUEST intent still works correctly."""
        mock_verify.return_value = {
            "email": "customer@gmail.com",
            "email_verified": True,
            "uid": "cust-alert",
        }
        with patch("backend.services.intent_service.classify_intent", return_value="SUPPORT_REQUEST"):
            with patch("backend.db.firestore_ops.create_alert", return_value="alert-123"):
                resp = client.post(
                    "/api/v1/feedback",
                    data={
                        "tenant_id": TENANT_ID,
                        "location": LOCATION,
                        "text_content": "Cho toi xin them giay an va nuoc mam voi",
                        "voucher_eligible": "true",
                        "firebase_id_token": "valid-token",
                    },
                )
                assert resp.status_code == 202
                assert resp.json()["status"] in ("processed", "processed_with_warning")


# ===========================================================================
# 7. P0: Fail-Closed OTP Verification
# ===========================================================================
class TestOtpFailClosed:
    def test_firestore_error_returns_503_not_bypass(self):
        """
        P0 REGRESSION: Firestore error when checking OTP session -> 503 (fail-closed).
        Must NOT return 202 (old fail-open behavior: except Exception: _otp_verified = True).
        """
        with patch("backend.db.firestore_client.get_firestore_client") as mock_fs:
            mock_fs.side_effect = Exception("Firestore connection refused")
            resp = client.post(
                "/api/v1/feedback",
                data={
                    "tenant_id": TENANT_ID,
                    "location": LOCATION,
                    "text_content": "Do an rat ngon",
                    "customer_phone": "failclosed@gmail.com",
                    "voucher_eligible": "true",
                },
            )
            assert resp.status_code == 503, (
                f"P0 FAIL: Expected 503 (fail-closed) but got {resp.status_code}. "
                f"Old code would return 202 (bypass). Response: {resp.text}"
            )

    def test_otp_not_verified_returns_403(self):
        """Session exists but verified=False -> 403 Forbidden."""
        contact = f"unverified_{uuid.uuid4().hex[:8]}@gmail.com"
        session_key = _hash_contact_for_otp(contact)
        now = datetime.now(timezone.utc)
        _memory_sessions[session_key] = {
            "otp_code_hash": _hash_otp_code("999999"),
            "expires_at": now + timedelta(minutes=5),
            "verified": False,
            "attempts": 0,
            "created_at": now,
            "send_hour": now.strftime("%Y-%m-%dT%H"),
            "send_count": 1,
        }
        try:
            with patch("backend.db.firestore_client.get_firestore_client") as mock_fs:
                mock_snap = MagicMock()
                mock_snap.exists = False
                mock_fs.return_value.collection.return_value.document.return_value.get.return_value = mock_snap

                resp = client.post(
                    "/api/v1/feedback",
                    data={
                        "tenant_id": TENANT_ID,
                        "location": LOCATION,
                        "text_content": "Test feedback",
                        "customer_phone": contact,
                        "voucher_eligible": "true",
                    },
                )
                assert resp.status_code == 403
        finally:
            _memory_sessions.pop(session_key, None)

    def test_verified_session_expired_ttl_returns_403(self):
        """Verified session with verified_at > OTP_VERIFIED_SESSION_TTL_MINUTES -> 403."""
        contact = f"expired_{uuid.uuid4().hex[:8]}@gmail.com"
        session_key = _hash_contact_for_otp(contact)
        old_time = datetime.now(timezone.utc) - timedelta(minutes=OTP_VERIFIED_SESSION_TTL_MINUTES + 5)
        _memory_sessions[session_key] = {
            "otp_code_hash": _hash_otp_code("111111"),
            "expires_at": old_time + timedelta(minutes=5),
            "verified": True,
            "verified_at": old_time,  # Past TTL
            "attempts": 0,
            "created_at": old_time,
            "send_hour": old_time.strftime("%Y-%m-%dT%H"),
            "send_count": 1,
        }
        try:
            with patch("backend.db.firestore_client.get_firestore_client") as mock_fs:
                mock_snap = MagicMock()
                mock_snap.exists = False
                mock_fs.return_value.collection.return_value.document.return_value.get.return_value = mock_snap

                resp = client.post(
                    "/api/v1/feedback",
                    data={
                        "tenant_id": TENANT_ID,
                        "location": LOCATION,
                        "text_content": "Test feedback",
                        "customer_phone": contact,
                        "voucher_eligible": "true",
                    },
                )
                assert resp.status_code == 403
        finally:
            _memory_sessions.pop(session_key, None)

    def test_session_missing_verified_at_returns_403(self):
        """Legacy session without verified_at -> 403 (backward safe, NOT default valid)."""
        contact = f"legacy_{uuid.uuid4().hex[:8]}@gmail.com"
        session_key = _hash_contact_for_otp(contact)
        now = datetime.now(timezone.utc)
        _memory_sessions[session_key] = {
            "otp_code_hash": _hash_otp_code("222222"),
            "expires_at": now + timedelta(minutes=5),
            "verified": True,
            # verified_at INTENTIONALLY MISSING - backward compat test
            "attempts": 0,
            "created_at": now,
            "send_hour": now.strftime("%Y-%m-%dT%H"),
            "send_count": 1,
        }
        try:
            with patch("backend.db.firestore_client.get_firestore_client") as mock_fs:
                mock_snap = MagicMock()
                mock_snap.exists = False
                mock_fs.return_value.collection.return_value.document.return_value.get.return_value = mock_snap

                resp = client.post(
                    "/api/v1/feedback",
                    data={
                        "tenant_id": TENANT_ID,
                        "location": LOCATION,
                        "text_content": "Test feedback",
                        "customer_phone": contact,
                        "voucher_eligible": "true",
                    },
                )
                assert resp.status_code == 403
        finally:
            _memory_sessions.pop(session_key, None)

    def test_valid_verified_session_passes(self):
        """Valid session: verified=True, fresh verified_at within TTL -> 202."""
        contact = f"valid_{uuid.uuid4().hex[:8]}@gmail.com"
        session_key = _hash_contact_for_otp(contact)
        now = datetime.now(timezone.utc)
        _memory_sessions[session_key] = {
            "otp_code_hash": _hash_otp_code("333333"),
            "expires_at": now + timedelta(minutes=5),
            "verified": True,
            "verified_at": now,  # Fresh - within TTL
            "attempts": 0,
            "created_at": now,
            "send_hour": now.strftime("%Y-%m-%dT%H"),
            "send_count": 1,
        }
        try:
            with patch("backend.db.firestore_client.get_firestore_client") as mock_fs:
                mock_snap = MagicMock()
                mock_snap.exists = False
                mock_fs.return_value.collection.return_value.document.return_value.get.return_value = mock_snap

                with patch("backend.api.routes.feedback.check_rate_limit") as mock_rate:
                    from backend.services.rate_limit_service import RateLimitResult
                    mock_rate.return_value = RateLimitResult(allowed=True, reason=None, next_allowed_at=None)

                    resp = client.post(
                        "/api/v1/feedback",
                        data={
                            "tenant_id": TENANT_ID,
                            "location": LOCATION,
                            "text_content": "Pho ngon lam, toi rat thich",
                            "customer_phone": contact,
                            "voucher_eligible": "true",
                        },
                    )
                    assert resp.status_code == 202
        finally:
            _memory_sessions.pop(session_key, None)


# ===========================================================================
# 8. P0: OTP Reuse Prevention
# ===========================================================================
class TestOtpReusePrevention:
    def test_otp_cannot_be_verified_twice(self):
        """Single OTP can only be used once - second verify must fail."""
        contact = f"reuse_{uuid.uuid4().hex[:8]}@gmail.com"
        session_key = _hash_contact_for_otp(contact)
        now = datetime.now(timezone.utc)
        otp_code = "456789"

        _memory_sessions[session_key] = {
            "otp_code_hash": _hash_otp_code(otp_code),
            "expires_at": now + timedelta(minutes=5),
            "verified": False,
            "attempts": 0,
            "created_at": now,
            "send_hour": now.strftime("%Y-%m-%dT%H"),
            "send_count": 1,
        }
        try:
            with patch("backend.db.firestore_client.get_firestore_client") as mock_fs:
                mock_fs.side_effect = Exception("No Firestore in test")

                result1 = verify_otp_session(contact, otp_code)
                assert result1.success is True, "First verify must succeed"

                result2 = verify_otp_session(contact, otp_code)
                assert result2.success is False, "Second verify must fail (reuse prevention)"
        finally:
            _memory_sessions.pop(session_key, None)


# ===========================================================================
# 9. P1: Hourly OTP Rate Limit
# ===========================================================================
class TestOtpHourlyRateLimit:
    @patch("backend.api.routes.otp.get_otp_provider")
    def test_hourly_limit_blocks_after_limit_reached(self, mock_get_provider):
        """After OTP_HOURLY_SEND_LIMIT sends in same hour, next send -> 429."""
        mock_provider = MagicMock()
        mock_provider.send_otp.return_value = MagicMock(success=True, error=None, message="Sent.")
        mock_get_provider.return_value = mock_provider

        contact = f"hourly_{uuid.uuid4().hex[:8]}@gmail.com"
        session_key = _hash_contact_for_otp(contact)
        now = datetime.now(timezone.utc)
        current_hour = now.strftime("%Y-%m-%dT%H")

        # Pre-inject: already at limit, cooldown expired (>60s)
        _memory_sessions[session_key] = {
            "otp_code_hash": _hash_otp_code("000000"),
            "expires_at": now - timedelta(seconds=10),
            "created_at": now - timedelta(seconds=70),  # Cooldown passed
            "verified": False,
            "attempts": 0,
            "send_hour": current_hour,
            "send_count": OTP_HOURLY_SEND_LIMIT,  # Already at limit
        }
        try:
            resp = client.post(
                "/api/v1/otp/send",
                json={"contact": contact, "tenant_id": TENANT_ID},
            )
            assert resp.status_code == 429, (
                f"Expected 429 (hourly limit) but got {resp.status_code}: {resp.text}"
            )
        finally:
            _memory_sessions.pop(session_key, None)

    @patch("backend.api.routes.otp.get_otp_provider")
    def test_hourly_limit_resets_next_hour(self, mock_get_provider):
        """New hour resets send_count - allows sending again."""
        mock_provider = MagicMock()
        mock_provider.send_otp.return_value = MagicMock(success=True, error=None, message="Sent.")
        mock_get_provider.return_value = mock_provider

        contact = f"newhr_{uuid.uuid4().hex[:8]}@gmail.com"
        session_key = _hash_contact_for_otp(contact)
        now = datetime.now(timezone.utc)
        past_hour = (now - timedelta(hours=1)).strftime("%Y-%m-%dT%H")

        _memory_sessions[session_key] = {
            "otp_code_hash": _hash_otp_code("000000"),
            "expires_at": now - timedelta(seconds=10),
            "created_at": now - timedelta(seconds=70),  # Cooldown passed
            "verified": False,
            "attempts": 0,
            "send_hour": past_hour,  # Previous hour
            "send_count": OTP_HOURLY_SEND_LIMIT,
        }
        try:
            resp = client.post(
                "/api/v1/otp/send",
                json={"contact": contact, "tenant_id": TENANT_ID},
            )
            assert resp.status_code == 200, (
                f"Expected 200 (new hour reset) but got {resp.status_code}: {resp.text}"
            )
        finally:
            _memory_sessions.pop(session_key, None)


# ===========================================================================
# 10. P1: Provider Failure Rollback
# ===========================================================================
class TestProviderFailureRollback:
    @patch("backend.api.routes.otp.get_otp_provider")
    def test_provider_failure_allows_resend(self, mock_get_provider):
        """After provider fail, session rolled back -> resend allowed without cooldown block."""
        mock_provider = MagicMock()
        mock_provider.provider_name.return_value = "MockFailProvider"
        mock_provider.send_otp.return_value = MagicMock(success=False, error="SMTP timeout")
        mock_get_provider.return_value = mock_provider

        contact = f"failresend_{uuid.uuid4().hex[:8]}@gmail.com"
        session_key = _hash_contact_for_otp(contact)

        # Send 1: provider fail -> 503
        r1 = client.post("/api/v1/otp/send", json={"contact": contact, "tenant_id": TENANT_ID})
        assert r1.status_code == 503

        # Check session was rolled back
        session_after_fail = _memory_sessions.get(session_key)
        if session_after_fail:
            assert session_after_fail.get("send_failed") is True
            assert session_after_fail.get("created_at") is None, "Cooldown must be reset after fail"

        # Send 2: provider success -> 200 (no cooldown block after rollback)
        mock_provider.send_otp.return_value = MagicMock(success=True, error=None, message="Sent.")
        r2 = client.post("/api/v1/otp/send", json={"contact": contact, "tenant_id": TENANT_ID})
        assert r2.status_code == 200, (
            f"Expected 200 after rollback, got {r2.status_code}: {r2.text}"
        )
        _memory_sessions.pop(session_key, None)

    @patch("backend.api.routes.otp.get_otp_provider")
    def test_provider_failure_still_increments_send_count(self, mock_get_provider):
        """Provider fail still counts toward send_count (anti-spam)."""
        mock_provider = MagicMock()
        mock_provider.provider_name.return_value = "MockFailProvider"
        mock_provider.send_otp.return_value = MagicMock(success=False, error="timeout")
        mock_get_provider.return_value = mock_provider

        contact = f"countfail_{uuid.uuid4().hex[:8]}@gmail.com"
        session_key = _hash_contact_for_otp(contact)

        resp = client.post("/api/v1/otp/send", json={"contact": contact, "tenant_id": TENANT_ID})
        assert resp.status_code == 503

        session = _memory_sessions.get(session_key)
        if session:
            assert session.get("send_count", 0) >= 1, "send_count must increase even on failure"
        _memory_sessions.pop(session_key, None)


# ===========================================================================
# 11. P0: Production vs Development/Test In-Memory Fallback Differentiation
# ===========================================================================
class TestProductionVsDevFallback:
    """
    Chứng minh:
      - Trong production: KHÔNG fallback sang _memory_sessions khi Firestore
        thiếu document hoặc gặp lỗi đọc/ghi. Fail-closed an toàn.
      - Trong development/test: cho phép in-memory fallback phục vụ test suite.
    """

    def test_production_rejects_ram_fallback_when_firestore_doc_missing(self, monkeypatch):
        """Production: document không có trên Firestore -> từ chối, KHÔNG đọc từ RAM."""
        monkeypatch.setenv("ENVIRONMENT", "production")

        contact = f"prod_missing_{uuid.uuid4().hex[:8]}@gmail.com"
        session_key = _hash_contact_for_otp(contact)
        now = datetime.now(timezone.utc)

        # Giả lập có session hợp lệ nằm trong RAM
        _memory_sessions[session_key] = {
            "otp_code_hash": _hash_otp_code("654321"),
            "expires_at": now + timedelta(minutes=5),
            "verified": True,
            "verified_at": now,
            "attempts": 0,
            "created_at": now,
            "send_hour": now.strftime("%Y-%m-%dT%H"),
            "send_count": 1,
        }
        try:
            with patch("backend.db.firestore_client.get_firestore_client") as mock_fs:
                mock_snap = MagicMock()
                mock_snap.exists = False
                mock_fs.return_value.collection.return_value.document.return_value.get.return_value = mock_snap

                # 1. check_verified_session_valid từ chối
                is_valid, reason = check_verified_session_valid(contact)
                assert is_valid is False
                assert reason == "session_not_found"

                # 2. verify_otp_session từ chối
                verify_res = verify_otp_session(contact, "654321")
                assert verify_res.success is False
                assert "không tồn tại hoặc đã hết hạn" in verify_res.message
        finally:
            _memory_sessions.pop(session_key, None)

    def test_production_verify_fails_closed_on_firestore_error(self, monkeypatch):
        """Production: lỗi đọc Firestore khi verify -> trả 503, KHÔNG lấy session từ RAM."""
        monkeypatch.setenv("ENVIRONMENT", "production")

        contact = f"prod_fserr_{uuid.uuid4().hex[:8]}@gmail.com"
        session_key = _hash_contact_for_otp(contact)
        now = datetime.now(timezone.utc)

        _memory_sessions[session_key] = {
            "otp_code_hash": _hash_otp_code("111222"),
            "expires_at": now + timedelta(minutes=5),
            "verified": False,
            "attempts": 0,
            "created_at": now,
            "send_hour": now.strftime("%Y-%m-%dT%H"),
            "send_count": 1,
        }
        try:
            with patch("backend.db.firestore_client.get_firestore_client") as mock_fs:
                mock_fs.side_effect = Exception("Firestore connection timeout")

                verify_res = verify_otp_session(contact, "111222")
                assert verify_res.success is False
                assert "tạm thời không khả dụng" in verify_res.message
        finally:
            _memory_sessions.pop(session_key, None)

    def test_production_create_session_fails_closed_on_firestore_error(self, monkeypatch):
        """Production: lỗi lưu Firestore khi create -> raise RuntimeError, không lưu RAM."""
        import pytest
        monkeypatch.setenv("ENVIRONMENT", "production")

        contact = f"prod_create_err_{uuid.uuid4().hex[:8]}@gmail.com"
        session_key = _hash_contact_for_otp(contact)

        try:
            with patch("backend.db.firestore_client.get_firestore_client") as mock_fs:
                mock_fs.side_effect = Exception("Firestore write quota exceeded")

                with pytest.raises(RuntimeError) as exc_info:
                    create_otp_session(contact)
                assert "Không thể lưu OTP session vào cơ sở dữ liệu" in str(exc_info.value)
                assert session_key not in _memory_sessions

                # Endpoint /otp/send trả 503
                resp = client.post("/api/v1/otp/send", json={"contact": contact, "tenant_id": TENANT_ID})
                assert resp.status_code == 503
        finally:
            _memory_sessions.pop(session_key, None)

    def test_production_rate_limit_fails_closed_on_firestore_error(self, monkeypatch):
        """Production: lỗi đọc rate limit từ Firestore -> từ chối gửi OTP với HTTP 503."""
        import pytest
        monkeypatch.setenv("ENVIRONMENT", "production")

        contact = f"prod_rl_err_{uuid.uuid4().hex[:8]}@gmail.com"

        with patch("backend.db.firestore_client.get_firestore_client") as mock_fs:
            mock_fs.side_effect = Exception("Firestore unavailable")

            with pytest.raises(RuntimeError):
                check_otp_hourly_rate_limit(contact)

            resp = client.post("/api/v1/otp/send", json={"contact": contact, "tenant_id": TENANT_ID})
            assert resp.status_code == 503
            assert "tạm thời không khả dụng" in resp.json()["detail"]

    def test_dev_environment_allows_ram_fallback(self, monkeypatch):
        """Dev/test: Firestore không có doc -> in-memory fallback hoạt động bình thường."""
        monkeypatch.setenv("ENVIRONMENT", "test")

        contact = f"dev_ok_{uuid.uuid4().hex[:8]}@gmail.com"
        session_key = _hash_contact_for_otp(contact)
        now = datetime.now(timezone.utc)

        _memory_sessions[session_key] = {
            "otp_code_hash": _hash_otp_code("999888"),
            "expires_at": now + timedelta(minutes=5),
            "verified": True,
            "verified_at": now,
            "attempts": 0,
            "created_at": now,
            "send_hour": now.strftime("%Y-%m-%dT%H"),
            "send_count": 1,
        }
        try:
            with patch("backend.db.firestore_client.get_firestore_client") as mock_fs:
                mock_snap = MagicMock()
                mock_snap.exists = False
                mock_fs.return_value.collection.return_value.document.return_value.get.return_value = mock_snap

                is_valid, reason = check_verified_session_valid(contact)
                assert is_valid is True
                assert reason == ""
        finally:
            _memory_sessions.pop(session_key, None)


# ===========================================================================
# 12. P1: Provider Exception Handling & Rollback
# ===========================================================================
class TestProviderExceptionHandling:
    """
    Kiểm tra trường hợp provider.send_otp() ném exception hoặc timeout bất ngờ:
      - Trả HTTP 503, không trả thành công giả.
      - Thông báo công khai sạch sẽ (không lộ stack trace, SMTP host, internal error).
      - Rollback session: không thể verify OTP của session lỗi.
      - Bảo toàn send_count cho hourly rate limit.
    """

    @patch("backend.api.routes.otp.get_otp_provider")
    def test_provider_exception_returns_503_sanitized_and_invalidates_code(self, mock_get_provider):
        """Provider ném TimeoutError -> trả 503 sanitized, session rollback, không thể verify."""
        mock_provider = MagicMock()
        mock_provider.provider_name.return_value = "MockTimeoutProvider"
        mock_provider.send_otp.side_effect = TimeoutError("SMTP connection timed out to smtp.gmail.com:587")
        mock_get_provider.return_value = mock_provider

        contact = f"procexc_{uuid.uuid4().hex[:8]}@gmail.com"
        session_key = _hash_contact_for_otp(contact)

        resp = client.post("/api/v1/otp/send", json={"contact": contact, "tenant_id": TENANT_ID})
        assert resp.status_code == 503

        # Đảm bảo không lộ thông tin nhạy cảm/nội bộ
        assert "SMTP connection timed out" not in resp.text
        assert "smtp.gmail.com" not in resp.text
        assert resp.json()["detail"] == "Không thể gửi mã OTP lúc này. Vui lòng thử lại sau."

        # Kiểm tra session bị vô hiệu hoá và send_count được bảo toàn
        session = _memory_sessions.get(session_key)
        assert session is not None
        assert session.get("send_failed") is True
        assert session.get("otp_code_hash") is None
        assert session.get("created_at") is None
        assert session.get("send_count") >= 1

        # Cố verify với bất kỳ code nào cũng phải thất bại
        verify_res = verify_otp_session(contact, "123456")
        assert verify_res.success is False
        assert "thất bại" in verify_res.message

        _memory_sessions.pop(session_key, None)

    @patch("backend.api.routes.otp.create_otp_session")
    def test_atomic_rate_limit_race_defense(self, mock_create):
        """Nếu create_otp_session phát hiện chạm hạn mức do race condition -> trả 429."""
        mock_create.side_effect = ValueError("Đã vượt giới hạn 5 lần gửi OTP trong giờ này.")
        contact = f"race_{uuid.uuid4().hex[:8]}@gmail.com"

        resp = client.post("/api/v1/otp/send", json={"contact": contact, "tenant_id": TENANT_ID})
        assert resp.status_code == 429
        assert "Đã vượt giới hạn gửi OTP" in resp.json()["detail"]


# ===========================================================================
# 13. P0: Firestore Rollback Failure in Production
# ===========================================================================
class TestFirestoreRollbackFailureInProduction:
    def test_production_delete_session_fails_closed_when_firestore_rollback_fails(self, monkeypatch):
        """Production: delete_otp_session_on_send_failure raises RuntimeError if Firestore update fails."""
        import pytest
        from backend.services.otp_service import delete_otp_session_on_send_failure
        monkeypatch.setenv("ENVIRONMENT", "production")

        contact = f"prod_rb_fail_{uuid.uuid4().hex[:8]}@gmail.com"
        with patch("backend.db.firestore_client.get_firestore_client") as mock_fs:
            mock_fs.side_effect = Exception("Firestore network disconnect during rollback")
            with pytest.raises(RuntimeError) as exc_info:
                delete_otp_session_on_send_failure(contact)
            assert "Lỗi rollback OTP session trên Firestore" in str(exc_info.value)

    @patch("backend.api.routes.otp.create_otp_session")
    @patch("backend.api.routes.otp.delete_otp_session_on_send_failure")
    @patch("backend.api.routes.otp.get_otp_provider")
    def test_production_send_route_handles_rollback_failure_fails_closed(
        self, mock_get_provider, mock_rollback, mock_create, monkeypatch
    ):
        """Production: when provider fails AND rollback fails on Firestore -> returns 503, never 200, clean response."""
        monkeypatch.setenv("ENVIRONMENT", "production")
        mock_create.return_value = "123456"
        mock_rollback.side_effect = RuntimeError("Rollback failed on Firestore")

        mock_provider = MagicMock()
        mock_provider.send_otp.return_value = MagicMock(success=False, error="Provider down")
        mock_provider.provider_name.return_value = "MockProvider"
        mock_get_provider.return_value = mock_provider

        contact = f"prod_send_rbfail_{uuid.uuid4().hex[:8]}@gmail.com"
        resp = client.post("/api/v1/otp/send", json={"contact": contact, "tenant_id": TENANT_ID})

        # Xác minh mock create_otp_session, mock send_otp và mock rollback đều thực sự được gọi
        mock_create.assert_called_once()
        mock_provider.send_otp.assert_called_once_with(contact, "123456")
        mock_rollback.assert_called_once_with(contact)

        assert resp.status_code == 503
        assert resp.json()["detail"] == "Không thể gửi mã OTP lúc này. Vui lòng thử lại sau."
        assert "Rollback failed" not in resp.text
        assert "Provider down" not in resp.text

    @patch("backend.api.routes.otp.create_otp_session")
    @patch("backend.api.routes.otp.delete_otp_session_on_send_failure")
    @patch("backend.api.routes.otp.get_otp_provider")
    def test_production_send_route_handles_provider_exception_with_rollback_failure(
        self, mock_get_provider, mock_rollback, mock_create, monkeypatch
    ):
        """Production: provider throws exception AND rollback fails -> returns 503 sanitized, mock called."""
        monkeypatch.setenv("ENVIRONMENT", "production")
        mock_create.return_value = "654321"
        mock_rollback.side_effect = RuntimeError("Firestore unavailable during rollback")

        mock_provider = MagicMock()
        mock_provider.send_otp.side_effect = TimeoutError("SMTP connection timed out")
        mock_get_provider.return_value = mock_provider

        contact = f"prod_exc_rbfail_{uuid.uuid4().hex[:8]}@gmail.com"
        resp = client.post("/api/v1/otp/send", json={"contact": contact, "tenant_id": TENANT_ID})

        mock_create.assert_called_once()
        mock_provider.send_otp.assert_called_once_with(contact, "654321")
        mock_rollback.assert_called_once_with(contact)

        assert resp.status_code == 503
        assert resp.json()["detail"] == "Không thể gửi mã OTP lúc này. Vui lòng thử lại sau."
        assert "SMTP connection timed out" not in resp.text
        assert "Firestore unavailable" not in resp.text


# ===========================================================================
# 14. P1: Atomic Rate Limit Transaction Verification
# ===========================================================================
class TestAtomicRateLimitTransaction:
    def test_atomic_rate_limit_transaction_blocks_excess_send(self):
        """
        Unit test với mock Firestore transaction:
        Kiểm tra callback logic của _atomic_create_txn: khi send_count trong giờ hiện tại >= 5,
        transaction abort bằng ValueError trước khi thực hiện transaction.set().
        LƯU Ý: Đây là unit test với mock để kiểm tra logic transaction handler, không dùng Emulator.
        """
        import pytest
        contact = f"txn_rl_{uuid.uuid4().hex[:8]}@gmail.com"
        now = datetime.now(timezone.utc)
        current_hour = now.strftime("%Y-%m-%dT%H")

        with patch("backend.db.firestore_client.get_firestore_client") as mock_fs:
            mock_doc = MagicMock()
            mock_fs.return_value.collection.return_value.document.return_value = mock_doc

            # Simulate existing document at limit (send_count=5 in current hour)
            mock_snap_at_limit = MagicMock()
            mock_snap_at_limit.exists = True
            mock_snap_at_limit.to_dict.return_value = {
                "send_hour": current_hour,
                "send_count": OTP_HOURLY_SEND_LIMIT,
            }

            mock_doc.get.return_value = mock_snap_at_limit
            mock_txn = MagicMock()
            mock_txn.get.return_value = mock_snap_at_limit
            mock_fs.return_value.transaction.return_value = mock_txn

            with pytest.raises(ValueError) as exc_info:
                create_otp_session(contact)
            assert f"Đã vượt giới hạn {OTP_HOURLY_SEND_LIMIT} lần gửi OTP" in str(exc_info.value)
            # Crucial: transaction.set must NOT have been called because it was blocked inside transaction
            mock_txn.set.assert_not_called()

    def test_atomic_rate_limit_transaction_increments_when_allowed(self):
        """When send_count in current hour is < 5, transaction sets doc with increment."""
        contact = f"txn_ok_{uuid.uuid4().hex[:8]}@gmail.com"
        now = datetime.now(timezone.utc)
        current_hour = now.strftime("%Y-%m-%dT%H")

        with patch("backend.db.firestore_client.get_firestore_client") as mock_fs:
            mock_doc = MagicMock()
            mock_fs.return_value.collection.return_value.document.return_value = mock_doc

            mock_snap_under_limit = MagicMock()
            mock_snap_under_limit.exists = True
            mock_snap_under_limit.to_dict.return_value = {
                "send_hour": current_hour,
                "send_count": 3,
            }

            mock_doc.get.return_value = mock_snap_under_limit
            mock_txn = MagicMock()
            mock_txn.get.return_value = mock_snap_under_limit
            mock_fs.return_value.transaction.return_value = mock_txn

            otp_code = create_otp_session(contact)
            assert len(otp_code) == 6
            mock_txn.set.assert_called_once()
            called_args = mock_txn.set.call_args[0]
            new_data = called_args[1]
            assert new_data["send_count"] == 4
            assert new_data["send_hour"] == current_hour

    def test_atomic_transaction_blocks_and_does_not_write_when_within_cooldown(self):
        """
        Unit test với mock Firestore transaction:
        Kiểm tra callback logic của _atomic_create_txn: khi created_at của session trước đó
        vẫn còn trong khoảng thời gian cooldown 60 giây, transaction abort bằng OtpCooldownError
        và tuyệt đối không gọi transaction.set() để ghi session mới.
        LƯU Ý: Đây là unit test với mock kiểm tra logic callback handler, không phải kiểm chứng live Firestore.
        """
        import pytest
        contact = f"txn_cd_{uuid.uuid4().hex[:8]}@gmail.com"
        now = datetime.now(timezone.utc)
        current_hour = now.strftime("%Y-%m-%dT%H")
        recent_created_at = now - timedelta(seconds=20)  # Còn 40s cooldown

        with patch("backend.db.firestore_client.get_firestore_client") as mock_fs:
            mock_doc = MagicMock()
            mock_fs.return_value.collection.return_value.document.return_value = mock_doc

            mock_snap_in_cooldown = MagicMock()
            mock_snap_in_cooldown.exists = True
            mock_snap_in_cooldown.to_dict.return_value = {
                "created_at": recent_created_at,
                "send_hour": current_hour,
                "send_count": 1,
            }

            mock_doc.get.return_value = mock_snap_in_cooldown
            mock_txn = MagicMock()
            mock_txn.get.return_value = mock_snap_in_cooldown
            mock_fs.return_value.transaction.return_value = mock_txn

            with pytest.raises(OtpCooldownError) as exc_info:
                create_otp_session(contact)

            assert exc_info.value.remaining_seconds >= 38
            assert "Vui lòng đợi" in str(exc_info.value)
            # Transaction.set KHÔNG được gọi khi cooldown còn hiệu lực
            mock_txn.set.assert_not_called()

    @patch("backend.api.routes.otp.get_otp_provider")
    @patch("backend.api.routes.otp.create_otp_session")
    def test_route_handles_transaction_cooldown_error_does_not_call_provider(
        self, mock_create, mock_get_provider
    ):
        """
        Khi create_otp_session ném OtpCooldownError từ bên trong transaction:
        Endpoint /api/v1/otp/send trả HTTP 429 với message cooldown, và KHÔNG gọi provider.send_otp.
        """
        mock_create.side_effect = OtpCooldownError(remaining_seconds=45)
        mock_provider = MagicMock()
        mock_get_provider.return_value = mock_provider

        contact = f"route_cd_{uuid.uuid4().hex[:8]}@gmail.com"
        resp = client.post("/api/v1/otp/send", json={"contact": contact, "tenant_id": TENANT_ID})

        assert resp.status_code == 429
        assert "Vui lòng đợi 45 giây trước khi yêu cầu mã OTP mới." in resp.json()["detail"]
        mock_provider.send_otp.assert_not_called()


# ===========================================================================
# 15. P1: Attempt Tracking Fail-Closed
# ===========================================================================
class TestAttemptTrackingFailClosed:
    def test_production_verify_wrong_code_fails_closed_if_attempts_update_fails(self, monkeypatch):
        """
        Production: when wrong code is entered, if writing attempts to Firestore fails,
        must fail-closed (503 Service Unavailable), NOT bypass attempt limit or continue as normal wrong code.
        """
        monkeypatch.setenv("ENVIRONMENT", "production")
        contact = f"prod_wrong_attempt_fail_{uuid.uuid4().hex[:8]}@gmail.com"
        now = datetime.now(timezone.utc)

        with patch("backend.db.firestore_client.get_firestore_client") as mock_fs:
            mock_doc = MagicMock()
            mock_snap = MagicMock()
            mock_snap.exists = True
            mock_snap.to_dict.return_value = {
                "otp_code_hash": _hash_otp_code("654321"),
                "expires_at": now + timedelta(minutes=5),
                "verified": False,
                "attempts": 0,
                "created_at": now,
                "send_hour": now.strftime("%Y-%m-%dT%H"),
                "send_count": 1,
            }
            mock_fs.return_value.collection.return_value.document.return_value = mock_doc
            mock_doc.get.return_value = mock_snap

            mock_txn = MagicMock()
            mock_txn.get.return_value = mock_snap
            mock_txn.update.side_effect = Exception("Firestore transaction write error on attempts")
            mock_fs.return_value.transaction.return_value = mock_txn

            res = verify_otp_session(contact, "000000")  # Wrong code
            assert res.success is False
            assert "tạm thời không khả dụng" in res.message


# ===========================================================================
# 16. P1: Single-Use OTP Concurrency
# ===========================================================================
class TestSingleUseOtpConcurrency:
    def test_concurrent_otp_verification_single_use(self):
        """
        Unit test với thread-safe mock datastore:
        Kiểm tra callback logic của _atomic_verify_txn: khi 2 thread cùng gọi verify_otp_session
        với cùng một mã OTP hợp lệ, transaction chỉ cho phép đúng 1 request thành công
        và request kia nhận 'Mã OTP này đã được sử dụng'.
        LƯU Ý: Đây là unit test với mock, không dùng Firestore Emulator và không khẳng định
        đã mô phỏng toàn bộ Firestore OCC/retry trên multi-instance live.
        """
        import threading
        from concurrent.futures import ThreadPoolExecutor

        contact = f"concurrent_verify_{uuid.uuid4().hex[:8]}@gmail.com"
        valid_code = "789123"
        now = datetime.now(timezone.utc)

        doc_lock = threading.Lock()
        doc_state = {
            "otp_code_hash": _hash_otp_code(valid_code),
            "expires_at": now + timedelta(minutes=5),
            "verified": False,
            "attempts": 0,
            "created_at": now,
            "send_hour": now.strftime("%Y-%m-%dT%H"),
            "send_count": 1,
        }

        with patch("backend.db.firestore_client.get_firestore_client") as mock_fs:
            mock_doc = MagicMock()
            mock_fs.return_value.collection.return_value.document.return_value = mock_doc

            def mock_transaction():
                txn = MagicMock()
                def txn_get(ref=None, transaction=None):
                    snap = MagicMock()
                    with doc_lock:
                        snap.exists = True
                        snap.to_dict.return_value = dict(doc_state)
                    return snap
                def txn_update(ref, data):
                    with doc_lock:
                        doc_state.update(data)
                txn.get = txn_get
                txn.update = txn_update
                return txn

            mock_fs.return_value.transaction = mock_transaction
            mock_doc.get = lambda transaction=None: mock_transaction().get()

            with ThreadPoolExecutor(max_workers=2) as executor:
                f1 = executor.submit(verify_otp_session, contact, valid_code)
                f2 = executor.submit(verify_otp_session, contact, valid_code)
                r1 = f1.result()
                r2 = f2.result()

            results = [r1, r2]
            successes = [r for r in results if r.success]
            failures = [r for r in results if not r.success]

            assert len(successes) == 1, f"Expected exactly 1 success, got {len(successes)}"
            assert len(failures) == 1, f"Expected exactly 1 failure, got {len(failures)}"
            assert "đã được sử dụng" in failures[0].message


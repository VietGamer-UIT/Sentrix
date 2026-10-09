import os
import pytest
import backend.db.firestore_client
from backend.services.otp_service import (
    get_otp_provider,
    EmailOtpProvider,
    ZaloZnsOtpProvider,
    MockOtpProvider,
    DisabledPhoneOtpProvider,
    create_otp_session,
    _memory_sessions,
    _hash_contact_for_otp
)

def test_otp_provider_routing(monkeypatch):
    # Test 1: Email contact always gets EmailOtpProvider
    provider = get_otp_provider("test@gmail.com")
    assert isinstance(provider, EmailOtpProvider)

    # Test 2: Phone contact with zalo provider
    monkeypatch.setenv("OTP_PROVIDER", "zalo")
    provider = get_otp_provider("0901234567")
    assert isinstance(provider, ZaloZnsOtpProvider)

    # Test 3: Phone contact with mock in DEV environment
    monkeypatch.setenv("OTP_PROVIDER", "mock")
    monkeypatch.setenv("ENVIRONMENT", "development")
    provider = get_otp_provider("0901234567")
    assert isinstance(provider, MockOtpProvider)

    # Test 4: Phone contact with mock in PROD environment -> Disabled
    monkeypatch.setenv("ENVIRONMENT", "production")
    provider = get_otp_provider("0901234567")
    assert isinstance(provider, DisabledPhoneOtpProvider)

    # Test 5: DisabledPhoneOtpProvider behavior
    disabled_provider = DisabledPhoneOtpProvider()
    res = disabled_provider.send_otp("0901234567", "123456")
    assert res.success is False
    assert "chưa khả dụng" in res.error

def test_create_session_mock_accept_all_dev(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("OTP_PROVIDER", "mock")
    monkeypatch.setenv("OTP_MOCK_ACCEPT_ALL", "true")
    # Force fallback to memory
    monkeypatch.setattr("backend.db.firestore_client.get_firestore_client", lambda: (_ for _ in ()).throw(Exception("Force memory")))

    _memory_sessions.clear()

    create_otp_session("0901234567")
    key = _hash_contact_for_otp("0901234567")
    assert key in _memory_sessions
    assert _memory_sessions[key]["verified"] is True

def test_create_session_no_mock_prod(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("OTP_PROVIDER", "mock")
    monkeypatch.setenv("OTP_MOCK_ACCEPT_ALL", "true")
    # Force fallback to memory
    monkeypatch.setattr("backend.db.firestore_client.get_firestore_client", lambda: (_ for _ in ()).throw(Exception("Force memory")))

    _memory_sessions.clear()

    create_otp_session("0988888888")
    key = _hash_contact_for_otp("0988888888")
    assert _memory_sessions[key]["verified"] is False

@pytest.mark.parametrize("env", ["", "staging", "production", "invalid"])
def test_verify_session_no_bypass_safe_envs(monkeypatch, env):
    monkeypatch.setenv("ENVIRONMENT", env)
    monkeypatch.setenv("OTP_PROVIDER", "mock")
    monkeypatch.setenv("OTP_MOCK_ACCEPT_ALL", "true")
    # Force fallback to memory
    monkeypatch.setattr("backend.db.firestore_client.get_firestore_client", lambda: (_ for _ in ()).throw(Exception("Force memory")))

    from backend.services.otp_service import verify_otp_session, _memory_sessions
    _memory_sessions.clear()

    # If bypass is active, this would return True.
    # Since it's production/safe env, it should skip bypass and fail (because session "0988888888" doesn't exist).
    result = verify_otp_session("0988888888", "123456")
    assert result.success is False

@pytest.mark.parametrize("env", ["development", "dev", "test"])
def test_verify_session_bypass_dev_envs(monkeypatch, env):
    monkeypatch.setenv("ENVIRONMENT", env)
    monkeypatch.setenv("OTP_PROVIDER", "mock")
    monkeypatch.setenv("OTP_MOCK_ACCEPT_ALL", "true")

    from backend.services.otp_service import verify_otp_session
    # If bypass is active, this returns True immediately for phone numbers.
    result = verify_otp_session("0988888888", "123456")
    assert result.success is True
@pytest.mark.parametrize("env", ["", "staging", "production", "invalid"])
def test_create_session_safe_envs_ignore_mock_code(monkeypatch, env):
    monkeypatch.setenv("ENVIRONMENT", env)
    monkeypatch.setenv("OTP_PROVIDER", "mock")
    monkeypatch.setenv("OTP_MOCK_CODE", "999999")
    monkeypatch.setattr("backend.db.firestore_client.get_firestore_client", lambda: (_ for _ in ()).throw(Exception("Force memory")))
    monkeypatch.setattr("backend.services.otp_service._generate_otp_code", lambda: "123456")

    from backend.services.otp_service import create_otp_session
    otp = create_otp_session("0900000000")
    assert otp == "123456"

@pytest.mark.parametrize("env", ["development", "dev", "test"])
def test_create_session_dev_envs_uses_mock_code(monkeypatch, env):
    monkeypatch.setenv("ENVIRONMENT", env)
    monkeypatch.setenv("OTP_PROVIDER", "mock")
    monkeypatch.setenv("OTP_MOCK_CODE", "999999")
    monkeypatch.setattr("backend.db.firestore_client.get_firestore_client", lambda: (_ for _ in ()).throw(Exception("Force memory")))

    from backend.services.otp_service import create_otp_session
    otp = create_otp_session("0900000000")
    assert otp == "999999"

def test_disabled_phone_provider_logging(caplog):
    from backend.services.otp_service import DisabledPhoneOtpProvider
    import logging

    provider = DisabledPhoneOtpProvider()
    with caplog.at_level(logging.WARNING):
        provider.send_otp("0912345678", "123456")

    assert "0912345678" not in caplog.text
    assert "Từ chối gửi OTP qua SĐT vì chưa cấu hình SMS/Zalo." in caplog.text

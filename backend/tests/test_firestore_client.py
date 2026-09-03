"""
Test Giai đoạn 2 — Firestore Client
-------------------------------------
Chạy: pytest backend/tests/test_firestore_client.py -v
(chạy từ thư mục gốc repo: d:\\Sentrix)

Giai đoạn này chưa kết nối Firestore thật — chỉ kiểm tra:
1. Lỗi thiếu credentials được raise rõ ràng (không crash im lặng).
2. Singleton pattern hoạt động đúng (chỉ init 1 lần).
3. Hàm reset_firestore_client() hoạt động cho testing.
"""

import os
import pytest

# Đảm bảo không có biến Firebase nào từ môi trường thật can thiệp vào test
@pytest.fixture(autouse=True)
def clean_firebase_env(monkeypatch):
    """Reset Firebase singleton + xóa mọi biến môi trường Firebase trước mỗi test.

    Quan trọng: reset_firestore_client() phải chạy TRƯỚC khi xóa env vars (và
    trước yield) để đảm bảo firebase_admin._apps bị xóa. Nếu không, một test
    trước đó đã init Firebase App thì _initialize_firebase_app() sẽ thấy _apps
    đã có và return sớm (line 59-61 firestore_client.py) mà không raise EnvironmentError.
    """
    # Bước 1: Reset singleton TRƯỚC để đảm bảo Firebase App bị xóa hoàn toàn
    from backend.db.firestore_client import reset_firestore_client
    reset_firestore_client()

    # Bước 2: Xóa mọi biến môi trường Firebase để test ở trạng thái "không credentials"
    for var in [
        "FIREBASE_CREDENTIALS_PATH",
        "FIREBASE_PROJECT_ID",
        "FIREBASE_PRIVATE_KEY",
        "FIREBASE_CLIENT_EMAIL",
    ]:
        monkeypatch.delenv(var, raising=False)

    yield

    # Teardown: reset lại sau mỗi test để test tiếp theo bắt đầu sạch
    reset_firestore_client()


def test_missing_all_credentials_raises_environment_error():
    """Thiếu TẤT CẢ credentials → EnvironmentError với message rõ ràng."""
    from backend.db.firestore_client import get_firestore_client

    with pytest.raises(EnvironmentError) as exc_info:
        get_firestore_client()

    error_msg = str(exc_info.value)
    assert "FIREBASE_PROJECT_ID" in error_msg, "Message lỗi phải nhắc đến FIREBASE_PROJECT_ID"
    assert "FIREBASE_PRIVATE_KEY" in error_msg, "Message lỗi phải nhắc đến FIREBASE_PRIVATE_KEY"
    assert "FIREBASE_CLIENT_EMAIL" in error_msg, "Message lỗi phải nhắc đến FIREBASE_CLIENT_EMAIL"


def test_invalid_credentials_path_raises_file_not_found(monkeypatch):
    """FIREBASE_CREDENTIALS_PATH trỏ đến file không tồn tại → FileNotFoundError."""
    monkeypatch.setenv("FIREBASE_CREDENTIALS_PATH", "backend/non_existent_key.json")
    from backend.db.firestore_client import get_firestore_client

    with pytest.raises(FileNotFoundError) as exc_info:
        get_firestore_client()

    error_msg = str(exc_info.value)
    assert "non_existent_key.json" in error_msg, "Message lỗi phải chứa tên file sai"
    assert "Firebase Console" in error_msg, "Message lỗi phải hướng dẫn cách lấy credentials"


def test_missing_partial_credentials_raises_environment_error(monkeypatch):
    """Có 1 trong 3 biến env nhưng thiếu 2 biến còn lại → EnvironmentError."""
    monkeypatch.setenv("FIREBASE_PROJECT_ID", "my-project")
    # FIREBASE_PRIVATE_KEY và FIREBASE_CLIENT_EMAIL còn thiếu

    from backend.db.firestore_client import get_firestore_client

    with pytest.raises(EnvironmentError) as exc_info:
        get_firestore_client()

    error_msg = str(exc_info.value)
    assert "FIREBASE_PRIVATE_KEY" in error_msg
    assert "FIREBASE_CLIENT_EMAIL" in error_msg
    # FIREBASE_PROJECT_ID không nên xuất hiện trong list "còn thiếu"
    # (đã cung cấp rồi)


def test_reset_client_clears_singleton():
    """reset_firestore_client() phải xóa singleton để test tiếp theo khởi tạo lại."""
    from backend.db.firestore_client import reset_firestore_client, _firestore_client
    import backend.db.firestore_client as fc_module

    # Gán giả một client vào singleton
    fc_module._firestore_client = "fake_client"
    assert fc_module._firestore_client == "fake_client"

    # Reset
    reset_firestore_client()

    # Sau reset phải là None
    assert fc_module._firestore_client is None

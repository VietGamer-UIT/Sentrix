"""
Firestore Client — Khởi tạo kết nối Firebase Admin SDK
========================================================
Author: Nguyễn Thanh Tuyền (AI & Data Architect)
Giai đoạn: 2 (khởi tạo client) + 8 (đọc/ghi dữ liệu thật)

CÁCH DÙNG:
    from backend.db.firestore_client import get_firestore_client

    db = get_firestore_client()
    # Sau đó dùng db để thao tác Firestore (giai đoạn 8)
    # doc = db.collection("tenants").document(tenant_id).get()

BIẾN MÔI TRƯỜNG CẦN THIẾT (xem .env.example ở root repo):
    FIREBASE_CREDENTIALS_PATH  — đường dẫn đến file serviceAccountKey.json
                                  Ví dụ: backend/serviceAccountKey.json
    HOẶC (thay thế, dùng khi deploy lên Render.com để tránh lưu file JSON):
    FIREBASE_PROJECT_ID        — Project ID của Firebase
    FIREBASE_PRIVATE_KEY       — Private Key (dạng string, có \\n)
    FIREBASE_CLIENT_EMAIL      — Client Email của Service Account

    Nếu có FIREBASE_CREDENTIALS_PATH → dùng file JSON (ưu tiên, dễ dùng local).
    Nếu không có file → fallback sang 3 biến riêng lẻ (phù hợp deploy production).
"""

import os
import logging
from typing import Optional

import firebase_admin
from firebase_admin import credentials, firestore

logger = logging.getLogger(__name__)

# Biến module-level để đảm bảo Firebase App chỉ khởi tạo 1 lần (singleton)
# Firebase Admin SDK ném ValueError nếu bạn gọi initialize_app() 2 lần
_firestore_client: Optional[firestore.Client] = None


def _initialize_firebase_app() -> None:
    """
    Khởi tạo Firebase Admin App (chỉ chạy 1 lần trong suốt vòng đời process).

    Ưu tiên:
    1. File credentials JSON (FIREBASE_CREDENTIALS_PATH)
    2. Biến môi trường riêng lẻ (FIREBASE_PROJECT_ID + FIREBASE_PRIVATE_KEY + FIREBASE_CLIENT_EMAIL)
    3. Application Default Credentials (khi chạy trên Google Cloud — không dùng ở đây)

    Raises:
        EnvironmentError: Nếu thiếu credentials và không thể khởi tạo.
        FileNotFoundError: Nếu FIREBASE_CREDENTIALS_PATH trỏ đến file không tồn tại.
    """
    # Nếu đã có app rồi thì không khởi tạo lại
    if firebase_admin._apps:
        logger.debug("Firebase App đã được khởi tạo trước đó — bỏ qua.")
        return

    cred_path = os.getenv("FIREBASE_CREDENTIALS_PATH", "").strip()

    if cred_path:
        # --- Cách 1: Dùng file serviceAccountKey.json ---
        if not os.path.exists(cred_path):
            raise FileNotFoundError(
                f"[Firestore] FIREBASE_CREDENTIALS_PATH trỏ đến file không tồn tại: '{cred_path}'\n"
                f"  → Kiểm tra: file có đúng vị trí không? Đã download từ Firebase Console chưa?\n"
                f"  → Hướng dẫn: Firebase Console → Project Settings → Service Accounts → Generate new private key"
            )
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
        logger.info(f"[Firestore] Khởi tạo bằng file credentials: {cred_path}")

    else:
        # --- Cách 2: Dùng biến môi trường riêng lẻ (cho production/Render.com) ---
        project_id = os.getenv("FIREBASE_PROJECT_ID", "").strip()
        private_key = os.getenv("FIREBASE_PRIVATE_KEY", "").strip()
        client_email = os.getenv("FIREBASE_CLIENT_EMAIL", "").strip()

        missing = []
        if not project_id:
            missing.append("FIREBASE_PROJECT_ID")
        if not private_key:
            missing.append("FIREBASE_PRIVATE_KEY")
        if not client_email:
            missing.append("FIREBASE_CLIENT_EMAIL")

        if missing:
            raise EnvironmentError(
                f"[Firestore] Thiếu credentials để kết nối Firebase.\n"
                f"  → Biến môi trường còn thiếu: {', '.join(missing)}\n"
                f"  → Cách 1: Đặt FIREBASE_CREDENTIALS_PATH=backend/serviceAccountKey.json\n"
                f"  → Cách 2: Đặt đủ FIREBASE_PROJECT_ID + FIREBASE_PRIVATE_KEY + FIREBASE_CLIENT_EMAIL\n"
                f"  → Xem .env.example ở root repo để biết format đúng."
            )

        # FIREBASE_PRIVATE_KEY trong .env lưu dạng "-----BEGIN RSA...\\n..." (escaped \n)
        # Cần replace "\\n" thành "\n" thực sự
        private_key = private_key.replace("\\n", "\n")

        cred = credentials.Certificate({
            "type": "service_account",
            "project_id": project_id,
            "private_key": private_key,
            "client_email": client_email,
            "token_uri": "https://oauth2.googleapis.com/token",
        })
        firebase_admin.initialize_app(cred)
        logger.info(
            f"[Firestore] Khởi tạo bằng biến môi trường. Project: {project_id}"
        )


def get_firestore_client() -> firestore.Client:
    """
    Trả về Firestore Client đã khởi tạo (singleton — chỉ khởi tạo 1 lần).

    Returns:
        firestore.Client: Client để thao tác Firestore.

    Raises:
        EnvironmentError: Thiếu credentials.
        FileNotFoundError: File credentials không tồn tại.
        Exception: Lỗi Firebase khác (network, credentials sai...).

    Example:
        db = get_firestore_client()
        tenant_ref = db.collection("tenants").document("pho-ba-lan_172250000000")
    """
    global _firestore_client

    if _firestore_client is not None:
        return _firestore_client

    try:
        _initialize_firebase_app()
        _firestore_client = firestore.client()
        logger.info("[Firestore] Client khởi tạo thành công.")
        return _firestore_client

    except (EnvironmentError, FileNotFoundError) as e:
        # Lỗi do thiếu/sai credentials — log rõ ràng, không crash im lặng
        logger.error(str(e))
        raise

    except Exception as e:
        logger.error(
            f"[Firestore] Lỗi không xác định khi khởi tạo client: {type(e).__name__}: {e}"
        )
        raise


def reset_firestore_client() -> None:
    """
    Reset singleton client (dùng cho unit testing).
    KHÔNG gọi hàm này trong production code.
    """
    global _firestore_client
    _firestore_client = None
    # Reset firebase app để có thể init lại với credentials khác khi test
    if firebase_admin._apps:
        for app in list(firebase_admin._apps.values()):
            firebase_admin.delete_app(app)
    logger.debug("[Firestore] Client và Firebase App đã được reset (testing only).")

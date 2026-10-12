"""
Email Validation Service — Kiểm tra email hợp lệ và chống disposable email
=============================================================================
Author: Sentrix Security Team
Module: Customer Authentication & Anti-Spam

Chức năng:
  - Chuẩn hóa email: strip, lowercase, trích xuất domain chính xác.
  - Kiểm tra định dạng email cơ bản.
  - Chặn các domain disposable email (tạm thời / rác):
    - Denylist mặc định: datadudi.com, comzx.com.
    - Hỗ trợ mở rộng qua biến môi trường DISPOSABLE_EMAIL_DOMAINS (comma-separated).
    - Hỗ trợ subdomain (ví dụ: mail.datadudi.com).
    - So khớp an toàn (không dùng substring search để tránh false positive).
  - Trả thông báo lỗi thân thiện, bảo mật (không tiết lộ cơ chế denylist nội bộ).
"""

import os
import re
from typing import Optional, Set

# Biểu thức kiểm tra email hợp lệ RFC-5322 cơ bản
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$')

# Danh sách disposable email domains mặc định
DEFAULT_DISPOSABLE_DOMAINS: Set[str] = {
    "datadudi.com",
    "comzx.com",
}

FRIENDLY_DISPOSABLE_ERROR_MESSAGE = (
    "Địa chỉ email không được hỗ trợ. Vui lòng sử dụng địa chỉ email chính thức hoặc thử lại."
)


def get_disposable_domains() -> Set[str]:
    """
    Lấy tập hợp các domain bị chặn.
    Gộp denylist mặc định và các domain từ biến môi trường DISPOSABLE_EMAIL_DOMAINS.
    """
    domains = set(DEFAULT_DISPOSABLE_DOMAINS)
    env_domains = os.getenv("DISPOSABLE_EMAIL_DOMAINS", "")
    if env_domains:
        for d in env_domains.split(","):
            cleaned = d.strip().lower()
            if cleaned:
                domains.add(cleaned)
    return domains


def normalize_email(email: str) -> str:
    """
    Chuẩn hoá email: loại bỏ khoảng trắng và chuyển về chữ thường.
    """
    if not email:
        return ""
    return email.strip().lower()


def extract_domain(email: str) -> Optional[str]:
    """
    Trích xuất domain từ email đã chuẩn hoá.
    Trả về None nếu định dạng email không hợp lệ.
    """
    clean_email = normalize_email(email)
    if not clean_email or "@" not in clean_email:
        return None
    
    parts = clean_email.rsplit("@", 1)
    if len(parts) != 2 or not parts[0] or not parts[1]:
        return None
    
    domain = parts[1].strip().lower()
    # Kiểm tra domain có chứa dấu chấm hợp lệ
    if "." not in domain or domain.startswith(".") or domain.endswith("."):
        return None
    
    return domain


def is_valid_email_format(email: str) -> bool:
    """
    Kiểm tra định dạng email hợp lệ.
    """
    clean_email = normalize_email(email)
    if not clean_email:
        return False
    return bool(EMAIL_REGEX.match(clean_email))


def is_disposable_email(email: str) -> bool:
    """
    Kiểm tra xem email có thuộc domain disposable (tạm thời / rác) hay không.
    
    Quy tắc so khớp:
      - Khớp chính xác domain (ví dụ: datadudi.com == datadudi.com).
      - Khớp subdomain (ví dụ: temp.datadudi.com kết thúc bằng .datadudi.com).
      - KHÔNG so khớp substring tự do (tránh chặn nhầm mydatadudi.com.vn hoặc notdatadudi.com).
    """
    domain = extract_domain(email)
    if not domain:
        # Email sai định dạng sẽ được xử lý bởi validator định dạng
        return False

    disposable_set = get_disposable_domains()
    
    for banned in disposable_set:
        banned = banned.strip().lower()
        if not banned:
            continue
        # 1. Khớp chính xác domain
        if domain == banned:
            return True
        # 2. Khớp subdomain (ví dụ sub.datadudi.com)
        if domain.endswith("." + banned):
            return True

    return False


def mask_email(email: Optional[str]) -> str:
    """
    Ẩn danh hóa email an toàn cho logging và hiển thị:
    - "customer@gmail.com" -> "c***r@gmail.com"
    - "ab@example.com" -> "a***b@example.com"
    - "a@example.com" -> "a***@example.com"
    """
    if not email:
        return "***"
    clean = normalize_email(email)
    if "@" not in clean:
        return "***" + clean[-3:] if len(clean) >= 3 else "***"
    parts = clean.split("@", 1)
    name, domain = parts[0], parts[1]
    if len(name) <= 1:
        masked_name = name + "***"
    elif len(name) == 2:
        masked_name = name[0] + "***" + name[1]
    else:
        masked_name = name[0] + "***" + name[-1]
    return f"{masked_name}@{domain}"

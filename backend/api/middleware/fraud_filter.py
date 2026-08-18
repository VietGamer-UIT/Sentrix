"""
Fraud Filter — Lọc rác/gian lận cơ bản (không dùng AI)
=========================================================
Author: Nguyễn Thanh Tuyền (AI & Data Architect)
Giai đoạn: 3 (stub cơ bản) → sẽ tăng cường ở Giai đoạn 6 (ABSA-aware filtering)

MỤC ĐÍCH:
  Lọc sơ bộ các phản hồi rõ ràng là rác/spam TRƯỚC KHI gọi bất kỳ AI nào.
  Điều này tiết kiệm chi phí API (Whisper, Gemini) — không lãng phí token
  cho những input vô nghĩa.

CÁC KIỂM TRA HIỆN TẠI (Giai đoạn 3 — rule-based, không cần AI):
  Audio:
    1. Kích thước file = 0 byte (file rỗng).
    2. Kích thước quá nhỏ → tương đương < 1 giây ghi âm
       (WebM/Opus ~8kbps → 1 giây ≈ 1000 bytes; dùng ngưỡng 800 bytes an toàn).

  Text:
    1. Chuỗi rỗng hoặc chỉ toàn khoảng trắng.
    2. Toàn ký tự lặp lại (ví dụ: "aaaaaaaa", "asdasdasd") — chỉ tính ký tự
       NON-SPACE để tránh false positive với tiếng Việt nhiều dấu cách tự nhiên.
    3. Quá ngắn sau khi trim (< 3 ký tự) — không đủ nội dung để phân tích.
    4. Tỷ lệ ký tự không phải chữ/số/dấu câu quá cao (> 60%) — kiểu spam ký tự đặc biệt.

THAY ĐỔI so với phiên bản cũ (fix false positive tiếng Việt):
  - _check_repeated_chars(): bỏ khoảng trắng khỏi phép đếm ký tự phổ biến nhất.
    Tiếng Việt tự nhiên có nhiều dấu cách giữa các âm tiết — không phải spam.
  - Ngưỡng pattern lặp tăng từ repetitions >= 3 lên >= 4 để tránh nhận nhầm
    các cụm từ ngắn tiếng Việt ("ngon tuyệt", "phục vụ" v.v.).

KẾ HOẠCH MỞ RỘNG (Giai đoạn 6):
  - Sau khi có transcript từ Whisper, tái chạy fraud_filter trên text kết quả.
  - Kết hợp LLM classifier để bắt spam tinh vi hơn (ví dụ: "abcdefghijk" nói ra miệng).
"""

import re
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Hằng số ngưỡng — đặt ở đây để dễ hiệu chỉnh sau
# ---------------------------------------------------------------------------
AUDIO_MIN_BYTES = 800        # ~1 giây WebM/Opus @8kbps (an toàn về phía thấp)
TEXT_MIN_CHARS = 3           # tối thiểu 3 ký tự sau trim
TEXT_MAX_REPEAT_RATIO = 0.7  # nếu > 70% ký tự NON-SPACE là lặp → spam
TEXT_MAX_SPECIAL_RATIO = 0.6 # nếu > 60% ký tự đặc biệt → spam
REPEAT_PATTERN_MIN_COUNT = 4  # pattern lặp phải >= 4 lần mới bị flag (tránh false positive tiếng Việt)


@dataclass
class FraudFilterResult:
    """Kết quả kiểm tra fraud filter."""
    is_suspicious: bool       # True nếu bị đánh dấu nghi ngờ spam
    reason: str               # Lý do cụ thể (để log và debug)
    should_reject: bool       # True nếu nên từ chối ngay (lỗi nghiêm trọng)
                              # False = chỉ đánh dấu nghi ngờ, vẫn xử lý tiếp


def _check_repeated_chars(text: str) -> tuple[bool, str]:
    """
    Kiểm tra văn bản có toàn ký tự lặp không.
    Ví dụ: "aaaaaaa", "asdasdasd", "hahahaha"

    LƯU Ý: Bỏ khoảng trắng khỏi phép đếm để tránh false positive với tiếng Việt.
    Tiếng Việt có nhiều âm tiết ngắn, dấu cách tự nhiên xuất hiện nhiều — không phải spam.

    Returns:
        (is_repeated, reason_message)
    """
    if not text:
        return False, ""

    # Loại bỏ khoảng trắng trước khi đếm ký tự phổ biến nhất
    text_no_space = text.lower().replace(" ", "")
    if not text_no_space:
        return False, ""

    # Tính tần suất ký tự (không tính space)
    char_counts: dict[str, int] = {}
    for ch in text_no_space:
        char_counts[ch] = char_counts.get(ch, 0) + 1

    # Ký tự xuất hiện nhiều nhất chiếm bao nhiêu % (trong số ký tự non-space)
    most_common_count = max(char_counts.values())
    most_common_ratio = most_common_count / len(text_no_space)

    if most_common_ratio >= TEXT_MAX_REPEAT_RATIO:
        most_common_char = max(char_counts, key=lambda c: char_counts[c])
        return (
            True,
            f"Ký tự '{most_common_char}' chiếm {most_common_ratio:.0%} nội dung (ngưỡng {TEXT_MAX_REPEAT_RATIO:.0%})"
        )

    # Kiểm tra pattern lặp chuỗi (ví dụ "asdasdasd")
    # Nếu chuỗi có thể được tạo ra bằng cách lặp 1 pattern ngắn
    text_lower = text.lower().strip()
    for pattern_len in range(1, len(text_lower) // 2 + 1):
        pattern = text_lower[:pattern_len]
        # Số lần cần lặp để tạo thành chuỗi gốc
        repetitions = len(text_lower) // pattern_len
        # Tăng ngưỡng lên >= 4 (thay vì >= 3) để tránh false positive với tiếng Việt
        if repetitions >= REPEAT_PATTERN_MIN_COUNT and pattern * repetitions == text_lower[:pattern_len * repetitions]:
            return (
                True,
                f"Phát hiện pattern lặp '{pattern}' x{repetitions} lần"
            )

    return False, ""


def _check_special_char_ratio(text: str) -> tuple[bool, str]:
    """
    Kiểm tra tỷ lệ ký tự đặc biệt (không phải chữ cái, số, dấu câu thông thường).
    """
    if not text:
        return False, ""

    # Đếm ký tự "bình thường": chữ cái (Unicode, bao gồm tiếng Việt), số, khoảng trắng, dấu câu phổ biến
    normal_pattern = re.compile(r'[\w\s\.,!?\-\'\"àáảãạăắặẳẵặâầấậẩẫèéẻẽẹêềếệểễìíỉĩịòóỏõọôồốộổỗơờớợởỡùúủũụưừứựửữỳýỷỹỵđÀÁẢÃẠĂẮẶẲẴẶÂẦẤẬẨẪÈÉẺẼẸÊỀẾỆỂỄÌÍỈĨỊÒÓỎÕỌÔỒỐỘỔỖƠỜỚỢỞỠÙÚỦŨỤƯỪỨỰỬỮỲÝỶỸỴĐ]', re.UNICODE)
    normal_chars = len(normal_pattern.findall(text))
    special_ratio = 1 - (normal_chars / len(text))

    if special_ratio > TEXT_MAX_SPECIAL_RATIO:
        return (
            True,
            f"Tỷ lệ ký tự đặc biệt {special_ratio:.0%} (ngưỡng {TEXT_MAX_SPECIAL_RATIO:.0%})"
        )

    return False, ""


def _check_keyboard_mash(text: str) -> tuple[bool, str]:
    """
    Kiểm tra có gõ bừa trên bàn phím hay không (dựa trên chuỗi phụ âm liên tiếp dài).
    Ví dụ: 'adcadfasdf' sẽ có 7 phụ âm liên tiếp. Trong tiếng Việt hiếm khi > 3.
    """
    if not text:
        return False, ""
    
    text_lower = text.lower().strip()
    
    # Các nguyên âm trong tiếng Việt (có dấu và không dấu)
    vowels = set("aeiouyáàãảạâấầẫẩậăắằẵẳặéèẽẻẹêếềễểệíìĩỉịóòõỏọôốồỗổộơớờỡởợúùũủụưứừữửựýỳỹỷỵ")
    
    max_streak = 0
    current_streak = 0
    
    # Rule 1: Từ đơn rác không có khoảng trắng chứa hỗn hợp chữ + số (ví dụ 'asd23123')
    import re
    if ' ' not in text_lower and len(text_lower) >= 5:
        if re.search(r'[a-z]', text_lower) and re.search(r'\d', text_lower) and not re.search(r'^[a-z]+\d+$', text_lower):
            return True, "Chuỗi ký tự pha trộn chữ và số bất thường (nghi ngờ gõ bừa)"
        if len(text_lower) >= 6 and re.match(r'^[a-z0-9]+$', text_lower) and not any(v in text_lower for v in "aeiouyáàãảạâấầẫẩậăắằẵẳặéèẽẻẹêếềễểệíìĩỉịóòõỏọôốồỗổộơớờỡởợúùũủụưứừữửựýỳỹỷỵ"):
            return True, "Chuỗi từ đơn không có nguyên âm tiếng Việt"

    # Rule 2: Home-row mashing & keyboard pattern (ví dụ "asdasd", "adcadfasdt", "qweqwe")
    if len(text_lower) >= 5 and ' ' not in text_lower:
        consonants = [ch for ch in text_lower if ch.isalpha() and ch not in vowels]
        if len(text_lower) >= 6 and (len(consonants) / len(text_lower)) >= 0.65:
            return True, "Từ đơn dài không có khoảng trắng chứa tỷ lệ phụ âm bất thường (nghi ngờ gõ bừa)"
        if not any(v in text_lower for v in "aeiouyáàãảạâấầẫẩậăắằẵẳặéèẽẻẹêếềễểệíìĩỉịóòõỏọôốồỗổộơớờỡởợúùũủụưứừữửựýỳỹỷỵ"):
            return True, "Chuỗi từ đơn không có nguyên âm tiếng Việt (nghi ngờ gõ bừa)"
        if re.match(r'^[asdfghjkl0-9;]+$', text_lower):
            return True, "Gõ bừa hàng phím giữa (home-row mashing)"
        if re.match(r'^[qwertyuiop0-9]+$', text_lower) and not any(v in text_lower for v in "aeiouyáàãảạâấầẫẩậăắằẵẳặéèẽẻẹêếềễểệíìĩỉịóòõỏọôốồỗổộơớờỡởợúùũủụưứừữửựýỳỹỷỵ"):
            return True, "Gõ bừa hàng phím trên"

    # Rule 3: Quá 4 phụ âm liên tiếp
    for ch in text_lower:
        if ch.isalpha() and ch not in vowels:
            current_streak += 1
            max_streak = max(max_streak, current_streak)
        else:
            current_streak = 0
            
    if max_streak >= 4:
        return True, f"Phát hiện {max_streak} phụ âm liên tiếp, nghi ngờ gõ bừa"
        
    return False, ""


def basic_fraud_filter(
    audio_bytes: int | None = None,
    text_content: str | None = None,
) -> FraudFilterResult:
    """
    Kiểm tra sơ bộ phản hồi để phát hiện spam/rác KHÔNG dùng AI.

    Args:
        audio_bytes: Kích thước file audio (bytes). None nếu không có audio.
        text_content: Nội dung văn bản. None nếu không có text.

    Returns:
        FraudFilterResult: Kết quả kiểm tra với lý do cụ thể.

    Note:
        Hàm này chỉ ĐÁNH DẤU nghi ngờ, không tự động từ chối.
        Quyết định từ chối hay tiếp tục xử lý do endpoint thực hiện.
    """
    # --- Kiểm tra audio ---
    if audio_bytes is not None:
        if audio_bytes == 0:
            logger.warning("[FraudFilter] Audio file rỗng (0 bytes)")
            return FraudFilterResult(
                is_suspicious=True,
                reason="File audio rỗng (0 bytes)",
                should_reject=True,
            )

        if audio_bytes < AUDIO_MIN_BYTES:
            logger.warning(
                f"[FraudFilter] Audio quá ngắn: {audio_bytes} bytes < {AUDIO_MIN_BYTES} bytes (~1 giây)"
            )
            return FraudFilterResult(
                is_suspicious=True,
                reason=f"Audio quá ngắn ({audio_bytes} bytes, tương đương < 1 giây)",
                should_reject=True,
            )

    # --- Kiểm tra text ---
    if text_content is not None:
        text_stripped = text_content.strip()

        if not text_stripped:
            logger.warning("[FraudFilter] Text rỗng hoặc toàn khoảng trắng")
            return FraudFilterResult(
                is_suspicious=True,
                reason="Nội dung text rỗng",
                should_reject=True,
            )

        if len(text_stripped) < TEXT_MIN_CHARS:
            logger.warning(f"[FraudFilter] Text quá ngắn: '{text_stripped}' ({len(text_stripped)} ký tự)")
            return FraudFilterResult(
                is_suspicious=True,
                reason=f"Text quá ngắn ({len(text_stripped)} ký tự, tối thiểu {TEXT_MIN_CHARS})",
                should_reject=True,
            )

        # Kiểm tra ký tự lặp
        is_repeated, repeat_reason = _check_repeated_chars(text_stripped)
        if is_repeated:
            logger.warning(f"[FraudFilter] Text nghi ngờ spam lặp: {repeat_reason}")
            return FraudFilterResult(
                is_suspicious=True,
                reason=f"Nghi ngờ spam: {repeat_reason}",
                should_reject=False,  # Đánh dấu nhưng vẫn xử lý — có thể là false positive
            )

        # Kiểm tra tỷ lệ ký tự đặc biệt
        is_special, special_reason = _check_special_char_ratio(text_stripped)
        if is_special:
            logger.warning(f"[FraudFilter] Text nghi ngờ ký tự lạ: {special_reason}")
            return FraudFilterResult(
                is_suspicious=True,
                reason=f"Nghi ngờ spam: {special_reason}",
                should_reject=False,
            )

        # Kiểm tra gõ bừa (keyboard mash)
        is_mash, mash_reason = _check_keyboard_mash(text_stripped)
        if is_mash:
            logger.warning(f"[FraudFilter] Text nghi ngờ gõ bừa: {mash_reason}")
            return FraudFilterResult(
                is_suspicious=True,
                reason=f"Nghi ngờ spam: {mash_reason}",
                should_reject=False,
            )

    # --- Tất cả kiểm tra qua → hợp lệ ---
    return FraudFilterResult(
        is_suspicious=False,
        reason="Hợp lệ",
        should_reject=False,
    )

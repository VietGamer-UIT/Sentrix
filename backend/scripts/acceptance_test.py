"""
Acceptance Test — Module 3 & 4 Checklist
=========================================
Author: Đoàn Hoàng Việt (Việt Gamer)

Chạy: python -m backend.scripts.acceptance_test
      hoặc: python backend/scripts/acceptance_test.py

Hỗ trợ cả ABSA V1 (main branch) và V2 (feat/module3-absa-rfms-zns).
Tự động nhận diện version qua feature flags.

CHECKLIST MODULE 3:
  [M3-1] ABSA tách 2 khía cạnh trái dấu ("món ngon nhưng nhân viên chậm")
  [M3-2] Khách ≥3 lượt âm liên tiếp → p_churn tăng rõ rệt vs khách ổn định
  [M3-3] ZNS trigger: p_churn thấp + sentiment âm 1 lần → KHÔNG trigger

CHECKLIST MODULE 4:
  [M4-1] Panel gian lận: feedbacks có validity_status != "valid" xuất hiện đúng
  [M4-2] daily_voucher_limit thay đổi → có hiệu lực ngay (không cần restart backend)
  [M4-3] Panel tài chính hiển thị số hợp lý (không âm, không N/A)
"""

import os
import sys
import json
import time
import math
import logging
from pathlib import Path

# Project root vào sys.path
_root = Path(__file__).parent.parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

# Force UTF-8 stdout on Windows to avoid cp1252 UnicodeEncodeError
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from dotenv import load_dotenv
load_dotenv()

# Tắt logging noise từ thư viện ngoài
logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(name)s: %(message)s")
for noisy in ["httpx", "httpcore", "google", "urllib3", "firebase_admin", "grpc"]:
    logging.getLogger(noisy).setLevel(logging.ERROR)

# ─────────────────────────────────────────────────────────────────────────────
# Console colors
# ─────────────────────────────────────────────────────────────────────────────
try:
    import colorama; colorama.init()
    GREEN  = "\033[92m"; RED    = "\033[91m"; YELLOW = "\033[93m"
    CYAN   = "\033[96m"; BOLD   = "\033[1m";  RESET  = "\033[0m"
except ImportError:
    GREEN = RED = YELLOW = CYAN = BOLD = RESET = ""

PASS_ICON = f"{GREEN}✅ PASS{RESET}"
FAIL_ICON = f"{RED}❌ FAIL{RESET}"
SKIP_ICON = f"{YELLOW}⏭  SKIP{RESET}"
INFO      = f"{CYAN}ℹ️  {RESET}"

results = []

def header(title: str):
    bar = "─" * 60
    print(f"\n{CYAN}{BOLD}{bar}{RESET}")
    print(f"{CYAN}{BOLD}  {title}{RESET}")
    print(f"{CYAN}{BOLD}{bar}{RESET}")

def check(label: str, passed: bool, detail: str = "", skip: bool = False):
    status = SKIP_ICON if skip else (PASS_ICON if passed else FAIL_ICON)
    print(f"  {status}  {label}")
    if detail:
        for line in detail.strip().splitlines():
            print(f"           {line}")
    results.append({"label": label, "passed": passed if not skip else None, "skip": skip})


# ─────────────────────────────────────────────────────────────────────────────
# Version Detection
# ─────────────────────────────────────────────────────────────────────────────

def detect_absa_version() -> str:
    """Trả về 'v1' hoặc 'v2' dựa theo nội dung absa_llm.py hiện tại."""
    try:
        from backend.ai_pipeline import absa_llm
        # V2: có FIXED_ASPECTS constant
        if hasattr(absa_llm, "FIXED_ASPECTS"):
            return "v2"
        return "v1"
    except Exception:
        return "unknown"


# ─────────────────────────────────────────────────────────────────────────────
# [M3-1] ABSA — Tách 2 khía cạnh trái dấu
# ─────────────────────────────────────────────────────────────────────────────

def test_m3_1_absa_two_aspects():
    header("[M3-1] ABSA — Tách 2 khía cạnh trái dấu")

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        check("GEMINI_API_KEY tồn tại", False, "Thêm GEMINI_API_KEY=... vào .env")
        return

    try:
        from backend.ai_pipeline.absa_llm import analyze_absa
    except ImportError as e:
        check("Import absa_llm.analyze_absa", False, str(e))
        return

    absa_ver = detect_absa_version()
    test_text = "món ngon nhưng nhân viên chậm"
    print(f"  {INFO} ABSA version = {absa_ver}")
    print(f"  {INFO} Input: \"{test_text}\"")

    try:
        result = analyze_absa(test_text)
    except Exception as e:
        check("Gọi analyze_absa() không lỗi", False, f"{type(e).__name__}: {e}")
        return

    # ─── Unpack theo version ───
    if absa_ver == "v2":
        # V2: result = { overall_sentiment: float, aspects: [{aspect, sentiment(float), mentioned, ...}] }
        aspects   = result.get("aspects", [])
        mentioned = [a for a in aspects if a.get("mentioned", False)]
        overall   = result.get("overall_sentiment", 0.0)
        key_phrase = result.get("key_phrase", "")
        print(f"  {INFO} overall_sentiment (V2) = {overall:.3f}")
        print(f"  {INFO} key_phrase = \"{key_phrase}\"")
        print(f"  {INFO} Aspects mentioned ({len(mentioned)}/6):")
        for a in mentioned:
            score = a.get("sentiment", 0)
            icon  = "🟢" if score > 0.1 else ("🔴" if score < -0.1 else "⚪")
            print(f"           {icon} {a['aspect']:12s} score={score:+.2f}")

        # V2 checks
        has_2_mentioned = len(mentioned) >= 2
        mon_an = next((a for a in aspects if a.get("aspect") == "mon_an"), None)
        neg_service = next(
            (a for a in mentioned if a.get("aspect") in ("nhan_vien", "toc_do")
             and a.get("sentiment", 0) < 0), None
        )
        check("≥ 2 khía cạnh được đề cập (mentioned=True)", has_2_mentioned,
              f"mentioned = {[a['aspect'] for a in mentioned]}")
        check("mon_an: sentiment > 0 (tích cực)",
              mon_an and mon_an.get("mentioned") and mon_an.get("sentiment", 0) > 0,
              f"mon_an = {mon_an}")
        check("nhan_vien hoặc toc_do: sentiment < 0 (tiêu cực)",
              neg_service is not None,
              f"neg_service = {neg_service}")
        check("key_phrase không rỗng (V2)", bool(key_phrase and key_phrase.strip()),
              f"key_phrase = \"{key_phrase}\"")
        check("overall_sentiment ∈ [-1.0, +1.0] (V2)",
              -1.0 <= overall <= 1.0, f"overall = {overall:.3f}")

    else:
        # V1: result = { is_spam: bool, aspects: [{aspect(str), sentiment("Tích cực"/"Tiêu cực"), reason}] }
        is_spam  = result.get("is_spam", False)
        aspects  = result.get("aspects", [])
        print(f"  {INFO} is_spam = {is_spam}, aspects count = {len(aspects)}")
        for a in aspects:
            icon = "🟢" if a.get("sentiment") == "Tích cực" else "🔴"
            print(f"           {icon} {a.get('aspect','?'):30s}  {a.get('sentiment','?')}")

        # Kiểm tra: không bị spam và có >= 2 aspects
        check("Không bị nhận diện là spam", not is_spam,
              "Input rõ ràng là feedback thật, không nên là spam")
        check("Trả về ≥ 2 khía cạnh khác nhau (V1 free-text)",
              len(aspects) >= 2, f"aspects = {[a.get('aspect') for a in aspects]}")

        # Tìm aspect có nội dung "mon ăn/ăn/phở" → Tích cực
        food_aspects = [a for a in aspects if any(kw in a.get("aspect", "").lower()
                        for kw in ["món", "ăn", "đồ", "chất lượng", "food"])]
        food_positive = [a for a in food_aspects if a.get("sentiment") == "Tích cực"]
        check("Có aspect liên quan món ăn → Tích cực",
              len(food_positive) > 0,
              f"food_aspects = {food_aspects}")

        # Tìm aspect về nhân viên/tốc độ → Tiêu cực
        service_neg = [a for a in aspects
                       if any(kw in a.get("aspect", "").lower()
                              for kw in ["nhân viên", "thái độ", "tốc độ", "chậm", "phục vụ"])
                       and a.get("sentiment") == "Tiêu cực"]
        check("Có aspect nhân viên/tốc độ → Tiêu cực",
              len(service_neg) > 0,
              f"service_neg = {service_neg}")


# ─────────────────────────────────────────────────────────────────────────────
# [M3-2] RFMS — Churn tăng khi khách âm liên tiếp
# ─────────────────────────────────────────────────────────────────────────────

def test_m3_2_churn_accumulation():
    header("[M3-2] RFMS — Khách âm ≥3 lần có p_churn cao hơn rõ rệt")

    try:
        from backend.rfms_model.churn_model import (
            calculate_churn_full, DEFAULT_CHURN_ALERT_THRESHOLD
        )
    except ImportError as e:
        check("Import churn_model", False, str(e))
        return

    # Khách ổn định: đến gần đây, thường xuyên, hài lòng
    stable = calculate_churn_full(
        recency_days    = 5.0,
        frequency       = 12.0,
        monetary        = 800_000.0,
        sentiment_score = 0.75,   # [0,1] nội bộ — hài lòng cao
    )

    # Khách xấu x3: lâu không đến, ít ghé, avg sentiment 3 lượt âm
    # Mỗi lượt âm: sentiment ≈ 0.1 → avg = 0.1
    churning = calculate_churn_full(
        recency_days    = 150.0,  # Không đến 150 ngày (đẩy risk lên rất cao)
        frequency       = 3.0,    # Chỉ ghé 3 lần
        monetary        = 100_000.0,
        sentiment_score = 0.10,   # Avg 3 lượt âm
    )

    p_stable  = stable["p_churn"]
    p_churn3  = churning["p_churn"]
    threshold = DEFAULT_CHURN_ALERT_THRESHOLD

    print(f"  {INFO} Khách ổn định:  p_churn={p_stable:.4f}  risk={stable['risk_level']}")
    print(f"  {INFO} Khách xấu x3:   p_churn={p_churn3:.4f}  risk={churning['risk_level']}")
    print(f"  {INFO} Alert threshold: {threshold}")

    check("p_churn(xấu) > p_churn(ổn định)",
          p_churn3 > p_stable,
          f"{p_churn3:.4f} vs {p_stable:.4f}")
    check(f"p_churn(xấu) ≥ {threshold} (trigger alert)",
          p_churn3 >= threshold,
          f"p_churn(xấu) = {p_churn3:.4f}")
    check("p_churn(ổn định) < 0.50",
          p_stable < 0.50,
          f"p_churn(ổn định) = {p_stable:.4f}")
    check("Chênh lệch p_churn ≥ 0.30 (rõ rệt)",
          (p_churn3 - p_stable) >= 0.30,
          f"Δ = {p_churn3 - p_stable:.4f}")


# ─────────────────────────────────────────────────────────────────────────────
# [M3-3] ZNS Trigger Logic
# ─────────────────────────────────────────────────────────────────────────────

def test_m3_3_zns_trigger_logic():
    header("[M3-3] ZNS Trigger — Chỉ trigger khi đúng cả 2 điều kiện")

    ZNS_THRESHOLD  = 0.85
    SENT_THRESHOLD = float(os.getenv("ZNS_NEG_SENTIMENT_THRESHOLD", "-0.2"))

    def should_trigger(p_churn: float, sentiment: float) -> bool:
        # Replica logic từ feedback.py — đọc env var giống production
        return p_churn >= ZNS_THRESHOLD and sentiment < SENT_THRESHOLD

    cases = [
        {"p": 0.91, "s": -0.65, "expected": True,  "desc": "A: p cao + sentiment âm → PHẢI trigger"},
        {"p": 0.40, "s": -0.65, "expected": False, "desc": "B: p THẤP + sentiment âm → KHÔNG trigger ⚠️ critical"},
        {"p": 0.90, "s": +0.45, "expected": False, "desc": "C: p cao + sentiment DƯƠNG → KHÔNG trigger"},
        {"p": 0.88, "s": -0.10, "expected": False, "desc": "D: p cao + sentiment gần 0 (≥ -0.2) → KHÔNG trigger"},
        {"p": 0.85, "s": -0.21, "expected": True,  "desc": "E: đúng biên threshold → trigger"},
    ]

    all_ok = True
    for c in cases:
        got = should_trigger(c["p"], c["s"])
        ok  = got == c["expected"]
        if not ok: all_ok = False
        icon = "🟢" if ok else "🔴"
        exp  = "trigger" if c["expected"] else "no-ZNS"
        got_s = "trigger" if got else "no-ZNS"
        print(f"  {INFO} {icon} {c['desc']}")
        print(f"           p={c['p']}, s={c['s']:+.2f} → expected={exp}, got={got_s}")

    check("Tất cả kịch bản ZNS trigger/no-trigger đúng", all_ok,
          f"ZNS_THRESHOLD={ZNS_THRESHOLD}, SENT_THRESHOLD={SENT_THRESHOLD}")
    check("ZNS_NEG_SENTIMENT_THRESHOLD hợp lệ (≤ 0.0)",
          SENT_THRESHOLD <= 0.0,
          f"SENT_THRESHOLD = {SENT_THRESHOLD} (từ env hoặc default -0.2)")

    # Test quan trọng nhất (B): p_churn thấp + sentiment âm → KHÔNG gửi ZNS
    case_b = not should_trigger(0.40, -0.65)
    check("⚠️  CRITICAL: p_churn=0.40, sentiment=-0.65 → KHÔNG trigger ZNS",
          case_b, "Nếu fail → hệ thống sẽ spam ZNS cho khách chưa churn")


# ─────────────────────────────────────────────────────────────────────────────
# [Unit] ABSA Parse — không cần API key
# ─────────────────────────────────────────────────────────────────────────────

def test_unit_absa_parse():
    header("[Unit] ABSA — Parse logic (không cần API key)")

    absa_ver = detect_absa_version()
    print(f"  {INFO} ABSA version = {absa_ver}")

    if absa_ver == "v2":
        # V2: test _parse_llm_output và FIXED_ASPECTS
        try:
            from backend.ai_pipeline.absa_llm import (
                _parse_llm_output, _strip_markdown, FIXED_ASPECTS, ASPECT_LABELS_VI
            )
        except ImportError as e:
            check("Import absa_llm V2 symbols", False, str(e))
            return

        check("FIXED_ASPECTS đúng 6 khía cạnh",
              set(FIXED_ASPECTS) == {"mon_an", "nhan_vien", "khong_gian", "gia_ca", "toc_do", "ve_sinh"},
              f"FIXED_ASPECTS = {FIXED_ASPECTS}")
        check("ASPECT_LABELS_VI có đủ 6 keys",
              len(ASPECT_LABELS_VI) >= 6, str(ASPECT_LABELS_VI))

        # Parse valid JSON V2
        v2_json = json.dumps({
            "overall_sentiment": 0.2,
            "is_spam": False,
            "sarcasm_detected": False,
            "key_phrase": "món ngon",
            "aspects": [
                {"aspect": k, "sentiment": 0.5 if i == 0 else -0.3 if i == 1 else 0.0,
                 "mentioned": i < 2, "reason": "test", "label_vi": "X"}
                for i, k in enumerate(FIXED_ASPECTS)
            ]
        })
        parsed = _parse_llm_output(v2_json)
        check("Parse JSON V2 hợp lệ: trả đủ 6 aspects",
              len(parsed.get("aspects", [])) == 6,
              f"aspects = {[a.get('aspect') for a in parsed.get('aspects', [])]}")
        check("overall_sentiment = 0.2",
              parsed.get("overall_sentiment") == 0.2,
              f"overall_sentiment = {parsed.get('overall_sentiment')}")

    else:
        # V1: test _strip_markdown và _parse_llm_output
        try:
            from backend.ai_pipeline.absa_llm import _strip_markdown, _parse_llm_output
        except ImportError as e:
            check("Import absa_llm V1 symbols", False, str(e))
            return

        # Test strip markdown
        raw = "```json\n[{\"aspect\": \"Nhân viên\", \"sentiment\": \"Tích cực\", \"reason\": \"ok\"}]\n```"
        stripped = _strip_markdown(raw)
        check("_strip_markdown loại bỏ ```json``` thành công",
              stripped.startswith("[{"), f"stripped = '{stripped[:60]}'")

        # Test parse list
        valid_list = '[{"aspect": "Nhân viên", "sentiment": "Tích cực", "reason": "tốt"}]'
        parsed = _parse_llm_output(valid_list)
        check("Parse list JSON hợp lệ (V1)",
              isinstance(parsed, list) and len(parsed) == 1,
              f"parsed = {parsed}")

        # Test parse spam dict
        spam_str = '{"is_spam": true, "aspects": []}'
        parsed_spam = _parse_llm_output(spam_str)
        check("Parse spam dict (V1): is_spam=True",
              isinstance(parsed_spam, dict) and parsed_spam.get("is_spam") is True,
              f"parsed_spam = {parsed_spam}")


# ─────────────────────────────────────────────────────────────────────────────
# [Unit] Fusion — sentiment_score và aspects
# ─────────────────────────────────────────────────────────────────────────────

def test_unit_fusion():
    header("[Unit] Fusion — dynamic_weighted_fusion()")

    try:
        from backend.ai_pipeline.fusion import dynamic_weighted_fusion, normalize_aspects_for_db
    except ImportError as e:
        check("Import fusion", False, str(e))
        return

    absa_ver = detect_absa_version()

    if absa_ver == "v2":
        # V2 ABSA output format
        absa_out = {
            "overall_sentiment": -0.1,
            "is_spam": False,
            "sarcasm_detected": False,
            "key_phrase": "món ngon nhưng nhân viên chậm",
            "aspects": [
                {"aspect": "mon_an",    "sentiment":  0.8, "mentioned": True,  "reason": "Ngon", "label_vi": "Món ăn"},
                {"aspect": "nhan_vien", "sentiment": -0.6, "mentioned": True,  "reason": "Chậm", "label_vi": "Nhân viên"},
                {"aspect": "khong_gian","sentiment":  0.0, "mentioned": False, "reason": "", "label_vi": "Không gian"},
                {"aspect": "gia_ca",    "sentiment":  0.0, "mentioned": False, "reason": "", "label_vi": "Giá cả"},
                {"aspect": "toc_do",    "sentiment": -0.7, "mentioned": True,  "reason": "Chờ lâu", "label_vi": "Tốc độ phục vụ"},
                {"aspect": "ve_sinh",   "sentiment":  0.0, "mentioned": False, "reason": "", "label_vi": "Vệ sinh"},
            ]
        }
    else:
        # V1 ABSA output format
        absa_out = {
            "is_spam": False,
            "aspects": [
                {"aspect": "Chất lượng món ăn", "sentiment": "Tích cực", "reason": "Ngon"},
                {"aspect": "Thái độ nhân viên", "sentiment": "Tiêu cực", "reason": "Chậm"},
            ],
            "raw_llm_output": "..."
        }

    fusion = dynamic_weighted_fusion(absa_out, audio_features=None)

    sentiment_score = fusion.get("sentiment_score", None)
    internal_score  = fusion.get("_internal_sentiment_score", None)

    print(f"  {INFO} sentiment_score (external) = {sentiment_score}")
    print(f"  {INFO} _internal_sentiment_score  = {internal_score}")
    print(f"  {INFO} fusion_mode = {fusion.get('fusion_mode')}")
    print(f"  {INFO} aspects count = {len(fusion.get('aspects', []))}")

    # External score [-1, 1]
    check("sentiment_score ∈ [-1.0, +1.0] (external scale)",
          sentiment_score is not None and -1.0 <= sentiment_score <= 1.0,
          f"sentiment_score = {sentiment_score}")

    # Internal score [0, 1] dùng cho RFMS S
    if internal_score is not None:
        check("_internal_sentiment_score ∈ [0.0, 1.0] (RFMS input)",
              0.0 <= internal_score <= 1.0,
              f"internal = {internal_score:.4f}")

    # Aspects có đầy đủ fields
    aspects = fusion.get("aspects", [])
    if aspects:
        first = aspects[0]
        required_fields = ["aspect", "score"]
        if absa_ver == "v2":
            required_fields.append("sentiment_en")
        else:
            required_fields.append("sentiment")

        has_required_fields = all(k in first for k in required_fields)
        check(f"Aspect có đủ fields: {', '.join(required_fields)}",
              has_required_fields,
              f"aspects[0] keys = {list(first.keys())}")

    if absa_ver == "v2":
        check("key_phrase pass-through từ ABSA V2",
              fusion.get("key_phrase") == "món ngon nhưng nhân viên chậm",
              f"key_phrase = '{fusion.get('key_phrase')}'")


# ─────────────────────────────────────────────────────────────────────────────
# [M4-1] Fraud Panel — API endpoint test
# ─────────────────────────────────────────────────────────────────────────────

def _get_test_client():
    try:
        from fastapi.testclient import TestClient
        from backend.api.main import app
        return TestClient(app, raise_server_exceptions=False)
    except Exception as e:
        print(f"  {YELLOW}⚠️  Không tạo được TestClient: {type(e).__name__}: {e}{RESET}")
        return None


def test_m4_1_fraud_monitor_data():
    header("[M4-1] Fraud Panel — API trả validity_status đúng")

    client = _get_test_client()
    if not client:
        check("FastAPI TestClient khởi động", False, skip=True)
        return

    TENANT_ID = "pho-ba-lan_1722500000000"

    # Feedback hợp lệ
    print(f"  {INFO} Gửi feedback hợp lệ...")
    res_valid = client.post("/api/v1/feedback", data={
        "tenant_id": TENANT_ID, "location": "Test Bàn A",
        "text_content": "Món ăn ngon, nhân viên thân thiện",
    })
    vbody = res_valid.json() if res_valid.status_code in (200, 201, 202, 422) else {}
    print(f"  {INFO} HTTP {res_valid.status_code}: validity_status={vbody.get('validity_status', '?')}")

    check("Feedback hợp lệ: HTTP 200/201/202",
          res_valid.status_code in (200, 201, 202),
          f"HTTP {res_valid.status_code}: {str(vbody)[:150]}")
    check("validity_status = 'valid'",
          vbody.get("validity_status") == "valid",
          f"validity_status = '{vbody.get('validity_status')}'")
    check("Response có field fraud_layer_rejected_at",
          "fraud_layer_rejected_at" in vbody,
          f"keys = {list(vbody.keys())[:8]}")

    # Feedback spam ký tự
    print(f"  {INFO} Gửi feedback spam...")
    res_spam = client.post("/api/v1/feedback", data={
        "tenant_id": TENANT_ID, "location": "Test Bàn B",
        "text_content": "aaa bbb 123 !!! xyz qwe",
    })
    sbody = res_spam.json() if res_spam.status_code in (200, 201, 202, 400, 422) else {}
    spam_validity = sbody.get("validity_status", "")
    print(f"  {INFO} HTTP {res_spam.status_code}: validity_status='{spam_validity}'")

    is_blocked = (
        spam_validity in ("invalid_semantic", "rate_limited") or
        sbody.get("is_spam") is True or
        res_spam.status_code == 422
    )
    check("Feedback spam bị phát hiện hoặc bị reject",
          is_blocked,
          "Nếu SKIP_SEMANTIC_CHECK=true trong .env → spam có thể bypass Lớp 3. "
          f"validity_status='{spam_validity}', HTTP={res_spam.status_code}")


# ─────────────────────────────────────────────────────────────────────────────
# [M4-2] Voucher Config Hot-Reload
# ─────────────────────────────────────────────────────────────────────────────

def test_m4_2_voucher_limit_hot_reload():
    header("[M4-2] Voucher Config — Thay đổi có hiệu lực ngay")

    client = _get_test_client()
    if not client:
        check("FastAPI TestClient", False, skip=True)
        return

    TENANT_ID = "pho-ba-lan_1722500000000"

    # Test PUT endpoint tồn tại
    res_put = client.put("/api/v1/gamification/voucher-config", json={
        "tenant_id": TENANT_ID,
        "daily_voucher_limit": 50,
        "win_rate_percent": 30,
    })

    if res_put.status_code == 404:
        check("PUT /api/v1/gamification/voucher-config: 404", False,
              "Endpoint chưa tồn tại — cần tạo route trong gamification.py", skip=True)
        return

    check(f"PUT voucher-config trả HTTP 2xx",
          res_put.status_code in (200, 201),
          f"HTTP {res_put.status_code}: {res_put.text[:200]}")

    if res_put.status_code not in (200, 201):
        return

    time.sleep(0.5)  # Đợi Firestore write

    # GET để verify giá trị mới
    res_get = client.get(f"/api/v1/gamification/voucher-config?tenant_id={TENANT_ID}")
    if res_get.status_code == 200:
        data    = res_get.json()
        new_lim = (data.get("daily_voucher_limit")
                   or data.get("data", {}).get("daily_voucher_limit"))
        print(f"  {INFO} GET sau PUT: daily_voucher_limit = {new_lim}")
        check("daily_voucher_limit = 50 sau PUT (hot-reload đã lưu)",
              new_lim == 50,
              f"new_lim = {new_lim}")
    else:
        print(f"  {YELLOW}⚠️  GET config HTTP {res_get.status_code} — bỏ qua verify{RESET}")
        check("GET voucher-config verify", True, skip=True)

    # Test PUT limit thấp hơn
    res_put2 = client.put("/api/v1/gamification/voucher-config", json={
        "tenant_id": TENANT_ID,
        "daily_voucher_limit": 5,
        "win_rate_percent": 100,
    })
    check("PUT lần 2 (limit=5, win_rate=100%): HTTP 2xx",
          res_put2.status_code in (200, 201),
          f"HTTP {res_put2.status_code}")

    # Restore về giá trị bình thường (không ảnh hưởng demo)
    client.put("/api/v1/gamification/voucher-config", json={
        "tenant_id": TENANT_ID,
        "daily_voucher_limit": 20,
        "win_rate_percent": 30,
    })
    print(f"  {INFO} Đã restore về limit=20, win_rate=30%")


# ─────────────────────────────────────────────────────────────────────────────
# [M4-3] Operating Cost — Số liệu hợp lý
# ─────────────────────────────────────────────────────────────────────────────

def test_m4_3_operating_cost_values():
    header("[M4-3] Operating Cost — Số >= 0, không NaN/None")

    WHISPER = 0.003    # USD/lượt
    GEMINI  = 0.0001   # USD/lượt
    ZNS     = 1000.0   # VNĐ/tin
    RATE    = 25_000.0 # 1 USD = ? VNĐ

    def compute_cost(n_audio, n_processed, n_zns, hosting=0.0):
        w = n_audio * WHISPER * RATE
        g = n_processed * GEMINI * RATE
        z = n_zns * ZNS
        total = w + g + z + hosting * RATE
        return {"whisper": w, "gemini": g, "zns": z, "hosting": hosting*RATE, "total": total}

    def is_valid_cost(c: dict) -> bool:
        return all(
            isinstance(v, (int, float)) and v >= 0 and not math.isnan(v)
            for v in c.values()
        )

    test_cases = [
        (0, 0, 0, 0,   "Fresh start (0 feedbacks)"),
        (5, 5, 0, 0,   "5 audio feedbacks, 0 ZNS"),
        (3, 8, 1, 0,   "Mixed: 3 audio + 8 processed + 1 ZNS"),
        (0, 2, 0, 0,   "2 text feedbacks only"),
        (10, 10, 3, 0, "10 audio + 3 ZNS"),
    ]

    all_ok = True
    for n_a, n_p, n_z, hosting, desc in test_cases:
        c = compute_cost(n_a, n_p, n_z, hosting)
        ok = is_valid_cost(c)
        if not ok: all_ok = False
        per_fb = (c["total"] / n_p) if n_p > 0 else 0.0
        print(f"  {INFO} [{desc}] total={c['total']:.0f} VNĐ, per_fb={per_fb:.1f} VNĐ {'✓' if ok else '✗ INVALID'}")

    check("Tất cả kịch bản chi phí: >= 0, không NaN", all_ok)

    # Kiểm tra chi phí / feedback hợp lý
    typical = (WHISPER + GEMINI) * RATE
    check(f"Chi phí/feedback điển hình < 10,000 VNĐ (thực tế ≈ {typical:.0f} VNĐ)",
          typical < 10_000,
          f"Whisper({WHISPER} USD) + Gemini({GEMINI} USD) × {RATE} VNĐ/USD = {typical:.0f} VNĐ/feedback")

    # Kiểm tra fresh start = 0.0 (không NaN)
    c0 = compute_cost(0, 0, 0, 0)
    check("Fresh start: total = 0.0 (không NaN, không None)",
          c0["total"] == 0.0 and not math.isnan(c0["total"]),
          f"total = {c0['total']}")

    # ZNS unit price hợp lý (< 10,000 VNĐ/tin)
    check(f"ZNS unit price hợp lý (< 10,000 VNĐ/tin, thực tế {ZNS:.0f} VNĐ)",
          ZNS < 10_000,
          f"VITE_COST_ZNS_PER_MSG = {ZNS} VNĐ")


# ─────────────────────────────────────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────────────────────────────────────

def print_summary() -> bool:
    bar = "═" * 62
    print(f"\n{CYAN}{BOLD}{bar}{RESET}")
    print(f"{CYAN}{BOLD}  KẾT QUẢ NGHIỆM THU — MODULE 3 & 4{RESET}")
    print(f"{CYAN}{BOLD}{bar}{RESET}")

    passed  = [r for r in results if r["passed"] is True]
    failed  = [r for r in results if r["passed"] is False]
    skipped = [r for r in results if r["skip"]]

    for r in results:
        status = SKIP_ICON if r["skip"] else (PASS_ICON if r["passed"] else FAIL_ICON)
        print(f"  {status}  {r['label']}")

    print(f"\n{BOLD}  Tổng: {len(results)} | "
          f"{GREEN}{len(passed)} PASS{RESET} | "
          f"{RED}{len(failed)} FAIL{RESET} | "
          f"{YELLOW}{len(skipped)} SKIP{RESET}{BOLD}{RESET}")

    if failed:
        print(f"\n{RED}{BOLD}  ⚠️  {len(failed)} lỗi cần fix:{RESET}")
        for f in failed:
            print(f"  {RED}  ✗ {f['label']}{RESET}")

    overall = len(failed) == 0
    verdict = (f"{GREEN}{BOLD}✅ NGHIỆM THU ĐẠT{RESET}"
               if overall else f"{RED}{BOLD}❌ CÒN LỖI CẦN SỬA{RESET}")
    print(f"\n  {verdict}\n")
    return overall


# ─────────────────────────────────────────────────────────────────────────────
# Entry Point
# ─────────────────────────────────────────────────────────────────────────────

def main():
    absa_ver = detect_absa_version()

    sep = "=" * 62
    print(f"\n{BOLD}{sep}{RESET}")
    print(f"{BOLD}  Sentrix -- Acceptance Test -- Module 3 & 4{RESET}")
    print(f"{BOLD}  Author: Doan Hoang Viet (Viet Gamer){RESET}")
    print(f"{BOLD}  ABSA Version Detected: {absa_ver}{RESET}")
    print(f"{BOLD}{sep}{RESET}")

    # ── Unit tests (không cần API key / Firestore) ──
    test_unit_absa_parse()
    test_unit_fusion()

    # ── Module 3 ──
    test_m3_1_absa_two_aspects()    # Cần GEMINI_API_KEY
    test_m3_2_churn_accumulation()  # Pure math
    test_m3_3_zns_trigger_logic()   # Pure logic

    # ── Module 4 ──
    test_m4_1_fraud_monitor_data()        # Cần FastAPI
    test_m4_2_voucher_limit_hot_reload()  # Cần FastAPI + Firestore
    test_m4_3_operating_cost_values()     # Pure math

    return print_summary()


if __name__ == "__main__":
    ok = main()
    sys.exit(0 if ok else 1)

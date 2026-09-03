# SENTRIX — CURRENT SYSTEM MAP
Generated: 2026-09-03 | Phase: DEMO / MVP / PILOT-READY
Source: Code scan thuc te, khong gia dinh

## BASELINE TEST RESULTS (2026-09-03)
Total: 141 tests | PASS: 133 | FAIL: 8

FAIL list:
1. test_valid_audio_returns_202 — fake x00 bytes rejected by audio quality gate (422 not 202)
2. test_both_audio_and_text_returns_202 — same
3. test_sentiment_score_in_range — fusion sarcasm path returns score outside [0,1]
4. test_missing_all_credentials_raises_environment_error — Firebase init doesn not raise EnvironmentError
5. test_logic_only (RFMS) — p_churn=0.49 -> medium, test expects low
6. test_normalize_aspects_list_adds_fields — missing category field
7. test_normalize_unknown_sentiment_defaults_neutral — missing sentiment_en field
8. test_nhan_vien_phuc_vu_kem_gets_negative_score — text_sentiment_score scale mismatch

## HARD-CODED VALUES
- LandingPage.jsx:26 — businessName = Pho Ba Lan (PILOT BLOCKER)
- RecordingPage.jsx:89 — tenantId fallback hardcode
- useFirestore.js:27 — VITE_DEMO_TENANT_ID fallback

## MISSING FEATURES vs SPECIFICATION
1. Intent Classification (SUPPORT_REQUEST/FEEDBACK/INVALID) — NOT IMPLEMENTED
2. Staff Alert System (alerts collection) — NOT IMPLEMENTED  
3. Dashboard Alerts Tab + realtime — NOT IMPLEMENTED
4. Alert lifecycle API (acknowledge/resolve) — NOT IMPLEMENTED
5. businessName from tenant API — Hard-coded only
6. Tenant validation (valid/invalid/inactive) — NOT IMPLEMENTED
7. Recovery Action (review invitation) — NOT IMPLEMENTED
8. Audit Events in Firestore — Logs only

## WORKING FEATURES
- Voice recording -> Groq Whisper STT -> Firestore (end-to-end)
- Text -> Gemini ABSA -> Firestore (end-to-end)
- Anti-fraud 4 layers (rate limit, audio quality, semantic validity, voucher budget)
- RFMS + P_churn calculation
- Consent PDPA recording
- Audio deletion after STT
- Voucher budget system + gamification spin
- Dashboard realtime (Firestore onSnapshot when VITE_USE_MOCK_FIRESTORE=false)
- Dashboard auth (Firebase Google Sign-In)

"""
Batch RFMS Recompute — Chạy RFMS pipeline cho tất cả tenants
==============================================================
Author: Đoàn Hoàng Việt (Việt Gamer)
Mục đích: Script CLI để chạy RFMS recompute hàng đêm (cron job)

CÁCH CHẠY:
  # Recompute tất cả tenants tìm thấy trong Firestore:
  python -m backend.scripts.batch_rfms

  # Recompute 1 tenant cụ thể:
  python -m backend.scripts.batch_rfms --tenant demo_restaurant_01

  # Ép dùng Synthetic LR (chế độ B) dù ít data:
  python -m backend.scripts.batch_rfms --force-synthetic

  # Dry-run (không ghi Firestore):
  python -m backend.scripts.batch_rfms --dry-run

CRON JOB (Render.com):
  Render chưa có cron job native ở free tier.
  Thay thế: Dùng GitHub Actions schedule:
    on:
      schedule:
        - cron: '0 2 * * *'  # 2:00 UTC = 9:00 ICT hàng ngày
    steps:
      - run: curl -X POST https://sentrix-backend.onrender.com/api/v1/rfms/recompute ...
"""

import argparse
import logging
import os
import sys
from pathlib import Path

# Ensure project root is in path khi chạy trực tiếp
_root = Path(__file__).parent.parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from dotenv import load_dotenv
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def get_all_tenant_ids() -> list[str]:
    """Lấy danh sách tất cả tenant IDs từ Firestore."""
    try:
        from backend.db.firestore_client import get_firestore_client
        db = get_firestore_client()
        tenants = db.collection("tenants").stream()
        ids = [t.id for t in tenants]
        logger.info(f"[Batch RFMS] Tìm thấy {len(ids)} tenants: {ids}")
        return ids
    except Exception as e:
        logger.error(f"[Batch RFMS] Không đọc được tenants: {e}")
        return []


def main():
    parser = argparse.ArgumentParser(description="Batch RFMS Recompute")
    parser.add_argument("--tenant", type=str, default=None, help="Tenant ID cụ thể (bỏ qua = tất cả)")
    parser.add_argument("--force-synthetic", action="store_true", help="Ép dùng Synthetic LR")
    parser.add_argument("--dry-run", action="store_true", help="Không ghi Firestore")
    args = parser.parse_args()

    from backend.rfms_model.rfms_pipeline import compute_rfms_for_tenant

    if args.tenant:
        tenant_ids = [args.tenant]
    else:
        tenant_ids = get_all_tenant_ids()

    if not tenant_ids:
        logger.warning("[Batch RFMS] Không có tenant nào để xử lý.")
        return

    total_updated = 0
    total_errors = 0

    for tenant_id in tenant_ids:
        logger.info(f"\n{'='*60}")
        logger.info(f"[Batch RFMS] Xử lý tenant: {tenant_id}")
        try:
            result = compute_rfms_for_tenant(
                tenant_id=tenant_id,
                force_synthetic=args.force_synthetic,
                update_firestore=not args.dry_run,
            )
            total_updated += result.get("n_updated", 0)
            total_errors += len(result.get("errors", []))

            logger.info(
                f"[Batch RFMS] ✅ {tenant_id}: "
                f"mode={result['mode']}, "
                f"updated={result['n_updated']}/{result['n_customers']}, "
                f"high_risk={result['churn_rate']:.1%}"
            )
            if result.get("errors"):
                logger.warning(f"  ⚠️ Errors: {result['errors'][:3]}")
        except Exception as e:
            logger.error(f"[Batch RFMS] ❌ {tenant_id} thất bại: {e}")
            total_errors += 1

    logger.info(f"\n{'='*60}")
    logger.info(
        f"[Batch RFMS] Hoàn tất: {len(tenant_ids)} tenants, "
        f"tổng updated={total_updated}, "
        f"errors={total_errors}"
        + (" [DRY-RUN — không ghi Firestore]" if args.dry_run else "")
    )


if __name__ == "__main__":
    main()

import os
import sys
import argparse
from typing import List, Dict, Any

# Ép console xuất utf-8 để tránh lỗi 'charmap' trên Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

from dotenv import load_dotenv

# Đảm bảo đường dẫn gốc của project nằm trong sys.path để import module "backend"
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.append(project_root)

# Load biến môi trường từ .env ở root
load_dotenv(os.path.join(project_root, ".env"))

from backend.db.firestore_client import get_firestore_client

from backend.db.firestore_client import get_firestore_client

# Define what constitutes a "test/spam" record
SPAM_PATTERNS = [
    "asdasd", "aaaa", "test", "123", "xyz", "qwe", "bbla"
]

def is_spam_record(doc_data: Dict[str, Any]) -> bool:
    """Check if a document is likely a test or spam record."""
    if doc_data.get("is_suspicious") is True:
        return True
    
    if doc_data.get("is_spam") is True:
        return True

    transcript = (doc_data.get("transcript") or "").lower()
    
    # Check for empty or very short transcript
    if len(transcript.strip()) < 3 and doc_data.get("input_type") == "text":
        return True
        
    # Check for known spam patterns
    for pattern in SPAM_PATTERNS:
        if pattern in transcript:
            return True
            
    return False

def cleanup_demo_data(tenant_id: str, execute: bool = False):
    """Scan and optionally delete spam/test records from a tenant."""
    print(f"--- DEMO DATA CLEANUP FOR TENANT: {tenant_id} ---")
    print(f"Mode: {'EXECUTE (DELETING)' if execute else 'DRY RUN (NO DELETION)'}\n")
    
    try:
        db = get_firestore_client()
        feedbacks_ref = db.collection("tenants").document(tenant_id).collection("feedbacks")
        
        # Get all feedbacks
        all_docs = list(feedbacks_ref.stream())
        print(f"Total feedbacks found: {len(all_docs)}")
        
        spam_docs = []
        for doc in all_docs:
            data = doc.to_dict()
            if is_spam_record(data):
                spam_docs.append((doc.id, data))
                
        print(f"\nFound {len(spam_docs)} spam/test records to clean up:")
        
        for doc_id, data in spam_docs:
            reason = []
            if data.get("is_suspicious"): reason.append("is_suspicious=True")
            if data.get("is_spam"): reason.append("is_spam=True")
            transcript = (data.get("transcript") or "")[:50]
            print(f"- ID: {doc_id} | Reasons: {', '.join(reason)} | Transcript: '{transcript}'")
            
        print("-" * 50)
        
        if execute:
            if not spam_docs:
                print("No spam records to delete.")
                return
                
            print(f"\nDeleting {len(spam_docs)} records...")
            batch = db.batch()
            batch_count = 0
            
            for doc_id, _ in spam_docs:
                doc_ref = feedbacks_ref.document(doc_id)
                batch.delete(doc_ref)
                batch_count += 1
                
                # Firestore batch limit is 500
                if batch_count >= 400:
                    batch.commit()
                    print(f"Committed batch of {batch_count} deletions...")
                    batch = db.batch()
                    batch_count = 0
            
            if batch_count > 0:
                batch.commit()
                print(f"Committed final batch of {batch_count} deletions.")
                
            print("\nCleanup completed successfully!")
        else:
            print("\nDRY RUN complete. Run with --execute to actually delete these records.")
            
    except Exception as e:
        print(f"Error during cleanup: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Cleanup spam and test data for AISC demo")
    parser.add_argument("--tenant", type=str, default="pho-ba-lan_1722500000000", help="Tenant ID")
    parser.add_argument("--execute", action="store_true", help="Actually delete the records (default is dry-run)")
    
    args = parser.parse_args()
    cleanup_demo_data(args.tenant, args.execute)

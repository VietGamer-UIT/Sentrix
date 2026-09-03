"""
test_alerts.py - Unit tests for Staff Alert API (Milestone 4)
=============================================================
Chay: pytest backend/tests/test_alerts.py -v

Dung mock Firestore - khong can credentials thuc.
"""
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from backend.api.main import app

client = TestClient(app)

TENANT = "demo-tenant-001"
BASE   = f"/api/v1/tenants/{TENANT}/alerts"


def _make_alert_doc(alert_id="alert-001", status="CREATED"):
    snap = MagicMock()
    snap.exists = True
    snap.id     = alert_id
    snap.to_dict.return_value = {
        "feedback_id":     "fb-001",
        "location":        "Ban 5",
        "status":          status,
        "intent":          "SUPPORT_REQUEST",
        "transcript":      "Cho toi them nuoc da",
        "created_at":      None,
        "acknowledged_at": None,
        "resolved_at":     None,
    }
    return snap


# ---------------------------------------------------------------------------
# Test: POST /alerts
# ---------------------------------------------------------------------------

class TestCreateAlert:
    def test_create_alert_success(self):
        """POST /alerts -> 201 voi alert_id."""
        with patch("backend.api.routes.alerts.create_alert", return_value="alert-abc") as mock_create:
            resp = client.post(BASE, json={
                "feedback_id": "fb-001",
                "location":    "Ban 5",
                "transcript":  "Cho toi them nuoc da",
                "intent":      "SUPPORT_REQUEST",
            })
        assert resp.status_code == 201
        data = resp.json()
        assert data["alert_id"] == "alert-abc"
        assert data["status"]   == "CREATED"
        mock_create.assert_called_once()

    def test_create_alert_firestore_error_returns_500(self):
        """Neu Firestore loi -> 500."""
        with patch("backend.api.routes.alerts.create_alert", side_effect=Exception("fs error")):
            resp = client.post(BASE, json={
                "feedback_id": "fb-002",
                "location":    "Ban 3",
                "transcript":  "Can ho don",
                "intent":      "SUPPORT_REQUEST",
            })
        assert resp.status_code == 500


# ---------------------------------------------------------------------------
# Test: GET /alerts
# ---------------------------------------------------------------------------

class TestListAlerts:
    def _make_stream(self, snaps):
        """Tra ve iterator gia lap Firestore stream."""
        return iter(snaps)

    def test_list_alerts_returns_empty(self):
        """Khong co alerts -> {"alerts": [], "count": 0}."""
        with patch("backend.api.routes.alerts.get_alerts", return_value=[]) as mock_get:
            resp = client.get(BASE)
        assert resp.status_code == 200
        assert resp.json() == {"alerts": [], "count": 0}

    def test_list_alerts_returns_items(self):
        """Co 2 alerts -> count=2."""
        mock_alerts = [
            {"alert_id": "a1", "status": "CREATED",      "feedback_id": "f1",
             "location": "Ban 1", "transcript": "T1", "intent": "SUPPORT_REQUEST",
             "created_at": None, "acknowledged_at": None, "resolved_at": None},
            {"alert_id": "a2", "status": "ACKNOWLEDGED", "feedback_id": "f2",
             "location": "Ban 2", "transcript": "T2", "intent": "SUPPORT_REQUEST",
             "created_at": None, "acknowledged_at": None, "resolved_at": None},
        ]
        with patch("backend.api.routes.alerts.get_alerts", return_value=mock_alerts):
            resp = client.get(BASE)
        assert resp.status_code == 200
        assert resp.json()["count"] == 2

    def test_list_alerts_invalid_status_returns_400(self):
        """status=INVALID_STATUS -> 400."""
        resp = client.get(BASE, params={"status": "INVALID_STATUS"})
        assert resp.status_code == 400

    def test_list_alerts_valid_status_filter(self):
        """status=CREATED -> goi get_alerts voi status_filter dung."""
        with patch("backend.api.routes.alerts.get_alerts", return_value=[]) as mock_get:
            resp = client.get(BASE, params={"status": "CREATED"})
        assert resp.status_code == 200
        mock_get.assert_called_once_with(
            tenant_id=TENANT,
            limit=50,
            status_filter="CREATED",
        )


# ---------------------------------------------------------------------------
# Test: PATCH /alerts/{id}/acknowledge
# ---------------------------------------------------------------------------

class TestAcknowledgeAlert:
    def test_acknowledge_success(self):
        """PATCH /acknowledge -> 200 voi status ACKNOWLEDGED."""
        with patch("backend.api.routes.alerts.acknowledge_alert", return_value=True):
            resp = client.patch(f"{BASE}/alert-001/acknowledge")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ACKNOWLEDGED"

    def test_acknowledge_not_found_returns_404(self):
        """Alert khong ton tai -> 404."""
        with patch("backend.api.routes.alerts.acknowledge_alert", return_value=False):
            resp = client.patch(f"{BASE}/nonexistent/acknowledge")
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Test: PATCH /alerts/{id}/resolve
# ---------------------------------------------------------------------------

class TestResolveAlert:
    def test_resolve_success(self):
        """PATCH /resolve -> 200 voi status RESOLVED."""
        with patch("backend.api.routes.alerts.resolve_alert", return_value=True):
            resp = client.patch(f"{BASE}/alert-001/resolve")
        assert resp.status_code == 200
        assert resp.json()["status"] == "RESOLVED"

    def test_resolve_not_found_returns_404(self):
        """Alert khong ton tai -> 404."""
        with patch("backend.api.routes.alerts.resolve_alert", return_value=False):
            resp = client.patch(f"{BASE}/nonexistent/resolve")
        assert resp.status_code == 404

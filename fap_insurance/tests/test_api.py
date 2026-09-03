"""FAP-Insurance API Tests"""
import pytest
from fastapi.testclient import TestClient
from fap_insurance.api import app
from fap_insurance.pricing import PricingCalculator, get_pricing_summary
from fap_insurance.report_generator import AdjusterReport

client = TestClient(app)

# ─── Health ──────────────────────────────────────────────────────────

def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "healthy"
    assert "version" in data

def test_pricing_endpoint():
    r = client.get("/pricing")
    assert r.status_code == 200
    data = r.json()
    assert "tiers" in data
    assert "pilot" in data["tiers"]
    assert "carrier" in data["tiers"]

def test_pricing_specific_tier():
    r = client.get("/pricing?tier=carrier")
    assert r.status_code == 200
    data = r.json()
    assert data["tier"] == "Carrier License"
    assert data["price_per_verification"] == 0.08

def test_demo_endpoint():
    r = client.get("/demo")
    assert r.status_code == 200
    data = r.json()
    assert data["legitimate"]["verdict"] == "STRICT"
    assert data["fraudulent"]["verdict"] == "QUARANTINE"
    assert data["legitimate"]["score"] == 0.9175
    assert data["fraudulent"]["score"] == 0.3675

# ─── Pricing Engine ──────────────────────────────────────────────────

def test_pricing_calculator_pilot():
    calc = PricingCalculator("pilot")
    result = calc.calculate_cost(500)
    assert result["cost"] == 0.0
    assert result["tier"] == "Pilot Program"

def test_pricing_calculator_starter():
    calc = PricingCalculator("starter")
    result = calc.calculate_cost(1000)
    assert result["cost"] == 100.0
    assert result["price_per"] == 0.10

def test_pricing_calculator_exceeds_limit():
    calc = PricingCalculator("pilot")
    calc.verifications_this_month = 900
    result = calc.calculate_cost(200)
    assert "error" in result

def test_roi_projection():
    calc = PricingCalculator("carrier")
    roi = calc.roi_projection(fraud_caught_percentage=0.05, avg_fraud_claim_value=15000)
    assert roi["fraud_caught"] == 2500
    assert roi["money_saved"] == 37_500_000
    assert roi["monthly_cost"] == 4000

def test_tier_suggestion():
    calc = PricingCalculator()
    assert calc.suggest_tier(500) == "pilot"
    assert calc.suggest_tier(3000) == "starter"
    assert calc.suggest_tier(30000) == "carrier"
    assert calc.suggest_tier(100000) == "enterprise"

def test_pricing_summary_readable():
    summary = get_pricing_summary()
    assert "PILOT" in summary
    assert "ROI" in summary
    assert "$0.08" in summary

# ─── Report Generator ────────────────────────────────────────────────

def test_report_html_generation():
    fap_result = {
        "artifact_id": "test_123",
        "verdict": "STRICT",
        "total_score": 0.9175,
        "confidence": 0.01,
        "components": {"solar": 1.0, "signature": 0.95, "hardware": 1.0, "weather": 0.85, "witness": 1.0, "gps": 0.5},
        "provenance_hash": "abc123",
        "audit_trail": []
    }
    req_data = {
        "lat": 29.53, "lon": -98.46,
        "timestamp_claimed": "2026-07-28T18:00:00+00:00",
        "device_manufacturer": "Apple", "device_model": "iPhone15,2",
        "witness_ids": ["w1", "w2"]
    }
    report = AdjusterReport(
        claim_id="CLM-001", policy_number="POL-123",
        adjuster_notes="Test note", fap_result=fap_result, request_data=req_data
    )
    html = report.to_html()
    assert "FAP Verification Report" in html
    assert "0.9175" in html
    assert "STRICT" in html
    assert "Test note" in html
    assert "APPROVE" in html

def test_report_markdown_generation():
    fap_result = {
        "artifact_id": "test_456",
        "verdict": "QUARANTINE",
        "total_score": 0.3675,
        "confidence": 0.4,
        "components": {"solar": 0.0, "signature": 0.95, "hardware": 0.0, "weather": 0.85, "witness": 0.0, "gps": 0.0},
        "provenance_hash": "def456",
        "audit_trail": []
    }
    report = AdjusterReport(
        claim_id="CLM-002", policy_number="POL-456",
        adjuster_notes="", fap_result=fap_result, request_data={"witness_ids": []}
    )
    md = report.to_markdown()
    assert "QUARANTINE" in md
    assert "0.3675" in md
    assert "DENY / ESCALATE" in md

# ─── Config ──────────────────────────────────────────────────────────

def test_config_thresholds():
    from fap_insurance.config import config
    assert config.STRICT_LABEL == "VERIFIED — Proceed with claim"
    assert config.QUARANTINE_LABEL == "FRAUD RISK — Deny / escalate to SIU"

def test_pricing_tiers_complete():
    from fap_insurance.config import config
    assert "pilot" in config.TIERS
    assert "starter" in config.TIERS
    assert "carrier" in config.TIERS
    assert "enterprise" in config.TIERS
    assert config.TIERS["pilot"].price_per_verification == 0.0

"""FAP-Insurance Adjuster Report Generator"""
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from jinja2 import Template
import json

class AdjusterReport:
    def __init__(self, claim_id: str, policy_number: Optional[str], 
                 adjuster_notes: Optional[str], fap_result: dict, request_data: dict):
        self.claim_id = claim_id
        self.policy_number = policy_number or "N/A"
        self.adjuster_notes = adjuster_notes or ""
        self.fap = fap_result
        self.req = request_data
        self.generated_at = datetime.now(timezone.utc)

    def _verdict_badge(self, verdict: str) -> str:
        colors = {
            "STRICT": "#22c55e",
            "PROBABLE": "#3b82f6", 
            "SUSPICIOUS": "#f59e0b",
            "QUARANTINE": "#ef4444"
        }
        return colors.get(verdict, "#6b7280")

    def _score_bar(self, score: float) -> str:
        pct = int(score * 100)
        color = "#22c55e" if score >= 0.9 else "#3b82f6" if score >= 0.7 else "#f59e0b" if score >= 0.4 else "#ef4444"
        return f"""
        <div style="width:100%;background:#e5e7eb;height:24px;border-radius:12px;overflow:hidden;">
            <div style="width:{pct}%;background:{color};height:100%;transition:width 0.5s;"></div>
        </div>
        <div style="text-align:center;font-weight:bold;margin-top:4px;">{pct}%</div>
        """

    def _component_table(self, components: dict) -> str:
        rows = []
        labels = {
            "solar": "Solar Anchor (NOAA GOES X-ray)",
            "signature": "Media Signature",
            "hardware": "Device Enrollment",
            "weather": "Weather Oracle",
            "witness": "Witness Consensus",
            "gps": "GPS Plausibility"
        }
        for key, label in labels.items():
            val = components.get(key, 0.0)
            icon = "✓" if val >= 0.7 else "~" if val >= 0.4 else "✗"
            color = "#22c55e" if val >= 0.7 else "#f59e0b" if val >= 0.4 else "#ef4444"
            rows.append(f"""
            <tr>
                <td style="padding:8px;border-bottom:1px solid #e5e7eb;">{label}</td>
                <td style="padding:8px;border-bottom:1px solid #e5e7eb;text-align:center;color:{color};font-weight:bold;">{icon} {val:.2f}</td>
            </tr>
            """)
        return "<table style="width:100%;border-collapse:collapse;">" + "".join(rows) + "</table>"

    def to_html(self) -> str:
        verdict = self.fap.get("verdict", "UNKNOWN")
        score = self.fap.get("total_score", 0.0)
        components = self.fap.get("components", {})
        artifact_id = self.fap.get("artifact_id", "N/A")
        confidence = self.fap.get("confidence", 0.0)

        return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>FAP Verification Report — Claim {self.claim_id}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 800px; margin: 40px auto; padding: 20px; color: #1f2937; }}
        .header {{ border-bottom: 3px solid #111827; padding-bottom: 20px; margin-bottom: 30px; }}
        .badge {{ display: inline-block; padding: 8px 16px; border-radius: 20px; color: white; font-weight: bold; font-size: 14px; }}
        .score-box {{ background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 12px; padding: 24px; margin: 20px 0; }}
        .section {{ margin: 30px 0; }}
        .section h2 {{ color: #111827; border-left: 4px solid #3b82f6; padding-left: 12px; }}
        .footer {{ margin-top: 40px; padding-top: 20px; border-top: 1px solid #e5e7eb; font-size: 12px; color: #6b7280; }}
        .recommendation {{ background: #eff6ff; border-left: 4px solid #3b82f6; padding: 16px; margin: 20px 0; border-radius: 0 8px 8px 0; }}
        .recommendation.deny {{ background: #fef2f2; border-left-color: #ef4444; }}
        .recommendation.warn {{ background: #fffbeb; border-left-color: #f59e0b; }}
        .recommendation.approve {{ background: #f0fdf4; border-left-color: #22c55e; }}
        table {{ font-size: 14px; }}
        .meta-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }}
        .meta-item {{ background: #f3f4f6; padding: 12px; border-radius: 8px; }}
        .meta-label {{ font-size: 11px; text-transform: uppercase; color: #6b7280; letter-spacing: 0.05em; }}
        .meta-value {{ font-size: 14px; font-weight: 600; margin-top: 4px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1 style="margin:0;font-size:28px;">📋 FAP Verification Report</h1>
        <p style="margin:8px 0 0 0;color:#6b7280;">Claim <strong>#{self.claim_id}</strong> &nbsp;|&nbsp; Policy <strong>{self.policy_number}</strong></p>
    </div>

    <div style="display:flex;align-items:center;gap:16px;margin:20px 0;">
        <span class="badge" style="background:{self._verdict_badge(verdict)};">{verdict}</span>
        <span style="color:#6b7280;font-size:14px;">Verification ID: <code>{artifact_id}</code></span>
    </div>

    <div class="score-box">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">
            <span style="font-size:18px;font-weight:600;">Provenance Score</span>
            <span style="font-size:24px;font-weight:800;">{score:.4f}</span>
        </div>
        {self._score_bar(score)}
        <div style="margin-top:12px;font-size:13px;color:#6b7280;">
            Confidence: {confidence:.4f} &nbsp;|&nbsp; 
            Witnesses: {len(self.req.get('witness_ids', []))} &nbsp;|&nbsp;
            Device Enrolled: {"Yes" if components.get('hardware', 0) > 0.5 else "No"}
        </div>
    </div>

    <div class="section">
        <h2>Component Breakdown</h2>
        {self._component_table(components)}
    </div>

    <div class="section">
        <h2>Claim Metadata</h2>
        <div class="meta-grid">
            <div class="meta-item">
                <div class="meta-label">Claimed Location</div>
                <div class="meta-value">{self.req.get('lat')}, {self.req.get('lon')}</div>
            </div>
            <div class="meta-item">
                <div class="meta-label">Claimed Timestamp</div>
                <div class="meta-value">{self.req.get('timestamp_claimed', 'N/A')}</div>
            </div>
            <div class="meta-item">
                <div class="meta-label">Device</div>
                <div class="meta-value">{self.req.get('device_manufacturer', 'N/A')} {self.req.get('device_model', 'N/A')}</div>
            </div>
            <div class="meta-item">
                <div class="meta-label">OS Version</div>
                <div class="meta-value">{self.req.get('device_os', 'N/A')}</div>
            </div>
        </div>
    </div>

    <div class="section">
        <h2>Adjuster Recommendation</h2>
        <div class="recommendation {"approve" if verdict == "STRICT" else "warn" if verdict in ["PROBABLE", "SUSPICIOUS"] else "deny"}">
            <strong>{"APPROVE" if verdict == "STRICT" else "REVIEW" if verdict in ["PROBABLE", "SUSPICIOUS"] else "DENY / ESCALATE"}</strong><br>
            {"Photo provenance verified against live NOAA solar data. All oracles confirm authenticity. Proceed with standard processing." if verdict == "STRICT" else 
             "Multiple verification signals are weak or missing. Require claimant interview and secondary documentation." if verdict == "SUSPICIOUS" else
             "High probability of fabricated timestamp or unknown device. Escalate to Special Investigations Unit."}
        </div>
    </div>

    {f'<div class="section"><h2>Adjuster Notes</h2><p style="background:#f9fafb;padding:12px;border-radius:8px;">{self.adjuster_notes}</p></div>' if self.adjuster_notes else ''}

    <div class="footer">
        <p><strong>FAP-Core Insurance Verification</strong> v0.1.0</p>
        <p>Report generated at {self.generated_at.isoformat()} UTC</p>
        <p>This report is based on publicly available NOAA GOES X-ray data, Open-Meteo weather records, and cryptographic media signatures. It does not constitute legal proof of fraud or innocence.</p>
        <p style="margin-top:8px;">🔗 Verification hash: <code>{artifact_id}</code> | 🔗 Provenance hash: <code>{self.fap.get('provenance_hash', 'N/A')}</code></p>
    </div>
</body>
</html>"""

    def to_markdown(self) -> str:
        verdict = self.fap.get("verdict", "UNKNOWN")
        score = self.fap.get("total_score", 0.0)
        components = self.fap.get("components", {})

        lines = [
            f"# FAP Verification Report — Claim #{self.claim_id}",
            "",
            f"**Policy:** {self.policy_number}  ",
            f"**Verdict:** {verdict}  ",
            f"**Score:** {score:.4f}  ",
            f"**Generated:** {self.generated_at.isoformat()} UTC",
            "",
            "## Component Scores",
            "",
            "| Component | Score | Status |",
            "|-----------|-------|--------|",
        ]
        for k, v in components.items():
            status = "PASS" if v >= 0.7 else "WARN" if v >= 0.4 else "FAIL"
            lines.append(f"| {k} | {v:.2f} | {status} |")

        lines.extend([
            "",
            "## Recommendation",
            "",
            self._recommendation_text(verdict),
            "",
            "---",
            "*Generated by FAP-Core v0.2.0 | Solar-verified provenance*"
        ])
        return "\n".join(lines)

    def _recommendation_text(self, verdict: str) -> str:
        if verdict == "STRICT":
            return "**APPROVE** — Photo provenance verified. Proceed with standard claim processing."
        elif verdict == "PROBABLE":
            return "**REVIEW** — Photo likely authentic. Recommend standard review with spot-check."
        elif verdict == "SUSPICIOUS":
            return "**HOLD** — Multiple anomalies. Require claimant interview and secondary documentation."
        else:
            return "**DENY / ESCALATE** — High fraud probability. Escalate to SIU."

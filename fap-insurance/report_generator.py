"""FAP-Insurance Adjuster Report Generator."""
from datetime import datetime, timezone
from typing import Optional
from html import escape

class AdjusterReport:
    def __init__(self, claim_id: str, policy_number: Optional[str], adjuster_notes: Optional[str], fap_result: dict, request_data: dict):
        self.claim_id = claim_id
        self.policy_number = policy_number or "N/A"
        self.adjuster_notes = adjuster_notes or ""
        self.fap = fap_result
        self.req = request_data
        self.generated_at = datetime.now(timezone.utc)

    def _verdict_badge(self, verdict: str) -> str:
        return {"STRICT": "#22c55e", "PROBABLE": "#3b82f6", "SUSPICIOUS": "#f59e0b", "QUARANTINE": "#ef4444"}.get(verdict, "#6b7280")

    def _score_bar(self, score: float) -> str:
        pct = int(score * 100)
        color = "#22c55e" if score >= 0.9 else "#3b82f6" if score >= 0.7 else "#f59e0b" if score >= 0.4 else "#ef4444"
        return f'<div style="width:100%;background:#e5e7eb;height:24px;border-radius:12px;overflow:hidden;"><div style="width:{pct}%;background:{color};height:100%;"></div></div><div>{pct}%</div>'

    def _component_table(self, components: dict) -> str:
        labels = {"solar": "Solar Anchor (NOAA GOES X-ray)", "signature": "Media Signature", "hardware": "Device Enrollment", "weather": "Weather Oracle", "witness": "Witness Consensus", "gps": "GPS Plausibility"}
        rows = []
        for key, label in labels.items():
            val = components.get(key, 0.0)
            icon = "✓" if val >= 0.7 else "~" if val >= 0.4 else "✗"
            rows.append(f'<tr><td>{label}</td><td>{icon} {val:.2f}</td></tr>')
        return '<table><tbody>' + ''.join(rows) + '</tbody></table>'

    def to_html(self) -> str:
        verdict = self.fap.get("verdict", "UNKNOWN")
        score = self.fap.get("total_score", 0.0)
        components = self.fap.get("components", {})
        artifact_id = self.fap.get("artifact_id", "N/A")
        confidence = self.fap.get("confidence", 0.0)
        action = "APPROVE" if verdict == "STRICT" else "REVIEW" if verdict in ["PROBABLE", "SUSPICIOUS"] else "DENY / ESCALATE"
        recommendation = "Photo provenance verified against live NOAA solar data. All oracles confirm authenticity. Proceed with standard processing." if verdict == "STRICT" else "Multiple verification signals are weak or missing. Require claimant interview and secondary documentation." if verdict == "SUSPICIOUS" else "High probability of fabricated timestamp or unknown device. Escalate to Special Investigations Unit."
        notes = f'<div><h2>Adjuster Notes</h2><p>{escape(self.adjuster_notes)}</p></div>' if self.adjuster_notes else ''
        return f'''<!DOCTYPE html><html><head><meta charset="UTF-8"><title>FAP Verification Report — Claim {escape(self.claim_id)}</title></head><body>
<h1>📋 FAP Verification Report</h1><p>Claim <strong>#{escape(self.claim_id)}</strong> | Policy <strong>{escape(self.policy_number)}</strong></p>
<p><strong style="background:{self._verdict_badge(verdict)};color:white;padding:8px;">{escape(verdict)}</strong> Verification ID: <code>{escape(str(artifact_id))}</code></p>
<h2>Provenance Score</h2><strong>{score:.4f}</strong>{self._score_bar(score)}<p>Confidence: {confidence:.4f} | Witnesses: {len(self.req.get('witness_ids', []))} | Device Enrolled: {"Yes" if components.get("hardware", 0) > 0.5 else "No"}</p>
<h2>Component Breakdown</h2>{self._component_table(components)}
<h2>Claim Metadata</h2><p>Claimed Location: {self.req.get("lat")}, {self.req.get("lon")}</p><p>Claimed Timestamp: {self.req.get("timestamp_claimed", "N/A")}</p><p>Device: {self.req.get("device_manufacturer", "N/A")} {self.req.get("device_model", "N/A")}</p>
<h2>Adjuster Recommendation</h2><p><strong>{action}</strong><br>{recommendation}</p>{notes}
<footer><p><strong>FAP-Core Insurance Verification</strong> v0.1.0</p><p>Report generated at {self.generated_at.isoformat()} UTC</p><p>This report is based on publicly available NOAA GOES X-ray data, Open-Meteo weather records, and cryptographic media signatures. It does not constitute legal proof of fraud or innocence.</p><p>🔗 Verification hash: <code>{escape(str(artifact_id))}</code> | 🔗 Provenance hash: <code>{escape(str(self.fap.get("provenance_hash", "N/A")))}</code></p></footer></body></html>'''

    def to_markdown(self) -> str:
        verdict = self.fap.get("verdict", "UNKNOWN")
        score = self.fap.get("total_score", 0.0)
        components = self.fap.get("components", {})
        lines = [f"# FAP Verification Report — Claim #{self.claim_id}", "", f"**Policy:** {self.policy_number}  ", f"**Verdict:** {verdict}  ", f"**Score:** {score:.4f}  ", f"**Generated:** {self.generated_at.isoformat()} UTC", "", "## Component Scores", "", "| Component | Score | Status |", "|-----------|-------|--------|"]
        for key, value in components.items():
            status = "PASS" if value >= 0.7 else "WARN" if value >= 0.4 else "FAIL"
            lines.append(f"| {key} | {value:.2f} | {status} |")
        lines.extend(["", "## Recommendation", "", self._recommendation_text(verdict), "", "---", "*Generated by FAP-Core v0.2.0 | Solar-verified provenance*"])
        return "\n".join(lines)

    def _recommendation_text(self, verdict: str) -> str:
        if verdict == "STRICT":
            return "**APPROVE** — Photo provenance verified. Proceed with standard claim processing."
        if verdict == "PROBABLE":
            return "**REVIEW** — Photo likely authentic. Recommend standard review with spot-check."
        if verdict == "SUSPICIOUS":
            return "**HOLD** — Multiple anomalies. Require claimant interview and secondary documentation."
        return "**DENY / ESCALATE** — High fraud probability. Escalate to SIU."

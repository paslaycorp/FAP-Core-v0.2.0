"""FAP-Insurance Pricing Engine"""
from typing import Dict, Optional
from dataclasses import asdict
from .config import config, PricingTier

class PricingCalculator:
    def __init__(self, tier_key: str = "pilot"):
        self.tier = config.TIERS.get(tier_key, config.TIERS["pilot"])
        self.verifications_this_month = 0

    def calculate_cost(self, count: int) -> Dict:
        """Calculate cost for N verifications at current tier."""
        remaining = self.tier.max_verifications_per_month - self.verifications_this_month
        if count > remaining:
            return {
                "error": f"Exceeds monthly limit. Remaining: {remaining}",
                "requested": count,
                "remaining": remaining
            }

        cost = count * self.tier.price_per_verification
        if self.tier.monthly_cap > 0:
            cost = min(cost, self.tier.monthly_cap)

        return {
            "tier": self.tier.name,
            "verifications": count,
            "cost": round(cost, 2),
            "price_per": self.tier.price_per_verification,
            "monthly_cap": self.tier.monthly_cap,
            "remaining_after": remaining - count
        }

    def suggest_tier(self, monthly_volume: int) -> str:
        """Suggest best tier based on expected monthly volume."""
        if monthly_volume <= 1000:
            return "pilot"
        elif monthly_volume <= 5000:
            return "starter"
        elif monthly_volume <= 50000:
            return "carrier"
        else:
            return "enterprise"

    def roi_projection(self, fraud_caught_percentage: float = 0.05, 
                       avg_fraud_claim_value: float = 15000.0) -> Dict:
        """Project ROI based on fraud detection rate."""
        # Conservative: 5% of claims have photo fraud
        # Average fraudulent claim value: $15,000
        monthly_volume = self.tier.max_verifications_per_month
        fraud_caught = int(monthly_volume * fraud_caught_percentage)
        money_saved = fraud_caught * avg_fraud_claim_value
        monthly_cost = self.tier.monthly_cap if self.tier.monthly_cap > 0 else 0

        return {
            "monthly_volume": monthly_volume,
            "fraud_caught": fraud_caught,
            "money_saved": money_saved,
            "monthly_cost": monthly_cost,
            "net_benefit": money_saved - monthly_cost,
            "roi_multiplier": round(money_saved / max(monthly_cost, 1), 2),
            "assumptions": {
                "fraud_rate": fraud_caught_percentage,
                "avg_fraud_value": avg_fraud_claim_value
            }
        }

    def compare_tiers(self) -> Dict:
        """Side-by-side tier comparison for sales conversations."""
        return {
            key: {
                "name": tier.name,
                "max_monthly": tier.max_verifications_per_month,
                "price_per": tier.price_per_verification,
                "monthly_cap": tier.monthly_cap,
                "effective_price_at_cap": round(tier.monthly_cap / tier.max_verifications_per_month, 4) 
                    if tier.monthly_cap > 0 and tier.max_verifications_per_month > 0 else tier.price_per_verification,
                "features": tier.features
            }
            for key, tier in config.TIERS.items()
        }

def get_pricing_summary() -> str:
    """Human-readable pricing summary for outreach."""
    lines = [
        "FAP-INSURANCE PRICING",
        "=" * 50,
        "",
        "🚀 PILOT PROGRAM (Free)",
        "   • 1,000 verifications/month at $0.00",
        "   • No contract. No credit card. Cancel anytime.",
        "   • Perfect for: Independent adjusters testing the water",
        "",
        "💼 STARTER ($0.10/verification, $500 cap)",
        "   • Up to 5,000 verifications/month",
        "   • Effective rate drops to $0.10 at scale",
        "   • Perfect for: Small-to-mid carriers, CAT teams",
        "",
        "🏢 CARRIER ($0.08/verification, $4,000 cap)",
        "   • Up to 50,000 verifications/month",
        "   • SIU webhook integration",
        "   • Perfect for: Regional carriers, TPA firms",
        "",
        "🏭 ENTERPRISE (Custom)",
        "   • Unlimited volume",
        "   • On-premise deployment option",
        "   • Perfect for: National carriers, government",
        "",
        "ROI EXAMPLE (Carrier tier, 5% fraud rate):",
        "   • 50,000 verifications × 5% fraud = 2,500 fraud cases caught",
        "   • 2,500 × $15,000 avg claim = $37,500,000 saved",
        "   • Monthly cost: $4,000",
        "   • Net benefit: $37,496,000",
        "   • ROI: 9,374x",
        "",
        "Every verification takes <3 seconds.",
        "Every fraud case caught pays for 3,750 verifications."
    ]
    return "\n".join(lines)

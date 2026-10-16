"""Rule engine for claims validation — mirrors the 5 SQL rules in claims_rules_synced."""
import json


def _parse_damage_prediction(dp):
    """Parse damage_prediction from JSONB string or dict."""
    if isinstance(dp, str):
        try:
            return json.loads(dp)
        except (json.JSONDecodeError, TypeError):
            return {}
    return dp if isinstance(dp, dict) else {}


def evaluate_rules(claim):
    """Evaluate all 4 checks + fund-release decision for a single claim.

    Parameters
    ----------
    claim : dict
        Row from claims_synced (or form submission data) with at least:
        severity, damage_prediction, sum_insured, total,
        pol_eff_date, pol_expiry_date, claim_date, telematics_speed.

    Returns
    -------
    dict  {"checks": {...}, "risk_assessment": str, "recommendation": str}
    """
    checks = {}

    # ── Rule 3: Severity Check (ML prediction vs reported severity) ──────
    severity = claim.get("severity", "")
    dp = _parse_damage_prediction(claim.get("damage_prediction", {}))
    label = dp.get("label", "")
    score = dp.get("score", 0)

    severity_map = {
        "Total Loss": "major",
        "Major Damage": "minor",
        "Minor Damage": "minor",
        "Trivial Damage": "minor",
    }
    expected = severity_map.get(severity, "")
    sev_match = label == expected
    checks["reported_severity_check"] = {
        "check_name": "Severity Check",
        "passed": sev_match,
        "result": "MATCH" if sev_match else "MISMATCH",
        "detail": f"Severity: {severity}",
        "ml_label": label,
        "ml_score": float(score) if score else 0.0,
    }

    # ── Rule 2: Policy Amount Check ──────────────────────────────────────
    sum_insured = float(claim.get("sum_insured") or 0)
    total = float(claim.get("total") or 0)
    amount_ok = sum_insured >= total
    checks["valid_amount"] = {
        "check_name": "Policy Amount",
        "passed": amount_ok,
        "result": "WITHIN LIMIT" if amount_ok else "OVER LIMIT",
        "detail": f"Claim: ${total:,.0f} | Limit: ${sum_insured:,.0f}",
    }

    # ── Rule 1: Policy Date Check ────────────────────────────────────────
    pol_eff = str(claim.get("pol_eff_date", ""))
    pol_exp = str(claim.get("pol_expiry_date", ""))
    c_date = str(claim.get("claim_date", ""))
    if pol_eff and pol_exp and c_date:
        is_active = pol_eff <= c_date <= pol_exp
        checks["valid_date"] = {
            "check_name": "Policy Date",
            "passed": is_active,
            "result": "ACTIVE" if is_active else "EXPIRED",
            "detail": f"Incident: {c_date} | Expires: {pol_exp}",
        }
    else:
        checks["valid_date"] = {
            "check_name": "Policy Date",
            "passed": False,
            "result": "MISSING DATA",
            "detail": "Policy dates not available",
        }

    # ── Rule 4: Speed Check ──────────────────────────────────────────────
    speed = claim.get("telematics_speed")
    if speed is not None and float(speed) > 0:
        speed_val = float(speed)
        speed_ok = speed_val <= 45
        checks["speed_check"] = {
            "check_name": "Speed Check",
            "passed": speed_ok,
            "result": f"{speed_val:.0f} mph",
            "detail": "Fine - Within speed limit" if speed_ok else "High Speed",
        }
    else:
        checks["speed_check"] = {
            "check_name": "Speed Check",
            "passed": True,
            "result": "N/A",
            "detail": "No speed data available",
        }

    # ── Rule 5: Fund Release (aggregate decision) ────────────────────────
    all_passed = all(v["passed"] for v in checks.values())
    checks["fund_release"] = {
        "check_name": "Fund Release",
        "passed": all_passed,
        "result": "Release Funds" if all_passed else "Needs Investigation",
        "detail": "All checks passed" if all_passed else "One or more checks failed",
    }

    # ── Risk assessment & recommendation ─────────────────────────────────
    failed = sum(
        1 for k, v in checks.items() if k != "fund_release" and not v["passed"]
    )
    if failed == 0:
        risk, rec = "low", "approve"
    elif failed == 1:
        risk, rec = "medium", "review"
    else:
        risk, rec = "high", "deny"

    return {"checks": checks, "risk_assessment": risk, "recommendation": rec}

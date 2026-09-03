import pandas as pd
import numpy as np
from typing import Dict, List, Any

def evaluate_forecast_confidence(df_company: pd.DataFrame) -> Dict[str, Any]:
    """
    Evaluates historical data depth, volatility, structural shifts, and cash burn
    to assign confidence scores, resolution status, exception type, financial drivers,
    and grounded controller action recommendations.
    """
    c_df = df_company.sort_values("period_idx").reset_index(drop=True)
    c_id = c_df["company_id"].iloc[0]
    c_name = c_df["company_name"].iloc[0]
    category = c_df["category"].iloc[0]

    num_periods = len(c_df)
    latest = c_df.iloc[-1]
    reasons = []
    drivers = []
    confidence_score = 1.0
    exception_type = "NONE"

    # Analyze operational drivers
    rev = latest["revenue"]
    cogs = latest["cost_of_goods_sold"]
    opex = latest["operating_expenses"]
    net_inc = latest["net_income"]
    cash = latest["cash"]
    ocf = latest["operating_cash_flow"]
    ar = latest["accounts_receivable"]
    ap = latest["accounts_payable"]
    st_debt = latest["short_term_debt"]
    lt_debt = latest["long_term_debt"]
    capex = latest["capital_expenditure"]

    # 1. Driver Extraction
    if ocf < 0:
        drivers.append(f"Negative Operating Cash Flow ({ocf:.2f} Cr) driven by operating expenses of {opex:.2f} Cr.")
    else:
        drivers.append(f"Positive Operating Cash Flow ({ocf:.2f} Cr) supporting cash balance.")

    if ar > (rev * 0.25):
        drivers.append(f"Elevated Accounts Receivable ({ar:.2f} Cr) absorbing liquidity in working capital.")

    if capex > (cash * 0.15):
        drivers.append(f"Substantial Capital Expenditure ({capex:.2f} Cr) requiring cash outlay.")

    if (st_debt + lt_debt) > 50.0:
        drivers.append(f"Heavy Debt Service Burden (Total Debt: {(st_debt + lt_debt):.2f} Cr).")

    # 2. Confidence & Exception Triggers
    # Condition A: Insufficient Historical Data
    if num_periods < 6:
        confidence_score -= 0.55
        exception_type = "INSUFFICIENT_HISTORY"
        reasons.append(f"Insufficient historical observations ({num_periods} periods available; minimum 6 required).")

    # Condition B: High Volatility
    if num_periods >= 4:
        ocf_vals = c_df["operating_cash_flow"].values
        std_ocf = np.std(ocf_vals)
        mean_ocf = np.abs(np.mean(ocf_vals)) + 1e-3
        cv = std_ocf / mean_ocf
        if cv > 0.65:
            confidence_score -= 0.35
            if exception_type == "NONE":
                exception_type = "HIGH_VOLATILITY"
            reasons.append(f"High cash flow volatility (Coefficient of Variation = {cv:.2f} > 0.65 threshold).")

    # Condition C: Structural Break / Sudden Shock
    if num_periods >= 4:
        rev_vals = c_df["revenue"].values
        recent_rev = rev_vals[-1]
        prior_mean_rev = np.mean(rev_vals[:-1])
        shift_ratio = abs(recent_rev - prior_mean_rev) / (prior_mean_rev + 1e-3)
        if shift_ratio > 0.50:
            confidence_score -= 0.40
            if exception_type == "NONE":
                exception_type = "STRUCTURAL_BREAK"
            reasons.append(f"Sudden structural revenue shift of {shift_ratio*100:.1f}% detected in latest period.")

    # Condition D: Cash Burn & Insolvency Risk
    if ocf < 0 and cash > 0:
        burn_rate = abs(ocf)
        runway_quarters = cash / (burn_rate + 1e-3)
        if runway_quarters < 2.0:
            confidence_score -= 0.45
            if exception_type == "NONE":
                exception_type = "SEVERE_CASH_BURN"
            reasons.append(f"Critical cash burn risk: Cash runway is only {runway_quarters:.1f} quarters ({cash:.1f} Cr remaining).")
    elif cash <= 0:
        confidence_score -= 0.60
        if exception_type == "NONE":
            exception_type = "INSOLVENCY_WARNING"
        reasons.append("Insolvency warning: Current cash balance is exhausted or negative.")

    # Clamp confidence score
    confidence_score = max(0.0, min(1.0, confidence_score))

    # 3. Assign Resolution Status & Confidence Classification
    if confidence_score >= 0.80:
        status = "HIGH"
        resolution_status = "RESOLVED"
        controller_action = "Automated cash forecast accepted. Standard working capital monitoring."
    elif confidence_score >= 0.50:
        status = "MEDIUM"
        resolution_status = "RESOLVED"
        controller_action = "Forecast accepted with caution. Monitor upcoming quarter receivables collection and vendor payables."
    else:
        status = "LOW"
        if exception_type == "INSUFFICIENT_HISTORY":
            resolution_status = "INSUFFICIENT_DATA"
        else:
            resolution_status = "NEEDS_HUMAN_REVIEW"

        # Grounded Controller Action
        if exception_type == "SEVERE_CASH_BURN":
            controller_action = "URGENT ACTION: Audit cash burn rate, freeze non-essential CapEx, and initiate short-term credit line review."
        elif exception_type == "HIGH_VOLATILITY":
            controller_action = "HUMAN REVIEW: Perform detailed cash flow variance audit on recent operational transactions."
        elif exception_type == "STRUCTURAL_BREAK":
            controller_action = "HUMAN REVIEW: Verify customer contract continuity following major structural revenue shift."
        else:
            controller_action = "HUMAN REVIEW: Conduct manual financial assessment before relying on automated cash projection."

    if not reasons:
        reasons.append("Stable historical cash flow trajectory and robust balance sheet liquidity.")

    return {
        "company_id": c_id,
        "company_name": c_name,
        "category": category,
        "latest_period": latest["period"],
        "historical_periods": num_periods,
        "target": "90-Day Cash Position",
        "confidence_status": status,
        "confidence_score": round(confidence_score, 2),
        "resolution_status": resolution_status,
        "is_resolved": resolution_status == "RESOLVED",
        "exception_type": exception_type,
        "reasons": reasons,
        "financial_drivers": drivers,
        "controller_action": controller_action
    }

def generate_portfolio_exception_report(df: pd.DataFrame) -> Dict[str, Any]:
    companies = df["company_id"].unique()
    reports = []
    exceptions = []
    resolved_count = 0
    needs_review_count = 0

    for c_id in companies:
        c_df = df[df["company_id"] == c_id]
        conf = evaluate_forecast_confidence(c_df)
        reports.append(conf)
        if conf["is_resolved"]:
            resolved_count += 1
        else:
            needs_review_count += 1
            exceptions.append(conf)

    total_co = len(companies)
    resolution_rate_pct = round((resolved_count / total_co) * 100.0, 2) if total_co > 0 else 0.0
    exception_rate_pct = round((needs_review_count / total_co) * 100.0, 2) if total_co > 0 else 0.0

    return {
        "total_companies": total_co,
        "total_forecasts_generated": total_co,
        "resolved_forecasts": resolved_count,
        "human_review_exceptions": needs_review_count,
        "resolution_rate_pct": resolution_rate_pct,
        "exception_rate_pct": exception_rate_pct,
        "exception_list": exceptions,
        "all_confidence_reports": reports
    }

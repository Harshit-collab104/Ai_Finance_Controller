from typing import Any
import numpy as np
import pandas as pd
from backend.forecasting_engine import generate_company_forecasts

def run_what_if_scenario(
    df_company: pd.DataFrame,
    revenue_change_pct: float = -0.10,
    opex_change_pct: float = 0.0,
    capex_adjustment: float = 0.0,
) -> dict[str, Any]:
    """
    Simulates custom financial scenario adjustments on historical tail, recalculates
    net income, operating cash flow, and resulting cash balance trajectory over 3 quarters.
    """
    c_df = df_company.sort_values("period_idx").reset_index(drop=True)
    latest = c_df.iloc[-1].to_dict()

    # 1. Base Forecast (Unadjusted)
    base_forecast_res = generate_company_forecasts(c_df, target_col="cash", horizon=3)
    base_cash_preds = base_forecast_res["predictions"]

    cur_rev = float(latest["revenue"])
    cur_cogs = float(latest["cost_of_goods_sold"])
    cur_opex = float(latest["operating_expenses"])
    cur_cash = float(latest["cash"])
    cur_ocf = float(latest["operating_cash_flow"])

    # 2. Apply Scenario Parameter Adjustments
    adj_rev = cur_rev * (1.0 + revenue_change_pct)
    # COGS shifts proportionally with revenue
    adj_cogs = cur_cogs * (1.0 + revenue_change_pct * 0.8)
    adj_opex = cur_opex * (1.0 + opex_change_pct)
    adj_gross_profit = adj_rev - adj_cogs
    adj_net_income = adj_gross_profit - adj_opex - 5.0  # Estimated tax/interest

    # OCF shift estimate
    delta_net_income = adj_net_income - float(latest["net_income"])
    adj_ocf = cur_ocf + delta_net_income - capex_adjustment

    # Project 3-quarter scenario cash balance trajectory
    scen_cash_preds = []
    accumulated_cash = cur_cash
    for q_idx in range(3):
        # Quarter cash flow impact
        q_impact = (adj_ocf / 4.0) + (base_cash_preds[q_idx] - base_cash_preds[max(0, q_idx - 1)]) * 0.5
        accumulated_cash = max(0.0, accumulated_cash + q_impact)
        scen_cash_preds.append(round(float(accumulated_cash), 2))

    scenario_delta = round(float(scen_cash_preds[-1] - base_cash_preds[-1]), 2)
    is_cash_depleted = float(scen_cash_preds[-1]) < 10.0

    c_name = latest["company_name"] if latest["company_name"] and latest["company_name"] != "CO" else f"Company {latest['company_id']}"

    return {
        "company_id": latest["company_id"],
        "company_name": c_name,
        "parameters": {
            "revenue_change_pct": round(revenue_change_pct * 100, 1),
            "opex_change_pct": round(opex_change_pct * 100, 1),
            "capex_adjustment": capex_adjustment,
        },
        "baseline_latest": {
            "period": latest["period"],
            "revenue": round(cur_rev, 2),
            "net_income": round(float(latest["net_income"]), 2),
            "operating_cash_flow": round(cur_ocf, 2),
            "cash_balance": round(cur_cash, 2),
            "forecast_cash_90d": round(float(base_cash_preds[-1]), 2),
        },
        "scenario_latest": {
            "revenue": round(float(adj_rev), 2),
            "cost_of_goods_sold": round(float(adj_cogs), 2),
            "operating_expenses": round(float(adj_opex), 2),
            "net_income": round(float(adj_net_income), 2),
            "operating_cash_flow": round(float(adj_ocf), 2),
            "forecast_cash_90d": round(float(scen_cash_preds[-1]), 2),
        },
        "cash_trajectory": {
            "quarter_1": {
                "base": round(float(base_cash_preds[0]), 2),
                "scenario": round(float(scen_cash_preds[0]), 2),
            },
            "quarter_2": {
                "base": round(float(base_cash_preds[1]), 2),
                "scenario": round(float(scen_cash_preds[1]), 2),
            },
            "quarter_3": {
                "base": round(float(base_cash_preds[2]), 2),
                "scenario": round(float(scen_cash_preds[2]), 2),
            },
        },
        "summary": {
            "scenario_delta_impact": scenario_delta,
            "is_cash_depleted": is_cash_depleted,
            "scenario_status": (
                "CRITICAL_LIQUIDITY_WARNING"
                if is_cash_depleted
                else "STABLE_SCENARIO"
            ),
        },
    }

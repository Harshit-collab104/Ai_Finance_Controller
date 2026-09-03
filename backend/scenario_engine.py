import pandas as pd
import numpy as np
from typing import Dict, Any, List
from backend.forecasting_engine import generate_company_forecasts

def run_what_if_scenario(
    df_company: pd.DataFrame,
    revenue_change_pct: float = -0.10,
    opex_change_pct: float = 0.0,
    capex_adjustment: float = 0.0
) -> Dict[str, Any]:
    """
    Simulates custom financial scenario adjustments on historical tail, recalculates
    net income, operating cash flow, and resulting cash balance trajectory over 3 quarters.
    """
    c_df = df_company.sort_values("period_idx").reset_index(drop=True)
    latest = c_df.iloc[-1].to_dict()
    
    # 1. Base Forecast (Unadjusted)
    base_forecast_res = generate_company_forecasts(c_df, target_col="cash", horizon=3)
    base_cash_preds = base_forecast_res["predictions"]

    # 2. Adjusted Baseline Values
    base_rev = latest["revenue"]
    base_cogs = latest["cost_of_goods_sold"]
    base_opex = latest["operating_expenses"]
    base_capex = latest["capital_expenditure"]
    base_cash = latest["cash"]

    adj_rev = base_rev * (1.0 + revenue_change_pct)
    # COGS scales proportionally with revenue (variable cost component 80%)
    cogs_ratio = (base_cogs / (base_rev + 1e-3))
    adj_cogs = adj_rev * cogs_ratio
    
    adj_opex = base_opex * (1.0 + opex_change_pct)
    adj_capex = max(0.5, base_capex + capex_adjustment)

    adj_gross_profit = adj_rev - adj_cogs
    adj_operating_income = adj_gross_profit - adj_opex
    
    # Interest & Tax calculation
    st_debt = latest["short_term_debt"]
    lt_debt = latest["long_term_debt"]
    interest_expense = (st_debt * 0.08 + lt_debt * 0.06) / 4.0
    tax_expense = max(0.0, (adj_operating_income - interest_expense) * 0.25)
    adj_net_income = adj_operating_income - interest_expense - tax_expense

    # Working capital & OCF estimate
    depreciation = adj_opex * 0.12
    adj_ocf = adj_net_income + depreciation - 1.0  # WC drag estimate

    # Simulate 3-quarter cash progression under scenario
    scenario_cash_preds = []
    sim_cash = base_cash
    for q in range(3):
        # OCF + ICF + FCF
        net_cf = adj_ocf - adj_capex - 1.0
        sim_cash = max(0.1, sim_cash + net_cf)
        scenario_cash_preds.append(round(float(sim_cash), 2))

    expected_base_change = round(base_cash_preds[-1] - base_cash, 2)
    expected_scenario_change = round(scenario_cash_preds[-1] - base_cash, 2)
    delta_cash_impact = round(scenario_cash_preds[-1] - base_cash_preds[-1], 2)

    return {
        "company_id": latest["company_id"],
        "company_name": latest["company_name"],
        "parameters": {
            "revenue_change_pct": round(revenue_change_pct * 100, 1),
            "opex_change_pct": round(opex_change_pct * 100, 1),
            "capex_adjustment": round(capex_adjustment, 2)
        },
        "baseline_latest": {
            "revenue": base_rev,
            "net_income": latest["net_income"],
            "operating_cash_flow": latest["operating_cash_flow"],
            "cash_balance": base_cash,
            "forecast_cash_90d": base_cash_preds[-1]
        },
        "scenario_latest": {
            "revenue": round(adj_rev, 2),
            "net_income": round(adj_net_income, 2),
            "operating_cash_flow": round(adj_ocf, 2),
            "forecast_cash_90d": scenario_cash_preds[-1]
        },
        "cash_trajectory": {
            "quarter_1": {"base": base_cash_preds[0], "scenario": scenario_cash_preds[0]},
            "quarter_2": {"base": base_cash_preds[1], "scenario": scenario_cash_preds[1]},
            "quarter_3": {"base": base_cash_preds[2], "scenario": scenario_cash_preds[2]}
        },
        "summary": {
            "expected_base_change": expected_base_change,
            "expected_scenario_change": expected_scenario_change,
            "scenario_delta_impact": delta_cash_impact,
            "is_cash_depleted": scenario_cash_preds[-1] <= 2.0
        }
    }

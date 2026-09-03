from typing import Any

import numpy as np
import pandas as pd


def compute_financial_ratios(df: pd.DataFrame) -> pd.DataFrame:
    """
    Enriches raw financial statement records with calculated financial ratios.
    Calculates Liquidity, Profitability, Leverage, and Cash Flow metrics.
    """
    df = df.copy()

    # Sort by company and period
    df = df.sort_values(["company_id", "period_idx"]).reset_index(drop=True)

    # Derived accounting totals
    df["total_debt"] = df["short_term_debt"] + df["long_term_debt"]
    df["current_liabilities"] = df["accounts_payable"] + df["short_term_debt"]
    df["current_assets"] = df["cash"] + df["accounts_receivable"] + df["inventory"]
    df["gross_profit"] = df["revenue"] - df["cost_of_goods_sold"]
    df["operating_income"] = df["gross_profit"] - df["operating_expenses"]

    # Estimated assets and equity
    df["total_assets"] = df["current_assets"] + df["capital_expenditure"] * 3.0 + 10.0
    df["total_equity"] = np.maximum(
        5.0, df["total_assets"] - df["total_debt"] - df["accounts_payable"]
    )

    # Estimated interest expense and EBITDA
    df["interest_expense"] = np.maximum(
        0.5, (df["short_term_debt"] * 0.08 + df["long_term_debt"] * 0.06) / 4.0
    )
    df["ebitda"] = df["operating_income"] + (df["operating_expenses"] * 0.12)

    # 1. Liquidity Ratios
    df["current_ratio"] = np.where(
        df["current_liabilities"] > 0,
        df["current_assets"] / df["current_liabilities"],
        np.nan,
    )
    df["quick_ratio"] = np.where(
        df["current_liabilities"] > 0,
        (df["cash"] + df["accounts_receivable"]) / df["current_liabilities"],
        np.nan,
    )
    df["cash_ratio"] = np.where(
        df["current_liabilities"] > 0, df["cash"] / df["current_liabilities"], np.nan
    )

    # 2. Profitability Ratios
    df["gross_margin"] = np.where(
        df["revenue"] > 0, df["gross_profit"] / df["revenue"], np.nan
    )
    df["operating_margin"] = np.where(
        df["revenue"] > 0, df["operating_income"] / df["revenue"], np.nan
    )
    df["net_profit_margin"] = np.where(
        df["revenue"] > 0, df["net_income"] / df["revenue"], np.nan
    )
    df["roa"] = np.where(
        df["total_assets"] > 0, df["net_income"] / df["total_assets"], np.nan
    )
    df["roe"] = np.where(
        df["total_equity"] > 0, df["net_income"] / df["total_equity"], np.nan
    )

    # Growth Metrics (grouped by company)
    df["revenue_growth"] = df.groupby("company_id")["revenue"].pct_change().fillna(0.0)
    df["net_income_growth"] = (
        df.groupby("company_id")["net_income"].pct_change().fillna(0.0)
    )

    # 3. Leverage Ratios
    df["debt_to_equity"] = np.where(
        df["total_equity"] > 0, df["total_debt"] / df["total_equity"], np.nan
    )
    df["debt_to_ebitda"] = np.where(
        df["ebitda"] > 0, df["total_debt"] / df["ebitda"], np.nan
    )
    df["interest_coverage"] = np.where(
        df["interest_expense"] > 0,
        df["operating_income"] / df["interest_expense"],
        np.nan,
    )

    # 4. Cash Flow Ratios & Indicators
    df["free_cash_flow"] = df["operating_cash_flow"] - df["capital_expenditure"]
    df["cash_burn_rate"] = np.where(
        df["operating_cash_flow"] < 0, np.abs(df["operating_cash_flow"]), 0.0
    )

    df["ocf_prev"] = df.groupby("company_id")["operating_cash_flow"].shift(1)
    df["cash_flow_growth"] = np.where(
        df["ocf_prev"].notna() & (df["ocf_prev"] != 0),
        (df["operating_cash_flow"] - df["ocf_prev"]) / np.abs(df["ocf_prev"]),
        0.0,
    )
    df.drop(columns=["ocf_prev"], inplace=True)

    # 3-period OCF Trend slope
    def get_slope(series):
        if len(series) < 3 or series.isnull().any():
            return 0.0
        x = np.array([0, 1, 2])
        y = series.values
        return float(np.polyfit(x, y, 1)[0])

    df["ocf_trend_slope"] = (
        df.groupby("company_id")["operating_cash_flow"]
        .transform(lambda s: s.rolling(3).apply(get_slope, raw=False))
        .fillna(0.0)
    )

    # Round ratio columns for clean display
    ratio_cols = [
        "current_ratio",
        "quick_ratio",
        "cash_ratio",
        "gross_margin",
        "operating_margin",
        "net_profit_margin",
        "roa",
        "roe",
        "revenue_growth",
        "net_income_growth",
        "debt_to_equity",
        "debt_to_ebitda",
        "interest_coverage",
        "free_cash_flow",
        "cash_burn_rate",
        "cash_flow_growth",
        "ocf_trend_slope",
    ]
    for c in ratio_cols:
        df[c] = df[c].round(4)

    return df


def get_latest_company_ratios(df: pd.DataFrame, company_id: str) -> dict[str, Any]:
    c_df = df[df["company_id"] == company_id].sort_values("period_idx")
    if c_df.empty:
        return {}
    latest = c_df.iloc[-1].to_dict()
    return latest

import time
import numpy as np
import pandas as pd
from typing import Dict, List, Any
from backend.config import TRAIN_PERIODS, TOTAL_PERIODS
from backend.forecasting_engine import generate_company_forecasts, BaselineNaiveModel, MovingAverageModel

def compute_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    if len(y_true) == 0:
        return {"mae": 0.0, "rmse": 0.0, "mape": 0.0}
    
    mae = float(np.mean(np.abs(y_true - y_pred)))
    rmse = float(np.sqrt(np.mean((y_true - y_pred) ** 2)))
    
    # Avoid zero division in MAPE
    denom = np.maximum(0.1, np.abs(y_true))
    mape = float(np.mean(np.abs(y_true - y_pred) / denom) * 100.0)
    
    return {
        "mae": round(mae, 2),
        "rmse": round(rmse, 2),
        "mape": round(mape, 2)
    }

def run_out_of_time_evaluation(df: pd.DataFrame, target_col: str = "cash") -> Dict[str, Any]:
    """
    Evaluates forecasting accuracy using strict time-based out-of-time split.
    Training: Periods 1 to 20 (2019-Q1 to 2023-Q4)
    Held-out Test: Periods 21 to 24 (2024-Q1 to 2024-Q4)
    Also measures execution throughput and latency timing.
    """
    start_time = time.time()
    companies = df["company_id"].unique()
    
    y_true_all = []
    y_pred_ml_all = []
    y_pred_naive_all = []
    y_pred_ma_all = []
    
    category_results = {}
    company_evaluations = []

    for c_id in companies:
        c_df = df[df["company_id"] == c_id].sort_values("period_idx").reset_index(drop=True)
        category = c_df["category"].iloc[0]

        # Training set up to period 20
        train_df = c_df[c_df["period_idx"] <= TRAIN_PERIODS]
        test_df = c_df[c_df["period_idx"] > TRAIN_PERIODS]

        if test_df.empty or len(train_df) < 2:
            continue

        test_horizon = len(test_df)
        actuals = test_df[target_col].values

        # 1. Winning ML / Selected Model Forecast
        res_ml = generate_company_forecasts(train_df, target_col=target_col, horizon=test_horizon)
        preds_ml = np.array(res_ml["predictions"][:test_horizon])

        # 2. Naive Baseline
        naive_mod = BaselineNaiveModel().fit(None, train_df[target_col])
        preds_naive = naive_mod.predict(steps=test_horizon)

        # 3. Moving Average Baseline
        ma_mod = MovingAverageModel(window=3).fit(None, train_df[target_col])
        preds_ma = ma_mod.predict(steps=test_horizon)

        # Accumulate
        y_true_all.extend(actuals)
        y_pred_ml_all.extend(preds_ml)
        y_pred_naive_all.extend(preds_naive)
        y_pred_ma_all.extend(preds_ma)

        # Per company metrics
        c_metrics = compute_metrics(actuals, preds_ml)
        company_evaluations.append({
            "company_id": c_id,
            "company_name": c_df["company_name"].iloc[0],
            "category": category,
            "selected_model": res_ml["selected_model"],
            "mae": c_metrics["mae"],
            "rmse": c_metrics["rmse"],
            "mape": c_metrics["mape"],
            "actuals": [round(float(a), 2) for a in actuals],
            "predictions": [round(float(p), 2) for p in preds_ml]
        })

        if category not in category_results:
            category_results[category] = {"y_true": [], "y_pred": []}
        category_results[category]["y_true"].extend(actuals)
        category_results[category]["y_pred"].extend(preds_ml)

    elapsed_sec = time.time() - start_time
    avg_sec_per_company = elapsed_sec / max(1, len(companies))

    # Portfolio level metrics
    overall_ml = compute_metrics(np.array(y_true_all), np.array(y_pred_ml_all))
    overall_naive = compute_metrics(np.array(y_true_all), np.array(y_pred_naive_all))
    overall_ma = compute_metrics(np.array(y_true_all), np.array(y_pred_ma_all))

    # Profile category breakdown
    category_summary = {}
    for cat, data in category_results.items():
        if len(data["y_true"]) > 0:
            category_summary[cat] = compute_metrics(np.array(data["y_true"]), np.array(data["y_pred"]))

    return {
        "target_col": target_col,
        "companies_evaluated": len(company_evaluations),
        "total_observations": len(y_true_all),
        "execution_time_sec": round(elapsed_sec, 3),
        "avg_time_per_company_sec": round(avg_sec_per_company, 4),
        "overall_ml_metrics": overall_ml,
        "overall_naive_metrics": overall_naive,
        "overall_ma_metrics": overall_ma,
        "category_summary": category_summary,
        "company_evaluations": company_evaluations
    }

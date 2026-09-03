import json
import os
import re
from pathlib import Path
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
import pandas as pd

from backend.database import init_db, get_all_records, get_company_records, get_company_list
from backend.ratio_engine import compute_financial_ratios, get_latest_company_ratios
from backend.forecasting_engine import generate_company_forecasts
from backend.evaluation_engine import run_out_of_time_evaluation
from backend.exception_engine import generate_portfolio_exception_report, evaluate_forecast_confidence
from backend.scenario_engine import run_what_if_scenario
from backend.ai_agent import AIFinancialAgent, FinancialAgentTools
from backend.config import BENCHMARK_JSON_PATH, BENCHMARK_REPORT_PATH

app = FastAPI(
    title="AI Forward Cash Controller API",
    version="2.1.0",
    description="Backend API for AI Finance Controller - Forward Cash Forecaster & Finance-Ops Loop"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory cache for benchmark & exception report evaluation to prevent thread freezing
_BENCHMARK_CACHE: Optional[Dict[str, Any]] = None
_EXCEPTIONS_CACHE: Optional[Dict[str, Any]] = None

@app.on_event("startup")
def startup_event():
    init_db()

class ChatRequest(BaseModel):
    query: str
    company_id: Optional[str] = None

class ScenarioRequest(BaseModel):
    company_id: str
    revenue_change_pct: float = -0.10
    opex_change_pct: float = 0.0
    capex_adjustment: float = 0.0

@app.get("/")
def read_root():
    return {
        "status": "online",
        "service": "AI Forward Cash Controller API",
        "version": "2.1.0",
        "direction": "Forward Cash Forecaster"
    }

@app.get("/api/portfolio/summary")
def get_portfolio_summary():
    df = get_all_records()
    if df.empty:
        raise HTTPException(status_code=404, detail="No financial data found.")

    exception_report = get_exceptions()
    eval_results = get_benchmark_report()

    total_companies = df["company_id"].nunique()
    total_obs = len(df)
    category_counts = df.groupby("company_id")["category"].first().value_counts().to_dict()

    return {
        "total_companies": total_companies,
        "total_observations": total_obs,
        "forecasts_generated": exception_report["total_forecasts_generated"],
        "resolved_forecasts": exception_report["resolved_forecasts"],
        "human_review_exceptions": exception_report["human_review_exceptions"],
        "resolution_rate_pct": exception_report["resolution_rate_pct"],
        "exception_rate_pct": exception_report["exception_rate_pct"],
        "execution_time_sec": eval_results.get("execution_time_sec", 0.0),
        "avg_time_per_company_sec": eval_results.get("avg_time_per_company_sec", 0.0),
        "portfolio_cash_mape": eval_results["overall_ml_metrics"]["mape"],
        "portfolio_cash_mae": eval_results["overall_ml_metrics"]["mae"],
        "portfolio_cash_rmse": eval_results["overall_ml_metrics"]["rmse"],
        "naive_cash_mape": eval_results["overall_naive_metrics"]["mape"],
        "moving_avg_cash_mape": eval_results["overall_ma_metrics"]["mape"],
        "category_distribution": category_counts
    }

@app.get("/api/companies")
def list_companies():
    df = get_all_records()
    if df.empty:
        raise HTTPException(status_code=404, detail="No financial data found.")

    companies = []
    for c_id in df["company_id"].unique():
        c_df = df[df["company_id"] == c_id].sort_values("period_idx")
        latest = c_df.iloc[-1]
        conf = evaluate_forecast_confidence(c_df)
        fc = generate_company_forecasts(c_df, target_col="cash", horizon=3)
        risk = FinancialAgentTools.analyze_financial_risk(c_id)

        # Ensure full company_name is explicitly returned without substring truncation
        c_name = latest["company_name"] if latest["company_name"] and latest["company_name"] != "CO" else f"Company {c_id}"

        companies.append({
            "company_id": c_id,
            "company_name": c_name,
            "category": latest["category"],
            "latest_period": latest["period"],
            "revenue": latest["revenue"],
            "net_income": latest["net_income"],
            "current_cash": latest["cash"],
            "operating_cash_flow": latest["operating_cash_flow"],
            "forecast_cash_90d": fc["predictions"][-1],
            "expected_change": round(fc["predictions"][-1] - latest["cash"], 2),
            "selected_model": fc["selected_model"],
            "confidence_status": conf["confidence_status"],
            "confidence_score": conf["confidence_score"],
            "resolution_status": conf["resolution_status"],
            "risk_level": risk["risk_level"],
            "controller_action": conf["controller_action"],
            "is_resolved": conf["is_resolved"]
        })

    return companies

@app.get("/api/companies/{company_id}")
def get_company_detail(company_id: str):
    df = get_company_records(company_id)
    if df.empty:
        raise HTTPException(status_code=404, detail=f"Company {company_id} not found.")

    latest = df.iloc[-1].to_dict()
    c_name = latest["company_name"] if latest["company_name"] and latest["company_name"] != "CO" else f"Company {company_id}"
    latest["company_name"] = c_name

    ratios = get_latest_company_ratios(df, company_id)
    conf = evaluate_forecast_confidence(df)
    risk = FinancialAgentTools.analyze_financial_risk(company_id)
    
    cash_fc = generate_company_forecasts(df, target_col="cash", horizon=3)
    rev_fc = generate_company_forecasts(df, target_col="revenue", horizon=3)

    history = df[["period", "period_idx", "revenue", "cost_of_goods_sold", "operating_expenses",
                  "net_income", "cash", "operating_cash_flow", "capital_expenditure",
                  "short_term_debt", "long_term_debt", "current_ratio", "quick_ratio", "debt_to_equity"]].to_dict(orient="records")

    return {
        "company_id": company_id,
        "company_name": c_name,
        "category": latest["category"],
        "latest_period": latest["period"],
        "latest_metrics": latest,
        "ratios": ratios,
        "history": history,
        "cash_forecast": {
            "model": cash_fc["selected_model"],
            "predictions_30_60_90": cash_fc["predictions"],
            "expected_change": round(cash_fc["predictions"][-1] - latest["cash"], 2)
        },
        "revenue_forecast": {
            "model": rev_fc["selected_model"],
            "predictions_30_60_90": rev_fc["predictions"]
        },
        "confidence": conf,
        "risk": risk
    }

@app.get("/api/benchmark")
def get_benchmark_report():
    global _BENCHMARK_CACHE
    if _BENCHMARK_CACHE is not None:
        return _BENCHMARK_CACHE

    if BENCHMARK_JSON_PATH.exists():
        try:
            with open(BENCHMARK_JSON_PATH, "r", encoding="utf-8") as f:
                cached_data = json.load(f)
                _BENCHMARK_CACHE = cached_data["evaluation_summary"]
                return _BENCHMARK_CACHE
        except Exception:
            pass

    df = get_all_records()
    if df.empty:
        raise HTTPException(status_code=404, detail="No financial data found.")

    _BENCHMARK_CACHE = run_out_of_time_evaluation(df, target_col="cash")
    return _BENCHMARK_CACHE

@app.get("/api/exceptions")
def get_exceptions():
    global _EXCEPTIONS_CACHE
    if _EXCEPTIONS_CACHE is not None:
        return _EXCEPTIONS_CACHE

    if BENCHMARK_JSON_PATH.exists():
        try:
            with open(BENCHMARK_JSON_PATH, "r", encoding="utf-8") as f:
                cached_data = json.load(f)
                _EXCEPTIONS_CACHE = cached_data["exception_summary"]
                return _EXCEPTIONS_CACHE
        except Exception:
            pass

    df = get_all_records()
    if df.empty:
        raise HTTPException(status_code=404, detail="No financial data found.")

    _EXCEPTIONS_CACHE = generate_portfolio_exception_report(df)
    return _EXCEPTIONS_CACHE

@app.get("/api/benchmark/report/text", response_class=PlainTextResponse)
def get_benchmark_report_plain_text():
    """Serves reports in clean, human-readable plain text without raw markdown tags."""
    if not BENCHMARK_REPORT_PATH.exists():
        from scripts.generate_report import generate_markdown_report
        generate_markdown_report()

    with open(BENCHMARK_REPORT_PATH, "r", encoding="utf-8") as f:
        md_text = f.read()

    # Strip markdown headers, table separators, and asterisks into clean plain text
    plain = re.sub(r'#+\s*', '', md_text)
    plain = re.sub(r'\*\*(.*?)\*\*', r'\1', plain)
    plain = re.sub(r'`(.*?)`', r'\1', plain)
    plain = re.sub(r'\|?\s*:---:\s*\|?', '', plain)
    plain = re.sub(r'^\s*[\-\*]\s*', '• ', plain, flags=re.MULTILINE)
    return plain.strip()

@app.post("/api/scenario")
def simulate_scenario(req: ScenarioRequest):
    df = get_company_records(req.company_id)
    if df.empty:
        raise HTTPException(status_code=404, detail=f"Company {req.company_id} not found.")

    res = run_what_if_scenario(
        df,
        revenue_change_pct=req.revenue_change_pct,
        opex_change_pct=req.opex_change_pct,
        capex_adjustment=req.capex_adjustment
    )
    return res

@app.post("/api/chat")
def agent_chat(req: ChatRequest):
    agent = AIFinancialAgent()
    res = agent.process_query(req.query, company_id=req.company_id)
    return res

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)

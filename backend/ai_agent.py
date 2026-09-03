import os
import json
import re
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv

# Explicitly load .env file into environment memory
load_dotenv()

from backend.database import get_company_records, get_all_records
from backend.ratio_engine import compute_financial_ratios, get_latest_company_ratios
from backend.forecasting_engine import generate_company_forecasts
from backend.exception_engine import evaluate_forecast_confidence, generate_portfolio_exception_report
from backend.scenario_engine import run_what_if_scenario
from backend.config import GEMINI_API_KEY, OPENAI_API_KEY

try:
    from google import genai
    HAS_GENAI_SDK = True
except ImportError:
    HAS_GENAI_SDK = False

class FinancialAgentTools:
    """
    Registered tool calls for the AI Financial Controller Agent.
    All numerical data, ratios, forecasts, and exception metadata are
    obtained from underlying quantitative engines.
    """
    
    @staticmethod
    def get_company_financials(company_id: str) -> Dict[str, Any]:
        df = get_company_records(company_id)
        if df.empty:
            return {"error": f"Company {company_id} not found."}
        latest = df.iloc[-1].to_dict()
        c_name = latest["company_name"] if latest["company_name"] and latest["company_name"] != "CO" else f"Company {company_id}"
        return {
            "company_id": latest["company_id"],
            "company_name": c_name,
            "category": latest["category"],
            "period": latest["period"],
            "revenue": latest["revenue"],
            "cost_of_goods_sold": latest["cost_of_goods_sold"],
            "operating_expenses": latest["operating_expenses"],
            "net_income": latest["net_income"],
            "cash": latest["cash"],
            "accounts_receivable": latest["accounts_receivable"],
            "inventory": latest["inventory"],
            "accounts_payable": latest["accounts_payable"],
            "short_term_debt": latest["short_term_debt"],
            "long_term_debt": latest["long_term_debt"],
            "capital_expenditure": latest["capital_expenditure"],
            "operating_cash_flow": latest["operating_cash_flow"],
            "investing_cash_flow": latest["investing_cash_flow"],
            "financing_cash_flow": latest["financing_cash_flow"]
        }

    @staticmethod
    def calculate_financial_ratios(company_id: str) -> Dict[str, Any]:
        df = get_company_records(company_id)
        if df.empty:
            return {"error": f"Company {company_id} not found."}
        ratios = get_latest_company_ratios(df, company_id)
        return {
            "liquidity": {
                "current_ratio": ratios.get("current_ratio"),
                "quick_ratio": ratios.get("quick_ratio"),
                "cash_ratio": ratios.get("cash_ratio")
            },
            "profitability": {
                "gross_margin": ratios.get("gross_margin"),
                "operating_margin": ratios.get("operating_margin"),
                "net_profit_margin": ratios.get("net_profit_margin"),
                "revenue_growth": ratios.get("revenue_growth"),
                "roa": ratios.get("roa"),
                "roe": ratios.get("roe")
            },
            "leverage": {
                "debt_to_equity": ratios.get("debt_to_equity"),
                "debt_to_ebitda": ratios.get("debt_to_ebitda"),
                "interest_coverage": ratios.get("interest_coverage")
            },
            "cash_flow": {
                "free_cash_flow": ratios.get("free_cash_flow"),
                "cash_burn_rate": ratios.get("cash_burn_rate"),
                "cash_flow_growth": ratios.get("cash_flow_growth"),
                "ocf_trend_slope": ratios.get("ocf_trend_slope")
            }
        }

    @staticmethod
    def get_historical_trends(company_id: str) -> Dict[str, Any]:
        df = get_company_records(company_id)
        if df.empty:
            return {"error": f"Company {company_id} not found."}
        
        return {
            "company_id": company_id,
            "periods": df["period"].tolist(),
            "revenue_history": df["revenue"].tolist(),
            "cash_history": df["cash"].tolist(),
            "operating_cash_flow_history": df["operating_cash_flow"].tolist(),
            "net_income_history": df["net_income"].tolist()
        }

    @staticmethod
    def forecast_cash(company_id: str) -> Dict[str, Any]:
        df = get_company_records(company_id)
        if df.empty:
            return {"error": f"Company {company_id} not found."}
        
        conf = evaluate_forecast_confidence(df)
        forecast_res = generate_company_forecasts(df, target_col="cash", horizon=3)
        current_cash = df["cash"].iloc[-1]
        preds = forecast_res["predictions"]

        return {
            "company_id": company_id,
            "current_cash": current_cash,
            "forecast_model": forecast_res["selected_model"],
            "predictions_30_60_90_days": {
                "30_day": preds[0],
                "60_day": preds[1],
                "90_day": preds[2]
            },
            "expected_change": round(preds[2] - current_cash, 2),
            "expected_change_pct": round(((preds[2] - current_cash) / (current_cash + 1e-3)) * 100, 1),
            "confidence_status": conf["confidence_status"],
            "confidence_score": conf["confidence_score"],
            "resolution_status": conf["resolution_status"],
            "reasons": conf["reasons"],
            "controller_action": conf["controller_action"]
        }

    @staticmethod
    def forecast_revenue(company_id: str) -> Dict[str, Any]:
        df = get_company_records(company_id)
        if df.empty:
            return {"error": f"Company {company_id} not found."}
        
        forecast_res = generate_company_forecasts(df, target_col="revenue", horizon=3)
        current_rev = df["revenue"].iloc[-1]
        preds = forecast_res["predictions"]

        return {
            "company_id": company_id,
            "current_revenue": current_rev,
            "forecast_model": forecast_res["selected_model"],
            "revenue_forecast_30_60_90_days": {
                "30_day": preds[0],
                "60_day": preds[1],
                "90_day": preds[2]
            },
            "expected_change": round(preds[2] - current_rev, 2)
        }

    @staticmethod
    def analyze_financial_risk(company_id: str) -> Dict[str, Any]:
        df = get_company_records(company_id)
        if df.empty:
            return {"error": f"Company {company_id} not found."}
        
        latest = df.iloc[-1]
        ratios = get_latest_company_ratios(df, company_id)
        conf = evaluate_forecast_confidence(df)
        c_name = latest["company_name"] if latest["company_name"] and latest["company_name"] != "CO" else f"Company {company_id}"

        risk_score = 0
        risk_factors = []

        current_ratio = ratios.get("current_ratio", 1.5)
        if current_ratio < 1.0:
            risk_score += 3
            risk_factors.append(f"Low Current Ratio ({current_ratio:.2f} < 1.0): Short-term liquidity crunch risk.")
        elif current_ratio < 1.3:
            risk_score += 1
            risk_factors.append(f"Tight Current Ratio ({current_ratio:.2f}).")

        debt_equity = ratios.get("debt_to_equity", 0.5)
        if debt_equity > 2.5:
            risk_score += 3
            risk_factors.append(f"High Debt-to-Equity ({debt_equity:.2f}): Heavy interest burden.")
        elif debt_equity > 1.5:
            risk_score += 1
            risk_factors.append(f"Elevated Debt-to-Equity ({debt_equity:.2f}).")

        net_margin = ratios.get("net_profit_margin", 0.1)
        if net_margin < 0:
            risk_score += 2
            risk_factors.append(f"Negative Net Profit Margin ({net_margin*100:.1f}%): Operating losses.")

        ocf = latest["operating_cash_flow"]
        cash = latest["cash"]
        if ocf < 0:
            risk_score += 3
            runway = cash / (abs(ocf) + 1e-3)
            risk_factors.append(f"Negative Operating Cash Flow ({ocf:.1f} Cr). Cash runway: {runway:.1f} quarters.")

        if risk_score >= 6:
            risk_level = "HIGH RISK"
        elif risk_score >= 3:
            risk_level = "MEDIUM RISK"
        else:
            risk_level = "LOW RISK"

        return {
            "company_id": company_id,
            "company_name": c_name,
            "risk_level": risk_level,
            "risk_score": risk_score,
            "risk_factors": risk_factors,
            "forecast_confidence": conf["confidence_status"],
            "resolution_status": conf["resolution_status"],
            "controller_action": conf["controller_action"]
        }

    @staticmethod
    def get_forecast_confidence(company_id: str) -> Dict[str, Any]:
        df = get_company_records(company_id)
        if df.empty:
            return {"error": f"Company {company_id} not found."}
        return evaluate_forecast_confidence(df)

    @staticmethod
    def generate_finance_action(company_id: str) -> Dict[str, Any]:
        df = get_company_records(company_id)
        if df.empty:
            return {"error": f"Company {company_id} not found."}
        conf = evaluate_forecast_confidence(df)
        risk = FinancialAgentTools.analyze_financial_risk(company_id)

        return {
            "company_id": company_id,
            "company_name": conf["company_name"],
            "resolution_status": conf["resolution_status"],
            "risk_level": risk["risk_level"],
            "confidence_status": conf["confidence_status"],
            "confidence_score": conf["confidence_score"],
            "financial_drivers": conf["financial_drivers"],
            "controller_action": conf["controller_action"]
        }

    @staticmethod
    def get_exception_report() -> Dict[str, Any]:
        df = get_all_records()
        return generate_portfolio_exception_report(df)

    @staticmethod
    def run_scenario(company_id: str, revenue_change_pct: float, opex_change_pct: float, capex_adjustment: float) -> Dict[str, Any]:
        df = get_company_records(company_id)
        if df.empty:
            return {"error": f"Company {company_id} not found."}
        return run_what_if_scenario(df, revenue_change_pct, opex_change_pct, capex_adjustment)


class AIFinancialAgent:
    """
    LLM Financial Controller Agent.
    Integrates with live Gemini API when GEMINI_API_KEY is available, passing
    quantitative evidence context to produce dynamic, prompt-tailored financial reasoning.
    ALWAYS refers to companies by their full corporate name rather than company numbers/IDs.
    """
    def __init__(self):
        self.tools = FinancialAgentTools()
        self.api_key = os.environ.get("GEMINI_API_KEY", "") or GEMINI_API_KEY
        self.client = None
        if self.api_key and HAS_GENAI_SDK:
            try:
                self.client = genai.Client(api_key=self.api_key)
            except Exception as e:
                print(f"[WARN] Failed to initialize Gemini Client: {e}")

    def process_query(self, query: str, company_id: Optional[str] = None) -> Dict[str, Any]:
        query_upper = query.upper()
        if not company_id:
            match = re.search(r"C\d{3}", query_upper)
            if match:
                company_id = match.group(0)
            else:
                company_id = "C014"

        financials = self.tools.get_company_financials(company_id)
        if "error" in financials:
            return {
                "answer": f"Could not find financial records for the requested company. Please select a valid company.",
                "evidence": {}
            }

        ratios = self.tools.calculate_financial_ratios(company_id)
        trends = self.tools.get_historical_trends(company_id)
        cash_fc = self.tools.forecast_cash(company_id)
        rev_fc = self.tools.forecast_revenue(company_id)
        risk = self.tools.analyze_financial_risk(company_id)
        action_data = self.tools.generate_finance_action(company_id)

        is_scenario_query = any(k in query.lower() for k in ["what if", "scenario", "falls by", "revenue drops", "if revenue"])
        scenario_data = None
        if is_scenario_query:
            pct = -0.10
            m = re.search(r"(\d+)%", query)
            if m:
                val = float(m.group(1))
                pct = -val / 100.0 if "fall" in query.lower() or "drop" in query.lower() else val / 100.0
            scenario_data = self.tools.run_scenario(company_id, revenue_change_pct=pct, opex_change_pct=0.0, capex_adjustment=0.0)

        evidence_context = {
            "financials": financials,
            "ratios": ratios,
            "trends": trends,
            "cash_forecast": cash_fc,
            "revenue_forecast": rev_fc,
            "risk_analysis": risk,
            "action_data": action_data,
            "scenario_data": scenario_data
        }

        # 1. Live Gemini API Call Path (Dynamic Response)
        if self.client is not None:
            try:
                system_instruction = (
                    "You are a Senior AI Finance Controller. Analyze the provided quantitative financial "
                    "evidence and answer the user's question directly with professional financial reasoning. "
                    "ALWAYS refer to companies strictly by their full corporate name (e.g., 'Velox Medical Devices', 'Apex Tech Solutions', 'Horizon Logistics'). "
                    "NEVER refer to companies by their ID code or company number (do NOT say 'C014', 'C001', or 'Company C014'). "
                    "Use structured headings: "
                    "1. Forward Cash Forecast, 2. Primary Financial Drivers, 3. Financial Risk Assessment, "
                    "4. Confidence & Resolution Status, 5. Recommended Controller Action. "
                    "Do NOT invent numerical predictions; rely strictly on the provided evidence context."
                )
                user_prompt = f"Evidence Context:\n{json.dumps(evidence_context, indent=2)}\n\nUser Question: {query}"

                response = self.client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=user_prompt,
                    config={"system_instruction": system_instruction}
                )
                
                if response.text and len(response.text.strip()) > 0:
                    return {
                        "company_id": company_id,
                        "company_name": financials["company_name"],
                        "answer": response.text,
                        "evidence": evidence_context
                    }
            except Exception as err:
                print(f"[ERROR] Live Gemini API generation error: {err}")

        # 2. Fallback Deterministic Synthesis Engine
        return self._deterministic_fallback(query, company_id, evidence_context, is_scenario_query)

    def _deterministic_fallback(self, query: str, company_id: str, evidence: Dict[str, Any], is_scenario: bool) -> Dict[str, Any]:
        financials = evidence["financials"]
        cash_fc = evidence["cash_forecast"]
        risk = evidence["risk_analysis"]
        action_data = evidence["action_data"]
        scenario_data = evidence["scenario_data"]

        c_name = financials["company_name"]
        cur_cash = cash_fc["current_cash"]
        fc_30d = cash_fc["predictions_30_60_90_days"]["30_day"]
        fc_60d = cash_fc["predictions_30_60_90_days"]["60_day"]
        fc_90d = cash_fc["predictions_30_60_90_days"]["90_day"]
        chg = cash_fc["expected_change"]
        chg_pct = cash_fc["expected_change_pct"]
        status = cash_fc["confidence_status"]
        res_status = cash_fc["resolution_status"]
        model_used = cash_fc["forecast_model"]

        answer_parts = []

        if is_scenario and scenario_data:
            s_sum = scenario_data["summary"]
            s_param = scenario_data["parameters"]
            s_latest = scenario_data["scenario_latest"]
            answer_parts.append(f"### 🧪 **What-If Scenario Simulation: {c_name}**")
            answer_parts.append(f"**Status**: `SCENARIO - NOT A FORECAST`\n")
            answer_parts.append(f"**Scenario Parameter**: Revenue shift of **{s_param['revenue_change_pct']}%**\n")
            answer_parts.append(f"* **Adjusted Revenue**: {s_latest['revenue']} Cr")
            answer_parts.append(f"* **Adjusted Net Income**: {s_latest['net_income']} Cr")
            answer_parts.append(f"* **Adjusted Operating Cash Flow**: {s_latest['operating_cash_flow']} Cr")
            answer_parts.append(f"* **Simulated 90-Day Cash Position**: **{s_latest['forecast_cash_90d']} Cr** (vs Baseline {cur_cash} Cr)")
            answer_parts.append(f"* **Simulated Delta Impact**: **{s_sum['scenario_delta_impact']} Cr**\n")
            if s_sum["is_cash_depleted"]:
                answer_parts.append("⚠️ **Warning**: Under this demand shock, cash reserves fall into critical exhaustion territory. Immediate capital intervention required.")
            else:
                answer_parts.append("✅ **Scenario Assessment**: The balance sheet maintains positive cash liquidity buffers under this demand shock.")
        else:
            answer_parts.append(f"### 🏦 **AI Finance Controller Report: {c_name}**\n")
            answer_parts.append("#### 1. Forward Cash Forecast")
            answer_parts.append(f"* **Current Cash Balance**: `{cur_cash:.2f} Cr`")
            answer_parts.append(f"* **30-Day Forecast**: `{fc_30d:.2f} Cr`")
            answer_parts.append(f"* **60-Day Forecast**: `{fc_60d:.2f} Cr`")
            answer_parts.append(f"* **90-Day Forecast**: `{fc_90d:.2f} Cr`")
            answer_parts.append(f"* **Expected Net Change**: `{chg:+.2f} Cr` (`{chg_pct:+.1f}%`)\n")

            answer_parts.append("#### 2. Primary Financial Drivers")
            for driver in action_data["financial_drivers"]:
                answer_parts.append(f"* {driver}")
            answer_parts.append("")

            answer_parts.append("#### 3. Financial Risk Assessment")
            answer_parts.append(f"* **Risk Level**: **`{risk['risk_level']}`** (Score: {risk['risk_score']}/10)")
            for factor in risk["risk_factors"]:
                answer_parts.append(f"  - {factor}")
            answer_parts.append("")

            answer_parts.append("#### 4. Confidence & Resolution Status")
            answer_parts.append(f"* **Forecast Status**: **`{res_status}`**")
            answer_parts.append(f"* **Confidence Level**: **`{status}`** (`{cash_fc['confidence_score']*100:.0f}%` score)")
            answer_parts.append(f"* **Statistical Model**: `{model_used}`")
            for r in cash_fc["reasons"]:
                answer_parts.append(f"  - {r}")
            answer_parts.append("")

            answer_parts.append("#### 5. Recommended Controller Action")
            answer_parts.append(f"> 📋 **Action Item**: {action_data['controller_action']}")

        return {
            "company_id": company_id,
            "company_name": c_name,
            "answer": "\n".join(answer_parts),
            "evidence": evidence
        }

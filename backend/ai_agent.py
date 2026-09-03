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
    Supports both Global Portfolio Queries across all 55 companies and Company-Specific Queries.
    Strictly answers specific questions directly without un-requested forecast dumps.
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

    def process_query(self, query: str, company_id: Optional[str] = None, scope: Optional[str] = None) -> Dict[str, Any]:
        query_upper = query.upper()
        
        is_global_query = (
            company_id == "GLOBAL" or scope == "global" or
            any(k in query.lower() for k in [
                "exception", "low confidence", "human review", "manual review", 
                "all companies", "portfolio", "across companies", "list exceptions", 
                "how many exceptions", "flagged"
            ])
        )

        if is_global_query:
            return self._process_global_query(query)

        if not company_id or company_id == "GLOBAL":
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
        risk = self.tools.analyze_financial_risk(company_id)
        action_data = self.tools.generate_finance_action(company_id)

        q_lower = query.lower()
        is_forecast_query = any(k in q_lower for k in ["forecast", "prediction", "predict", "trajectory", "30-day", "60-day", "90-day", "future cash", "cash position", "next quarter", "report", "review", "overview", "summary"])

        evidence_context = {
            "financials": financials,
            "ratios": ratios,
            "trends": trends,
            "risk_analysis": risk,
            "action_data": action_data
        }

        if is_forecast_query:
            evidence_context["cash_forecast"] = self.tools.forecast_cash(company_id)
            evidence_context["revenue_forecast"] = self.tools.forecast_revenue(company_id)

        is_scenario_query = any(k in q_lower for k in ["what if", "scenario", "falls by", "revenue drops", "if revenue"])
        if is_scenario_query:
            pct = -0.10
            m = re.search(r"(\d+)%", query)
            if m:
                val = float(m.group(1))
                pct = -val / 100.0 if "fall" in query.lower() or "drop" in query.lower() else val / 100.0
            evidence_context["scenario_data"] = self.tools.run_scenario(company_id, revenue_change_pct=pct, opex_change_pct=0.0, capex_adjustment=0.0)

        # 1. Live Gemini API Call Path (Company Scope)
        if self.client is not None:
            try:
                if is_forecast_query:
                    system_instruction = (
                        "You are a Senior AI Finance Controller. Provide a comprehensive 5-step forward cash forecast report "
                        "for the requested company based on evidence context. "
                        "ALWAYS refer to companies strictly by full corporate name (e.g. 'Velox Medical Devices')."
                    )
                    user_prompt = f"Evidence Context:\n{json.dumps(evidence_context, indent=2)}\n\nUser Question: {query}\n\nPlease output a structured 5-step controller report."
                else:
                    system_instruction = (
                        "You are a concise financial assistant. Answer ONLY the specific question asked in 1 or 2 sentences. "
                        "ALWAYS refer to companies by full corporate name (e.g. 'Velox Medical Devices')."
                    )
                    user_prompt = (
                        f"Company: {financials['company_name']}\n"
                        f"Evidence Data: {json.dumps(evidence_context, indent=2)}\n\n"
                        f"User Question: {query}\n\n"
                        f"OUTPUT REQUIREMENT: Answer ONLY the user's specific question directly in 1-2 plain sentences. "
                        f"DO NOT include markdown section headers, DO NOT write '1. Forward Cash Forecast', and DO NOT write '2. Primary Financial Drivers'. Write ONLY the answer to the user's question."
                    )

                response = self.client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=user_prompt,
                    config={"system_instruction": system_instruction}
                )
                
                if response.text and len(response.text.strip()) > 0:
                    return {
                        "scope": "company",
                        "company_id": company_id,
                        "company_name": financials["company_name"],
                        "answer": response.text,
                        "evidence": evidence_context
                    }
            except Exception as err:
                print(f"[ERROR] Live Gemini API generation error: {err}")

        # 2. Fallback Deterministic Synthesis Engine
        return self._deterministic_fallback(query, company_id, evidence_context, is_scenario_query)

    def _process_global_query(self, query: str) -> Dict[str, Any]:
        """Handles portfolio-wide queries across all 55 companies."""
        exception_report = self.tools.get_exception_report()

        if self.client is not None:
            try:
                system_instruction = (
                    "You are a Senior AI Finance Controller evaluating a portfolio of 55 companies. "
                    "Analyze the provided portfolio exception report and answer the user's question directly. "
                    "ALWAYS refer to companies by their full corporate name (e.g. 'Shockwave Retail', 'Volatile Dynamics'). "
                    "Do NOT refer to companies by ID numbers like 'C047'. "
                    "Answer ONLY what is asked. Do not dump un-requested tables unless asked for exception reports or portfolio lists."
                )
                user_prompt = f"Portfolio Exception Evidence Context:\n{json.dumps(exception_report, indent=2)}\n\nUser Question: {query}"

                response = self.client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=user_prompt,
                    config={"system_instruction": system_instruction}
                )

                if response.text and len(response.text.strip()) > 0:
                    return {
                        "scope": "global",
                        "answer": response.text,
                        "evidence": exception_report
                    }
            except Exception as err:
                print(f"[ERROR] Global Gemini API generation error: {err}")

        answer_parts = []
        answer_parts.append("### 🛡️ **Portfolio-Wide Low-Confidence Exception Report**\n")
        answer_parts.append(f"* **Total Companies Analyzed**: `{exception_report['total_companies']}`")
        answer_parts.append(f"* **Automated Forecast Resolution Rate**: `{exception_report['resolution_rate_pct']}%` ({exception_report['resolved_forecasts']}/55 companies resolved)")
        answer_parts.append(f"* **Human-Review Exception Flags**: `{exception_report['human_review_exceptions']}` companies ({exception_rate_pct}% exception rate)\n")
        
        answer_parts.append("#### 📋 Flagged Exception Companies Requiring Manual Review:\n")
        for exc in exception_report["exception_list"]:
            c_name = exc["company_name"] if exc["company_name"] and exc["company_name"] != "CO" else f"Company {exc['company_id']}"
            reasons_str = " ".join(exc["reasons"])
            answer_parts.append(f"* **{c_name}**")
            answer_parts.append(f"  - **Target Metric**: `{exc['target']}` | **Status**: `{exc['resolution_status']}`")
            answer_parts.append(f"  - **Confidence**: `{exc['confidence_status']}` (`{exc['confidence_score']}` score)")
            answer_parts.append(f"  - **Exception Trigger**: `{reasons_str}`")
            answer_parts.append(f"  - 📋 **Controller Action**: {exc['controller_action']}\n")

        return {
            "scope": "global",
            "answer": "\n".join(answer_parts),
            "evidence": exception_report
        }

    def _deterministic_fallback(self, query: str, company_id: str, evidence: Dict[str, Any], is_scenario: bool) -> Dict[str, Any]:
        financials = evidence["financials"]
        ratios = evidence["ratios"]
        cash_fc = evidence.get("cash_forecast", {})
        risk = evidence["risk_analysis"]
        action_data = evidence["action_data"]
        scenario_data = evidence.get("scenario_data")

        c_name = financials["company_name"]
        cur_cash = financials.get("cash", 0.0)

        q_lower = query.lower()
        is_forecast_query = any(k in q_lower for k in ["forecast", "prediction", "predict", "trajectory", "30-day", "60-day", "90-day", "future cash", "cash position", "next quarter", "report", "review", "overview", "summary"])
        is_risk_query = any(k in q_lower for k in ["risk", "insolvent", "default", "health", "hazard", "vulnerable", "warning", "burn"])
        is_ratio_query = any(k in q_lower for k in ["ratio", "current ratio", "quick ratio", "liquidity", "debt to equity", "leverage", "margin", "coverage"])
        is_metrics_query = any(k in q_lower for k in ["revenue", "net income", "income", "profit", "operating cash flow", "expenses", "cogs", "capex", "balance sheet"])

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
        
        elif is_ratio_query and not is_forecast_query:
            answer_parts.append(f"### 📊 **Financial Ratios & Liquidity: {c_name}**\n")
            answer_parts.append(f"* **Current Ratio**: `{ratios['liquidity']['current_ratio']:.2f}` (Short-term liquidity buffer)")
            answer_parts.append(f"* **Quick Ratio**: `{ratios['liquidity']['quick_ratio']:.2f}`")
            answer_parts.append(f"* **Gross Margin**: `{ratios['profitability']['gross_margin']*100:.1f}%`")
            answer_parts.append(f"* **Net Profit Margin**: `{ratios['profitability']['net_profit_margin']*100:.1f}%`")
            answer_parts.append(f"* **Debt-to-Equity**: `{ratios['leverage']['debt_to_equity']:.2f}`")
            answer_parts.append(f"* **Interest Coverage**: `{ratios['leverage']['interest_coverage']:.1f}x`\n")
            answer_parts.append(f"> 📋 **Controller Takeaway**: {action_data['controller_action']}")

        elif is_risk_query and not is_forecast_query:
            answer_parts.append(f"### ⚠️ **Financial Risk Assessment: {c_name}**\n")
            answer_parts.append(f"* **Risk Level**: **`{risk['risk_level']}`** (Risk Score: {risk['risk_score']}/10)")
            answer_parts.append("\n**Primary Risk Drivers & Triggers:**")
            for factor in risk["risk_factors"]:
                answer_parts.append(f"* {factor}")
            answer_parts.append(f"\n> 📋 **Controller Action**: {action_data['controller_action']}")

        elif is_metrics_query and not is_forecast_query:
            answer_parts.append(f"### 🧾 **Financial Statement Highlights: {c_name}**\n")
            answer_parts.append(f"* **Latest Period**: `{financials['period']}`")
            answer_parts.append(f"* **Revenue**: `{financials['revenue']:.2f} Cr`")
            answer_parts.append(f"* **Cost of Goods Sold**: `{financials['cost_of_goods_sold']:.2f} Cr`")
            answer_parts.append(f"* **Operating Expenses**: `{financials['operating_expenses']:.2f} Cr`")
            answer_parts.append(f"* **Net Income**: `{financials['net_income']:.2f} Cr`")
            answer_parts.append(f"* **Operating Cash Flow**: `{financials['operating_cash_flow']:.2f} Cr`")
            answer_parts.append(f"* **Current Cash Balance**: `{financials['cash']:.2f} Cr`\n")
            answer_parts.append(f"> 📋 **Controller Guidance**: {action_data['controller_action']}")

        else:
            fc_30d = cash_fc.get("predictions_30_60_90_days", {}).get("30_day", cur_cash)
            fc_60d = cash_fc.get("predictions_30_60_90_days", {}).get("60_day", cur_cash)
            fc_90d = cash_fc.get("predictions_30_60_90_days", {}).get("90_day", cur_cash)
            chg = cash_fc.get("expected_change", 0.0)
            chg_pct = cash_fc.get("expected_change_pct", 0.0)
            status = cash_fc.get("confidence_status", "HIGH")
            res_status = cash_fc.get("resolution_status", "RESOLVED")
            model_used = cash_fc.get("forecast_model", "Ridge Linear Regression")

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
            answer_parts.append(f"* **Confidence Level**: **`{status}`**")
            answer_parts.append(f"* **Statistical Model**: `{model_used}`")
            answer_parts.append("")

            answer_parts.append("#### 5. Recommended Controller Action")
            answer_parts.append(f"> 📋 **Action Item**: {action_data['controller_action']}")

        return {
            "scope": "company",
            "company_id": company_id,
            "company_name": c_name,
            "answer": "\n".join(answer_parts),
            "evidence": evidence
        }

import numpy as np
import pandas as pd
import random
from typing import List, Dict
from backend.config import CSV_FILE_PATH

# Seed for reproducible synthetic financial dataset
np.random.seed(42)
random.seed(42)

COMPANY_NAMES = [
    "Apex Tech Solutions", "Horizon Logistics", "Beacon Healthcare", "Vanguard Manufacturing",
    "Solaris Energy", "Quantum Dynamics", "Pinnacle Bio", "Nexus Cloud Systems",
    "Titan Heavy Industries", "Aura Consumer Goods", "Sterling Retail", "Frontier Aerospace",
    "Omni Financial", "Atlas Infrastructure", "Velox Medical Devices", "Echo Communications",
    "Crestline Automotive", "Zenith Software", "Orion Chemicals", "Meridian Materials",
    "Pulse Digital", "Veritas Agritech", "Hyperion Robotics", "Catalyst Renewables",
    "Summit Real Estate", "Starlight Media", "Vortex Defense", "Solstice Pharma",
    "Prism Gaming", "Cascade Beverage", "Novus Microelectronics", "Valence Metals",
    "Infinitum Supply Chain", "Aegis Security", "Terra CleanTech", "Core Analytics",
    "Radiant Lighting", "Synthetix Genetics", "Velocity Mobility", "AeroVentures",
    "BlueShift Logistics", "Elysium Networks", "Kinetix Motors", "Optima Health",
    "Alpha Micro-Cap (Truncated)", "Beta Startup (Truncated)", "Gamma Ventures (Truncated)", "Delta Tech (Truncated)",
    "Shockwave Retail (Revenue Spike)", "Volatile Dynamics (Expense Spike)", "BurnRate Systems (Insolvent)", "CashDrain Inc (Insolvent)",
    "Chaos Labs (High Volatility)", "Turbulence Capital (High Volatility)", "Wildcard Corp (High Volatility)"
]

def generate_periods() -> List[str]:
    periods = []
    for year in range(2019, 2025):
        for q in range(1, 5):
            periods.append(f"{year}-Q{q}")
    return periods

def generate_company_dataset() -> pd.DataFrame:
    all_periods = generate_periods()
    total_companies = 55
    records = []

    # Assign category profiles
    categories = [
        "Growing", "Stable", "Declining", "Highly Leveraged",
        "Cash-Rich", "Cash-Constrained", "Highly Volatile"
    ]

    for i in range(total_companies):
        c_id = f"C{i+1:03d}"
        c_name = COMPANY_NAMES[i] if i < len(COMPANY_NAMES) else f"Company {c_id}"

        # Assign profile behavior
        if i < 10:
            category = "Growing"
        elif i < 20:
            category = "Stable"
        elif i < 28:
            category = "Declining"
        elif i < 34:
            category = "Highly Leveraged"
        elif i < 40:
            category = "Cash-Rich"
        elif i < 44:
            category = "Cash-Constrained"
        else:
            category = "Highly Volatile"

        # Edge cases & exception flags
        is_truncated = 44 <= i <= 47  # C045 - C048: Only 3 to 5 historical periods available
        is_spike = 48 <= i <= 49      # C049 - C050: Sudden extreme revenue/expense spike
        is_insolvent = 50 <= i <= 51  # C051 - C052: Severe cash burn exceeding liquidity
        is_wild_volatile = 52 <= i <= 54  # C053 - C055: Extreme chaotic volatility

        # Historical periods subset
        if is_truncated:
            company_periods = all_periods[:random.randint(3, 5)]
        else:
            company_periods = all_periods

        # Base financial values in Crores (Cr) / Millions
        if category == "Growing":
            base_rev = np.random.uniform(50.0, 120.0)
            rev_growth_rate = np.random.uniform(0.04, 0.08)
            cogs_ratio = np.random.uniform(0.40, 0.50)
            opex_ratio = np.random.uniform(0.20, 0.28)
            base_cash = np.random.uniform(25.0, 60.0)
            st_debt = np.random.uniform(5.0, 15.0)
            lt_debt = np.random.uniform(10.0, 30.0)
        elif category == "Stable":
            base_rev = np.random.uniform(80.0, 150.0)
            rev_growth_rate = np.random.uniform(0.005, 0.02)
            cogs_ratio = np.random.uniform(0.50, 0.60)
            opex_ratio = np.random.uniform(0.25, 0.32)
            base_cash = np.random.uniform(30.0, 70.0)
            st_debt = np.random.uniform(10.0, 20.0)
            lt_debt = np.random.uniform(20.0, 40.0)
        elif category == "Declining":
            base_rev = np.random.uniform(70.0, 130.0)
            rev_growth_rate = np.random.uniform(-0.04, -0.01)
            cogs_ratio = np.random.uniform(0.58, 0.68)
            opex_ratio = np.random.uniform(0.30, 0.38)
            base_cash = np.random.uniform(15.0, 40.0)
            st_debt = np.random.uniform(15.0, 30.0)
            lt_debt = np.random.uniform(30.0, 60.0)
        elif category == "Highly Leveraged":
            base_rev = np.random.uniform(100.0, 200.0)
            rev_growth_rate = np.random.uniform(0.01, 0.03)
            cogs_ratio = np.random.uniform(0.55, 0.65)
            opex_ratio = np.random.uniform(0.25, 0.32)
            base_cash = np.random.uniform(10.0, 25.0)
            st_debt = np.random.uniform(35.0, 70.0)
            lt_debt = np.random.uniform(80.0, 160.0)
        elif category == "Cash-Rich":
            base_rev = np.random.uniform(90.0, 180.0)
            rev_growth_rate = np.random.uniform(0.03, 0.06)
            cogs_ratio = np.random.uniform(0.35, 0.45)
            opex_ratio = np.random.uniform(0.18, 0.25)
            base_cash = np.random.uniform(90.0, 180.0)
            st_debt = np.random.uniform(0.0, 5.0)
            lt_debt = np.random.uniform(0.0, 10.0)
        elif category == "Cash-Constrained":
            base_rev = np.random.uniform(40.0, 90.0)
            rev_growth_rate = np.random.uniform(-0.01, 0.02)
            cogs_ratio = np.random.uniform(0.62, 0.72)
            opex_ratio = np.random.uniform(0.28, 0.35)
            base_cash = np.random.uniform(3.0, 10.0)
            st_debt = np.random.uniform(20.0, 40.0)
            lt_debt = np.random.uniform(25.0, 50.0)
        else:  # Highly Volatile
            base_rev = np.random.uniform(60.0, 140.0)
            rev_growth_rate = 0.01
            cogs_ratio = np.random.uniform(0.50, 0.60)
            opex_ratio = np.random.uniform(0.25, 0.35)
            base_cash = np.random.uniform(20.0, 50.0)
            st_debt = np.random.uniform(10.0, 25.0)
            lt_debt = np.random.uniform(15.0, 35.0)

        current_cash = base_cash
        current_rev = base_rev

        for p_idx, p_name in enumerate(company_periods):
            # Quarterly trend evolution
            seasonal_factor = 1.0 + 0.06 * np.sin(p_idx * np.pi / 2.0)
            
            if is_wild_volatile:
                noise = np.random.uniform(-0.45, 0.45)
            else:
                noise = np.random.normal(0.0, 0.03)

            rev = current_rev * (1.0 + rev_growth_rate + noise) * seasonal_factor
            
            # Inject sudden spike in period 19/20 for spike test cases
            if is_spike and p_idx >= len(company_periods) - 2:
                if i == 48:
                    rev *= 2.8  # 280% sudden spike
                else:
                    cogs_ratio = 0.95  # Sudden cost spike destroying margin

            cogs = rev * cogs_ratio * (1.0 + np.random.uniform(-0.02, 0.02))
            opex = rev * opex_ratio * (1.0 + np.random.uniform(-0.02, 0.02))
            
            # Additional cost injection for insolvent test cases
            if is_insolvent:
                opex *= 1.45  # Heavy cash burn

            gross_profit = rev - cogs
            operating_income = gross_profit - opex
            
            # Debt interest
            interest_expense = (st_debt * 0.08 + lt_debt * 0.06) / 4.0
            tax_expense = max(0.0, (operating_income - interest_expense) * 0.25)
            net_income = operating_income - interest_expense - tax_expense

            # Balance sheet components
            ar = rev * np.random.uniform(0.20, 0.30)
            inventory = cogs * np.random.uniform(0.15, 0.25)
            ap = cogs * np.random.uniform(0.18, 0.28)

            # Cash flow breakdown
            depreciation = opex * 0.12
            working_capital_change = np.random.uniform(-3.0, 3.0)
            ocf = net_income + depreciation + working_capital_change
            
            capex = max(1.0, rev * np.random.uniform(0.04, 0.09))
            icf = -capex + np.random.uniform(0.0, 1.5)
            
            # Financing CF (debt servicing & dividends)
            debt_change = np.random.uniform(-2.0, 2.0)
            fcf = debt_change - max(0.0, net_income * 0.15)
            
            net_cash_flow = ocf + icf + fcf
            
            # Update cash balance accounting relation
            current_cash = max(0.5, current_cash + net_cash_flow)

            records.append({
                "company_id": c_id,
                "company_name": c_name,
                "category": category,
                "period": p_name,
                "period_idx": p_idx + 1,
                "revenue": round(rev, 2),
                "cost_of_goods_sold": round(cogs, 2),
                "operating_expenses": round(opex, 2),
                "net_income": round(net_income, 2),
                "cash": round(current_cash, 2),
                "accounts_receivable": round(ar, 2),
                "inventory": round(inventory, 2),
                "accounts_payable": round(ap, 2),
                "short_term_debt": round(st_debt, 2),
                "long_term_debt": round(lt_debt, 2),
                "capital_expenditure": round(capex, 2),
                "operating_cash_flow": round(ocf, 2),
                "investing_cash_flow": round(icf, 2),
                "financing_cash_flow": round(fcf, 2)
            })

            # Update next period base revenue
            current_rev = rev / seasonal_factor

    df = pd.DataFrame(records)
    return df

def save_dataset() -> pd.DataFrame:
    df = generate_company_dataset()
    df.to_csv(CSV_FILE_PATH, index=False)
    print(f"Generated synthetic dataset with {len(df)} observations across {df['company_id'].nunique()} companies.")
    return df

if __name__ == "__main__":
    save_dataset()

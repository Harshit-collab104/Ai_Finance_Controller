import pandas as pd
from pathlib import Path
from backend.database import get_all_records, get_company_records
from backend.forecasting_engine import generate_company_forecasts
from backend.exception_engine import evaluate_forecast_confidence

def generate_forecasts_csv():
    df = get_all_records()
    companies = sorted(df['company_id'].unique())
    rows = []

    for c_id in companies:
        c_df = get_company_records(c_id)
        latest = c_df.iloc[-1]
        c_name = latest['company_name'] if latest['company_name'] and latest['company_name'] != 'CO' else f'Company {c_id}'
        
        fc = generate_company_forecasts(c_df, target_col='cash', horizon=3)
        conf = evaluate_forecast_confidence(c_df)
        
        preds = fc['predictions']
        cur_cash = round(float(latest['cash']), 2)
        fc_30d = round(float(preds[0]), 2)
        fc_60d = round(float(preds[1]), 2)
        fc_90d = round(float(preds[2]), 2)
        net_change = round(fc_90d - cur_cash, 2)
        
        rows.append({
            'Company Number': c_id,
            'Company Name': c_name,
            'Category': latest['category'],
            'Current Cash (Cr)': cur_cash,
            '30-Day Forecast (Cr)': fc_30d,
            '60-Day Forecast (Cr)': fc_60d,
            '90-Day Forecast (Cr)': fc_90d,
            'Expected Net Change (Cr)': net_change,
            'Selected Forecast Model': fc['selected_model'],
            'Resolution Status': conf['resolution_status']
        })

    out_df = pd.DataFrame(rows)
    
    out_dir = Path("data")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "forecasted_cash_positions.csv"
    out_df.to_csv(out_path, index=False)
    print(f"[SUCCESS] Forecasted cash CSV generated at {out_path.resolve()}")
    return out_df

if __name__ == "__main__":
    generate_forecasts_csv()

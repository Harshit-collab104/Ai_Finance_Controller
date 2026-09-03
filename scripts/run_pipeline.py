import json
import time
from backend.data_generator import save_dataset
from backend.database import init_db, get_all_records
from backend.evaluation_engine import run_out_of_time_evaluation
from backend.exception_engine import generate_portfolio_exception_report
from backend.config import BENCHMARK_JSON_PATH

def execute_pipeline():
    start_total = time.time()
    print("=== Step 1: Generating Synthetic Financial Dataset (55 Companies, 1200+ Observations) ===")
    df = save_dataset()

    print("\n=== Step 2: Initializing Database & Computing Financial Ratios ===")
    init_db(df)

    print("\n=== Step 3: Running Time-Based Out-of-Time Evaluation Pipeline (2019-2023 Train vs 2024 Test) ===")
    df_all = get_all_records()
    eval_results = run_out_of_time_evaluation(df_all, target_col="cash")

    print("\n=== Step 4: Generating Portfolio Exception & Finance-Ops Resolution Report ===")
    exception_report = generate_portfolio_exception_report(df_all)

    total_time_sec = round(time.time() - start_total, 3)
    avg_time_per_company_sec = round(total_time_sec / max(1, exception_report["total_companies"]), 4)

    combined_benchmark = {
        "execution_summary": {
            "total_processing_time_sec": total_time_sec,
            "avg_processing_time_per_company_sec": avg_time_per_company_sec
        },
        "evaluation_summary": eval_results,
        "exception_summary": exception_report
    }

    with open(BENCHMARK_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(combined_benchmark, f, indent=2)

    print(f"\n[SUCCESS] Pipeline Execution Complete! Saved to {BENCHMARK_JSON_PATH}")
    print("\nPortfolio Operational Results:")
    print(f"  Companies Processed:          {exception_report['total_companies']}")
    print(f"  Financial Observations:     {eval_results['total_observations'] * 6:.0f}")
    print(f"  Forecasts Generated:        {exception_report['total_forecasts_generated']}")
    print(f"  Resolved Forecasts:         {exception_report['resolved_forecasts']}")
    print(f"  Human Review Exceptions:    {exception_report['human_review_exceptions']}")
    print(f"  Resolution Rate:            {exception_report['resolution_rate_pct']}%")
    print(f"  Exception Rate:             {exception_report['exception_rate_pct']}%")
    print(f"  Total Processing Time:      {total_time_sec} s")
    print(f"  Avg Time per Company:       {avg_time_per_company_sec} s/company")
    print("\nModel Forecast Accuracy Metrics (Out-of-Time 2024 Actuals):")
    print(f"  Selected ML Model Cash MAPE: {eval_results['overall_ml_metrics']['mape']}%")
    print(f"  Selected ML Model Cash MAE:  {eval_results['overall_ml_metrics']['mae']} Cr")
    print(f"  Selected ML Model Cash RMSE: {eval_results['overall_ml_metrics']['rmse']} Cr")
    print(f"  Naive Baseline Cash MAPE:    {eval_results['overall_naive_metrics']['mape']}%")
    print(f"  Moving Avg Baseline Cash MAPE: {eval_results['overall_ma_metrics']['mape']}%")

if __name__ == "__main__":
    execute_pipeline()

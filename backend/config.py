import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

CSV_FILE_PATH = DATA_DIR / "financial_dataset.csv"
DB_FILE_PATH = DATA_DIR / "financials.db"
BENCHMARK_REPORT_PATH = BASE_DIR / "BENCHMARK_REPORT.md"
BENCHMARK_JSON_PATH = DATA_DIR / "benchmark_results.json"

# Evaluation Split Parameters
TOTAL_PERIODS = 24  # 2019-Q1 to 2024-Q4 (6 years)
TRAIN_PERIODS = 20  # 2019-Q1 to 2023-Q4 (5 years training split)
TEST_PERIODS = 4    # 2024-Q1 to 2024-Q4 (1 year out-of-time evaluation split)

# Company Categories
CATEGORIES = [
    "Growing",
    "Stable",
    "Declining",
    "Highly Leveraged",
    "Cash-Rich",
    "Cash-Constrained",
    "Highly Volatile"
]

# API Keys & LLM settings
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")

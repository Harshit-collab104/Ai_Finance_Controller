import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Any
from sklearn.linear_model import Ridge
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from statsmodels.tsa.api import Holt

class BaselineNaiveModel:
    def fit(self, X, y):
        self.last_val = y.iloc[-1] if hasattr(y, 'iloc') else y[-1]
        return self

    def predict(self, steps=1):
        return np.full(steps, self.last_val)

class MovingAverageModel:
    def __init__(self, window=3):
        self.window = window

    def fit(self, X, y):
        vals = y.values if hasattr(y, 'values') else np.array(y)
        self.ma_val = np.mean(vals[-self.window:]) if len(vals) >= self.window else np.mean(vals)
        return self

    def predict(self, steps=1):
        return np.full(steps, self.ma_val)

class HoltExponentialSmoothingModel:
    def fit(self, X, y):
        vals = y.values if hasattr(y, 'values') else np.array(y)
        try:
            if len(vals) >= 4:
                model = Holt(vals, initialization_method="estimated").fit(smoothing_level=0.4, smoothing_trend=0.2)
                self.model = model
                self.fallback_val = None
            else:
                self.model = None
                self.fallback_val = vals[-1]
        except Exception:
            self.model = None
            self.fallback_val = vals[-1]
        return self

    def predict(self, steps=1):
        if self.model is not None:
            try:
                preds = self.model.forecast(steps)
                return np.maximum(0.1, preds)
            except Exception:
                pass
        return np.full(steps, self.fallback_val if self.fallback_val is not None else 10.0)

class MLSequenceForecaster:
    def __init__(self, model_type="rf"):
        self.model_type = model_type
        if model_type == "linear":
            self.model = Ridge(alpha=1.0)
        elif model_type == "rf":
            self.model = RandomForestRegressor(n_estimators=30, max_depth=4, random_state=42)
        elif model_type == "gbm":
            self.model = GradientBoostingRegressor(n_estimators=30, max_depth=3, random_state=42)
        else:
            self.model = Ridge(alpha=1.0)

    def _create_features(self, df_comp: pd.DataFrame, target_col: str) -> Tuple[np.ndarray, np.ndarray]:
        vals = df_comp[target_col].values
        rev = df_comp["revenue"].values if "revenue" in df_comp else vals
        ocf = df_comp["operating_cash_flow"].values if "operating_cash_flow" in df_comp else vals

        X, y = [], []
        # Require lag 1 and lag 2
        for i in range(2, len(vals)):
            feat = [
                vals[i-1],                    # Target Lag 1
                vals[i-2],                    # Target Lag 2
                vals[i-1] - vals[i-2],        # Momentum
                np.mean(vals[max(0, i-3):i]), # 3-period Rolling Mean
                rev[i-1] if i < len(rev) else vals[i-1],
                ocf[i-1] if i < len(ocf) else vals[i-1],
                i                             # Time index
            ]
            X.append(feat)
            y.append(vals[i])
        return np.array(X), np.array(y)

    def fit(self, df_comp: pd.DataFrame, target_col: str):
        self.target_col = target_col
        self.df_comp = df_comp.copy()
        vals = df_comp[target_col].values
        self.last_vals = list(vals)

        X, y = self._create_features(df_comp, target_col)
        if len(X) >= 3:
            self.model.fit(X, y)
            self.is_fitted = True
        else:
            self.is_fitted = False
        return self

    def predict(self, steps=4) -> np.ndarray:
        if not self.is_fitted:
            return np.full(steps, self.last_vals[-1])

        predictions = []
        history = list(self.last_vals)
        rev_history = list(self.df_comp["revenue"].values) if "revenue" in self.df_comp else list(history)
        ocf_history = list(self.df_comp["operating_cash_flow"].values) if "operating_cash_flow" in self.df_comp else list(history)

        for step in range(steps):
            t_idx = len(history)
            feat = np.array([[
                history[-1],
                history[-2],
                history[-1] - history[-2],
                np.mean(history[-3:]),
                rev_history[-1],
                ocf_history[-1],
                t_idx
            ]])
            pred = self.model.predict(feat)[0]
            # Ensure non-negative bounds where appropriate
            pred = max(0.1, pred)
            predictions.append(pred)
            history.append(pred)
            rev_history.append(rev_history[-1])
            ocf_history.append(ocf_history[-1])

        return np.array(predictions)


def generate_company_forecasts(
    df_company: pd.DataFrame,
    target_col: str = "cash",
    horizon: int = 4
) -> Dict[str, Any]:
    """
    Fits baseline and ML models for a single company, evaluates candidate models
    on validation tail, selects the best model, and outputs multi-step forecasts.
    """
    df_c = df_company.sort_values("period_idx").reset_index(drop=True)

    if len(df_c) < 3:
        # Edge case: Short history
        last_val = df_c[target_col].iloc[-1]
        preds = np.full(horizon, last_val)
        return {
            "selected_model": "Naive Baseline (Short History)",
            "predictions": [round(float(p), 2) for p in preds],
            "validation_mape": 0.0,
            "confidence_score": 0.3
        }

    # Split for validation (last 2 available train periods)
    val_size = min(2, len(df_c) - 2)
    train_part = df_c.iloc[:-val_size] if val_size > 0 else df_c
    val_part = df_c.iloc[-val_size:] if val_size > 0 else df_c

    candidates = {
        "Naive Baseline": BaselineNaiveModel(),
        "Moving Average (3P)": MovingAverageModel(window=3),
        "Exponential Smoothing": HoltExponentialSmoothingModel(),
        "Ridge Linear Regression": MLSequenceForecaster(model_type="linear"),
        "Random Forest Regressor": MLSequenceForecaster(model_type="rf"),
        "Gradient Boosting Regressor": MLSequenceForecaster(model_type="gbm")
    }

    best_model_name = "Naive Baseline"
    best_mape = float("inf")
    best_model_obj = candidates["Naive Baseline"]

    for name, model in candidates.items():
        try:
            if isinstance(model, MLSequenceForecaster):
                model.fit(train_part, target_col)
                preds = model.predict(steps=val_size)
            else:
                model.fit(None, train_part[target_col])
                preds = model.predict(steps=val_size)

            actuals = val_part[target_col].values
            # Compute MAPE
            denom = np.maximum(0.1, np.abs(actuals))
            mape = np.mean(np.abs(preds - actuals) / denom) * 100.0

            if mape < best_mape:
                best_mape = mape
                best_model_name = name
                best_model_obj = model
        except Exception:
            continue

    # Re-fit winning model on full company history for final forward forecasting
    try:
        if isinstance(best_model_obj, MLSequenceForecaster):
            winner = MLSequenceForecaster(model_type=best_model_obj.model_type)
            winner.fit(df_c, target_col)
            final_preds = winner.predict(steps=horizon)
        elif isinstance(best_model_obj, HoltExponentialSmoothingModel):
            winner = HoltExponentialSmoothingModel()
            winner.fit(None, df_c[target_col])
            final_preds = winner.predict(steps=horizon)
        elif isinstance(best_model_obj, MovingAverageModel):
            winner = MovingAverageModel(window=3)
            winner.fit(None, df_c[target_col])
            final_preds = winner.predict(steps=horizon)
        else:
            winner = BaselineNaiveModel()
            winner.fit(None, df_c[target_col])
            final_preds = winner.predict(steps=horizon)
    except Exception:
        final_preds = np.full(horizon, df_c[target_col].iloc[-1])

    return {
        "selected_model": best_model_name,
        "predictions": [round(float(p), 2) for p in final_preds],
        "validation_mape": round(float(best_mape if best_mape != float("inf") else 0.0), 2)
    }

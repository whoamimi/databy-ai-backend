"""
core/agent/tools/statistical_methods.py

Mock tools for missing data analysis.

TODO:
- 9.9.2025: Refactor code to be less mentally taxing.
- 10.13.2025: update - what the actual
"""

import pandas as pd
import numpy as np
from typing import List, Optional, Dict, Any, Union, Tuple

from scipy.stats import chi2_contingency, chisquare, norm, pearsonr
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score
from sklearn.cluster import KMeans
import statsmodels.api as sm

from ..core._skeleton import Actuator

statistical_methods = Actuator('statistical_methods')

# ====================================================
# Helpers
# ====================================================

_NUMERIC_KINDS = set("buifc")  # bool, unsigned int, int, float, complex

def _ensure_numeric_df(df: pd.DataFrame, cols: Optional[List[str]] = None) -> pd.DataFrame:
    """Return a copy with only numeric columns (or assert if non-numeric present)."""
    use = df if cols is None else df[cols]
    nonnum = [c for c in use.columns if use[c].dtype.kind not in _NUMERIC_KINDS]
    if nonnum:
        raise ValueError(f"Non-numeric columns found: {nonnum}. Cast to numeric first.")
    return use.copy()

def _drop_na_align(X: pd.DataFrame, y: pd.Series) -> Tuple[pd.DataFrame, pd.Series]:
    """Drop rows with NA in X, align y."""
    X2 = X.dropna()
    y2 = y.loc[X2.index]
    return X2, y2

@statistical_methods
def littles_mcar_test(df: pd.DataFrame) -> pd.DataFrame:
    """
    Proxy for Little’s MCAR test by inspecting correlation among missingness indicators.
    Interpret: strong positive correlations between missing-indicator columns -> evidence against MCAR.
    NOTE: This requires all columns to be present
    """
    missing_matrix = df.isna().astype(int)
    corr = missing_matrix.corr()
    return corr

@statistical_methods
def chi_square_missingness(df: pd.DataFrame, target_col: str, group_col: str, alpha: float = 0.05) -> Dict[str, Any]:
    """
    Chi-square test of independence: missingness in target_col vs categories in group_col.
    """
    miss_indicator = df[target_col].isna().astype(int)
    contingency = pd.crosstab(miss_indicator, df[group_col])
    chi2, p, dof, expected = chi2_contingency(contingency)
    return {"chi2": chi2, "p_value": p, "dof": dof, "reject_null": bool(p < alpha), "expected": expected.tolist()}

@statistical_methods
def test_uniform_missing_multilabel(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Goodness-of-fit test: are missing counts uniform across columns?
    Uses one-sample chi-square (chisquare) comparing observed column-wise missing counts to a uniform expectation.
    """
    missing_counts = df.isna().sum()
    observed = missing_counts.values.astype(float)
    if observed.sum() == 0:
        return {"chi2": 0.0, "p_value": 1.0, "note": "No missing values in dataframe."}
    expected = np.full_like(observed, observed.mean(), dtype=float)
    chi2, p = chisquare(f_obs=observed, f_exp=expected)
    return {"chi2": float(chi2), "p_value": float(p), "observed": observed.tolist(), "expected": expected.tolist()}

# ====================================================
# Step 2: Test MAR (Dependence on Observed Data)
# ====================================================

@statistical_methods
def logistic_regression_missingness(df: pd.DataFrame, target_col: str, features: List[str]) -> Dict[str, Any]:
    """
    Logistic regression: indicator(target_col is missing) ~ features.
    Returns coefficients, intercept, and ROC-AUC on the training data as a quick separability diagnostic.
    """
    df = df.copy()
    df["__missing__"] = df[target_col].isna().astype(int)

    X = _ensure_numeric_df(df, features)
    y = df["__missing__"]
    X, y = _drop_na_align(X, y)

    if y.nunique() < 2:
        return {"error": "Missingness indicator has only one class; cannot fit logistic regression."}

    model = LogisticRegression(max_iter=2000, n_jobs=None)
    model.fit(X, y)
    proba = model.predict_proba(X)[:, 1]
    auc = roc_auc_score(y, proba)

    return {
        "coefficients": dict(zip(features, model.coef_[0].astype(float))),
        "intercept": float(model.intercept_[0]),
        "roc_auc_train": float(auc),
        "n_samples": int(len(y))
    }

@statistical_methods
def random_forest_importance(df: pd.DataFrame, target_col: str, features: List[str], n_estimators: int = 300, random_state: int = 42) -> Dict[str, Any]:
    """
    Random forest feature importance for predicting missingness.
    Higher importance -> stronger association between feature and missingness (evidence for MAR).
    """
    df = df.copy()
    df["__missing__"] = df[target_col].isna().astype(int)

    X = _ensure_numeric_df(df, features)
    y = df["__missing__"]
    X, y = _drop_na_align(X, y)

    if y.nunique() < 2:
        return {"error": "Missingness indicator has only one class; cannot fit random forest."}

    rf = RandomForestClassifier(n_estimators=n_estimators, random_state=random_state, n_jobs=-1)
    rf.fit(X, y)
    importances = dict(zip(features, rf.feature_importances_.astype(float)))

    proba = rf.predict_proba(X)[:, 1]
    auc = roc_auc_score(y, proba)

    return {"importances": importances, "roc_auc_train": float(auc), "n_samples": int(len(y))}

@statistical_methods
def clustering_missing_vs_nonmissing(df: pd.DataFrame, target_col: str, features: List[str], k: int = 2) -> Dict[str, Any]:
    """
    KMeans clustering on observed feature space as a rough structure check.
    Returns cluster centers and the distribution of missingness per cluster.
    """
    df = df.copy()
    df["__missing__"] = df[target_col].isna().astype(int)
    X = _ensure_numeric_df(df, features).dropna()

    if X.shape[0] < k:
        return {"error": f"Not enough rows ({X.shape[0]}) to form {k} clusters."}

    kmeans = KMeans(n_clusters=k, random_state=42, n_init="auto").fit(X)
    labels = pd.Series(kmeans.labels_, index=X.index, name="cluster")
    cluster_missing_rate = (
        pd.concat([labels, df.loc[X.index, "__missing__"]], axis=1)
        .groupby("cluster")["__missing__"].mean()
        .to_dict()
    )
    return {"cluster_centers": kmeans.cluster_centers_.tolist(), "missing_rate_by_cluster": cluster_missing_rate}

# ====================================================
# Step 3: Suspect MNAR (Dependence on Unobserved Values)
# ====================================================

@statistical_methods
def heckman_selection(y: pd.Series, X: pd.DataFrame, Z: pd.DataFrame) -> Dict[str, Any]:
    """
    Heckman two-step selection correction.
    y: outcome (may contain NaN for unobserved)
    X: regressors for outcome equation (observed only when y observed)
    Z: instruments/exogenous vars for selection equation (observed for all rows)
    """
    # Step 1: Probit selection model (1 if y observed, else 0)
    observed = (~y.isna()).astype(int)
    Zc = sm.add_constant(Z, has_constant="add")
    probit_res = sm.Probit(observed, Zc).fit(disp=False)

    # Inverse Mills Ratio (IMR) for observed rows
    linpred = np.asarray(Zc @ probit_res.params)
    cdf = norm.cdf(linpred)
    pdf = norm.pdf(linpred)
    # Avoid division by zero
    cdf = np.clip(cdf, 1e-9, 1 - 1e-9)
    imr = pdf / cdf  # for observed=1

    # Step 2: Outcome equation with IMR
    obs_idx = observed.astype(bool)
    Xc = sm.add_constant(X.loc[obs_idx], has_constant="add")
    X_imr = np.column_stack([Xc.values, imr[obs_idx]])
    ols_res = sm.OLS(y.loc[obs_idx].values, X_imr).fit()

    # Friendly names
    ols_param_names = list(Xc.columns) + ["IMR"]

    return {
        "selection_summary": probit_res.summary().as_text(),
        "outcome_params": dict(zip(ols_param_names, ols_res.params.astype(float))),
        "outcome_bse": dict(zip(ols_param_names, ols_res.bse.astype(float))),
        "outcome_rsquared": float(ols_res.rsquared),
        "outcome_nobs": int(ols_res.nobs)
    }

@statistical_methods
def sensitivity_analysis(
    df: pd.DataFrame,
    target_col: str,
    compare_with: Optional[str] = None,
    strategy: str = "extremes",
    shift: Union[int, float] = 10.0
) -> Dict[str, Any]:
    """
    Sensitivity analysis for MNAR suspicion.
    - 'extremes': fill missing with below-min and above-max (min - shift, max + shift)
    - 'bounds': fill with {min, max}
    - If compare_with provided (numeric), also report Pearson r with that column under each fill.
    """
    if target_col not in df.columns:
        return {"error": f"{target_col} not in dataframe."}

    base = df[target_col]
    if base.dtype.kind not in _NUMERIC_KINDS:
        raise ValueError(f"{target_col} must be numeric for sensitivity analysis.")

    mn, mx = base.min(skipna=True), base.max(skipna=True)

    def _metrics(series: pd.Series) -> Dict[str, Any]:
        out = {
            "mean": float(series.mean()),
            "median": float(series.median()),
            "std": float(series.std(ddof=1)),
        }
        if compare_with and compare_with in df.columns and df[compare_with].dtype.kind in _NUMERIC_KINDS:
            aligned = pd.concat([series, df[compare_with]], axis=1).dropna()
            if len(aligned) > 1:
                r, p = pearsonr(aligned.iloc[:, 0], aligned.iloc[:, 1])
                out["pearson_r_with_compare"] = float(r)
                out["pearson_p_with_compare"] = float(p)
        return out

    results: Dict[str, Any] = {}

    if strategy == "extremes":
        low_fill = base.fillna(mn - shift)
        high_fill = base.fillna(mx + shift)
        results["low_fill_extreme"] = _metrics(low_fill)
        results["high_fill_extreme"] = _metrics(high_fill)
    elif strategy == "bounds":
        min_fill = base.fillna(mn)
        max_fill = base.fillna(mx)
        results["min_fill"] = _metrics(min_fill)
        results["max_fill"] = _metrics(max_fill)
    else:
        return {"error": f"Unknown strategy '{strategy}'. Use 'extremes' or 'bounds'."}

    # Baseline (drop NA)
    baseline = base.dropna()
    if len(baseline) > 0:
        results["baseline_observed"] = _metrics(baseline)

    return results


class StatisticalMethods:
    def __init__(self, data: pd.DataFrame):
        self.data = data



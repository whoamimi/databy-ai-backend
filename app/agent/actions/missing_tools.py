"""
app.agent.actions.missing_tools

Actionable tools to handle missing values.
"""

import pandas as pd
import numpy as np
from ..core._skeleton import ActionSpace


missing_val_resolver = ActionSpace('missing_val_resolver')

# === Individual strategy tools ===
@missing_val_resolver
def drop_missing(df: pd.DataFrame, target_col: str) -> pd.DataFrame:
    """Drop rows all missing values relative to the column."""

    if target_col not in df.columns:
        raise ValueError

    return df.dropna()

@missing_val_resolver
def fill_with_mean(df: pd.DataFrame) -> pd.DataFrame:
    """Fill numeric columns with their mean."""
    return df.fillna(df.mean(numeric_only=True))

@missing_val_resolver
def fill_with_median(df: pd.DataFrame) -> pd.DataFrame:
    """Fill numeric columns with their median."""
    return df.fillna(df.median(numeric_only=True))

@missing_val_resolver
def fill_with_mode(df: pd.DataFrame) -> pd.DataFrame:
    """Fill each column with its mode."""
    for col in df.columns:
        mode_val = df[col].mode(dropna=True)
        if not mode_val.empty:
            df[col] = df[col].fillna(mode_val[0])
    return df

@missing_val_resolver
def fill_with_value(df: pd.DataFrame, fill_value=None) -> pd.DataFrame:
    """Fill missing values using a constant or inferred defaults."""
    df = df.copy()
    for col in df.columns:
        if fill_value is not None:
            df[col] = df[col].fillna(fill_value)
        else:
            if pd.api.types.is_numeric_dtype(df[col]):
                df[col] = df[col].fillna(0)
            else:
                mode_val = df[col].mode(dropna=True)
                if not mode_val.empty:
                    df[col] = df[col].fillna(mode_val[0])
                else:
                    df[col] = df[col].fillna("Unknown")
    return df

# === Unified handler ===

def handle_missing_values(df: pd.DataFrame, strategy: str = "fill", fill_value=None) -> pd.DataFrame:
    """
    Central tool that routes missing-value handling to subtools.
    """
    df = df.copy()
    strategy = strategy.lower()

    if strategy == "drop":
        return drop_missing(df)
    elif strategy == "mean":
        return fill_with_mean(df)
    elif strategy == "median":
        return fill_with_median(df)
    elif strategy == "mode":
        return fill_with_mode(df)
    elif strategy == "fill":
        return fill_with_value(df, fill_value)
    else:
        raise ValueError(f"Unknown strategy '{strategy}'")
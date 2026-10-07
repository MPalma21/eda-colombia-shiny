"""Servicio analítico no reactivo para EDA.

Encapsula transformaciones, agregaciones estadísticas y pruebas formales
para que sean verificables con pytest de forma independiente a la UI.
"""
from typing import Literal
import numpy as np
import pandas as pd
from scipy import stats


def classify_columns(df: pd.DataFrame) -> tuple[list[str], list[str], list[str]]:
    """Clasifica las columnas en numéricas, fechas y categóricas/texto."""
    if df.empty:
        return [], [], []
    num_cols = df.select_dtypes(include=["number"]).columns.tolist()
    date_cols = df.select_dtypes(include=["datetime", "datetimetz"]).columns.tolist()
    cat_cols = df.select_dtypes(include=["object", "category", "string"]).columns.tolist()
    return num_cols, date_cols, cat_cols


def compute_dataset_overview(df: pd.DataFrame) -> dict[str, float | int]:
    """Calcula métricas globales de integridad del dataset."""
    if df.empty:
        return {"rows": 0, "cols": 0, "num_cols": 0, "cat_cols": 0, "date_cols": 0, "missing_pct": 0.0}
    
    n_rows, n_cols = df.shape
    num_cols, date_cols, cat_cols = classify_columns(df)
    total_cells = n_rows * n_cols
    missing_cells = int(df.isnull().sum().sum())
    missing_pct = round((missing_cells / total_cells * 100), 2) if total_cells > 0 else 0.0

    return {
        "rows": n_rows,
        "cols": n_cols,
        "num_cols": len(num_cols),
        "cat_cols": len(cat_cols),
        "date_cols": len(date_cols),
        "missing_cells": missing_cells,
        "missing_pct": missing_pct,
    }


def compute_column_diagnostics(df: pd.DataFrame) -> pd.DataFrame:
    """Genera diagnóstico por columna (tipo detectado, recuento nulo y porcentaje)."""
    if df.empty:
        return pd.DataFrame()

    num_cols, date_cols, _ = classify_columns(df)
    diagnostics = []

    for col in df.columns:
        if col in num_cols:
            col_type = "Numérico"
        elif col in date_cols:
            col_type = "Fecha / Hora"
        else:
            col_type = "Categórico / Texto"

        null_count = int(df[col].isnull().sum())
        null_pct = round((null_count / len(df)) * 100, 2)
        unique_count = int(df[col].nunique(dropna=True))

        diagnostics.append({
            "Columna": col,
            "Tipo": col_type,
            "Valores Únicos": unique_count,
            "Faltantes": null_count,
            "% Faltante": null_pct,
        })

    return pd.DataFrame(diagnostics)


def compute_correlation_matrix(
    df: pd.DataFrame,
    method: Literal["pearson", "spearman", "kendall"] = "pearson"
) -> pd.DataFrame:
    """Calcula la matriz de correlación numérica."""
    num_cols, _, _ = classify_columns(df)
    if len(num_cols) < 2:
        return pd.DataFrame()
    return df[num_cols].corr(method=method).round(3)


def sample_scatter_rows(df: pd.DataFrame, columns: list[str], max_rows: int = 1500) -> pd.DataFrame:
    """Limita solo la visualización, con selección reproducible de filas completas."""
    rows = df[columns].dropna()
    if len(rows) > max_rows:
        rows = rows.sample(n=max_rows, random_state=42)
    return rows


def suggest_time_aggregation(column: str) -> str:
    """Propone suma solo para magnitudes aditivas identificables por nombre."""
    name = column.lower()
    non_additive_terms = ("tasa", "precio", "porcentaje", "promedio", "valor", "índice", "indice", "trm")
    if any(term in name for term in non_additive_terms):
        return "Promedio"
    additive_terms = ("cantidad", "conteo", "total", "monto", "importe", "volumen", "ventas", "unidades")
    return "Suma" if any(term in name for term in additive_terms) else "Promedio"


def compute_normality_tests(df: pd.DataFrame, max_cols: int = 10, sample_size: int = 5000) -> pd.DataFrame:
    """Ejecuta la prueba de normalidad Shapiro-Wilk sobre variables numéricas."""
    num_cols, _, _ = classify_columns(df)
    results = []

    for col in num_cols[:max_cols]:
        series = df[col].dropna()
        if len(series) < 3:
            continue
        sample = series.sample(min(len(series), sample_size), random_state=42)
        try:
            stat, p_val = stats.shapiro(sample)
            results.append({
                "Variable": col,
                "Estadístico W": round(float(stat), 4),
                "p-valor": round(float(p_val), 4),
                "Resultado (α=0.05)": "No se rechaza normalidad" if p_val >= 0.05 else "Se rechaza normalidad",
            })
        except Exception:
            continue

    return pd.DataFrame(results)


def compute_categorical_summary(df: pd.DataFrame, max_cols: int = 10) -> pd.DataFrame:
    """Genera tabla de frecuencias y modas para variables categóricas."""
    _, _, cat_cols = classify_columns(df)
    rows = []

    for col in cat_cols[:max_cols]:
        series = df[col].dropna()
        n_unique = int(series.nunique())
        if not series.empty:
            mode_val = str(series.mode().iloc[0])[:35]
            freq = int(series.value_counts().iloc[0])
            freq_pct = round((freq / len(df)) * 100, 1)
        else:
            mode_val, freq, freq_pct = "-", 0, 0.0

        rows.append({
            "Variable": col,
            "Valores Únicos": n_unique,
            "Moda": mode_val,
            "Frecuencia Moda": freq,
            "% Dominante": freq_pct,
        })

    return pd.DataFrame(rows)

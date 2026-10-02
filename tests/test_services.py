"""Pruebas unitarias para la lógica de negocio y servicios de análisis.

Validan el comportamiento de forma independiente sin sobrecarga de sesión web.
"""
import pytest
import pandas as pd
import numpy as np
from services.api_service import extract_resource_id
from services.stats_service import (
    classify_columns,
    compute_dataset_overview,
    compute_column_diagnostics,
    compute_correlation_matrix,
    compute_normality_tests,
    compute_categorical_summary
)


def test_extract_resource_id_from_url():
    """Valida la extracción correcta del identificador Socrata."""
    url_1 = "https://www.datos.gov.co/resource/gt2j-8ykr.json"
    url_2 = "https://www.datos.gov.co/d/gt2j-8ykr"
    raw_id = "gt2j-8ykr"

    assert extract_resource_id(url_1) == "gt2j-8ykr"
    assert extract_resource_id(url_2) == "gt2j-8ykr"
    assert extract_resource_id(raw_id) == "gt2j-8ykr"
    assert extract_resource_id("") == ""


def test_classify_columns_mixed_dataframe():
    """Valida la detección correcta de tipos numéricos, fechas y textos."""
    df = pd.DataFrame({
        "edad": [25, 30, 45, 60],
        "fecha": pd.to_datetime(["2023-01-01", "2023-01-02", "2023-01-03", "2023-01-04"]),
        "ciudad": ["Bogotá", "Medellín", "Cali", "Barranquilla"]
    })

    nums, dates, cats = classify_columns(df)
    assert nums == ["edad"]
    assert dates == ["fecha"]
    assert cats == ["ciudad"]


def test_compute_dataset_overview():
    """Valida el cálculo de métricas globales y porcentaje de nulos."""
    df = pd.DataFrame({
        "val_a": [1.0, 2.0, np.nan, 4.0],
        "val_b": ["a", "b", "c", None]
    })

    overview = compute_dataset_overview(df)
    assert overview["rows"] == 4
    assert overview["cols"] == 2
    assert overview["missing_cells"] == 2
    assert overview["missing_pct"] == 25.0


def test_compute_correlation_matrix():
    """Valida la computación de la matriz de correlación numérica."""
    df = pd.DataFrame({
        "x": [1, 2, 3, 4, 5],
        "y": [2, 4, 6, 8, 10],  # Correlación perfecta = 1.0
        "cat": ["A", "B", "C", "D", "E"]
    })

    corr = compute_correlation_matrix(df, method="pearson")
    assert not corr.empty
    assert corr.loc["x", "y"] == 1.0


def test_compute_normality_tests():
    """Valida la ejecución de la prueba Shapiro-Wilk sobre datos conocidos."""
    np.random.seed(42)
    normal_data = np.random.normal(loc=0, scale=1, size=100)
    df = pd.DataFrame({"normal_var": normal_data})

    res = compute_normality_tests(df)
    assert not res.empty
    assert "Estadístico W" in res.columns
    assert "p-valor" in res.columns


def test_compute_categorical_summary():
    """Valida el resumen de modas y frecuencias en columnas categóricas."""
    df = pd.DataFrame({
        "departamento": ["Antioquia", "Antioquia", "Cundinamarca", "Valle"]
    })

    cat_summary = compute_categorical_summary(df)
    assert not cat_summary.empty
    assert cat_summary.iloc[0]["Moda"] == "Antioquia"
    assert cat_summary.iloc[0]["Frecuencia Moda"] == 2

"""Pruebas unitarias para el servicio economico y econometrico.

Valida:
- Curva de Lorenz y Coeficiente de Gini
- Indice Herfindahl-Hirschman (HHI) y ratios de concentracion
- Estimacion econometrica (Log-Log / Elasticidad y MCO)
- Indice Base 100 y variaciones
- Brechas economicas entre grupos
"""
import pytest
import numpy as np
import pandas as pd
from services.economic_service import (
    compute_gini_coefficient,
    interpret_gini,
    compute_lorenz_curve,
    compute_hhi,
    estimate_econometric_model,
    compute_base_100_series,
    compute_economic_gaps,
    estimate_econometric_by_groups
)


def test_gini_coefficient_extremes():
    """Valida los casos limite de perfecta igualdad y perfecta desigualdad."""
    # Perfecta igualdad: Gini = 0.0
    equal_series = pd.Series([100.0, 100.0, 100.0, 100.0])
    assert compute_gini_coefficient(equal_series) == 0.0
    
    # Alta desigualdad
    unequal_series = pd.Series([0.0, 0.0, 0.0, 1000.0])
    gini_val = compute_gini_coefficient(unequal_series)
    assert gini_val > 0.70
    
    # Interpretacion
    assert interpret_gini(0.25)["nivel"] == "Baja Desigualdad"
    assert interpret_gini(0.55)["nivel"] == "Alta Desigualdad"


def test_lorenz_curve_structure():
    """Valida los puntos ordenados de la curva de Lorenz."""
    series = pd.Series([10, 20, 30, 40, 100])
    pop, vals, gini = compute_lorenz_curve(series, sample_points=50)
    
    assert len(pop) == len(vals)
    assert pop[0] == 0.0 and vals[0] == 0.0
    assert np.isclose(pop[-1], 1.0) and np.isclose(vals[-1], 1.0)
    # Todos los puntos de la curva de Lorenz estan en o debajo de la diagonal (L(p) <= p)
    assert np.all(vals <= pop + 1e-5)
    assert 0.0 < gini < 1.0


def test_hhi_market_concentration():
    """Valida el cálculo del HHI y ratios de concentracion."""
    # Monopolio puro: 1 participante = 10,000 HHI
    mono_df = pd.DataFrame({"empresa": ["Empresa A"] * 10, "monto": [100] * 10})
    res_mono = compute_hhi(mono_df, "empresa", "monto")
    assert res_mono["hhi"] == 10000.0
    assert "Alta Concentracion" in res_mono["clasificacion"]

    # Mercado competitivo: 10 participantes con cuotas iguales (10% cada uno -> HHI = 10 * 100 = 1000)
    comp_df = pd.DataFrame({
        "empresa": [f"Emp_{i}" for i in range(10)],
        "monto": [100] * 10
    })
    res_comp = compute_hhi(comp_df, "empresa", "monto")
    assert np.isclose(res_comp["hhi"], 1000.0, atol=1.0)
    assert "No Concentrado" in res_comp["clasificacion"]
    assert res_comp["cr4"] == 40.0


def test_estimate_econometric_elasticity_log_log():
    """Valida la estimación de elasticidad mediante modelo Log-Log."""
    # Y = 5 * X^2 -> ln(Y) = ln(5) + 2 * ln(X) -> Elasticidad exacta = 2.0
    x_vals = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], dtype=float)
    y_vals = 5.0 * (x_vals ** 2.0)
    df = pd.DataFrame({"ingreso": x_vals, "gasto": y_vals})
    
    reg = estimate_econometric_model(df, y_col="gasto", x_col="ingreso", model_type="log_log")
    assert reg["valido"] is True
    assert np.isclose(reg["beta_1"], 2.0, atol=1e-3)
    assert np.isclose(reg["r2"], 1.0, atol=1e-3)
    assert "Elastica" in reg["interpretacion"]


def test_estimate_econometric_linear_ols():
    """Valida la estimacion de MCO lineal estandar."""
    x_vals = np.array([10, 20, 30, 40, 50], dtype=float)
    y_vals = 100.0 + 3.5 * x_vals
    df = pd.DataFrame({"x": x_vals, "y": y_vals})
    
    reg = estimate_econometric_model(df, y_col="y", x_col="x", model_type="ols_linear")
    assert reg["valido"] is True
    assert np.isclose(reg["beta_1"], 3.5, atol=1e-3)
    assert np.isclose(reg["beta_0"], 100.0, atol=1e-3)
    assert np.isclose(reg["r2"], 1.0, atol=1e-3)


def test_compute_base_100_series():
    """Valida la creacion de series con indice 100 en fecha base."""
    df = pd.DataFrame({
        "fecha": pd.to_datetime(["2023-01-01", "2023-02-01", "2023-03-01"]),
        "precio": [50.0, 75.0, 100.0]
    })
    res = compute_base_100_series(df, "fecha", "precio", agg="mean")
    assert not res.empty
    assert res.iloc[0]["Indice_Base_100"] == 100.0
    assert res.iloc[1]["Indice_Base_100"] == 150.0
    assert res.iloc[2]["Indice_Base_100"] == 200.0
    assert res.iloc[1]["Variacion_Pct"] == 50.0


def test_compute_economic_gaps():
    """Valida el cálculo de brechas entre grupos economicos."""
    df = pd.DataFrame({
        "estrato": ["Estrato 6", "Estrato 6", "Estrato 1", "Estrato 1"],
        "puntaje": [400.0, 420.0, 200.0, 210.0]
    })
    gaps = compute_economic_gaps(df, "estrato", "puntaje")
    assert gaps["valido"] is True
    assert gaps["grupo_lider"] == "Estrato 6"
    assert gaps["grupo_rezagado"] == "Estrato 1"
    assert np.isclose(gaps["ratio_brecha"], 2.0, atol=0.1)


def test_estimate_econometric_by_groups():
    """Valida la estimación de modelos por subgrupos o departamentos."""
    np.random.seed(42)
    n = 40
    df = pd.DataFrame({
        "departamento": ["Bogota"] * n + ["Antioquia"] * n,
        "x": np.random.uniform(10, 50, 2 * n),
        "y": np.random.uniform(20, 100, 2 * n)
    })
    res_df = estimate_econometric_by_groups(df, y_col="y", x_col="x", group_col="departamento", min_obs=15)
    assert not res_df.empty
    assert len(res_df) == 2
    assert "Subgrupo / Departamento" in res_df.columns
    assert "Elasticidad (β₁)" in res_df.columns
    assert "R²" in res_df.columns
    assert "p-valor" in res_df.columns

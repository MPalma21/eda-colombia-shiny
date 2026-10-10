"""Servicio de calculos analiticos y econométricos.

Implementa herramientas de teoría económica pura para análisis de datos abiertos:
- Curva de Lorenz y Coeficiente de Gini (desigualdad).
- Indice Herfindahl-Hirschman (HHI) y ratios CR4/CR8 (concentracion de mercado).
- Estimacion econometrica de MCO y Elasticidades (modelos Log-Log, Semi-Log y Lineal).
- Normalizacion de series temporales a Base 100 y variaciones porcentuales.
- Analisis de brechas economicas y territoriales.
"""
from typing import Literal
import numpy as np
import pandas as pd
from scipy import stats


def compute_gini_coefficient(series: pd.Series) -> float:
    """Calcula el Coeficiente de Gini para una distribucion numerica no negativa.
    
    Formula:
    Gini = sum((2*i - n - 1) * y_(i)) / (n * sum(y_(i)))
    donde y_(i) son los valores ordenados ascendentemente.
    """
    clean_vals = series.dropna().to_numpy(dtype=float)
    clean_vals = clean_vals[clean_vals >= 0]
    
    if len(clean_vals) == 0 or np.sum(clean_vals) == 0:
        return 0.0
    
    clean_vals.sort()
    n = len(clean_vals)
    idx = np.arange(1, n + 1)
    gini = float(np.sum((2 * idx - n - 1) * clean_vals) / (n * np.sum(clean_vals)))
    return round(max(0.0, min(1.0, gini)), 4)


def interpret_gini(gini: float) -> dict[str, str]:
    """Proporciona una clasificacion estandar para el Coeficiente de Gini."""
    if gini < 0.30:
        return {
            "nivel": "Baja Desigualdad",
            "badge_class": "badge-status-ok",
            "descripcion": "Distribucion relativamente equitativa de los valores analizados."
        }
    elif gini < 0.45:
        return {
            "nivel": "Desigualdad Moderada",
            "badge_class": "badge-category",
            "descripcion": "Concentracion moderada comun en economias de ingreso medio."
        }
    elif gini < 0.60:
        return {
            "nivel": "Alta Desigualdad",
            "badge_class": "kpi-missing-mid",
            "descripcion": "Fuerte concentracion en los deciles superiores de la distribucion."
        }
    else:
        return {
            "nivel": "Extrema Desigualdad",
            "badge_class": "kpi-missing-high",
            "descripcion": "Alta concentracion donde una minoria acapara la casi totalidad del valor."
        }


def compute_lorenz_curve(series: pd.Series, sample_points: int = 100) -> tuple[np.ndarray, np.ndarray, float]:
    """Genera los puntos de la Curva de Lorenz (proporcion acumulada de poblacion vs valor).
    
    Retorna:
    (poblacion_acumulada, valor_acumulado, gini)
    """
    clean_vals = series.dropna().to_numpy(dtype=float)
    clean_vals = clean_vals[clean_vals >= 0]
    
    if len(clean_vals) == 0 or np.sum(clean_vals) == 0:
        x_base = np.linspace(0, 1, sample_points)
        return x_base, x_base, 0.0
    
    clean_vals.sort()
    total_val = np.sum(clean_vals)
    cum_vals = np.cumsum(clean_vals) / total_val
    n = len(clean_vals)
    cum_pop = np.arange(1, n + 1) / n
    
    # Agregar punto de origen (0, 0)
    p_pop = np.insert(cum_pop, 0, 0.0)
    p_val = np.insert(cum_vals, 0, 0.0)
    
    # Submuestreo para graficos responsivos eficientes si n es muy grande
    if len(p_pop) > sample_points:
        indices = np.linspace(0, len(p_pop) - 1, sample_points, dtype=int)
        p_pop = p_pop[indices]
        p_val = p_val[indices]
        
    gini = compute_gini_coefficient(series)
    return p_pop, p_val, gini


def compute_hhi(
    df: pd.DataFrame,
    group_col: str,
    val_col: str | None = None
) -> dict:
    """Calcula el Indice Herfindahl-Hirschman (HHI) y ratios de concentracion CR4 y CR8.
    
    - Si val_col es None, calcula concentracion por volumen/frecuencia de registros.
    - Si val_col se especifica, calcula concentracion por monto o valor acumulado.
    """
    if df.empty or group_col not in df.columns:
        return {
            "hhi": 0.0,
            "cr4": 0.0,
            "cr8": 0.0,
            "clasificacion": "Sin datos",
            "badge_class": "badge-category",
            "top_df": pd.DataFrame()
        }
    
    if val_col and val_col in df.columns:
        valid_df = df[[group_col, val_col]].dropna()
        shares = valid_df.groupby(group_col)[val_col].sum()
    else:
        valid_df = df[[group_col]].dropna()
        shares = valid_df[group_col].value_counts()
    
    total = shares.sum()
    if total <= 0:
        return {
            "hhi": 0.0,
            "cr4": 0.0,
            "cr8": 0.0,
            "clasificacion": "Sin datos",
            "badge_class": "badge-category",
            "top_df": pd.DataFrame()
        }
    
    pct_shares = (shares / total * 100).sort_values(ascending=False)
    
    # HHI = suma de cuotas de mercado al cuadrado
    hhi = float(np.sum(pct_shares.to_numpy() ** 2))
    
    cr4 = float(pct_shares.iloc[:4].sum()) if len(pct_shares) >= 4 else float(pct_shares.sum())
    cr8 = float(pct_shares.iloc[:8].sum()) if len(pct_shares) >= 8 else float(pct_shares.sum())
    
    # Clasificacion DOJ / FTC / Superintendencia de Industria y Comercio (SIC)
    if hhi < 1500:
        clasificacion = "Mercado No Concentrado / Competitivo"
        badge_class = "badge-status-ok"
        desc = "Alta competencia y pluralidad de participantes."
    elif hhi <= 2500:
        clasificacion = "Concentracion Moderada"
        badge_class = "kpi-missing-mid"
        desc = "Estructura oligopolica moderada con actores dominantes."
    else:
        clasificacion = "Alta Concentracion / Mercado Concentrado"
        badge_class = "kpi-missing-high"
        desc = "Dominancia pronunciada de pocos actores en el mercado o contratacion."
        
    top_table = pct_shares.head(10).reset_index()
    top_table.columns = ["Actor / Categoria", "Cuota (%)"]
    top_table["Cuota (%)"] = top_table["Cuota (%)"].round(2)
    top_table["Cuota Acumulada (%)"] = top_table["Cuota (%)"].cumsum().round(2)
    
    return {
        "hhi": round(hhi, 1),
        "cr4": round(cr4, 1),
        "cr8": round(cr8, 1),
        "clasificacion": clasificacion,
        "badge_class": badge_class,
        "descripcion": desc,
        "top_df": top_table,
        "total_actores": len(shares)
    }


def estimate_econometric_model(
    df: pd.DataFrame,
    y_col: str,
    x_col: str,
    model_type: Literal["log_log", "ols_linear", "log_lin"] = "log_log"
) -> dict:
    """Estima especificaciones econometricas univariadas e interpreta elasticidades.
    
    Modelos:
    - log_log: ln(Y) = b0 + b1 * ln(X) -> b1 es la Elasticidad directa (%dY / %dX).
    - ols_linear: Y = b0 + b1 * X -> b1 es la pendiente marginal directa (dY / dX).
    - log_lin: ln(Y) = b0 + b1 * X -> b1 es la semielasticidad (%dY / dX).
    """
    if df.empty or y_col not in df.columns or x_col not in df.columns or y_col == x_col:
        return {"valido": False, "error": "Variables no validas o insuficientes."}
    
    sub = df[[y_col, x_col]].dropna()
    
    # Para transformaciones logarítmicas se filtran valores <= 0
    if model_type in ("log_log", "log_lin"):
        sub = sub[sub[y_col] > 0]
    if model_type == "log_log":
        sub = sub[sub[x_col] > 0]
        
    if len(sub) < 5:
        return {"valido": False, "error": "Registros positivos insuficientes para estimacion econometrica (min 5)."}
    
    raw_x = sub[x_col].to_numpy(dtype=float)
    raw_y = sub[y_col].to_numpy(dtype=float)
    
    if model_type == "log_log":
        reg_x = np.log(raw_x)
        reg_y = np.log(raw_y)
        x_label = f"ln({x_col})"
        y_label = f"ln({y_col})"
    elif model_type == "log_lin":
        reg_x = raw_x
        reg_y = np.log(raw_y)
        x_label = x_col
        y_label = f"ln({y_col})"
    else:
        reg_x = raw_x
        reg_y = raw_y
        x_label = x_col
        y_label = y_col
        
    # Validar varianza no nula
    if np.std(reg_x) == 0 or np.std(reg_y) == 0:
        return {"valido": False, "error": "Varianza nula en alguna de las variables transformadas."}
        
    reg = stats.linregress(reg_x, reg_y)
    
    beta_1 = float(reg.slope)
    beta_0 = float(reg.intercept)
    r2 = float(reg.rvalue ** 2)
    p_val = float(reg.pvalue)
    stderr = float(reg.stderr)
    n_obs = len(reg_x)
    
    # R2 ajustado: 1 - [(1 - R2)*(n - 1) / (n - k - 1)] con k=1
    r2_adj = 1.0 - ((1.0 - r2) * (n_obs - 1) / max(1, n_obs - 2))
    
    # Significancia estadística
    if p_val < 0.001:
        sig_stars = "*** (p < 0.001)"
    elif p_val < 0.01:
        sig_stars = "** (p < 0.01)"
    elif p_val < 0.05:
        sig_stars = "* (p < 0.05)"
    elif p_val < 0.10:
        sig_stars = "· (p < 0.10)"
    else:
        sig_stars = "No significativo (p >= 0.10)"
        
    # Interpretacion economica en lenguaje natural
    if model_type == "log_log":
        elast_val = abs(beta_1)
        tipo_elast = "Elastica (|e| > 1)" if elast_val > 1.0 else ("Unitaria (|e| = 1)" if round(elast_val, 2) == 1.0 else "Inelastica (|e| < 1)")
        sentido = "positivo (directo)" if beta_1 > 0 else "negativo (inverso)"
        interpretacion = (
            f"Elasticidad estimada: {beta_1:+.3f} ({tipo_elast}). "
            f"Un incremento del 1% en '{x_col}' se asocia en promedio con una variacion del "
            f"{beta_1:+.3f}% en '{y_col}' con efecto {sentido}."
        )
    elif model_type == "log_lin":
        interpretacion = (
            f"Semielasticidad estimada: {beta_1:+.4f}. "
            f"Un aumento de 1 unidad en '{x_col}' se asocia aproximadamente con una variacion "
            f"porcentual del {(beta_1 * 100):+.2f}% en '{y_col}'."
        )
    else:
        interpretacion = (
            f"Efecto marginal MCO: {beta_1:+.4f}. "
            f"Un cambio unitario en '{x_col}' produce un cambio esperado de "
            f"{beta_1:+.4f} unidades en '{y_col}'."
        )
        
    # Predicciones para graficar recta de regresion
    x_sort = np.linspace(np.min(reg_x), np.max(reg_x), 100)
    y_pred = beta_0 + beta_1 * x_sort
    
    return {
        "valido": True,
        "model_type": model_type,
        "n_obs": n_obs,
        "beta_1": round(beta_1, 4),
        "beta_0": round(beta_0, 4),
        "r2": round(r2, 4),
        "r2_adj": round(max(0.0, r2_adj), 4),
        "p_val": round(p_val, 5),
        "stderr": round(stderr, 4),
        "t_stat": round(beta_1 / stderr, 3) if stderr > 0 else 0.0,
        "sig_stars": sig_stars,
        "interpretacion": interpretacion,
        "x_label": x_label,
        "y_label": y_label,
        "scatter_x": reg_x.tolist()[:1500],
        "scatter_y": reg_y.tolist()[:1500],
        "line_x": x_sort.tolist(),
        "line_y": y_pred.tolist(),
    }


def compute_base_100_series(
    df: pd.DataFrame,
    date_col: str,
    val_col: str,
    agg: Literal["mean", "sum"] = "mean"
) -> pd.DataFrame:
    """Calcula series temporales normalizadas con indice Base 100 y variacion porcentual."""
    if df.empty or date_col not in df.columns or val_col not in df.columns:
        return pd.DataFrame()
    
    sub = df[[date_col, val_col]].dropna().copy()
    sub[date_col] = pd.to_datetime(sub[date_col], errors="coerce")
    sub = sub.dropna()
    
    if sub.empty:
        return pd.DataFrame()
    
    grouped = sub.groupby(date_col)[val_col].agg(agg).sort_index().reset_index()
    if grouped.empty:
        return pd.DataFrame()
    
    base_val = grouped[val_col].iloc[0]
    if base_val != 0:
        grouped["Indice_Base_100"] = ((grouped[val_col] / base_val) * 100).round(2)
    else:
        grouped["Indice_Base_100"] = 100.0
        
    grouped["Variacion_Pct"] = (grouped[val_col].pct_change() * 100).round(2)
    grouped[val_col] = grouped[val_col].round(2)
    return grouped


def compute_economic_gaps(
    df: pd.DataFrame,
    cat_col: str,
    val_col: str,
    top_n: int = 15
) -> dict:
    """Calcula disparidades y brechas economicas entre grupos (e.g. departamentos, estratos)."""
    if df.empty or cat_col not in df.columns or val_col not in df.columns:
        return {"valido": False}
        
    sub = df[[cat_col, val_col]].dropna()
    if sub.empty:
        return {"valido": False}
        
    grouped = sub.groupby(cat_col)[val_col].agg(
        Media="mean",
        Mediana="median",
        Total="sum",
        Observaciones="count"
    ).reset_index()
    
    grouped = grouped[grouped["Observaciones"] >= 2].sort_values(by="Media", ascending=False)
    
    if len(grouped) < 2:
        return {"valido": False}
        
    top_group = grouped.iloc[0]
    bottom_group = grouped.iloc[-1]
    
    max_val = float(top_group["Media"])
    min_val = float(bottom_group["Media"])
    ratio_brecha = round(max_val / min_val, 2) if min_val > 0 else 0.0
    dif_absoluta = round(max_val - min_val, 2)
    
    # Redondeo para tabla
    display_df = grouped.head(top_n).copy()
    display_df["Media"] = display_df["Media"].round(2)
    display_df["Mediana"] = display_df["Mediana"].round(2)
    display_df["Total"] = display_df["Total"].round(2)
    
    return {
        "valido": True,
        "grupo_lider": str(top_group[cat_col]),
        "valor_lider": max_val,
        "grupo_rezagado": str(bottom_group[cat_col]),
        "valor_rezagado": min_val,
        "ratio_brecha": ratio_brecha,
        "dif_absoluta": dif_absoluta,
        "tabla": display_df
    }

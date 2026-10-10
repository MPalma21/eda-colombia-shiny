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


def estimate_econometric_by_groups(
    df: pd.DataFrame,
    y_col: str,
    x_col: str,
    group_col: str,
    model_type: Literal["log_log", "ols_linear", "log_lin"] = "log_log",
    min_obs: int = 15,
    top_n_groups: int = 25
) -> pd.DataFrame:
    """Estima especificaciones econometricas para cada subgrupo o departamento.
    
    Permite evaluar heterogeneidad territorial o sectorial en elasticidades y pendientes.
    """
    if df.empty or y_col not in df.columns or x_col not in df.columns or group_col not in df.columns:
        return pd.DataFrame()
        
    group_counts = df[group_col].dropna().value_counts()
    eligible_groups = group_counts[group_counts >= min_obs].head(top_n_groups).index.tolist()
    
    if not eligible_groups:
        return pd.DataFrame()
        
    results = []
    param_col = "Elasticidad (β₁)" if model_type == "log_log" else "Coeficiente (β₁)"
    
    for g_val in eligible_groups:
        sub_df = df[df[group_col] == g_val]
        res = estimate_econometric_model(sub_df, y_col, x_col, model_type=model_type)
        if res.get("valido", False):
            results.append({
                "Subgrupo / Departamento": str(g_val),
                param_col: res["beta_1"],
                "Error Estándar (SE)": res["stderr"],
                "Estadístico t": res["t_stat"],
                "p-valor": res["p_val"],
                "Significancia": res["sig_stars"],
                "R²": res["r2"],
                "Muestra (N)": res["n_obs"]
            })
            
    if not results:
        return pd.DataFrame()
        
    res_df = pd.DataFrame(results).sort_values(by=param_col, ascending=False)
    return res_df


def format_cop_currency(amount: float) -> str:
    """Formatea montos en pesos colombianos (COP) a escalas legibles ejecutivas."""
    if amount is None or np.isnan(amount) or amount == 0:
        return "$ 0 COP"
    abs_amt = abs(amount)
    sign = "-" if amount < 0 else ""
    if abs_amt >= 1e12:
        return f"{sign}$ {abs_amt / 1e12:.2f} Billones COP"
    elif abs_amt >= 1e9:
        return f"{sign}$ {abs_amt / 1e9:.2f} Mil Millones COP"
    elif abs_amt >= 1e6:
        return f"{sign}$ {abs_amt / 1e6:.2f} Millones COP"
    else:
        return f"{sign}$ {abs_amt:,.0f} COP"


def find_procurement_columns(
    df: pd.DataFrame,
    dept_col: str | None = None,
    val_col: str | None = None,
    prov_col: str | None = None,
    mod_col: str | None = None
) -> tuple[str | None, str | None, str | None, str | None]:
    """Detecta automaticamente o valida las columnas requeridas para analisis de contratacion."""
    if df.empty:
        return None, None, None, None
    
    cols = list(df.columns)
    cols_lower = {c.lower(): c for c in cols}
    
    # 1. Departamento / Territorio
    final_dept = dept_col if dept_col and dept_col in df.columns else None
    if not final_dept:
        dept_candidates = ["departamento", "departamento_entidad", "departamento_ejecucion", "depto", "dpto", "region", "municipio"]
        for cand in dept_candidates:
            if cand in cols_lower:
                final_dept = cols_lower[cand]
                break
        if not final_dept:
            for c_low, orig in cols_lower.items():
                if "depa" in c_low or "region" in c_low:
                    final_dept = orig
                    break

    # 2. Valor / Monto contractual
    final_val = val_col if val_col and val_col in df.columns else None
    if not final_val:
        val_candidates = ["valor_del_contrato", "cuantia_del_contrato", "valor_contrato", "cuantia", "valor", "monto", "presupuesto"]
        for cand in val_candidates:
            if cand in cols_lower:
                final_val = cols_lower[cand]
                break
        if not final_val:
            for c_low, orig in cols_lower.items():
                if any(k in c_low for k in ("valor", "monto", "cuantia", "precio")) and pd.api.types.is_numeric_dtype(df[orig]):
                    final_val = orig
                    break

    # 3. Proveedor / Contratista
    final_prov = prov_col if prov_col and prov_col in df.columns else None
    if not final_prov:
        prov_candidates = ["proveedor_adjudicado", "nombre_del_proveedor", "nom_razon_social_contratista", "proveedor", "contratista", "adjudicatario"]
        for cand in prov_candidates:
            if cand in cols_lower:
                final_prov = cols_lower[cand]
                break
        if not final_prov:
            for c_low, orig in cols_lower.items():
                if any(k in c_low for k in ("provee", "contrat", "adjudica")):
                    final_prov = orig
                    break

    # 4. Modalidad de Contratacion
    final_mod = mod_col if mod_col and mod_col in df.columns else None
    if not final_mod:
        mod_candidates = ["modalidad_de_contratacion", "modalidad", "tipo_de_proceso", "tipo_proceso", "tipo_contratacion"]
        for cand in mod_candidates:
            if cand in cols_lower:
                final_mod = cols_lower[cand]
                break
        if not final_mod:
            for c_low, orig in cols_lower.items():
                if "modalid" in c_low or "tipo_proceso" in c_low:
                    final_mod = orig
                    break

    return final_dept, final_val, final_prov, final_mod


def compute_procurement_risk_matrix(
    df: pd.DataFrame,
    dept_col: str | None = None,
    val_col: str | None = None,
    prov_col: str | None = None,
    mod_col: str | None = None,
    min_contracts_per_dept: int = 1
) -> pd.DataFrame:
    """Calcula el semaforo y matriz de riesgo territorial de contratacion publica por departamento.
    
    Variables analizadas:
    - HHI de contratistas (concentracion de adjudicaciones)
    - Cuota CR4 (% acaparado por los 4 mayores contratistas)
    - % de contratacion directa (en monto y volumen)
    - Score compuesto de riesgo (0 - 100) y clasificacion semaforica (🔴, 🟡, 🟢)
    """
    if df.empty:
        return pd.DataFrame()
        
    dept_c, val_c, prov_c, mod_c = find_procurement_columns(df, dept_col, val_col, prov_col, mod_col)
    
    if not dept_c:
        return pd.DataFrame()
        
    records = []
    grouped = df.groupby(dept_c)
    
    for dept_name, group in grouped:
        n_contracts = len(group)
        if n_contracts < min_contracts_per_dept:
            continue
            
        dept_str = str(dept_name).strip()
        if not dept_str or dept_str.lower() in ("nan", "none", "null", ""):
            continue
            
        # 1. Monto total
        if val_c and val_c in group.columns and pd.api.types.is_numeric_dtype(group[val_c]):
            clean_vals = group[val_c].dropna()
            monto_total = float(clean_vals[clean_vals >= 0].sum())
        else:
            monto_total = 0.0
            
        # 2. Contratacion directa
        pct_directa_cant = 0.0
        pct_directa_monto = 0.0
        if mod_c and mod_c in group.columns:
            mod_series = group[mod_c].astype(str).str.lower()
            direct_mask = mod_series.str.contains("direct|urgencia|especial|sin postulante|sin concurso", regex=True, na=False)
            direct_count = int(direct_mask.sum())
            pct_directa_cant = round((direct_count / n_contracts) * 100.0, 1) if n_contracts > 0 else 0.0
            
            if val_c and val_c in group.columns and monto_total > 0:
                direct_monto = float(group.loc[direct_mask, val_c].dropna().sum())
                pct_directa_monto = round((direct_monto / monto_total) * 100.0, 1)
            else:
                pct_directa_monto = pct_directa_cant
        
        # 3. Concentracion HHI y contratistas
        hhi = 0.0
        cr4 = 0.0
        top_contratista = "Sin datos"
        top_cuota = 0.0
        n_proveedores = 0
        
        if prov_c and prov_c in group.columns:
            if val_c and val_c in group.columns and monto_total > 0:
                valid_g = group[[prov_c, val_c]].dropna()
                prov_totals = valid_g.groupby(prov_c)[val_c].sum()
                tot = prov_totals.sum()
                prov_shares = (prov_totals / tot * 100.0).sort_values(ascending=False) if tot > 0 else pd.Series(dtype=float)
            else:
                prov_shares = (group[prov_c].dropna().value_counts(normalize=True) * 100.0)
                
            n_proveedores = len(prov_shares)
            if not prov_shares.empty:
                hhi = float(np.sum(prov_shares.to_numpy() ** 2))
                cr4 = float(prov_shares.iloc[:4].sum()) if len(prov_shares) >= 4 else float(prov_shares.sum())
                top_contratista = str(prov_shares.index[0])
                top_cuota = float(prov_shares.iloc[0])
                
        hhi = round(hhi, 1)
        cr4 = round(cr4, 1)
        top_cuota = round(top_cuota, 1)
        
        # 4. Clasificacion de Semaforo y Score (0 a 100)
        hhi_score = min(100.0, hhi / 100.0)
        score_riesgo = round(0.5 * hhi_score + 0.5 * pct_directa_monto, 1)
        
        if hhi > 2500 or pct_directa_monto > 65.0:
            nivel = "Alto Riesgo (Crítico)"
            badge_icon = "🔴"
            badge_class = "badge-risk-high"
        elif (1500 <= hhi <= 2500) or (35.0 <= pct_directa_monto <= 65.0):
            nivel = "Riesgo Moderado"
            badge_icon = "🟡"
            badge_class = "badge-risk-mid"
        else:
            nivel = "Bajo Riesgo (Competitivo)"
            badge_icon = "🟢"
            badge_class = "badge-risk-low"
            
        records.append({
            "departamento": dept_str,
            "n_contratos": n_contracts,
            "monto_total": monto_total,
            "pct_directa_monto": pct_directa_monto,
            "pct_directa_cant": pct_directa_cant,
            "hhi": hhi,
            "cr4": cr4,
            "top_contratista": top_contratista,
            "top_cuota": top_cuota,
            "n_proveedores": n_proveedores,
            "score_riesgo": score_riesgo,
            "nivel_riesgo": nivel,
            "badge_icon": badge_icon,
            "badge_class": badge_class,
        })
        
    if not records:
        return pd.DataFrame()
        
    res_df = pd.DataFrame(records).sort_values(by="score_riesgo", ascending=False).reset_index(drop=True)
    return res_df


def get_procurement_risk_summary(risk_df: pd.DataFrame) -> dict:
    """Calcula indicadores agregados nacionales para los Value Boxes de riesgo."""
    if risk_df.empty:
        return {
            "valido": False,
            "total_contratos": 0,
            "monto_total": 0.0,
            "n_departamentos": 0,
            "criticos": 0,
            "moderados": 0,
            "competitivos": 0,
            "pct_directa_promedio": 0.0,
            "hhi_promedio": 0.0,
            "depto_mayor_riesgo": "N/A",
            "score_mayor_riesgo": 0.0
        }
        
    total_contratos = int(risk_df["n_contratos"].sum())
    monto_total = float(risk_df["monto_total"].sum())
    n_deptos = len(risk_df)
    
    criticos = int((risk_df["nivel_riesgo"] == "Alto Riesgo (Crítico)").sum())
    moderados = int((risk_df["nivel_riesgo"] == "Riesgo Moderado").sum())
    competitivos = int((risk_df["nivel_riesgo"] == "Bajo Riesgo (Competitivo)").sum())
    
    if monto_total > 0:
        weights = risk_df["monto_total"] / monto_total
        pct_directa_ponderada = float(np.sum(risk_df["pct_directa_monto"] * weights))
        hhi_ponderado = float(np.sum(risk_df["hhi"] * weights))
    else:
        pct_directa_ponderada = float(risk_df["pct_directa_monto"].mean())
        hhi_ponderado = float(risk_df["hhi"].mean())
        
    top_critico = risk_df.iloc[0]
    
    return {
        "valido": True,
        "total_contratos": total_contratos,
        "monto_total": monto_total,
        "n_departamentos": n_deptos,
        "criticos": criticos,
        "moderados": moderados,
        "competitivos": competitivos,
        "pct_directa_promedio": round(pct_directa_ponderada, 1),
        "hhi_promedio": round(hhi_ponderado, 1),
        "depto_mayor_riesgo": str(top_critico["departamento"]),
        "score_mayor_riesgo": float(top_critico["score_riesgo"])
    }


def simulate_policy_procurement(
    base_monto: float,
    base_direct_pct: float,
    base_hhi: float,
    reduction_direct_pct: float,
    new_competitors_pct: float,
    saving_benchmark_pct: float = 12.5
) -> dict:
    """Calcula escenario contrafactual de politica publica para contratacion.
    
    Parametros:
    - base_monto: Monto total presupuestado en COP.
    - base_direct_pct: % actual de contratacion directa.
    - base_hhi: Indice HHI actual de concentracion de contratistas.
    - reduction_direct_pct: Reduccion porcentual de la contratacion directa (0 - 80%).
    - new_competitors_pct: Aumento porcentual de concurrencia/oferentes (0 - 100%).
    - saving_benchmark_pct: Rendimiento de ahorro fiscal por licitacion abierta (benchmark OCDE 12.5%).
    """
    base_monto = max(0.0, float(base_monto))
    base_direct_pct = max(0.0, min(100.0, float(base_direct_pct)))
    base_hhi = max(0.0, min(10000.0, float(base_hhi)))
    
    r_direct = max(0.0, min(80.0, float(reduction_direct_pct))) / 100.0
    r_comp = max(0.0, min(100.0, float(new_competitors_pct))) / 100.0
    
    # 1. Contratacion directa contrafactual
    nuevo_direct_pct = max(0.0, base_direct_pct * (1.0 - r_direct))
    monto_directo_base = base_monto * (base_direct_pct / 100.0)
    monto_trasladado_competencia = monto_directo_base * r_direct
    ahorro_fiscal_estimado = monto_trasladado_competencia * (saving_benchmark_pct / 100.0)
    
    # 2. Desconcentracion HHI
    factor_desconcentracion = 1.0 - (0.45 * r_direct + 0.55 * r_comp * 0.70)
    nuevo_hhi = max(100.0, base_hhi * max(0.20, factor_desconcentracion))
    delta_hhi = nuevo_hhi - base_hhi
    pct_reduccion_hhi = (abs(delta_hhi) / base_hhi * 100.0) if base_hhi > 0 else 0.0
    
    # 3. Clasificaciones de riesgo
    def _clasificar(hhi_val, dir_pct):
        if hhi_val > 2500 or dir_pct > 65.0:
            return "Alto Riesgo (Crítico)", "🔴", "badge-risk-high"
        elif (1500 <= hhi_val <= 2500) or (35.0 <= dir_pct <= 65.0):
            return "Riesgo Moderado", "🟡", "badge-risk-mid"
        else:
            return "Bajo Riesgo (Competitivo)", "🟢", "badge-risk-low"
            
    nivel_base, icon_base, class_base = _clasificar(base_hhi, base_direct_pct)
    nivel_nuevo, icon_nuevo, class_nuevo = _clasificar(nuevo_hhi, nuevo_direct_pct)
    
    nuevos_oferentes_est = int(np.round(15 * r_comp + 10 * r_direct))
    
    return {
        "base_monto": base_monto,
        "base_direct_pct": round(base_direct_pct, 1),
        "nuevo_direct_pct": round(nuevo_direct_pct, 1),
        "monto_directo_base": monto_directo_base,
        "monto_trasladado": monto_trasladado_competencia,
        "ahorro_fiscal_estimado": ahorro_fiscal_estimado,
        "base_hhi": round(base_hhi, 1),
        "nuevo_hhi": round(nuevo_hhi, 1),
        "delta_hhi": round(delta_hhi, 1),
        "pct_reduccion_hhi": round(pct_reduccion_hhi, 1),
        "nivel_base": nivel_base,
        "icon_base": icon_base,
        "class_base": class_base,
        "nivel_nuevo": nivel_nuevo,
        "icon_nuevo": icon_nuevo,
        "class_nuevo": class_nuevo,
        "mejora_categoria": nivel_base != nivel_nuevo and (nivel_base == "Alto Riesgo (Crítico)" or nivel_nuevo == "Bajo Riesgo (Competitivo)"),
        "nuevos_oferentes_est": nuevos_oferentes_est,
    }


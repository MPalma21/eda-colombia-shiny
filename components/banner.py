"""Banner compartido con contexto del recurso."""
import pandas as pd
from shiny import ui


def _dataset_scope(meta: dict, n_rows: int) -> str:
    total = meta.get("_eda_total_rows")
    query = meta.get("_eda_query", "")
    loaded = meta.get("_eda_loaded_rows", n_rows)
    if isinstance(total, int):
        scope = (
            f"Análisis de {n_rows:,} de {total:,} registros"
            if n_rows < total else f"Análisis de los {n_rows:,} registros disponibles"
        )
    else:
        scope = f"Análisis de {n_rows:,} registros cargados; total del recurso no disponible"
    if loaded != n_rows:
        scope += f" · {loaded:,} filas descargadas"
    if query:
        scope += f" · Filtro de origen: {query}"
    if meta.get("_eda_period_label"):
        scope += f" · Período: {meta['_eda_period_label']}"
    if isinstance(total, int) and loaded < total:
        if meta.get("_eda_fetch_mode") == "spread":
            scope += ". Descarga en bloques distribuidos por ID; no es una muestra aleatoria simple."
        else:
            scope += ". La descarga contiene las primeras filas por ID."
    if meta.get("_eda_sample_active"):
        scope += " Muestra aleatoria reproducible solo entre las filas descargadas."
    return scope


def render_context_banner(df: pd.DataFrame, meta: dict) -> ui.Tag:
    """Resume el recurso dentro de la cabecera global."""
    has_source = not df.empty or meta.get("_eda_loaded_rows", 0) > 0
    if has_source:
        title = meta.get("name") or "Conjunto de datos activo"
        summary = f"{title} · {len(df):,} registros · {len(df.columns)} variables"
        scope = _dataset_scope(meta, len(df))
        status = "Activo" if not df.empty else "Sin filas en la selección"
    else:
        summary = "Explora los datos abiertos de Colombia"
        scope = "Elige una colección o ingresa el ID de un recurso para comenzar."
        status = "Sin datos activos"

    return ui.div(
        ui.span(status, class_="navbar-context-status"),
        ui.span(summary, class_="navbar-context-summary"),
        ui.span(scope, class_="navbar-context-scope"),
        class_="navbar-context",
        aria_label="Contexto del análisis",
    )

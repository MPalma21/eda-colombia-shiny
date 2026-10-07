"""Banner compartido con contexto del recurso y créditos del proyecto."""
import pandas as pd
from shiny import ui


def _author_credits() -> ui.Tag:
    return ui.div(
        ui.div(
            ui.span("DESARROLLADO POR", class_="context-banner-author-label"),
            ui.strong("Miguelangel Palma", class_="context-banner-author-name"),
            class_="context-banner-author-name-group",
        ),
        ui.div(
            ui.tags.a("LinkedIn", href="https://www.linkedin.com/in/miguelangelpr", target="_blank", rel="noopener noreferrer"),
            ui.tags.a("GitHub", href="https://github.com/MPalma21", target="_blank", rel="noopener noreferrer"),
            ui.tags.a("Posit Connect", href="https://connect.posit.cloud", target="_blank", rel="noopener noreferrer"),
            class_="context-banner-author-links",
        ),
        class_="context-banner-author",
    )


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
    """Muestra el estado de la sesión en todas las vistas del análisis."""
    has_source = not df.empty or meta.get("_eda_loaded_rows", 0) > 0
    if has_source:
        title = meta.get("name") or "Conjunto de datos activo"
        author_info = meta.get("tableAuthor") or {}
        publisher = (
            author_info.get("displayName") or "Entidad no especificada"
            if isinstance(author_info, dict) else "Entidad no especificada"
        )
        eyebrow = "CONJUNTO DE DATOS ACTIVO"
        description = f"Publicado por {publisher}"
        status = "Datos cargados" if not df.empty else "Sin filas en la selección"
        context = ui.div(
            ui.div(
                ui.span(f"{len(df):,} registros", class_="badge badge-context"),
                ui.span(f"{len(df.columns)} variables", class_="badge badge-context"),
                class_="context-banner-metrics",
            ),
            ui.p(_dataset_scope(meta, len(df)), class_="context-banner-scope"),
        )
    else:
        title = "Explora los datos abiertos de Colombia"
        eyebrow = "PLATAFORMA DE ANÁLISIS EXPLORATORIO"
        description = "Carga un recurso de datos.gov.co para conocer su calidad, estadísticas y tendencias."
        status = "Sin datos activos"
        context = ui.p(
            "Elige una colección en el panel lateral o ingresa el ID de un recurso para comenzar.",
            class_="context-banner-scope",
        )

    return ui.tags.section(
        ui.div(
            ui.div(
                ui.span(eyebrow, class_="context-banner-eyebrow"),
                ui.h1(title, class_="context-banner-title"),
                ui.p(description, class_="context-banner-subtitle"),
                class_="context-banner-heading",
            ),
            ui.span(status, class_="context-banner-status"),
            class_="context-banner-top",
        ),
        context,
        _author_credits(),
        class_=f"context-banner mb-3{' context-banner-idle' if not has_source else ''}",
        aria_label="Contexto del análisis",
    )

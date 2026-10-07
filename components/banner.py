"""Componente reutilizable de Context Banner segun estandares Posit.

Proporciona contexto inmediato sobre el dataset activo, entidad publicadora,
recuento de registros y estado de la sesion analitica.
"""
from shiny import ui
import pandas as pd

SVG_CLOCK = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" class="text-slate-500 me-2 flex-shrink-0"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><circle cx="12" cy="16" r="1" fill="currentColor"/></svg>"""

SVG_CHECK = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" class="text-success me-2 flex-shrink-0"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>"""


def render_context_banner(df: pd.DataFrame, meta: dict) -> ui.Tag:
    """Genera una barra contextual sobria ubicada en la parte superior del espacio analitico."""
    if df.empty:
        return ui.div(
            ui.div(
                ui.div(
                    ui.HTML(SVG_CLOCK),
                    ui.span("Sesion en espera de datos:", class_="fw-bold text-slate-700 me-2"),
                    ui.span(
                        "Seleccione un recurso en el panel lateral y haga clic en 'Cargar y Analizar Datos' para inicializar el analisis.",
                        class_="text-slate-600"
                    ),
                    class_="d-flex align-items-center flex-wrap"
                ),
                class_="d-flex justify-content-between align-items-center flex-wrap"
            ),
            class_="context-banner context-banner-idle mb-3"
        )

    title = meta.get("name", "Conjunto de datos activo")
    author_info = meta.get("tableAuthor", {})
    author = author_info.get("displayName", "Entidad no especificada") if isinstance(author_info, dict) else "Entidad no especificada"
    n_rows, n_cols = df.shape

    return ui.div(
        ui.div(
            ui.div(
                ui.div(
                    ui.HTML(SVG_CHECK),
                    ui.span(title, class_="context-banner-title me-3"),
                    class_="d-flex align-items-center"
                ),
                ui.span(f"Entidad emisora: {author}", class_="context-banner-subtitle"),
                class_="d-flex flex-column flex-md-row align-items-md-center mb-2 mb-md-0"
            ),
            ui.div(
                ui.span(f"{n_rows:,} registros", class_="badge badge-context me-2"),
                ui.span(f"{n_cols} variables", class_="badge badge-context me-2"),
                ui.span("API datos.gov.co activa", class_="badge badge-status-ok"),
                class_="d-flex align-items-center flex-wrap"
            ),
            class_="d-flex justify-content-between align-items-center flex-wrap gap-2"
        ),
        class_="context-banner mb-3"
    )

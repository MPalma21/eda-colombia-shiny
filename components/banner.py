"""Componente reutilizable de Context Banner segun estandares Posit.

Proporciona contexto inmediato sobre el dataset activo, entidad publicadora,
recuento de registros y estado de la sesion analitica.
"""
from shiny import ui
import pandas as pd

SVG_CLOCK = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" class="text-slate-400 me-2 flex-shrink-0"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><circle cx="12" cy="16" r="1" fill="currentColor"/></svg>"""

SVG_CHECK = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2.5" class="text-emerald-600 me-2 flex-shrink-0"><polyline points="20 6 9 17 4 12"/></svg>"""


def render_context_banner(df: pd.DataFrame, meta: dict) -> ui.Tag:
    """Genera una barra contextual sobria ubicada en la parte superior del espacio analitico."""
    if df.empty:
        return ui.div(
            ui.div(
                ui.div(
                    ui.HTML(SVG_CLOCK),
                    ui.span("Estado de la sesion:", class_="fw-bold text-slate-700 me-2"),
                    ui.span(
                        "Sin datos activos. Elija un recurso en el panel lateral y presione 'Cargar y Analizar Datos'.",
                        class_="text-slate-500"
                    ),
                    class_="d-flex align-items-center flex-wrap"
                ),
                class_="d-flex justify-content-between align-items-center"
            ),
            class_="context-banner context-banner-idle mb-3"
        )

    title = meta.get("name", "Conjunto de datos activo")
    author_info = meta.get("tableAuthor", {})
    author = author_info.get("displayName", "Entidad no especificada") if isinstance(author_info, dict) else "Entidad no especificada"
    n_rows, n_cols = df.shape

    return ui.div(
        ui.div(
            # Bloque izquierdo: Identificacion del dataset
            ui.div(
                ui.div(
                    ui.HTML(SVG_CHECK),
                    ui.span(title, class_="context-banner-title me-2 text-truncate", style="max-width: 520px;"),
                    class_="d-flex align-items-center flex-wrap"
                ),
                ui.span(f"Entidad emisora: {author}", class_="context-banner-subtitle text-slate-500 mt-1 mt-md-0"),
                class_="d-flex flex-column flex-md-row align-items-md-center flex-wrap gap-md-2"
            ),
            # Bloque derecho: Metadatos rapidos de recuento
            ui.div(
                ui.span(f"{n_rows:,} registros", class_="badge badge-context"),
                ui.span(f"{n_cols} variables", class_="badge badge-context"),
                ui.span("API Socrata OK", class_="badge badge-status-ok"),
                class_="d-flex align-items-center flex-wrap gap-2 mt-2 mt-lg-0"
            ),
            class_="d-flex justify-content-between align-items-center flex-wrap gap-2"
        ),
        class_="context-banner mb-3"
    )

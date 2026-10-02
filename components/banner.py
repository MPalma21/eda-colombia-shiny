"""Componente reutilizable de Context Banner segun estandares Posit.

Proporciona contexto inmediato sobre el dataset activo, entidad publicadora,
recuento de registros y estado de la sesion analitica.
"""
from shiny import ui
import pandas as pd


def render_context_banner(df: pd.DataFrame, meta: dict) -> ui.Tag:
    """Genera una barra contextual sobria ubicada en la parte superior del espacio analitico."""
    if df.empty:
        return ui.div(
            ui.div(
                ui.span("Estado de la sesion: ", class_="fw-bold text-secondary me-2"),
                ui.span("Sin datos activos. Seleccione un recurso en el panel lateral y presione 'Cargar Dataset'."),
                class_="context-banner-text"
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
                ui.span(title, class_="context-banner-title me-3"),
                ui.span(f"Publicado por: {author}", class_="context-banner-subtitle me-3"),
                class_="d-flex flex-wrap align-items-center"
            ),
            ui.div(
                ui.span(f"{n_rows:,} registros", class_="badge badge-context me-2"),
                ui.span(f"{n_cols} variables", class_="badge badge-context me-2"),
                ui.span("Conexion API Socrata OK", class_="badge badge-status-ok"),
                class_="d-flex align-items-center mt-1 mt-md-0"
            ),
            class_="d-flex justify-content-between align-items-center flex-wrap"
        ),
        class_="context-banner mb-3"
    )

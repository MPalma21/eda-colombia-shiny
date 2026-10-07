"""Modulo de resumen y vision global del dataset."""
from shiny import module, ui, render, reactive
import pandas as pd
import plotly.express as px
from services.stats_service import compute_dataset_overview, compute_column_diagnostics
from components.banner import render_context_banner

# Iconos vectoriales compactos para Value Boxes
SVG_ICON_ROWS = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="28" height="28" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="16" rx="2"/><line x1="3" y1="9" x2="21" y2="9"/><line x1="3" y1="14" x2="21" y2="14"/></svg>"""

SVG_ICON_COLS = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="28" height="28" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="16" rx="2"/><line x1="9" y1="4" x2="9" y2="20"/><line x1="15" y1="4" x2="15" y2="20"/></svg>"""

SVG_ICON_NUM = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="28" height="28" fill="none" stroke="currentColor" stroke-width="2"><line x1="4" y1="19" x2="20" y2="19"/><polyline points="4 15 9 9 14 13 20 5"/></svg>"""

SVG_ICON_MISSING = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="28" height="28" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><circle cx="12" cy="16" r="1" fill="currentColor"/></svg>"""

SVG_EMPTY_BOX = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="42" height="42" fill="none" stroke="currentColor" stroke-width="1.5" class="text-slate-400 mb-2"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/><polyline points="3.27 6.96 12 12.01 20.73 6.96"/><line x1="12" y1="22.08" x2="12" y2="12"/></svg>"""


@module.ui
def summary_ui():
    return ui.div(
        ui.output_ui("context_banner_container"),
        ui.output_ui("kpi_value_boxes"),
        ui.layout_columns(
            ui.card(
                ui.card_header("Metadatos de la Fuente Oficial"),
                ui.output_ui("metadata_content"),
                full_screen=True
            ),
            ui.card(
                ui.card_header("Diagnostico por Columna y Completitud"),
                ui.output_data_frame("diagnostics_grid"),
                full_screen=True
            ),
            col_widths=[5, 7],
            class_="mb-3"
        ),
        ui.card(
            ui.card_header("Distribucion de Valores Faltantes por Variable"),
            ui.output_ui("missing_chart"),
            full_screen=True
        )
    )


@module.server
def summary_server(input, output, session, df_react, meta_react):
    
    @reactive.calc
    def dataset_metrics():
        df = df_react()
        return compute_dataset_overview(df)

    @output
    @render.ui
    def context_banner_container():
        return render_context_banner(df_react(), meta_react())

    @output
    @render.ui
    def kpi_value_boxes():
        df = df_react()
        if df.empty:
            return ui.card(
                ui.div(
                    ui.HTML(SVG_EMPTY_BOX),
                    ui.h5("Sin conjunto de datos cargado", class_="fw-bold text-slate-700 mb-2"),
                    ui.p(
                        "Seleccione una coleccion verificada en el panel lateral o ingrese el identificador de un recurso de datos.gov.co, "
                        "luego haga clic en 'Cargar y Analizar Datos' para desplegar metricas.",
                        class_="text-slate-500 mb-0 max-w-md mx-auto"
                    ),
                    class_="text-center py-5"
                ),
                class_="mb-3 empty-state-card"
            )

        m = dataset_metrics()
        missing_theme = "danger" if m["missing_pct"] > 15 else ("warning" if m["missing_pct"] > 5 else "success")

        return ui.layout_columns(
            ui.value_box(
                "Total Registros",
                f"{m['rows']:,}",
                showcase=ui.HTML(SVG_ICON_ROWS),
                theme="primary",
                class_="kpi-box-custom"
            ),
            ui.value_box(
                "Variables Totales",
                str(m['cols']),
                showcase=ui.HTML(SVG_ICON_COLS),
                theme="info",
                class_="kpi-box-custom"
            ),
            ui.value_box(
                "Variables Numericas",
                str(m['num_cols']),
                showcase=ui.HTML(SVG_ICON_NUM),
                theme="primary",
                class_="kpi-box-custom"
            ),
            ui.value_box(
                "Datos Faltantes",
                f"{m['missing_pct']}%",
                showcase=ui.HTML(SVG_ICON_MISSING),
                theme=missing_theme,
                class_="kpi-box-custom"
            ),
            col_widths=[3, 3, 3, 3],
            class_="mb-3"
        )

    @output
    @render.ui
    def metadata_content():
        meta = meta_react()
        if not meta:
            return ui.p("Metadatos no disponibles para este recurso.", class_="text-muted py-2")

        name = meta.get("name", "Dataset de datos.gov.co")
        desc = meta.get("description", "Sin descripcion registrada.")
        author_info = meta.get("tableAuthor", {})
        author = author_info.get("displayName", "No especificado") if isinstance(author_info, dict) else "No especificado"

        return ui.tags.table(
            ui.tags.tr(ui.tags.th("Titulo Oficial:", style="width: 140px;"), ui.tags.td(name)),
            ui.tags.tr(ui.tags.th("Entidad / Autor:"), ui.tags.td(author)),
            ui.tags.tr(ui.tags.th("Descripcion:"), ui.tags.td(desc[:350] + ("..." if len(desc) > 350 else ""))),
            class_="table table-sm custom-table mb-0"
        )

    @output
    @render.data_frame
    def diagnostics_grid():
        df = df_react()
        if df.empty:
            return render.DataGrid(pd.DataFrame(), height="240px")
        
        diag_df = compute_column_diagnostics(df)
        return render.DataGrid(diag_df, filters=False, height="260px")

    @output
    @render.ui
    def missing_chart():
        df = df_react()
        if df.empty:
            return ui.span()
        
        null_counts = df.isnull().sum()
        null_counts = null_counts[null_counts > 0].sort_values(ascending=False)

        if null_counts.empty:
            return ui.div(
                ui.p("El conjunto de datos esta completo. No se registraron valores nulos.", class_="status-success p-3 mb-0")
            )

        fig = px.bar(
            x=null_counts.index.tolist(),
            y=null_counts.values,
            labels={"x": "Variable", "y": "Valores Nulos"},
            title="Conteo de valores nulos por variable",
            color=null_counts.values,
            color_continuous_scale=["#cbd5e1", "#dc2626"]
        )
        fig.update_layout(
            height=280,
            margin=dict(t=40, b=40, l=40, r=40),
            coloraxis_showscale=False,
            plot_bgcolor="white",
            paper_bgcolor="white"
        )
        fig.update_xaxes(showgrid=True, gridcolor="#f1f5f9")
        fig.update_yaxes(showgrid=True, gridcolor="#f1f5f9")
        return ui.HTML(fig.to_html(full_html=False, include_plotlyjs="cdn", config={"responsive": True}))

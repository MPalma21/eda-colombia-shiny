"""Modulo de resumen y vision global del dataset."""
from shiny import module, ui, render, reactive
import pandas as pd
import plotly.express as px
from services.stats_service import compute_dataset_overview, compute_column_diagnostics
# Iconos vectoriales limpios envueltos en badges con fondos sutiles
SVG_ICON_ROWS = """<div class="kpi-icon-badge kpi-badge-blue"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="16" rx="2"/><line x1="3" y1="9" x2="21" y2="9"/><line x1="3" y1="14" x2="21" y2="14"/></svg></div>"""

SVG_ICON_COLS = """<div class="kpi-icon-badge kpi-badge-slate"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="16" rx="2"/><line x1="9" y1="4" x2="9" y2="20"/><line x1="15" y1="4" x2="15" y2="20"/></svg></div>"""

SVG_ICON_NUM = """<div class="kpi-icon-badge kpi-badge-teal"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2"><line x1="4" y1="19" x2="20" y2="19"/><polyline points="4 15 9 9 14 13 20 5"/></svg></div>"""

SVG_ICON_MISSING = """<div class="kpi-icon-badge kpi-badge-semantic"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><circle cx="12" cy="16" r="1" fill="currentColor"/></svg></div>"""

@module.ui
def summary_ui():
    return ui.div(
        ui.output_ui("kpi_value_boxes"),
        ui.layout_columns(
            ui.card(
                ui.card_header(
                    ui.span("Metadatos de la Fuente Oficial", class_="fw-bold"),
                    class_="d-flex justify-content-between align-items-center"
                ),
                ui.output_ui("metadata_content"),
                full_screen=True
            ),
            ui.card(
                ui.card_header(
                    ui.span("Diagnostico por Columna y Completitud", class_="fw-bold"),
                    class_="d-flex justify-content-between align-items-center"
                ),
                ui.output_data_frame("diagnostics_grid"),
                full_screen=True
            ),
            col_widths={"sm": (12, 12), "lg": (5, 7)},
            class_="mb-3 g-3"
        ),
        ui.card(
            ui.card_header(
                ui.span("Distribucion de Valores Faltantes por Variable", class_="fw-bold")
            ),
            ui.output_ui("missing_chart"),
            full_screen=True,
            class_="mb-3"
        ),
        class_="summary-container"
    )


@module.server
def summary_server(input, output, session, df_react, meta_react):
    
    @reactive.calc
    def dataset_metrics():
        df = df_react()
        return compute_dataset_overview(df)

    @output
    @render.ui
    def kpi_value_boxes():
        df = df_react()
        if df.empty:
            return ui.span()

        m = dataset_metrics()
        missing_val = m["missing_pct"]
        missing_class = "kpi-missing-high" if missing_val > 15 else ("kpi-missing-mid" if missing_val > 5 else "kpi-missing-low")

        return ui.layout_columns(
            ui.value_box(
                "Total Registros",
                f"{m['rows']:,}",
                showcase=ui.HTML(SVG_ICON_ROWS),
                theme=None,
                class_="kpi-card"
            ),
            ui.value_box(
                "Variables Totales",
                str(m['cols']),
                showcase=ui.HTML(SVG_ICON_COLS),
                theme=None,
                class_="kpi-card"
            ),
            ui.value_box(
                "Variables Numericas",
                str(m['num_cols']),
                showcase=ui.HTML(SVG_ICON_NUM),
                theme=None,
                class_="kpi-card"
            ),
            ui.value_box(
                "Datos Faltantes",
                f"{m['missing_pct']}%",
                showcase=ui.HTML(SVG_ICON_MISSING),
                theme=None,
                class_=f"kpi-card {missing_class}"
            ),
            col_widths={"sm": 12, "md": 6, "lg": 3},
            class_="mb-3 g-3"
        )

    @output
    @render.ui
    def metadata_content():
        meta = meta_react()
        if not meta:
            return ui.p("Metadatos descriptivos no disponibles para este recurso.", class_="text-muted py-3 px-2")

        name = meta.get("name", "Dataset de datos.gov.co")
        desc = meta.get("description", "Sin descripcion registrada.")
        author_info = meta.get("tableAuthor", {})
        author = author_info.get("displayName", "Entidad publica no especificada") if isinstance(author_info, dict) else "Entidad publica no especificada"
        category = meta.get("category", "General")

        return ui.div(
            ui.div(
                ui.div(
                    ui.span("TITULO OFICIAL", class_="metadata-item-label"),
                    ui.div(name, class_="metadata-item-title"),
                    class_="mb-3"
                ),
                ui.div(
                    ui.span("ENTIDAD RESPONSABLE", class_="metadata-item-label"),
                    ui.div(
                        ui.span(author, class_="badge badge-entity"),
                        ui.span(f"Categoria: {category}", class_="badge badge-category ms-2"),
                        class_="d-flex flex-wrap align-items-center mt-1"
                    ),
                    class_="mb-3"
                ),
                ui.div(
                    ui.span("DESCRIPCION INSTITUCIONAL", class_="metadata-item-label"),
                    ui.div(
                        desc[:400] + ("..." if len(desc) > 400 else ""),
                        class_="metadata-item-desc"
                    ),
                    class_="mb-0"
                ),
                class_="metadata-content-wrapper p-2"
            )
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
                ui.p("El conjunto de datos esta completo. No se registraron valores nulos.", class_="status-success py-3 px-3 mb-0")
            )

        fig = px.bar(
            x=null_counts.index.tolist(),
            y=null_counts.values,
            labels={"x": "Variable", "y": "Valores Nulos"},
            title="Conteo de valores nulos por variable",
            color=null_counts.values,
            color_continuous_scale=["#c5d8c8", "#b94f46"]
        )
        fig.update_layout(
            height=260,
            margin=dict(t=40, b=40, l=40, r=40),
            coloraxis_showscale=False,
            plot_bgcolor="white",
            paper_bgcolor="white"
        )
        fig.update_xaxes(showgrid=True, gridcolor="#edf2e9")
        fig.update_yaxes(showgrid=True, gridcolor="#edf2e9")
        return ui.HTML(fig.to_html(full_html=False, include_plotlyjs="cdn", config={"responsive": True}))

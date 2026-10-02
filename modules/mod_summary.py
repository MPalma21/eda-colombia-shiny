"""Modulo de resumen y vision global del dataset."""
from shiny import module, ui, render, reactive
import pandas as pd
import plotly.express as px
from services.stats_service import compute_dataset_overview, compute_column_diagnostics


@module.ui
def summary_ui():
    return ui.div(
        ui.output_ui("metrics_grid"),
        ui.layout_columns(
            ui.card(
                ui.card_header("Metadatos de la Fuente"),
                ui.output_ui("metadata_content"),
                full_screen=True
            ),
            ui.card(
                ui.card_header("Diagnostico por Columna"),
                ui.output_ui("diagnostics_table"),
                full_screen=True
            ),
            col_widths=[5, 7]
        ),
        ui.card(
            ui.card_header("Distribucion de Valores Faltantes"),
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
    def metrics_grid():
        df = df_react()
        if df.empty:
            return ui.div(
                ui.p("Seleccione o ingrese un dataset en el panel lateral para iniciar el analisis exploratorio.",
                     class_="text-muted text-center py-5")
            )
        
        m = dataset_metrics()
        missing_tile_class = "tile-red" if m["missing_pct"] > 15 else ("tile-amber" if m["missing_pct"] > 5 else "tile-green")

        return ui.layout_columns(
            ui.div(
                ui.div(f"{m['rows']:,}", class_="tile-num"),
                ui.div("Total Registros", class_="tile-label"),
                class_="metric-tile tile-blue"
            ),
            ui.div(
                ui.div(f"{m['cols']}", class_="tile-num"),
                ui.div("Variables", class_="tile-label"),
                class_="metric-tile tile-teal"
            ),
            ui.div(
                ui.div(f"{m['num_cols']}", class_="tile-num"),
                ui.div("Variables Numericas", class_="tile-label"),
                class_="metric-tile tile-blue"
            ),
            ui.div(
                ui.div(f"{m['missing_pct']}%", class_="tile-num"),
                ui.div("Datos Faltantes", class_="tile-label"),
                class_=f"metric-tile {missing_tile_class}"
            ),
            col_widths=[3, 3, 3, 3]
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
            ui.tags.tr(ui.tags.th("Titulo:", style="width: 130px;"), ui.tags.td(name)),
            ui.tags.tr(ui.tags.th("Entidad / Autor:"), ui.tags.td(author)),
            ui.tags.tr(ui.tags.th("Descripcion:"), ui.tags.td(desc[:350] + ("..." if len(desc) > 350 else ""))),
            class_="table table-sm custom-table mb-0"
        )

    @output
    @render.ui
    def diagnostics_table():
        df = df_react()
        if df.empty:
            return ui.span()
        
        diag_df = compute_column_diagnostics(df)
        return ui.div(
            ui.HTML(diag_df.to_html(index=False, classes="custom-table", border=0)),
            style="max-height: 280px; overflow-y: auto;"
        )

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

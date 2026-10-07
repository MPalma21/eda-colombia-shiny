"""Modulo de correlaciones lineales y matrices de dispersion."""
from shiny import module, ui, render, reactive
import pandas as pd
import plotly.express as px
from services.stats_service import classify_columns, compute_correlation_matrix


@module.ui
def correlations_ui():
    return ui.card(
        ui.card_header("Matriz de Correlacion y Dispersion"),
        ui.output_ui("corr_controls_ui"),
        ui.output_ui("corr_plot_container"),
        full_screen=True
    )


@module.server
def correlations_server(input, output, session, df_react):

    @output
    @render.ui
    def corr_controls_ui():
        df = df_react()
        if df.empty:
            return ui.p("Cargue un dataset para calcular correlaciones.", class_="text-muted")
        
        num_cols, _, _ = classify_columns(df)
        if len(num_cols) < 2:
            return ui.p("Se requieren al menos dos columnas numericas para el calculo de correlacion.", class_="status-warning")

        return ui.layout_columns(
            ui.input_select("corr_method", "Coeficiente de Correlacion:",
                            choices=["pearson", "spearman", "kendall"]),
            ui.input_select("corr_view", "Tipo de Visualizacion:",
                            choices=["Mapa de Calor (Heatmap)", "Matriz de Dispersion (Scatter Matrix)"]),
            col_widths={"sm": 12, "md": 6},
            class_="mb-3 g-2"
        )

    @reactive.calc
    def cached_corr_matrix():
        df = df_react()
        if df.empty:
            return pd.DataFrame()
        method = input.corr_method() if hasattr(input, "corr_method") else "pearson"
        return compute_correlation_matrix(df, method=method)

    @output
    @render.ui
    def corr_plot_container():
        df = df_react()
        if df.empty or not hasattr(input, "corr_view"):
            return ui.span()

        num_cols, _, _ = classify_columns(df)
        if len(num_cols) < 2:
            return ui.span()

        view = input.corr_view()

        if view == "Mapa de Calor (Heatmap)":
            corr = cached_corr_matrix()
            if corr.empty:
                return ui.p("No fue posible generar la matriz de correlacion.", class_="text-muted")

            fig = px.imshow(
                corr,
                text_auto=True,
                aspect="auto",
                color_continuous_scale="Blues",
                zmin=-1, zmax=1,
                title="Matriz de Correlacion"
            )
            fig.update_layout(height=480, margin=dict(t=50, b=40, l=40, r=40))

        else:
            sample_cols = num_cols[:6]
            fig = px.scatter_matrix(
                df,
                dimensions=sample_cols,
                title="Matriz de Dispersion (Variables numericas principales)",
                color_discrete_sequence=["#1d4ed8"]
            )
            fig.update_traces(diagonal_visible=False)
            fig.update_layout(height=540, margin=dict(t=50, b=40, l=40, r=40))

        fig.update_layout(plot_bgcolor="white", paper_bgcolor="white")
        return ui.HTML(fig.to_html(full_html=False, include_plotlyjs="cdn", config={"responsive": True}))

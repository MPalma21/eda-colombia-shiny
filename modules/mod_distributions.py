"""Modulo de distribuciones y analisis univariado."""
from shiny import module, ui, render, reactive
import pandas as pd
import numpy as np
from scipy import stats
import plotly.express as px
import plotly.graph_objects as go
from services.stats_service import classify_columns


@module.ui
def distributions_ui():
    return ui.card(
        ui.card_header("Distribuciones Univariadas"),
        ui.output_ui("dist_controls_ui"),
        ui.output_ui("dist_plot_container"),
        full_screen=True
    )


@module.server
def distributions_server(input, output, session, df_react):
    
    @output
    @render.ui
    def dist_controls_ui():
        df = df_react()
        if df.empty:
            return ui.p("Cargue un dataset para activar los controles.", class_="text-muted")
        
        num_cols, _, cat_cols = classify_columns(df)
        if not num_cols:
            return ui.p("El dataset no contiene columnas numericas para este analisis.", class_="status-warning")

        return ui.row(
            ui.column(4, ui.input_select("dist_variable", "Variable Numerica:", choices=num_cols)),
            ui.column(3, ui.input_select("chart_kind", "Tipo de Grafico:",
                                        choices=["Histograma + KDE", "Diagrama de Caja (Box Plot)", "Grafico de Violin", "Funcion Empirica (ECDF)"])),
            ui.column(2, ui.input_numeric("bins_count", "Intervalos (Bins):", value=30, min=5, max=100)),
            ui.column(3, ui.input_select("group_by_cat", "Segmentar por Categoria (opcional):", choices=["(Ninguna)"] + cat_cols))
        )

    @output
    @render.ui
    def dist_plot_container():
        df = df_react()
        if df.empty or not hasattr(input, "dist_variable"):
            return ui.span()

        var = input.dist_variable()
        if not var or var not in df.columns:
            return ui.span()

        chart_kind = input.chart_kind()
        bins = int(input.bins_count() or 30)
        group_col = input.group_by_cat() if hasattr(input, "group_by_cat") else "(Ninguna)"
        color_param = None if group_col == "(Ninguna)" or group_col not in df.columns else group_col

        series = df[var].dropna()
        if series.empty:
            return ui.p("Sin observaciones numericas suficientes en la variable seleccionada.", class_="text-muted")

        positron_palette = ["#447099", "#2585a6", "#64748b", "#d97706", "#059669", "#dc2626"]

        if chart_kind == "Histograma + KDE":
            fig = px.histogram(
                df, x=var, nbins=bins, color=color_param,
                marginal="box", title=f"Distribucion de {var}",
                barmode="overlay", opacity=0.8,
                color_discrete_sequence=positron_palette
            )
            if color_param is None and len(series) > 5:
                try:
                    kde_x = np.linspace(series.min(), series.max(), 250)
                    kde = stats.gaussian_kde(series)
                    scale = len(series) * (series.max() - series.min()) / bins
                    fig.add_trace(go.Scatter(
                        x=kde_x, y=kde(kde_x) * scale,
                        mode="lines", name="KDE",
                        line=dict(color="#dc2626", width=2)
                    ))
                except Exception:
                    pass

        elif chart_kind == "Diagrama de Caja (Box Plot)":
            fig = px.box(
                df, y=var, x=color_param, color=color_param,
                title=f"Box Plot: {var}", points="outliers",
                color_discrete_sequence=positron_palette
            )

        elif chart_kind == "Grafico de Violin":
            fig = px.violin(
                df, y=var, x=color_param, color=color_param,
                box=True, title=f"Violin Plot: {var}",
                color_discrete_sequence=positron_palette
            )

        else:
            fig = px.ecdf(
                df, x=var, color=color_param,
                title=f"Curva Empirica Acumulada (ECDF): {var}",
                color_discrete_sequence=positron_palette
            )

        fig.update_layout(
            height=460,
            margin=dict(t=50, b=40, l=40, r=40),
            plot_bgcolor="white",
            paper_bgcolor="white"
        )
        fig.update_xaxes(showgrid=True, gridcolor="#f1f5f9")
        fig.update_yaxes(showgrid=True, gridcolor="#f1f5f9")

        metrics_html = f"""
        <div class="row g-2 mt-2">
            <div class="col"><div class="metric-tile tile-blue"><div class="tile-num">{series.mean():,.2f}</div><div class="tile-label">Media</div></div></div>
            <div class="col"><div class="metric-tile tile-teal"><div class="tile-num">{series.median():,.2f}</div><div class="tile-label">Mediana</div></div></div>
            <div class="col"><div class="metric-tile tile-blue"><div class="tile-num">{series.std():,.2f}</div><div class="tile-label">Desv. Estandar</div></div></div>
            <div class="col"><div class="metric-tile tile-amber"><div class="tile-num">{float(stats.skew(series)):.2f}</div><div class="tile-label">Sesgo (Skewness)</div></div></div>
        </div>
        """

        return ui.div(
            ui.HTML(fig.to_html(full_html=False, include_plotlyjs="cdn", config={"responsive": True})),
            ui.HTML(metrics_html)
        )

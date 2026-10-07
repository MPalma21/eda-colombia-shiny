"""Modulo de analisis de series temporales."""
from shiny import module, ui, render
import pandas as pd
import plotly.express as px
from services.stats_service import classify_columns


@module.ui
def timeseries_ui():
    return ui.card(
        ui.card_header("Series de Tiempo y Tendencias"),
        ui.output_ui("ts_controls_ui"),
        ui.output_ui("ts_plot_container"),
        full_screen=True
    )


@module.server
def timeseries_server(input, output, session, df_react):

    @output
    @render.ui
    def ts_controls_ui():
        df = df_react()
        if df.empty:
            return ui.p("Cargue un dataset para verificar series temporales.", class_="text-muted")
        
        num_cols, date_cols, _ = classify_columns(df)
        if not date_cols:
            return ui.p("No se detectaron variables de fecha u hora en este dataset.", class_="status-warning")

        return ui.row(
            ui.column(4, ui.input_select("date_variable", "Variable Temporal (Fecha):", choices=date_cols)),
            ui.column(4, ui.input_select("metric_variable", "Variable Numerica:", choices=num_cols)),
            ui.column(4, ui.input_select("aggregation_type", "Agregacion:",
                                        choices=["Suma", "Promedio", "Conteo", "Maximo"]))
        )

    @output
    @render.ui
    def ts_plot_container():
        df = df_react()
        if df.empty or not hasattr(input, "date_variable"):
            return ui.span()

        _, date_cols, _ = classify_columns(df)
        if not date_cols:
            return ui.span()

        date_col = input.date_variable()
        metric_col = input.metric_variable()
        agg_choice = input.aggregation_type()

        if not date_col or not metric_col or date_col not in df.columns or metric_col not in df.columns:
            return ui.span()

        try:
            sub = df[[date_col, metric_col]].dropna()
            sub[date_col] = pd.to_datetime(sub[date_col], errors="coerce")
            sub = sub.dropna(subset=[date_col]).set_index(date_col).sort_index()
            sub[metric_col] = pd.to_numeric(sub[metric_col], errors="coerce")

            agg_methods = {"Suma": "sum", "Promedio": "mean", "Conteo": "count", "Maximo": "max"}
            freq = "D" if (sub.index.max() - sub.index.min()).days <= 180 else "ME"

            resampled = sub[metric_col].resample(freq).agg(agg_methods[agg_choice]).reset_index()
            resampled.columns = [date_col, metric_col]

            fig = px.line(
                resampled, x=date_col, y=metric_col,
                title=f"{agg_choice} de {metric_col} a lo largo del tiempo",
                markers=len(resampled) <= 80
            )
            fig.update_traces(line_color="#1d4ed8", line_width=2.4)

            if len(resampled) >= 6:
                resampled["Media_Movil"] = resampled[metric_col].rolling(window=5, min_periods=1).mean()
                fig.add_scatter(
                    x=resampled[date_col], y=resampled["Media_Movil"],
                    name="Tendencia Suavizada", mode="lines",
                    line=dict(color="#0284c7", dash="dash", width=2.2)
                )

            fig.update_layout(
                height=460,
                margin=dict(t=50, b=40, l=40, r=40),
                plot_bgcolor="white",
                paper_bgcolor="white"
            )
            fig.update_xaxes(showgrid=True, gridcolor="#f1f5f9")
            fig.update_yaxes(showgrid=True, gridcolor="#f1f5f9")
            return ui.HTML(fig.to_html(full_html=False, include_plotlyjs="cdn", config={"responsive": True}))

        except Exception as exc:
            return ui.p(f"Error procesando serie temporal: {exc}", class_="status-error")

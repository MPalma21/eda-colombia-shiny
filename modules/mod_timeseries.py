"""Modulo de Series de Tiempo, Precios e Indexacion Economica."""
from shiny import module, ui, render, reactive
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from services.stats_service import classify_columns, suggest_time_aggregation
from services.economic_service import compute_base_100_series


@module.ui
def timeseries_ui():
    return ui.card(
        ui.card_header(
            ui.div(
                ui.span("Dinamica Temporal, Precios & Evolucion Relativa", class_="fw-bold"),
                ui.span("Indexacion Base 100 · Variaciones Interperiodo", class_="text-muted", style="font-size: 0.78rem;")
            ),
            class_="d-flex justify-content-between align-items-center"
        ),
        ui.output_ui("ts_controls_ui"),
        ui.output_ui("ts_kpi_cards"),
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
        if not num_cols:
            return ui.p("Se requiere al menos una variable numerica para la serie temporal.", class_="status-warning")

        pref_nums = [c for c in num_cols if any(k in c.lower() for k in ("precio", "valor", "monto", "trm", "tasa", "total"))]
        default_num = pref_nums[0] if pref_nums else num_cols[0]

        return ui.layout_columns(
            ui.input_select("date_variable", "Variable Temporal (Fecha):", choices=date_cols),
            ui.input_select("metric_variable", "Variable Economica / Numerica:", choices=num_cols, selected=default_num),
            ui.input_select(
                "ts_transform",
                "Formato de Analisis Economico:",
                choices={
                    "level": "Nivel Observado (Suma o Promedio)",
                    "base100": "Indice Base 100 (Evolucion Relativa t₀ = 100)",
                    "pct_change": "Tasa de Variacion Interperiodo (%)"
                },
                selected="level"
            ),
            ui.input_select("aggregation_type", "Agregacion:",
                            choices=["Promedio", "Suma", "Maximo"],
                            selected=suggest_time_aggregation(default_num)),
            col_widths={"sm": 12, "md": 6, "lg": 3},
            class_="mb-2 g-2"
        )

    @reactive.effect
    def _suggest_for_metric():
        metric = input.metric_variable()
        if metric:
            ui.update_select("aggregation_type", selected=suggest_time_aggregation(metric))

    @reactive.calc
    def processed_ts_df():
        df = df_react()
        if df.empty or not hasattr(input, "date_variable") or not hasattr(input, "metric_variable"):
            return pd.DataFrame()

        date_col = input.date_variable()
        metric_col = input.metric_variable()
        agg_choice = input.aggregation_type() if hasattr(input, "aggregation_type") else "Promedio"

        if not date_col or not metric_col or date_col not in df.columns or metric_col not in df.columns:
            return pd.DataFrame()

        try:
            sub = df[[date_col, metric_col]].dropna().copy()
            sub[date_col] = pd.to_datetime(sub[date_col], errors="coerce")
            sub[metric_col] = pd.to_numeric(sub[metric_col], errors="coerce")
            sub = sub.dropna(subset=[date_col, metric_col]).set_index(date_col).sort_index()

            if sub.empty:
                return pd.DataFrame()

            agg_methods = {"Suma": "sum", "Promedio": "mean", "Maximo": "max"}
            freq = "D" if (sub.index.max() - sub.index.min()).days <= 180 else "ME"

            resampled = sub[metric_col].resample(freq).agg(agg_methods.get(agg_choice, "mean")).reset_index()
            resampled.columns = [date_col, metric_col]

            # Computar Indice Base 100 y Variacion Porcentual
            base_val = resampled[metric_col].iloc[0]
            if base_val != 0:
                resampled["Indice_Base_100"] = ((resampled[metric_col] / base_val) * 100).round(2)
            else:
                resampled["Indice_Base_100"] = 100.0

            resampled["Variacion_Pct"] = (resampled[metric_col].pct_change() * 100).round(2)
            return resampled
        except Exception:
            return pd.DataFrame()

    @output
    @render.ui
    def ts_kpi_cards():
        ts_df = processed_ts_df()
        if ts_df.empty or len(ts_df) < 2:
            return ui.span()

        date_col = input.date_variable()
        metric_col = input.metric_variable()

        val_inicial = float(ts_df[metric_col].iloc[0])
        val_final = float(ts_df[metric_col].iloc[-1])
        var_total_pct = ((val_final - val_inicial) / val_inicial * 100) if val_inicial != 0 else 0.0

        max_val = float(ts_df[metric_col].max())
        min_val = float(ts_df[metric_col].min())

        var_class = "badge-status-ok" if var_total_pct >= 0 else "kpi-missing-high"
        var_sign = "+" if var_total_pct > 0 else ""

        return ui.layout_columns(
            ui.value_box(
                "Valor Inicial (t₀)",
                f"{val_inicial:,.2f}",
                ui.p(f"Fecha: {ts_df[date_col].iloc[0].strftime('%Y-%m-%d')}", class_="text-muted mb-0", style="font-size: 0.78rem;"),
                showcase=ui.span("Base", class_="badge bg-slate-100 text-slate-700 p-2"),
                theme=None,
                class_="kpi-card"
            ),
            ui.value_box(
                "Ultimo Valor (t_fin)",
                f"{val_final:,.2f}",
                ui.p(f"Fecha: {ts_df[date_col].iloc[-1].strftime('%Y-%m-%d')}", class_="text-muted mb-0", style="font-size: 0.78rem;"),
                showcase=ui.span("Actual", class_="badge bg-slate-100 text-slate-700 p-2"),
                theme=None,
                class_="kpi-card"
            ),
            ui.value_box(
                "Variacion Acumulada Periodo",
                f"{var_sign}{var_total_pct:.2f}%",
                ui.p("Cambio porcentual punta a punta", class_="text-muted mb-0", style="font-size: 0.78rem;"),
                showcase=ui.span(f"{var_sign}{var_total_pct:.1f}%", class_=f"badge {var_class} p-2"),
                theme=None,
                class_="kpi-card"
            ),
            ui.value_box(
                "Rango Historico [Min - Max]",
                f"{min_val:,.1f} - {max_val:,.1f}",
                ui.p("Amplitud de la serie observada", class_="text-muted mb-0", style="font-size: 0.78rem;"),
                showcase=ui.span("Rango", class_="badge bg-slate-100 text-slate-700 p-2"),
                theme=None,
                class_="kpi-card"
            ),
            col_widths={"sm": 12, "md": 6, "lg": 3},
            class_="mb-3 g-2"
        )

    @output
    @render.ui
    def ts_plot_container():
        ts_df = processed_ts_df()
        if ts_df.empty:
            return ui.span()

        date_col = input.date_variable()
        metric_col = input.metric_variable()
        transform = input.ts_transform() if hasattr(input, "ts_transform") else "level"

        fig = go.Figure()

        if transform == "base100":
            # Indice normalizado Base 100
            fig.add_trace(go.Scatter(
                x=ts_df[date_col],
                y=ts_df["Indice_Base_100"],
                mode="lines+markers",
                name="Indice (Base 100)",
                line=dict(color="#1e40af", width=2.4),
                marker=dict(size=4)
            ))
            # Linea de referencia base 100
            fig.add_hline(y=100.0, line_dash="dash", line_color="#94a3b8", annotation_text="Base 100 = Período Inicial")
            y_title = "Indice Base 100 (t₀ = 100.0)"
            chart_title = f"Evolucion Relativa Normalizada (Base 100) · {metric_col}"

        elif transform == "pct_change":
            # Variaciones porcentuales interperiodo
            valid_changes = ts_df.dropna(subset=["Variacion_Pct"])
            colors = ["#059669" if val >= 0 else "#dc2626" for val in valid_changes["Variacion_Pct"]]
            fig.add_trace(go.Bar(
                x=valid_changes[date_col],
                y=valid_changes["Variacion_Pct"],
                name="Variacion %",
                marker_color=colors
            ))
            fig.add_hline(y=0.0, line_dash="solid", line_color="#cbd5e1")
            y_title = "Variacion Interperiodo (%)"
            chart_title = f"Tasa de Crecimiento Interperiodo (%) · {metric_col}"

        else:
            # Nivel original observado
            agg_choice = input.aggregation_type()
            fig.add_trace(go.Scatter(
                x=ts_df[date_col],
                y=ts_df[metric_col],
                mode="lines+markers",
                name=f"{agg_choice} {metric_col}",
                line=dict(color="#1e40af", width=2.4),
                marker=dict(size=4)
            ))
            if len(ts_df) >= 6:
                ma = ts_df[metric_col].rolling(window=5, min_periods=1).mean()
                fig.add_trace(go.Scatter(
                    x=ts_df[date_col],
                    y=ma,
                    mode="lines",
                    name="Tendencia Suavizada (Media Movil)",
                    line=dict(color="#d97706", dash="dash", width=2.0)
                ))
            y_title = f"{agg_choice} de {metric_col}"
            chart_title = f"Serie de Tiempo: {metric_col} ({agg_choice})"

        fig.update_layout(
            title=dict(text=chart_title, font=dict(size=14, color="#0f172a")),
            xaxis=dict(title="Fecha", gridcolor="#f1f5f9"),
            yaxis=dict(title=y_title, gridcolor="#f1f5f9"),
            height=360,
            margin=dict(t=50, b=45, l=60, r=30),
            plot_bgcolor="white",
            paper_bgcolor="white",
            legend=dict(x=0.02, y=0.98, bgcolor="rgba(255,255,255,0.85)")
        )

        return ui.HTML(fig.to_html(full_html=False, include_plotlyjs="cdn", config={"responsive": True}))

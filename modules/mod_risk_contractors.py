"""Modulo de Concentracion Empresarial y Contratistas Dominantes (Poder de Mercado).

Perspectiva 3 del Panel de Riesgo Territorial:
- Mapeo de grandes actores empresariales y adjudicatarios del gasto publico.
- Ratios oligopolicos de concentracion CR4 y CR8.
- Deteccion de contratistas favorecidos a dedo (% de facturacion por via directa).
- Grado de diversificacion e influencia interdepartamental.
- Tabla integral para veeduria y seguimiento de conglomerados.
"""
from shiny import module, ui, render, reactive
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from services.economic_service import (
    get_contractors_summary,
    find_procurement_columns,
    format_cop_currency
)


@module.ui
def risk_contractors_ui():
    return ui.div(
        # Tarjeta 1: KPIs Ejecutivos de Concentracion Empresarial
        ui.card(
            ui.card_header(
                ui.div(
                    ui.span("Poder de Mercado & Concentración de Contratistas (SECOP II)", class_="fw-bold"),
                    ui.span("Auditoría de Adjudicatarios, Ratios Oligopólicos y Tasa de Contratación a Dedo", class_="text-muted", style="font-size: 0.78rem;")
                ),
                class_="d-flex justify-content-between align-items-center"
            ),
            ui.output_ui("contractors_kpi_cards"),
            full_screen=False,
            class_="mb-3"
        ),

        # Tarjeta 2: Gráficos de Poder de Mercado y Dispersión
        ui.card(
            ui.card_header(
                ui.div(
                    ui.span("Estructura de Mercado · Grandes Acaparadores vs Vía de Adjudicación", class_="fw-bold"),
                    ui.span("Dispersión: Presupuesto Total vs Porcentaje Obtenido por Contratación Directa", class_="text-muted", style="font-size: 0.78rem;")
                ),
                class_="d-flex justify-content-between align-items-center"
            ),
            ui.layout_columns(
                ui.output_ui("contractors_bar_container"),
                ui.output_ui("contractors_scatter_container"),
                col_widths={"sm": 12, "lg": (6, 6)},
                class_="g-3"
            ),
            full_screen=True,
            class_="mb-3"
        ),

        # Tarjeta 3: Directorio de Contratistas Auditados
        ui.card(
            ui.card_header(
                ui.div(
                    ui.span("Directorio de Contratistas con Alertas de Riesgo Anticompetitivo", class_="fw-bold"),
                    ui.span("Seguimiento a Proveedores y Tasa de Dependencia de Contratación Directa", class_="text-muted", style="font-size: 0.78rem;")
                ),
                class_="d-flex justify-content-between align-items-center"
            ),
            ui.output_data_frame("contractors_data_table"),
            full_screen=True
        )
    )


@module.server
def risk_contractors_server(input, output, session, df_react):

    @reactive.calc
    def contractors_df():
        df = df_react()
        if df.empty:
            return pd.DataFrame()
        return get_contractors_summary(df, top_n=50)

    # -------------------------------------------------------------
    # 1. VALUE BOXES DE CONCENTRACIÓN
    # -------------------------------------------------------------
    @output
    @render.ui
    def contractors_kpi_cards():
        df = df_react()
        c_df = contractors_df()
        if df.empty or c_df.empty:
            return ui.p("Cargue datos para calcular la concentración empresarial.", class_="text-muted")

        total_provs = df[find_procurement_columns(df)[2]].nunique() if find_procurement_columns(df)[2] in df.columns else len(c_df)
        top1 = c_df.iloc[0]

        cr4_sum = float(c_df.head(4)["cuota_pct"].sum())
        direct_avg_top10 = float(c_df.head(10)["pct_directa"].mean())

        return ui.layout_columns(
            ui.value_box(
                "Oferentes Registrados",
                f"{total_provs:,}",
                ui.p(f"Top 50 auditados en detalle", class_="text-muted small mb-0"),
                showcase=ui.div(
                    ui.span("N", class_="fw-bold font-monospace text-primary", style="font-size: 1.1rem;"),
                    class_="kpi-icon-badge kpi-badge-blue"
                ),
                theme=None,
                class_="bslib-value-box"
            ),
            ui.value_box(
                "Contratista Líder",
                str(top1["proveedor"])[:22],
                ui.p(f"Monto: {format_cop_currency(top1['monto_total'])} ({top1['cuota_pct']:.1f}% cuota)", class_="text-muted small mb-0"),
                showcase=ui.div(
                    ui.span("#1", class_="fw-bold font-monospace text-teal", style="font-size: 1.1rem;"),
                    class_="kpi-icon-badge kpi-badge-teal"
                ),
                theme=None,
                class_="bslib-value-box"
            ),
            ui.value_box(
                "Concentración CR4",
                f"{cr4_sum:.1f}%",
                ui.p("Cuota acumulada de los 4 mayores actores", class_="text-muted small mb-0"),
                showcase=ui.div(
                    ui.span("CR4", class_="fw-bold font-monospace text-secondary", style="font-size: 0.95rem;"),
                    class_="kpi-icon-badge kpi-badge-slate"
                ),
                theme=None,
                class_="bslib-value-box kpi-missing-high" if cr4_sum > 50 else "bslib-value-box"
            ),
            ui.value_box(
                "Tasa Directa Top 10",
                f"{direct_avg_top10:.1f}%",
                ui.p("Promedio asignado a dedo a los líderes", class_="text-muted small mb-0"),
                showcase=ui.div(
                    ui.span("%Dir", class_="fw-bold font-monospace text-warning", style="font-size: 0.95rem;"),
                    class_="kpi-icon-badge kpi-badge-semantic"
                ),
                theme=None,
                class_="bslib-value-box kpi-missing-high" if direct_avg_top10 > 65 else "bslib-value-box"
            ),
            col_widths={"sm": 12, "md": 6, "lg": 3},
            class_="g-3 mb-2"
        )

    # -------------------------------------------------------------
    # 2. GRÁFICO DE BARRAS: TOP 15 CONTRATISTAS
    # -------------------------------------------------------------
    @output
    @render.ui
    def contractors_bar_container():
        c_df = contractors_df()
        if c_df.empty:
            return ui.span()

        top15 = c_df.head(15).iloc[::-1]

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=top15["monto_total"],
            y=[str(p)[:30] for p in top15["proveedor"]],
            orientation="h",
            marker=dict(color="#1d3190"),
            customdata=np.stack((
                top15["cuota_pct"],
                top15["n_contratos"],
                top15["pct_directa"],
                top15["n_departamentos"]
            ), axis=-1),
            hovertemplate=(
                "<b>%{y}</b><br>"
                "Presupuesto: %{x:$,.0f} COP<br>"
                "Cuota Nacional: %{customdata[0]:.2f}%<br>"
                "Contratos: %{customdata[1]:,}<br>"
                "% Contratación Directa: %{customdata[2]:.1f}%<br>"
                "Departamentos: %{customdata[3]}<extra></extra>"
            )
        ))

        fig.update_layout(
            title="Top 15 Contratistas por Presupuesto Acumulado",
            xaxis_title="Presupuesto Adjudicado (COP)",
            height=400,
            margin=dict(t=50, b=40, l=170, r=20),
            plot_bgcolor="white",
            paper_bgcolor="white"
        )
        fig.update_xaxes(showgrid=True, gridcolor="#edf2e9")
        fig.update_yaxes(showgrid=False)

        return ui.HTML(fig.to_html(include_plotlyjs=False, full_html=False))

    # -------------------------------------------------------------
    # 3. GRÁFICO DE DISPERSIÓN: MONTO VS % DIRECTA
    # -------------------------------------------------------------
    @output
    @render.ui
    def contractors_scatter_container():
        c_df = contractors_df()
        if c_df.empty:
            return ui.span()

        plot_df = c_df.head(30).copy()

        color_map = {
            "Predominio Directo (Sin Concurso)": "#dc2626",
            "Mixto / Moderado": "#d97706",
            "Concurso Competitivo": "#059669"
        }
        marker_colors = [color_map.get(a, "#1d3190") for a in plot_df["alerta"]]

        sizes = 10 + (plot_df["n_departamentos"] / max(1, plot_df["n_departamentos"].max())) * 25

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=plot_df["pct_directa"],
            y=plot_df["monto_total"],
            mode="markers+text",
            text=[str(p)[:18] for p in plot_df["proveedor"]],
            textposition="top center",
            textfont=dict(size=8.5, color="#273766"),
            marker=dict(
                size=sizes,
                color=marker_colors,
                opacity=0.85,
                line=dict(color="#ffffff", width=1.5)
            ),
            customdata=np.stack((
                plot_df["alerta"],
                plot_df["n_contratos"],
                plot_df["n_departamentos"],
                plot_df["monto_total"].apply(format_cop_currency)
            ), axis=-1),
            hovertemplate=(
                "<b>%{text}</b><br>"
                "Alerta: %{customdata[0]}<br>"
                "Contratación Directa: %{x:.1f}%<br>"
                "Presupuesto: %{customdata[3]}<br>"
                "Contratos: %{customdata[1]:,}<br>"
                "Departamentos de Presencia: %{customdata[2]}<extra></extra>"
            )
        ))

        fig.add_vline(x=65, line_dash="dash", line_color="#dc2626", annotation_text="Directa > 65%", annotation_position="top right")

        fig.update_layout(
            title="Presupuesto Adjudicado vs Tasa de Asignación a Dedo",
            xaxis_title="% de Presupuesto Obtenido por Contratación Directa",
            yaxis_title="Presupuesto Total (COP)",
            height=400,
            margin=dict(t=50, b=40, l=40, r=20),
            plot_bgcolor="#fcfdfd",
            paper_bgcolor="white"
        )
        fig.update_xaxes(showgrid=True, gridcolor="#edf2e9", range=[0, 105])
        fig.update_yaxes(showgrid=True, gridcolor="#edf2e9")

        return ui.HTML(fig.to_html(include_plotlyjs=False, full_html=False))

    # -------------------------------------------------------------
    # 4. TABLA DE CONTRATISTAS
    # -------------------------------------------------------------
    @output
    @render.data_frame
    def contractors_data_table():
        c_df = contractors_df()
        if c_df.empty:
            return pd.DataFrame()

        display_df = c_df[[
            "alerta", "proveedor", "monto_total", "n_contratos",
            "n_departamentos", "cuota_pct", "pct_directa"
        ]].copy()

        display_df["monto_total"] = display_df["monto_total"].apply(format_cop_currency)

        display_df.columns = [
            "Alerta de Riesgo", "Contratista / Razón Social", "Presupuesto Total",
            "Contratos", "Departamentos", "Cuota (%)", "% Contratación Directa"
        ]

        return render.DataGrid(display_df, filters=True, selection_mode="none")

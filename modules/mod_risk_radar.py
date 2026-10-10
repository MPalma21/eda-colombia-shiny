"""Modulo de Radar Territorial y Semaforos de Riesgo en Contratacion Publica (SECOP II).

Perspectiva 1 del Panel de Riesgo Territorial:
- Semaforos y clasificacion de riesgo departamental (Critico, Moderado, Competitivo).
- Filtros por nivel de alerta y volumen contractual.
- Ranking territorial por indice HHI y tasa de contratacion directa.
- Cuadrante analitico de dispersion (% Directa vs HHI de Concentracion).
- Panel de Alertas Tempranas con diagnostico de vulnerabilidades prioritarias.
"""
from shiny import module, ui, render, reactive
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from services.stats_service import classify_columns
from services.economic_service import (
    compute_procurement_risk_matrix,
    get_procurement_risk_summary,
    find_procurement_columns,
    format_cop_currency
)


@module.ui
def risk_radar_ui():
    return ui.div(
        # Tarjeta 1: Controles de Auditoria y Parametrizacion
        ui.card(
            ui.card_header(
                ui.div(
                    ui.span("Radar Territorial de Alertas y Semáforos de Contratación (SECOP II)", class_="fw-bold"),
                    ui.span("Metodología: Concentración HHI de Oferentes & Tasa de Contratación Directa", class_="text-muted", style="font-size: 0.78rem;")
                ),
                class_="d-flex justify-content-between align-items-center"
            ),
            ui.output_ui("radar_controls_ui"),
            ui.output_ui("radar_summary_cards"),
            full_screen=False,
            class_="mb-3"
        ),

        # Tarjeta 2: Visualizaciones Centrales (Ranking y Cuadrante de Riesgo)
        ui.card(
            ui.card_header(
                ui.div(
                    ui.span("Evaluación Comparativa Interdepartamental & Cuadrantes de Alerta", class_="fw-bold"),
                    ui.span("Líneas de Umbral Normativo: HHI = 2,500 pts | Contratación Directa = 65%", class_="text-muted", style="font-size: 0.78rem;")
                ),
                class_="d-flex justify-content-between align-items-center"
            ),
            ui.layout_columns(
                ui.output_ui("radar_bars_container"),
                ui.output_ui("radar_quadrant_container"),
                col_widths={"sm": 12, "lg": (7, 5)},
                class_="g-3"
            ),
            full_screen=True,
            class_="mb-3"
        ),

        # Tarjeta 3: Panel de Alertas Tempranas Prioritarias
        ui.card(
            ui.card_header(
                ui.div(
                    ui.span("Panel de Alertas Tempranas · Departamentos en Situación Crítica", class_="fw-bold"),
                    ui.span("Identificación de Factores Detonantes de Riesgo Fiscal y Anticompetitivo", class_="text-muted", style="font-size: 0.78rem;")
                ),
                class_="d-flex justify-content-between align-items-center"
            ),
            ui.output_ui("radar_early_alerts_container"),
            full_screen=True
        )
    )


@module.server
def risk_radar_server(input, output, session, df_react):

    # -------------------------------------------------------------
    # 1. CONTROLES Y FILTROS
    # -------------------------------------------------------------
    @output
    @render.ui
    def radar_controls_ui():
        df = df_react()
        if df.empty:
            return ui.div(
                ui.div(
                    ui.h5("Bienvenido al Panel de Alertas y Semáforos de Riesgo Territorial", class_="fw-bold text-primary mb-2"),
                    ui.p(
                        "Herramienta especializada de analítica económica e industrial para auditar la contratación estatal en Colombia. "
                        "Permite detectar concentración de mercado, falta de concurrencia y presunto direccionamiento de contratos públicos "
                        "en los 32 departamentos y el Distrito Capital a partir de microdatos de SECOP II.",
                        class_="text-secondary mb-3",
                        style="font-size: 0.92rem; line-height: 1.5;"
                    ),
                    ui.layout_columns(
                        ui.div(
                            ui.div(
                                ui.span("1", class_="guide-step-number"),
                                ui.h6("Configure la Consulta", class_="fw-bold text-dark mb-1", style="font-size: 0.88rem;"),
                                ui.p("En la barra lateral izquierda, seleccione la fuente (SECOP II recomendada) y el volumen de contratos a auditar.", class_="small text-muted mb-0"),
                                class_="guide-step-card"
                            )
                        ),
                        ui.div(
                            ui.div(
                                ui.span("2", class_="guide-step-number"),
                                ui.h6("Presione Cargar y Auditar", class_="fw-bold text-dark mb-1", style="font-size: 0.88rem;"),
                                ui.p("El sistema descargará los registros en tiempo real directamente desde la API oficial de datos.gov.co sin intermediarios.", class_="small text-muted mb-0"),
                                class_="guide-step-card"
                            )
                        ),
                        ui.div(
                            ui.div(
                                ui.span("3", class_="guide-step-number"),
                                ui.h6("Explore los 5 Módulos", class_="fw-bold text-dark mb-1", style="font-size: 0.88rem;"),
                                ui.p("Consulte el Radar Interdepartamental, audite contratos atípicos, analice oligopolios de proveedores y simule reformas fiscales.", class_="small text-muted mb-0"),
                                class_="guide-step-card"
                            )
                        ),
                        col_widths={"sm": 12, "md": 4},
                        class_="g-3 mb-3"
                    ),
                    ui.div(
                        ui.span("Criterios de Semáforo de un Vistazo: ", class_="fw-bold text-primary small"),
                        ui.span("Rojo (Crítico): HHI > 2,500 o Contratación Directa > 65% | Amarillo (Moderado): HHI 1,500-2,500 o Directa 35%-65% | Verde (Competitivo): HHI < 1,500 y Directa < 35%.", class_="small text-muted"),
                        class_="guide-callout"
                    ),
                    class_="guide-hero-card mb-2"
                )
            )

        num_cols, _, cat_cols = classify_columns(df)
        all_cols = list(df.columns)
        dept_c, val_c, prov_c, mod_c = find_procurement_columns(df)

        return ui.div(
            ui.layout_columns(
                ui.input_select("radar_risk_filter", "Filtrar por Nivel de Riesgo:", choices=[
                    "Todos los Departamentos",
                    "Solo Alto Riesgo (Críticos)",
                    "Solo Riesgo Moderado",
                    "Solo Bajo Riesgo (Competitivos)"
                ], selected="Todos los Departamentos"),
                ui.input_select("radar_dept_col", "Columna de Departamento:", choices=cat_cols or all_cols, selected=dept_c or (cat_cols[0] if cat_cols else all_cols[0])),
                ui.input_select("radar_val_col", "Columna de Monto Contractual:", choices=["(Solo conteo de contratos)"] + num_cols, selected=val_c or (num_cols[0] if num_cols else "(Solo conteo de contratos)")),
                ui.input_select("radar_mod_col", "Columna de Modalidad:", choices=["(Sin modalidad)"] + (cat_cols or all_cols), selected=mod_c or (cat_cols[2] if len(cat_cols) > 2 else "(Sin modalidad)")),
                col_widths={"sm": 12, "md": 6, "lg": 3},
                class_="g-2 mb-2"
            ),
            ui.div(
                ui.div(
                    ui.span("Guía de Interpretación del Radar y Cuadrantes: ", class_="fw-bold text-primary small"),
                    ui.span("Score de Riesgo Territorial = 0.55 × (% Directa) + 0.45 × (HHI / 100). ", class_="small text-secondary fw-semibold"),
                    ui.span("Cuadrante Superior Derecho: Territorios críticos con alta contratación a dedo y monopolio de contratistas. Cuadrante Inferior Izquierdo: Territorios competitivos con pluralidad de oferentes.", class_="small text-muted"),
                    class_="guide-callout mb-3"
                )
            )
        )

    # -------------------------------------------------------------
    # 2. CALCULO BASE DE MATRIZ DE RIESGO
    # -------------------------------------------------------------
    @reactive.calc
    def full_matrix_df():
        df = df_react()
        if df.empty:
            return pd.DataFrame()

        dept_col = input.radar_dept_col() if hasattr(input, "radar_dept_col") and input.radar_dept_col() else None
        val_col = input.radar_val_col() if hasattr(input, "radar_val_col") and input.radar_val_col() != "(Solo conteo de contratos)" else None
        mod_col = input.radar_mod_col() if hasattr(input, "radar_mod_col") and input.radar_mod_col() != "(Sin modalidad)" else None

        return compute_procurement_risk_matrix(
            df=df,
            dept_col=dept_col,
            val_col=val_col,
            mod_col=mod_col,
            min_contracts_per_dept=1
        )

    @reactive.calc
    def filtered_matrix_df():
        matrix = full_matrix_df()
        if matrix.empty:
            return matrix

        filt = input.radar_risk_filter() if hasattr(input, "radar_risk_filter") else "Todos los Departamentos"
        if filt == "Solo Alto Riesgo (Críticos)":
            return matrix[matrix["nivel_riesgo"] == "Alto Riesgo (Crítico)"].copy()
        elif filt == "Solo Riesgo Moderado":
            return matrix[matrix["nivel_riesgo"] == "Riesgo Moderado"].copy()
        elif filt == "Solo Bajo Riesgo (Competitivos)":
            return matrix[matrix["nivel_riesgo"] == "Bajo Riesgo (Competitivo)"].copy()
        return matrix

    # -------------------------------------------------------------
    # 3. VALUE BOXES NACIONALES
    # -------------------------------------------------------------
    @output
    @render.ui
    def radar_summary_cards():
        matrix = full_matrix_df()
        if matrix.empty:
            return ui.span()

        summary = get_procurement_risk_summary(matrix)
        if not summary.get("valido", False):
            return ui.span()

        criticos_badge_class = "bslib-value-box kpi-missing-high" if summary["criticos"] > 0 else "bslib-value-box"

        return ui.layout_columns(
            ui.value_box(
                "Presupuesto Auditado",
                format_cop_currency(summary["monto_total"]),
                ui.p(f"{summary['total_contratos']:,} contratos analizados", class_="text-muted small mb-0"),
                showcase=ui.div(
                    ui.span("COP", class_="fw-bold font-monospace text-primary", style="font-size: 0.95rem;"),
                    class_="kpi-icon-badge kpi-badge-blue"
                ),
                theme=None,
                class_="bslib-value-box"
            ),
            ui.value_box(
                "Alertas Críticas",
                f"{summary['criticos']} / {summary['n_departamentos']}",
                ui.p(f"Moderados: {summary['moderados']} | Competitivos: {summary['competitivos']}", class_="text-muted small mb-0"),
                showcase=ui.div(
                    ui.span("!", class_="fw-bold text-danger", style="font-size: 1.4rem;"),
                    class_="kpi-icon-badge kpi-badge-semantic"
                ),
                theme=None,
                class_=criticos_badge_class
            ),
            ui.value_box(
                "% Contratación Directa",
                f"{summary['pct_directa_promedio']:.1f}%",
                ui.p("Tasa nacional ponderada", class_="text-muted small mb-0"),
                showcase=ui.div(
                    ui.span("%", class_="fw-bold text-info", style="font-size: 1.4rem;"),
                    class_="kpi-icon-badge kpi-badge-teal"
                ),
                theme=None,
                class_="bslib-value-box"
            ),
            ui.value_box(
                "Concentración HHI",
                f"{summary['hhi_promedio']:,.0f} pts",
                ui.p(f"Mayor riesgo: {summary['depto_mayor_riesgo']}", class_="text-muted small mb-0"),
                showcase=ui.div(
                    ui.span("HHI", class_="fw-bold font-monospace text-secondary", style="font-size: 0.95rem;"),
                    class_="kpi-icon-badge kpi-badge-slate"
                ),
                theme=None,
                class_="bslib-value-box"
            ),
            col_widths={"sm": 12, "md": 6, "lg": 3},
            class_="g-3 mb-2"
        )

    # -------------------------------------------------------------
    # 4. RANKING DE BARRAS INTERDEPARTAMENTAL
    # -------------------------------------------------------------
    @output
    @render.ui
    def radar_bars_container():
        matrix = filtered_matrix_df()
        if matrix.empty:
            return ui.p("No hay departamentos que coincidan con el filtro seleccionado.", class_="text-muted")

        top_matrix = matrix.head(22).copy()

        color_map = {
            "Alto Riesgo (Crítico)": "#dc2626",
            "Riesgo Moderado": "#d97706",
            "Bajo Riesgo (Competitivo)": "#059669"
        }
        bar_colors = [color_map.get(lvl, "#1d3190") for lvl in top_matrix["nivel_riesgo"]]

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=top_matrix["departamento"],
            y=top_matrix["hhi"],
            marker=dict(color=bar_colors),
            customdata=np.stack((
                top_matrix["nivel_riesgo"],
                top_matrix["score_riesgo"],
                top_matrix["pct_directa_monto"],
                top_matrix["monto_total"].apply(format_cop_currency),
                top_matrix["top_contratista"],
                top_matrix["top_cuota"]
            ), axis=-1),
            hovertemplate=(
                "<b>%{x}</b><br>"
                "Semáforo: %{customdata[0]}<br>"
                "Score Riesgo: %{customdata[1]} pts<br>"
                "HHI Contratistas: %{y:,.1f}<br>"
                "% Contratación Directa: %{customdata[2]}%<br>"
                "Presupuesto: %{customdata[3]}<br>"
                "Top Contratista: %{customdata[4]} (%{customdata[5]}%)<extra></extra>"
            )
        ))

        fig.add_hline(y=2500, line_dash="dash", line_color="#dc2626", annotation_text="Límite Crítico (2500)", annotation_position="top right")
        fig.add_hline(y=1500, line_dash="dot", line_color="#d97706", annotation_text="Límite Moderado (1500)", annotation_position="top right")

        fig.update_layout(
            title="Ranking Departamental por Concentración (HHI) y Semáforo",
            xaxis_title="Departamento",
            yaxis_title="Índice HHI (0 - 10,000)",
            height=430,
            margin=dict(t=50, b=80, l=40, r=30),
            plot_bgcolor="white",
            paper_bgcolor="white"
        )
        fig.update_xaxes(tickangle=-40, showgrid=False)
        fig.update_yaxes(showgrid=True, gridcolor="#edf2e9")

        return ui.HTML(fig.to_html(include_plotlyjs="cdn", full_html=False))

    # -------------------------------------------------------------
    # 5. CUADRANTE DE RIESGO (% DIRECTA VS HHI)
    # -------------------------------------------------------------
    @output
    @render.ui
    def radar_quadrant_container():
        matrix = filtered_matrix_df()
        if matrix.empty:
            return ui.span()

        plot_df = matrix.copy()
        max_monto = plot_df["monto_total"].max()
        if max_monto > 0:
            sizes = 12 + (plot_df["monto_total"] / max_monto) * 35
        else:
            sizes = [15] * len(plot_df)

        color_map = {
            "Alto Riesgo (Crítico)": "#dc2626",
            "Riesgo Moderado": "#d97706",
            "Bajo Riesgo (Competitivo)": "#059669"
        }
        marker_colors = [color_map.get(lvl, "#1d3190") for lvl in plot_df["nivel_riesgo"]]

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=plot_df["pct_directa_monto"],
            y=plot_df["hhi"],
            mode="markers+text",
            text=plot_df["departamento"],
            textposition="top center",
            textfont=dict(size=9, color="#273766"),
            marker=dict(
                size=sizes,
                color=marker_colors,
                opacity=0.82,
                line=dict(color="#ffffff", width=1.5)
            ),
            customdata=np.stack((
                plot_df["nivel_riesgo"],
                plot_df["monto_total"].apply(format_cop_currency),
                plot_df["top_contratista"],
                plot_df["top_cuota"]
            ), axis=-1),
            hovertemplate=(
                "<b>%{text}</b><br>"
                "Semáforo: %{customdata[0]}<br>"
                "Contratación Directa: %{x:.1f}%<br>"
                "HHI Contratistas: %{y:,.1f}<br>"
                "Monto: %{customdata[1]}<br>"
                "Top Contratista: %{customdata[2]} (%{customdata[3]}%)<extra></extra>"
            )
        ))

        fig.add_vline(x=65, line_dash="dash", line_color="#dc2626", annotation_text="Directa > 65%", annotation_position="top right")
        fig.add_hline(y=2500, line_dash="dash", line_color="#dc2626", annotation_text="HHI > 2500", annotation_position="top left")

        fig.update_layout(
            title="Cuadrante de Riesgo: Directa vs Concentración",
            xaxis_title="% Contratación Directa (Monto)",
            yaxis_title="HHI de Concentración",
            height=430,
            margin=dict(t=50, b=40, l=40, r=30),
            plot_bgcolor="#fcfdfd",
            paper_bgcolor="white"
        )
        fig.update_xaxes(showgrid=True, gridcolor="#edf2e9", range=[0, 105])
        fig.update_yaxes(showgrid=True, gridcolor="#edf2e9", range=[0, max(3000, plot_df['hhi'].max() * 1.1)])

        return ui.HTML(fig.to_html(include_plotlyjs=False, full_html=False))

    # -------------------------------------------------------------
    # 6. PANEL DE ALERTAS TEMPRANAS
    # -------------------------------------------------------------
    @output
    @render.ui
    def radar_early_alerts_container():
        matrix = full_matrix_df()
        if matrix.empty:
            return ui.span()

        criticos = matrix[matrix["nivel_riesgo"] == "Alto Riesgo (Crítico)"].head(6)
        if criticos.empty:
            return ui.div(
                ui.span("No se detectaron departamentos en situación crítica bajo los umbrales seleccionados.", class_="text-success fw-bold"),
                class_="p-3 bg-light rounded"
            )

        alert_cards = []
        for _, row in criticos.iterrows():
            card = ui.div(
                ui.div(
                    ui.div(
                        ui.span(f"Alerta Crítica: {row['departamento']}", class_="fw-bold text-danger fs-6"),
                        ui.span(f"Score: {row['score_riesgo']:.1f} / 100", class_="badge-risk-high"),
                        class_="d-flex justify-content-between align-items-center mb-2"
                    ),
                    ui.div(
                        f"Presupuesto: {format_cop_currency(row['monto_total'])} ({row['n_contratos']:,} contratos)",
                        class_="small text-dark fw-semibold mb-1"
                    ),
                    ui.div(
                        ui.span("• Tasa Directa: ", class_="fw-bold text-secondary"),
                        ui.span(f"{row['pct_directa_monto']:.1f}% del presupuesto sin licitación.", class_="text-danger fw-semibold"),
                        class_="small mb-1"
                    ),
                    ui.div(
                        ui.span("• Concentración HHI: ", class_="fw-bold text-secondary"),
                        ui.span(f"{row['hhi']:,.1f} pts (mercado altamente oligopólico).", class_="text-danger fw-semibold"),
                        class_="small mb-1"
                    ),
                    ui.div(
                        ui.span("• Actor Dominante: ", class_="fw-bold text-secondary"),
                        ui.span(f"'{row['top_contratista']}' concentra el {row['top_cuota']:.1f}% de las adjudicaciones.", class_="text-secondary"),
                        class_="small"
                    ),
                    class_="p-3 bg-white rounded border border-danger shadow-sm h-100"
                ),
                class_="col-12 col-md-6 col-lg-4 mb-3"
            )
            alert_cards.append(card)

        return ui.div(
            ui.div(
                *alert_cards,
                class_="row g-3"
            )
        )

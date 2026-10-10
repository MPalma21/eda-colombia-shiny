"""Modulo de Simulador de Politica Economica y Desconcentracion Contractual.

Herramienta contrafactual '¿Que pasa si...?':
- Simula reduccion de contratacion directa y apertura competitiva a MIPYMES.
- Proyecta disminucion del indice HHI y desconcentracion del gasto publico.
- Estima ahorros fiscales para el erario bajo benchmarks internacionales de la OCDE (10-18%).
- Compara escenarios base vs reformado a nivel nacional o departamental.
"""
from shiny import module, ui, render, reactive
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from services.economic_service import (
    compute_procurement_risk_matrix,
    get_procurement_risk_summary,
    simulate_policy_procurement,
    format_cop_currency
)
from components.plot_theme import apply_ggplot2_theme, GGPLOT2_PALETTE


@module.ui
def simulator_ui():
    return ui.div(
        # Tarjeta 1: Parametros de Politica y Sliders
        ui.card(
            ui.card_header(
                ui.div(
                    ui.span("Simulador de Política Económica · Desconcentración y Ahorro Fiscal", class_="fw-bold"),
                    ui.span("Modelo Contrafactual de Reforma a la Contratación Pública", class_="text-muted", style="font-size: 0.78rem;")
                ),
                class_="d-flex justify-content-between align-items-center"
            ),
            ui.output_ui("sim_controls_ui"),
            full_screen=False,
            class_="mb-3"
        ),

        # Tarjeta 2: Banner de Impacto Fiscal y Proyecciones Contrafactuales
        ui.card(
            ui.card_header(
                ui.div(
                    ui.span("Resultados del Escenario Simulado vs Línea Base Actual", class_="fw-bold"),
                    ui.span("Benchmark OCDE: 12.5% de ahorro en compras migradas a concurso abierto", class_="text-muted", style="font-size: 0.78rem;")
                ),
                class_="d-flex justify-content-between align-items-center"
            ),
            ui.output_ui("sim_saving_banner_ui"),
            ui.output_ui("sim_comparison_cards_ui"),
            ui.layout_columns(
                ui.output_ui("sim_bars_plot_container"),
                ui.output_ui("sim_waterfall_plot_container"),
                col_widths={"sm": 12, "lg": (6, 6)},
                class_="g-3 mt-2"
            ),
            full_screen=True
        )
    )


@module.server
def simulator_server(input, output, session, df_react):

    # Calculo reactivo base de la matriz para alimentar opciones y totales
    @reactive.calc
    def baseline_matrix():
        df = df_react()
        if df.empty:
            return pd.DataFrame()
        return compute_procurement_risk_matrix(df, min_contracts_per_dept=1)

    @output
    @render.ui
    def sim_controls_ui():
        df = df_react()
        if df.empty:
            return ui.div(
                ui.div(
                    ui.h6("Simulador de Política Económica y Reforma a la Contratación", class_="fw-bold text-primary mb-2"),
                    ui.p(
                        "Este modelo econométrico contrafactual permite proyectar el impacto fiscal y competitivo de reformas públicas. "
                        "Simula la sustitución de convenios directos por licitaciones abiertas con pliegos tipo, calcula el ahorro fiscal "
                        "esperado (según benchmarks de la OCDE y Banco Mundial) y proyecta la desconcentración del índice HHI. "
                        "Cargue contratos desde la barra lateral izquierda para activar el simulador.",
                        class_="small text-secondary mb-0"
                    ),
                    class_="guide-callout mb-2"
                )
            )

        matrix = baseline_matrix()
        dept_choices = ["Nivel Nacional (Consolidado)"]
        if not matrix.empty:
            dept_choices += matrix["departamento"].tolist()

        return ui.div(
            ui.layout_columns(
                ui.input_select("sim_territory", "Ámbito Territorial a Reformar:", choices=dept_choices, selected="Nivel Nacional (Consolidado)"),
                ui.input_slider("sim_reduce_direct", "Reducción de Contratación Directa (%):", min=0, max=80, value=30, step=5),
                ui.input_slider("sim_concurrency", "Apertura a Nuevas MIPYMES / Oferentes (%):", min=0, max=100, value=25, step=5),
                ui.input_slider("sim_savings_rate", "Tasa de Ahorro por Licitación (%):", min=5.0, max=25.0, value=12.5, step=0.5),
                col_widths={"sm": 12, "md": 6, "lg": 3},
                class_="g-2 mb-2"
            ),
            ui.div(
                ui.span("Fundamento de Finanzas Públicas & Política Económica: ", class_="fw-bold text-primary small"),
                ui.span(
                    "Al sustituir convenios directos por licitaciones públicas de pliego tipo (Ley 2014 de 2019), la puja competitiva "
                    "reduce los sobrecostos de adjudicación (ahorro fiscal entre 8% y 20% según el Banco Mundial) y distribuye los contratos "
                    "entre más competidores, logrando una desconcentración estructural del índice HHI.",
                    class_="small text-muted"
                ),
                class_="guide-callout mb-1"
            )
        )

    # Calculo reactivo de la simulacion
    @reactive.calc
    def simulation_result():
        matrix = baseline_matrix()
        if matrix.empty or not hasattr(input, "sim_territory"):
            return {}

        territory = input.sim_territory()
        r_direct = float(input.sim_reduce_direct() if hasattr(input, "sim_reduce_direct") else 30)
        r_comp = float(input.sim_concurrency() if hasattr(input, "sim_concurrency") else 25)
        benchmark = float(input.sim_savings_rate() if hasattr(input, "sim_savings_rate") else 12.5)

        if territory == "Nivel Nacional (Consolidado)":
            summary = get_procurement_risk_summary(matrix)
            base_monto = summary["monto_total"]
            base_direct_pct = summary["pct_directa_promedio"]
            base_hhi = summary["hhi_promedio"]
        else:
            sub = matrix[matrix["departamento"] == territory]
            if sub.empty:
                return {}
            row = sub.iloc[0]
            base_monto = row["monto_total"]
            base_direct_pct = row["pct_directa_monto"]
            base_hhi = row["hhi"]

        # Si el monto es 0 (ej. dataset sin columna de valor), usamos 10,000,000,000 COP simulados
        if base_monto <= 0:
            base_monto = 5_000_000_000

        res = simulate_policy_procurement(
            base_monto=base_monto,
            base_direct_pct=base_direct_pct,
            base_hhi=base_hhi,
            reduction_direct_pct=r_direct,
            new_competitors_pct=r_comp,
            saving_benchmark_pct=benchmark
        )
        res["territorio"] = territory
        return res

    # -------------------------------------------------------------
    # BANNER DE AHORRO FISCAL DESTACADO
    # -------------------------------------------------------------
    @output
    @render.ui
    def sim_saving_banner_ui():
        res = simulation_result()
        if not res:
            return ui.span()

        ahorro_str = format_cop_currency(res["ahorro_fiscal_estimado"])
        trasladado_str = format_cop_currency(res["monto_trasladado"])

        return ui.div(
            ui.div(
                ui.div(
                    ui.span("AHORRO FISCAL PROYECTADO PARA EL ESTADO", class_="small text-white-50 fw-bold letter-spacing-1"),
                    ui.div(ahorro_str, class_="fs-2 fw-bold text-white my-1 font-monospace"),
                    ui.div(
                        f"Monto redireccionado a subasta abierta y licitaciones: {trasladado_str} "
                        f"| Nuevos oferentes y MIPYMES beneficiados: +{res['nuevos_oferentes_est']} proveedores",
                        class_="text-white-50 small"
                    ),
                    class_="d-flex flex-column"
                ),
                class_="sim-saving-banner mb-3"
            )
        )

    # -------------------------------------------------------------
    # TARJETAS ANTES VS DESPUES
    # -------------------------------------------------------------
    @output
    @render.ui
    def sim_comparison_cards_ui():
        res = simulation_result()
        if not res:
            return ui.span()

        delta_dir = res["nuevo_direct_pct"] - res["base_direct_pct"]
        delta_dir_str = f"{delta_dir:+.1f}%"

        delta_hhi_str = f"{res['delta_hhi']:+,.0f} pts (-{res['pct_reduccion_hhi']:.1f}%)"

        return ui.layout_columns(
            # Tarjeta 1: Escenario Actual
            ui.div(
                ui.div(
                    ui.span("LÍNEA BASE ACTUAL (SIN REFORMA)", class_="text-muted small fw-bold text-uppercase"),
                    ui.span(f"Territorio: {res['territorio']}", class_="small text-secondary fw-semibold"),
                    class_="d-flex justify-content-between align-items-center mb-3 border-bottom pb-2"
                ),
                ui.div(
                    ui.div(
                        ui.span("Contratación Directa:", class_="text-secondary small"),
                        ui.div(f"{res['base_direct_pct']:.1f}%", class_="fs-4 fw-bold font-monospace text-dark"),
                        class_="mb-2"
                    ),
                    ui.div(
                        ui.span("Índice de Concentración (HHI):", class_="text-secondary small"),
                        ui.div(f"{res['base_hhi']:,.1f} pts", class_="fs-4 fw-bold font-monospace text-dark"),
                        class_="mb-2"
                    ),
                    ui.div(
                        ui.span("Clasificación de Riesgo:", class_="text-secondary small d-block mb-1"),
                        ui.HTML(f"<span class='{res['class_base']}'>{res['icon_base']} {res['nivel_base']}</span>"),
                        class_="mb-1"
                    ),
                ),
                class_="sim-box-current"
            ),

            # Tarjeta 2: Escenario Contrafactual Reformado
            ui.div(
                ui.div(
                    ui.span("ESCENARIO SIMULADO (CON REFORMA)", class_="text-success small fw-bold text-uppercase"),
                    ui.span("Reforma Competitiva", class_="badge bg-success small"),
                    class_="d-flex justify-content-between align-items-center mb-3 border-bottom pb-2"
                ),
                ui.div(
                    ui.div(
                        ui.span("Nueva Contratación Directa:", class_="text-secondary small"),
                        ui.div(
                            f"{res['nuevo_direct_pct']:.1f}% ",
                            ui.span(delta_dir_str, class_="sim-kpi-diff-positive fs-6"),
                            class_="fs-4 fw-bold font-monospace text-dark"
                        ),
                        class_="mb-2"
                    ),
                    ui.div(
                        ui.span("Nuevo HHI Desconcentrado:", class_="text-secondary small"),
                        ui.div(
                            f"{res['nuevo_hhi']:,.1f} pts ",
                            ui.span(delta_hhi_str, class_="sim-kpi-diff-positive fs-6"),
                            class_="fs-4 fw-bold font-monospace text-dark"
                        ),
                        class_="mb-2"
                    ),
                    ui.div(
                        ui.span("Nueva Clasificación de Riesgo:", class_="text-secondary small d-block mb-1"),
                        ui.HTML(f"<span class='{res['class_nuevo']}'>{res['icon_nuevo']} {res['nivel_nuevo']}</span>"),
                        class_="mb-1"
                    ),
                ),
                class_="sim-box-counterfactual"
            ),
            col_widths={"sm": 12, "md": 6},
            class_="g-3 mb-2"
        )

    # -------------------------------------------------------------
    # GRÁFICO 1: COMPARATIVA VISUAL DE BARRAS ANTES VS DESPUÉS
    # -------------------------------------------------------------
    @output
    @render.ui
    def sim_bars_plot_container():
        res = simulation_result()
        if not res:
            return ui.span()

        fig = go.Figure()

        categories = ["% Contratación Directa", "HHI Normalizado (/100)"]
        vals_base = [res["base_direct_pct"], min(100.0, res["base_hhi"] / 100.0)]
        vals_sim = [res["nuevo_direct_pct"], min(100.0, res["nuevo_hhi"] / 100.0)]

        fig.add_trace(go.Bar(
            name="Escenario Actual",
            x=categories,
            y=vals_base,
            marker=dict(
                color="#dc2626",
                line=dict(color="#ffffff", width=1)
            ),
            opacity=0.88,
            text=[f"{v:.1f}" for v in vals_base],
            textposition="auto"
        ))

        fig.add_trace(go.Bar(
            name="Escenario Simulado",
            x=categories,
            y=vals_sim,
            marker=dict(
                color="#059669",
                line=dict(color="#ffffff", width=1)
            ),
            opacity=0.88,
            text=[f"{v:.1f}" for v in vals_sim],
            textposition="auto"
        ))

        fig.update_layout(barmode="group")
        apply_ggplot2_theme(
            fig,
            title=f"Impacto Regulatorio: {res['territorio']}",
            subtitle="Comparativa de indicadores clave entre statu quo y política reformada",
            yaxis_title="Escala Normalizada (0 - 100)",
            height=360,
            margin=dict(t=50, b=40, l=45, r=20),
            show_legend=True,
            legend_orientation="h",
            x_grid=False,
            y_grid=True
        )
        fig.update_yaxes(range=[0, max(110, max(vals_base) * 1.15)])

        return ui.HTML(fig.to_html(include_plotlyjs=False, full_html=False))

    # -------------------------------------------------------------
    # GRÁFICO 2: DESCOMPOSICIÓN DEL PRESUPUESTO Y AHORRO
    # -------------------------------------------------------------
    @output
    @render.ui
    def sim_waterfall_plot_container():
        res = simulation_result()
        if not res:
            return ui.span()

        total = res["base_monto"]
        ahorro = res["ahorro_fiscal_estimado"]
        competencia = res["monto_trasladado"] - ahorro
        directa_remanente = res["base_monto"] * (res["nuevo_direct_pct"] / 100.0)
        resto = max(0.0, total - (ahorro + competencia + directa_remanente))

        labels = [
            "Ahorro Fiscal Neto (OCDE)",
            "Monto Concursado Efectivo",
            "Contratación Directa Restante",
            "Otros Procesos Competitivos"
        ]
        values = [ahorro, competencia, directa_remanente, resto]
        colors = ["#059669", "#1d3190", "#dc2626", "#64748b"]

        fig = go.Figure(data=[go.Pie(
            labels=labels,
            values=values,
            hole=0.48,
            marker=dict(
                colors=colors,
                line=dict(color="#ffffff", width=2)
            ),
            hovertemplate="<b>%{label}</b><br>Monto: %{value:$,.0f} COP<br>Proporción: %{percent}<extra></extra>"
        )])

        apply_ggplot2_theme(
            fig,
            title="Estructura Presupuestal Contrafactual",
            subtitle="Descomposición presupuestal proyectada tras aplicar la reforma",
            height=360,
            margin=dict(t=50, b=30, l=20, r=20),
            show_legend=True,
            legend_orientation="v"
        )
        fig.update_xaxes(showline=False, ticks="", showgrid=False)
        fig.update_yaxes(showline=False, ticks="", showgrid=False)

        return ui.HTML(fig.to_html(include_plotlyjs=False, full_html=False))

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
from components.plot_theme import (
    apply_ggplot2_theme,
    to_ggplot2_html,
    BLUE_NAVY,
    BLUE_SKY,
    BLUE_COBALT,
    GGPLOT2_FONT_FAMILY,
    GGPLOT_SEMAPHORE,
    THEME_PRIMARY,
    THEME_CRITICAL
)


@module.ui
def risk_contractors_ui():
    return ui.div(
        # Tarjeta 1: KPIs Ejecutivos de Concentracion Empresarial
        ui.card(
            ui.card_header(
                ui.div(
                    ui.div("Poder de Mercado & Concentración de Contratistas (SECOP II)", class_="card-header-title"),
                    ui.div("Auditoría de Adjudicatarios, Ratios Oligopólicos y Tasa de Contratación a Dedo", class_="card-header-subtitle"),
                    class_="card-header-heading"
                )
            ),
            ui.output_ui("contractors_kpi_cards"),
            full_screen=False,
            class_="mb-3"
        ),

        # Tarjeta 2: Gráficos de Poder de Mercado y Auditoría de Adjudicación
        ui.card(
            ui.card_header(
                ui.div(
                    ui.div("Estructura de Mercado · Grandes Acaparadores y Vía de Adjudicación", class_="card-header-title"),
                    ui.div("Auditoría de concentración presupuestal y modalidad de contratación pública", class_="card-header-subtitle"),
                    class_="card-header-heading"
                )
            ),
            ui.layout_columns(
                ui.output_ui("contractors_bar_container"),
                ui.output_ui("contractors_breakdown_container"),
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
                    ui.div("Directorio de Contratistas con Alertas de Riesgo Anticompetitivo", class_="card-header-title"),
                    ui.div("Seguimiento a Proveedores y Tasa de Dependencia de Contratación Directa", class_="card-header-subtitle"),
                    class_="card-header-heading"
                )
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
            return ui.div(
                ui.div(
                    ui.h6("Auditoría de Poder de Mercado y Contratistas Dominantes", class_="fw-bold text-primary mb-2"),
                    ui.p(
                        "Este módulo identifica a los mayores acaparadores del presupuesto público, evalúa el ratio oligopólico CR4 "
                        "(cuota acumulada de los 4 mayores contratistas) y analiza qué empresas dependen desproporcionadamente de contratos directos a dedo. "
                        "Cargue contratos desde la barra lateral izquierda para activar este análisis.",
                        class_="small text-secondary mb-0"
                    ),
                    class_="guide-callout mb-2"
                )
            )

        total_provs = df[find_procurement_columns(df)[2]].nunique() if find_procurement_columns(df)[2] in df.columns else len(c_df)
        top1 = c_df.iloc[0]

        cr4_sum = float(c_df.head(4)["cuota_pct"].sum())
        direct_avg_top10 = float(c_df.head(10)["pct_directa"].mean())

        return ui.div(
            ui.div(
                ui.span("Marco de Análisis de Economía Industrial: ", class_="fw-bold text-primary small"),
                ui.span("El Ratio CR4 mide el porcentaje del gasto público absorbido por los 4 mayores contratistas. ", class_="small text-secondary fw-semibold"),
                ui.span("Según los estándares de la OCDE y la Superintendencia de Industria y Comercio, un CR4 superior al 50% indica riesgo de mercado oligopólico y posibles barreras artificiales de entrada.", class_="small text-muted"),
                class_="guide-callout mb-3"
            ),
            ui.layout_columns(
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
            marker=dict(
                color=BLUE_COBALT,
                line=dict(color="#ffffff", width=1)
            ),
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

        apply_ggplot2_theme(
            fig,
            title="Top 15 Contratistas por Presupuesto Acumulado",
            subtitle="Ranking nacional consolidado en el ámbito de datos cargado",
            xaxis_title="Presupuesto Adjudicado (COP)",
            height=410,
            margin=dict(t=65, b=85, l=175, r=25),
            x_grid=True,
            y_grid=False
        )

        return ui.HTML(to_ggplot2_html(fig))

    # -------------------------------------------------------------
    # 3. GRÁFICO DE COMPOSICIÓN: DIRECTA VS COMPETITIVA (TOP 15)
    # -------------------------------------------------------------
    @output
    @render.ui
    def contractors_breakdown_container():
        c_df = contractors_df()
        if c_df.empty:
            return ui.span()

        top15 = c_df.head(15).iloc[::-1].copy()
        pct_direct = top15["pct_directa"].to_numpy()
        pct_comp = np.maximum(0.0, 100.0 - pct_direct)

        monto_total = top15["monto_total"].to_numpy()
        monto_dir = monto_total * (pct_direct / 100.0)
        monto_com = monto_total * (pct_comp / 100.0)

        # Etiquetas internas legibles solo cuando el segmento es >= 12% para evitar solapamientos
        text_dir = [f"{p:.0f}%" if p >= 12 else "" for p in pct_direct]
        text_com = [f"{p:.0f}%" if p >= 12 else "" for p in pct_comp]

        fig = go.Figure()

        # Segmento 1: Contratacion Directa (Azul Marino profundo - alerta / sin concurso)
        fig.add_trace(go.Bar(
            y=[str(p)[:30] for p in top15["proveedor"]],
            x=pct_direct,
            name="Contratación Directa (Sin Concurso)",
            orientation="h",
            marker=dict(
                color=BLUE_NAVY,
                line=dict(color="#ffffff", width=1)
            ),
            text=text_dir,
            textposition="inside",
            insidetextanchor="middle",
            textfont=dict(color="#ffffff", size=10, family=GGPLOT2_FONT_FAMILY),
            customdata=np.stack((
                [format_cop_currency(v) for v in monto_dir],
                [format_cop_currency(v) for v in monto_total],
                top15["n_contratos"]
            ), axis=-1),
            hovertemplate=(
                "<b>%{y}</b><br>"
                "Modalidad: <b>Contratación Directa</b><br>"
                "Proporción: <b>%{x:.1f}%</b><br>"
                "Monto Directo: %{customdata[0]}<br>"
                "Monto Total: %{customdata[1]}<br>"
                "Total Contratos: %{customdata[2]:,}<extra></extra>"
            )
        ))

        # Segmento 2: Concurso Competitivo / Licitacion (Azul Cielo luminoso)
        fig.add_trace(go.Bar(
            y=[str(p)[:30] for p in top15["proveedor"]],
            x=pct_comp,
            name="Concurso Público / Licitación",
            orientation="h",
            marker=dict(
                color=BLUE_SKY,
                line=dict(color="#ffffff", width=1)
            ),
            text=text_com,
            textposition="inside",
            insidetextanchor="middle",
            textfont=dict(color="#080c42", size=10, family=GGPLOT2_FONT_FAMILY),
            customdata=np.stack((
                [format_cop_currency(v) for v in monto_com],
                [format_cop_currency(v) for v in monto_total],
                top15["n_contratos"]
            ), axis=-1),
            hovertemplate=(
                "<b>%{y}</b><br>"
                "Modalidad: <b>Concurso Público / Abierto</b><br>"
                "Proporción: <b>%{x:.1f}%</b><br>"
                "Monto Competitivo: %{customdata[0]}<br>"
                "Monto Total: %{customdata[1]}<br>"
                "Total Contratos: %{customdata[2]:,}<extra></extra>"
            )
        ))

        fig.update_layout(barmode="stack")

        fig.add_vline(
            x=65,
            line_dash="dash",
            line_color=BLUE_COBALT,
            annotation_text="Alerta Crítica (>65%)",
            annotation_position="bottom right",
            annotation_font=dict(size=10, color=BLUE_COBALT, family=GGPLOT2_FONT_FAMILY)
        )

        apply_ggplot2_theme(
            fig,
            title="Desglose de Adjudicación: Directa vs Competitiva",
            subtitle="Proporción asignada a dedo vs concurso abierto por contratista líder",
            xaxis_title="% del Presupuesto del Contratista",
            height=410,
            margin=dict(t=65, b=85, l=175, r=25),
            show_legend=True,
            legend_orientation="h",
            x_grid=True,
            y_grid=False
        )
        fig.update_xaxes(range=[0, 100], ticksuffix="%")

        return ui.HTML(to_ggplot2_html(fig))

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

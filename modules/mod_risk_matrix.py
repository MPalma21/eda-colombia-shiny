"""Modulo de Semaforo de Riesgo Territorial en Contratacion Publica (SECOP II).

Herramientas analiticas para observatorio de politicas publicas:
- Matriz de riesgo interdepartamental basada en HHI y % de contratacion directa.
- Semáforo y cuadrante de alerta (🔴 Critico / Alto Riesgo, 🟡 Moderado, 🟢 Competitivo).
- Descomposicion y drill-down territorial por departamento seleccionado.
- Tabla integral para auditoria y veeduria ciudadana.
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
def risk_ui():
    return ui.div(
        # Tarjeta 1: Alertas y Semáforos Territoriales
        ui.card(
            ui.card_header(
                ui.div(
                    ui.span("Alertas y Semáforos de Riesgo Territorial en Contratación Pública", class_="fw-bold"),
                    ui.span("Metodología: Índice HHI de Contratistas & Tasa de Contratación Directa", class_="text-muted", style="font-size: 0.78rem;")
                ),
                class_="d-flex justify-content-between align-items-center"
            ),
            ui.output_ui("risk_controls_ui"),
            ui.output_ui("risk_summary_cards"),
            ui.layout_columns(
                ui.output_ui("risk_bar_container"),
                ui.output_ui("risk_quadrant_container"),
                col_widths={"sm": 12, "lg": (7, 5)},
                class_="g-3 mt-1"
            ),
            full_screen=True,
            class_="mb-3"
        ),

        # Tarjeta 2: Inspección y Drill-Down Departamental
        ui.card(
            ui.card_header(
                ui.div(
                    ui.span("Auditoría Departamental a Profundidad · Concentración y Modalidades", class_="fw-bold"),
                    ui.span("Inspección de Principales Contratistas y Vías de Adjudicación", class_="text-muted", style="font-size: 0.78rem;")
                ),
                class_="d-flex justify-content-between align-items-center"
            ),
            ui.output_ui("drilldown_controls_ui"),
            ui.output_ui("drilldown_summary_ui"),
            ui.layout_columns(
                ui.output_ui("dept_top_contractors_container"),
                ui.output_ui("dept_modalities_container"),
                col_widths={"sm": 12, "lg": (7, 5)},
                class_="g-3 mt-1"
            ),
            full_screen=True,
            class_="mb-3"
        ),

        # Tarjeta 3: Matriz Tabular de Riesgo Completa
        ui.card(
            ui.card_header(
                ui.div(
                    ui.span("Matriz de Evaluación de Riesgo por Jurisdicción", class_="fw-bold"),
                    ui.span("Microdatos Agregados por Departamento", class_="text-muted", style="font-size: 0.78rem;")
                ),
                class_="d-flex justify-content-between align-items-center"
            ),
            ui.output_data_frame("risk_data_table"),
            full_screen=True
        )
    )


@module.server
def risk_server(input, output, session, df_react):

    # -------------------------------------------------------------
    # 1. CONTROLES Y RECONOCIMIENTO DE COLUMNAS
    # -------------------------------------------------------------
    @output
    @render.ui
    def risk_controls_ui():
        df = df_react()
        if df.empty:
            return ui.p("Cargue un conjunto de datos (por ejemplo, SECOP II) para activar el semáforo de riesgo.", class_="text-muted")

        num_cols, _, cat_cols = classify_columns(df)
        all_cols = list(df.columns)

        dept_c, val_c, prov_c, mod_c = find_procurement_columns(df)

        return ui.div(
            ui.layout_columns(
                ui.input_select("dept_col", "Columna de Departamento / Territorio:", choices=cat_cols or all_cols, selected=dept_c or (cat_cols[0] if cat_cols else all_cols[0])),
                ui.input_select("val_col", "Columna de Valor / Monto Contractual:", choices=["(Solo conteo de contratos)"] + num_cols, selected=val_c or (num_cols[0] if num_cols else "(Solo conteo de contratos)")),
                ui.input_select("prov_col", "Columna de Proveedor / Contratista:", choices=["(Sin proveedor)"] + (cat_cols or all_cols), selected=prov_c or (cat_cols[1] if len(cat_cols) > 1 else "(Sin proveedor)")),
                ui.input_select("mod_col", "Columna de Modalidad de Contrato:", choices=["(Sin modalidad)"] + (cat_cols or all_cols), selected=mod_c or (cat_cols[2] if len(cat_cols) > 2 else "(Sin modalidad)")),
                col_widths={"sm": 12, "md": 6, "lg": 3},
                class_="g-2 mb-2"
            ),
            ui.div(
                ui.span("💡 Criterio de Riesgo: ", class_="fw-bold text-secondary"),
                ui.span("🔴 Alto Riesgo: HHI > 2500 o Contratación Directa > 65% | 🟡 Moderado: HHI 1500-2500 o Directa 35%-65% | 🟢 Bajo Riesgo: HHI < 1500 y Directa < 35%.", class_="text-muted"),
                class_="small p-2 bg-light rounded border border-subtle mb-3"
            )
        )

    # -------------------------------------------------------------
    # 2. CÁLCULO REACTIVO DE LA MATRIZ DE RIESGO
    # -------------------------------------------------------------
    @reactive.calc
    def risk_matrix_df():
        df = df_react()
        if df.empty:
            return pd.DataFrame()

        dept_col = input.dept_col() if hasattr(input, "dept_col") and input.dept_col() else None
        val_col = input.val_col() if hasattr(input, "val_col") and input.val_col() != "(Solo conteo de contratos)" else None
        prov_col = input.prov_col() if hasattr(input, "prov_col") and input.prov_col() != "(Sin proveedor)" else None
        mod_col = input.mod_col() if hasattr(input, "mod_col") and input.mod_col() != "(Sin modalidad)" else None

        return compute_procurement_risk_matrix(
            df=df,
            dept_col=dept_col,
            val_col=val_col,
            prov_col=prov_col,
            mod_col=mod_col,
            min_contracts_per_dept=1
        )

    # -------------------------------------------------------------
    # 3. VALUE BOXES RESUMEN NACIONAL
    # -------------------------------------------------------------
    @output
    @render.ui
    def risk_summary_cards():
        matrix = risk_matrix_df()
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
                    ui.span("💰", style="font-size: 1.4rem;"),
                    class_="kpi-icon-badge kpi-badge-blue"
                ),
                theme=None,
                class_="bslib-value-box"
            ),
            ui.value_box(
                "Alertas Críticas (🔴)",
                f"{summary['criticos']} / {summary['n_departamentos']}",
                ui.p(f"Moderados: {summary['moderados']} | Competitivos: {summary['competitivos']}", class_="text-muted small mb-0"),
                showcase=ui.div(
                    ui.span("🚨", style="font-size: 1.4rem;"),
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
                    ui.span("⚖️", style="font-size: 1.4rem;"),
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
                    ui.span("📊", style="font-size: 1.4rem;"),
                    class_="kpi-icon-badge kpi-badge-slate"
                ),
                theme=None,
                class_="bslib-value-box"
            ),
            col_widths={"sm": 12, "md": 6, "lg": 3},
            class_="g-3 mb-2"
        )

    # -------------------------------------------------------------
    # 4. GRÁFICO 1: BARRAS DE DEPARTAMENTOS POR RIESGO Y HHI
    # -------------------------------------------------------------
    @output
    @render.ui
    def risk_bar_container():
        matrix = risk_matrix_df()
        if matrix.empty:
            return ui.p("Sin datos suficientes para graficar alertas territoriales.", class_="text-muted")

        top_matrix = matrix.head(20).copy()

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

        # Líneas de umbral HHI
        fig.add_hline(y=2500, line_dash="dash", line_color="#dc2626", annotation_text="Límite Crítico (2500)", annotation_position="top right")
        fig.add_hline(y=1500, line_dash="dot", line_color="#d97706", annotation_text="Límite Moderado (1500)", annotation_position="top right")

        fig.update_layout(
            title="Ranking Territorial por Concentración (HHI) y Nivel de Riesgo",
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
    # 5. GRÁFICO 2: CUADRANTE DE ALERTA (% DIRECTA VS HHI)
    # -------------------------------------------------------------
    @output
    @render.ui
    def risk_quadrant_container():
        matrix = risk_matrix_df()
        if matrix.empty:
            return ui.span()

        plot_df = matrix.copy()

        # Normalizar tamaño de burbuja
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

        # Líneas de cuadrantes
        fig.add_vline(x=65, line_dash="dash", line_color="#dc2626", annotation_text="Directa > 65%", annotation_position="top right")
        fig.add_hline(y=2500, line_dash="dash", line_color="#dc2626", annotation_text="HHI > 2500", annotation_position="top left")

        fig.update_layout(
            title="Cuadrante de Riesgo: Directa vs Concentración",
            xaxis_title="% Contratación Directa (Monto)",
            yaxis_title="HHI de Adjudicaciones",
            height=430,
            margin=dict(t=50, b=40, l=40, r=30),
            plot_bgcolor="#fcfdfd",
            paper_bgcolor="white"
        )
        fig.update_xaxes(showgrid=True, gridcolor="#edf2e9", range=[0, 105])
        fig.update_yaxes(showgrid=True, gridcolor="#edf2e9", range=[0, max(3000, plot_df['hhi'].max() * 1.1)])

        return ui.HTML(fig.to_html(include_plotlyjs=False, full_html=False))

    # -------------------------------------------------------------
    # 6. DRILL-DOWN DEPARTAMENTAL
    # -------------------------------------------------------------
    @output
    @render.ui
    def drilldown_controls_ui():
        matrix = risk_matrix_df()
        if matrix.empty:
            return ui.span()

        depts = matrix["departamento"].tolist()
        return ui.div(
            ui.input_select("selected_dept", "Seleccionar Departamento para Auditoría Detallada:", choices=depts, selected=depts[0]),
            class_="mb-2"
        )

    @output
    @render.ui
    def drilldown_summary_ui():
        matrix = risk_matrix_df()
        if matrix.empty or not hasattr(input, "selected_dept"):
            return ui.span()

        chosen = input.selected_dept()
        sub = matrix[matrix["departamento"] == chosen]
        if sub.empty:
            return ui.span()

        row = sub.iloc[0]

        badge_html = f"<span class='{row['badge_class']}'>{row['badge_icon']} {row['nivel_riesgo']}</span>"

        return ui.div(
            ui.div(
                ui.div(
                    ui.span(f"Auditoría: {chosen}", class_="fw-bold fs-5 text-primary me-2"),
                    ui.HTML(badge_html),
                    class_="d-flex align-items-center mb-2"
                ),
                ui.div(
                    f"Presupuesto: {format_cop_currency(row['monto_total'])} | "
                    f"Contratos: {row['n_contratos']:,} | "
                    f"Contratación Directa: {row['pct_directa_monto']:.1f}% | "
                    f"Índice HHI: {row['hhi']:,.1f} | "
                    f"Proveedor dominante: {row['top_contratista']} ({row['top_cuota']:.1f}% de cuota)",
                    class_="text-secondary small"
                ),
                class_="p-3 bg-light rounded border border-subtle mb-3"
            )
        )

    @output
    @render.ui
    def dept_top_contractors_container():
        df = df_react()
        matrix = risk_matrix_df()
        if df.empty or matrix.empty or not hasattr(input, "selected_dept"):
            return ui.span()

        dept_col = input.dept_col() if hasattr(input, "dept_col") and input.dept_col() else None
        val_col = input.val_col() if hasattr(input, "val_col") and input.val_col() != "(Solo conteo de contratos)" else None
        prov_col = input.prov_col() if hasattr(input, "prov_col") and input.prov_col() != "(Sin proveedor)" else None

        if not dept_col or not prov_col or dept_col not in df.columns or prov_col not in df.columns:
            return ui.p("Configure la columna de proveedor para visualizar los contratistas dominantes.", class_="text-muted")

        chosen = input.selected_dept()
        dept_data = df[df[dept_col] == chosen]
        if dept_data.empty:
            return ui.span()

        if val_col and val_col in dept_data.columns and pd.api.types.is_numeric_dtype(dept_data[val_col]):
            shares = dept_data.groupby(prov_col)[val_col].sum()
            tot = shares.sum()
            shares_pct = (shares / tot * 100.0) if tot > 0 else (shares * 0)
        else:
            shares_pct = dept_data[prov_col].value_counts(normalize=True) * 100.0

        top5 = shares_pct.sort_values(ascending=True).tail(6)
        if top5.empty:
            return ui.p("Sin contratistas registrados.", class_="text-muted")

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=top5.values,
            y=[str(n)[:35] for n in top5.index],
            orientation="h",
            marker=dict(color="#1d3190"),
            hovertemplate="<b>%{y}</b><br>Cuota: %{x:.2f}%<extra></extra>"
        ))

        fig.update_layout(
            title=f"Top Contratistas en {chosen} (% Cuota de Mercado)",
            xaxis_title="Cuota de Adjudicación (%)",
            height=340,
            margin=dict(t=40, b=40, l=150, r=20),
            plot_bgcolor="white",
            paper_bgcolor="white"
        )
        fig.update_xaxes(showgrid=True, gridcolor="#edf2e9")
        fig.update_yaxes(showgrid=False)

        return ui.HTML(fig.to_html(include_plotlyjs=False, full_html=False))

    @output
    @render.ui
    def dept_modalities_container():
        df = df_react()
        matrix = risk_matrix_df()
        if df.empty or matrix.empty or not hasattr(input, "selected_dept"):
            return ui.span()

        dept_col = input.dept_col() if hasattr(input, "dept_col") and input.dept_col() else None
        mod_col = input.mod_col() if hasattr(input, "mod_col") and input.mod_col() != "(Sin modalidad)" else None
        val_col = input.val_col() if hasattr(input, "val_col") and input.val_col() != "(Solo conteo de contratos)" else None

        if not dept_col or not mod_col or dept_col not in df.columns or mod_col not in df.columns:
            return ui.p("Configure la columna de modalidad para visualizar las vías de adjudicación.", class_="text-muted")

        chosen = input.selected_dept()
        dept_data = df[df[dept_col] == chosen]
        if dept_data.empty:
            return ui.span()

        if val_col and val_col in dept_data.columns and pd.api.types.is_numeric_dtype(dept_data[val_col]):
            mod_shares = dept_data.groupby(mod_col)[val_col].sum().sort_values(ascending=False).head(5)
        else:
            mod_shares = dept_data[mod_col].value_counts().head(5)

        if mod_shares.empty:
            return ui.p("Sin modalidades registradas.", class_="text-muted")

        brand_palette = ["#1d3190", "#dc2626", "#d97706", "#0284c7", "#3b82f6"]

        fig = go.Figure(data=[go.Pie(
            labels=[str(lbl)[:30] for lbl in mod_shares.index],
            values=mod_shares.values,
            hole=0.45,
            marker=dict(colors=brand_palette)
        )])

        fig.update_layout(
            title=f"Modalidades de Contratación en {chosen}",
            height=340,
            margin=dict(t=40, b=20, l=20, r=20),
            showlegend=True,
            paper_bgcolor="white"
        )

        return ui.HTML(fig.to_html(include_plotlyjs=False, full_html=False))

    # -------------------------------------------------------------
    # 7. TABLA DE DATOS FORMATEADA
    # -------------------------------------------------------------
    @output
    @render.data_frame
    def risk_data_table():
        matrix = risk_matrix_df()
        if matrix.empty:
            return pd.DataFrame()

        display_df = matrix[[
            "badge_icon", "departamento", "nivel_riesgo", "score_riesgo",
            "monto_total", "n_contratos", "pct_directa_monto", "hhi",
            "cr4", "top_contratista", "top_cuota"
        ]].copy()

        display_df["monto_total"] = display_df["monto_total"].apply(format_cop_currency)

        display_df.columns = [
            "Alerta", "Departamento", "Nivel de Riesgo", "Score (0-100)",
            "Presupuesto Auditado", "Contratos", "% Directa", "HHI",
            "CR4 (%)", "Top Contratista", "Cuota Top (%)"
        ]

        return render.DataGrid(display_df, filters=True, selection_mode="none")

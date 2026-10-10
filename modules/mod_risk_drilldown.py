"""Modulo de Auditoria Departamental a Profundidad (Drill-Down Territorial).

Perspectiva 2 del Panel de Riesgo Territorial:
- Ficha tecnica integral y semaforo individual del departamento inspeccionado.
- Ranking y concentracion de los mayores contratistas en la jurisdiccion.
- Desglose de modalidades de adjudicacion (Directa vs Competitiva).
- Deteccion de megacontratos atipicos de mayor cuantia individual.
- Dictamen y diagnostico institucional automatizado para veeduria y control fiscal.
"""
from shiny import module, ui, render, reactive
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from services.economic_service import (
    compute_procurement_risk_matrix,
    get_department_atypical_contracts,
    get_department_diagnosis,
    find_procurement_columns,
    format_cop_currency
)
from components.plot_theme import (
    apply_ggplot2_theme,
    to_ggplot2_html,
    get_modality_color,
    THEME_PRIMARY
)


@module.ui
def risk_drilldown_ui():
    return ui.div(
        # Tarjeta 1: Selector y Ficha Ejecutiva del Departamento
        ui.card(
            ui.card_header(
                ui.div(
                    ui.span("Auditoría Departamental a Profundidad · Expediente Territorial", class_="fw-bold"),
                    ui.span("Inspección Detallada de Vulnerabilidades y Contratación por Jurisdicción", class_="text-muted", style="font-size: 0.78rem;")
                ),
                class_="d-flex justify-content-between align-items-center"
            ),
            ui.output_ui("drilldown_selector_ui"),
            ui.output_ui("drilldown_profile_ui"),
            full_screen=False,
            class_="mb-3"
        ),

        # Tarjeta 2: Análisis Gráfico de Oferentes y Modalidades
        ui.card(
            ui.card_header(
                ui.div(
                    ui.span("Estructura de Competencia Local · Contratistas y Vías de Adjudicación", class_="fw-bold"),
                    ui.span("Cuotas de Mercado de los Mayores Adjudicatarios vs Modalidades Utilizadas", class_="text-muted", style="font-size: 0.78rem;")
                ),
                class_="d-flex justify-content-between align-items-center"
            ),
            ui.layout_columns(
                ui.output_ui("drilldown_contractors_chart"),
                ui.output_ui("drilldown_modalities_chart"),
                col_widths={"sm": 12, "lg": (7, 5)},
                class_="g-3"
            ),
            full_screen=True,
            class_="mb-3"
        ),

        # Tarjeta 3: Megacontratos Atípicos y Dictamen Técnico
        ui.card(
            ui.card_header(
                ui.div(
                    ui.span("Megacontratos Atípicos & Dictamen Técnico para Control Fiscal", class_="fw-bold"),
                    ui.span("Auditoría de Contratos de Mayor Cuantía y Recomendaciones de Política", class_="text-muted", style="font-size: 0.78rem;")
                ),
                class_="d-flex justify-content-between align-items-center"
            ),
            ui.layout_columns(
                ui.output_ui("drilldown_atypical_container"),
                ui.output_ui("drilldown_diagnosis_container"),
                col_widths={"sm": 12, "lg": (7, 5)},
                class_="g-3"
            ),
            full_screen=True
        )
    )


@module.server
def risk_drilldown_server(input, output, session, df_react):

    @reactive.calc
    def matrix_df():
        df = df_react()
        if df.empty:
            return pd.DataFrame()
        return compute_procurement_risk_matrix(df, min_contracts_per_dept=1)

    # -------------------------------------------------------------
    # 1. SELECTOR DE DEPARTAMENTO
    # -------------------------------------------------------------
    @output
    @render.ui
    def drilldown_selector_ui():
        matrix = matrix_df()
        if matrix.empty:
            return ui.div(
                ui.div(
                    ui.h6("Expediente de Auditoría Departamental Individual", class_="fw-bold text-primary mb-2"),
                    ui.p(
                        "Este módulo profundiza en una jurisdicción territorial específica para inspeccionar la estructura de sus oferentes locales, "
                        "el reparto por modalidades de selección (licitaciones vs convenios directos), los contratos individuales de mayor monto "
                        "y el dictamen automático de control fiscal. Cargue los datos en la barra lateral para habilitar este expediente.",
                        class_="small text-secondary mb-0"
                    ),
                    class_="guide-callout mb-2"
                )
            )

        depts = matrix["departamento"].tolist()
        return ui.div(
            ui.div(
                ui.input_select(
                    "selected_dept",
                    "Seleccionar Departamento para Expediente de Auditoría:",
                    choices=depts,
                    selected=depts[0]
                ),
                class_="col-12 col-md-6"
            ),
            ui.div(
                ui.div(
                    ui.span("Instrucciones de Auditoría: ", class_="fw-bold text-primary small"),
                    ui.span("Cambie el departamento en el selector para refrescar automáticamente la ficha ejecutiva, la curva de contratación y el dictamen fiscal automatizado.", class_="small text-muted"),
                    class_="guide-callout"
                ),
                class_="col-12 col-md-6"
            ),
            class_="row align-items-center g-2 mb-3"
        )

    # -------------------------------------------------------------
    # 2. FICHA EJECUTIVA DEL DEPARTAMENTO
    # -------------------------------------------------------------
    @output
    @render.ui
    def drilldown_profile_ui():
        matrix = matrix_df()
        if matrix.empty or not hasattr(input, "selected_dept"):
            return ui.span()

        chosen = input.selected_dept()
        sub = matrix[matrix["departamento"] == chosen]
        if sub.empty:
            return ui.span()

        row = sub.iloc[0]
        promedio_contrato = (row["monto_total"] / row["n_contratos"]) if row["n_contratos"] > 0 else 0.0

        badge_html = f"<span class='{row['badge_class']} fs-6 px-3 py-1'>{row['badge_icon']} {row['nivel_riesgo']}</span>"

        return ui.div(
            ui.div(
                ui.div(
                    ui.div(
                        ui.span(f"Expediente Territorial: {chosen}", class_="fs-4 fw-bold text-primary me-3"),
                        ui.HTML(badge_html),
                        class_="d-flex align-items-center mb-2"
                    ),
                    ui.div(
                        f"Puntuación Compuesta de Riesgo: {row['score_riesgo']:.1f} / 100 pts | "
                        f"Herfindahl-Hirschman (HHI): {row['hhi']:,.1f} | "
                        f"Tasa de Contratación Directa: {row['pct_directa_monto']:.1f}%",
                        class_="text-secondary fw-semibold small"
                    ),
                    class_="col-12 col-md-8"
                ),
                ui.div(
                    ui.div("PRESUPUESTO TOTAL AUDITADO", class_="text-muted small fw-bold"),
                    ui.div(format_cop_currency(row["monto_total"]), class_="fs-4 fw-bold font-monospace text-dark"),
                    ui.div(f"{row['n_contratos']:,} contratos | {row['n_proveedores']:,} oferentes", class_="text-secondary small"),
                    class_="col-12 col-md-4 text-md-end border-md-start ps-md-3"
                ),
                class_="row align-items-center p-3 bg-light rounded border border-subtle"
            ),
            ui.layout_columns(
                ui.div(
                    ui.span("Promedio por Contrato", class_="metadata-item-label"),
                    ui.span(format_cop_currency(promedio_contrato), class_="fs-5 fw-bold font-monospace text-dark"),
                    class_="mini-kpi-card mt-3"
                ),
                ui.div(
                    ui.span("Contratación Directa (% Monto)", class_="metadata-item-label"),
                    ui.span(f"{row['pct_directa_monto']:.1f}%", class_="fs-5 fw-bold font-monospace text-danger" if row['pct_directa_monto'] > 65 else "fs-5 fw-bold font-monospace text-dark"),
                    class_="mini-kpi-card mt-3"
                ),
                ui.div(
                    ui.span("Concentración CR4 (% Top 4)", class_="metadata-item-label"),
                    ui.span(f"{row['cr4']:.1f}%", class_="fs-5 fw-bold font-monospace text-dark"),
                    class_="mini-kpi-card mt-3"
                ),
                ui.div(
                    ui.span("Contratista Preponderante", class_="metadata-item-label"),
                    ui.span(f"{str(row['top_contratista'])[:25]} ({row['top_cuota']:.1f}%)", class_="fs-6 fw-bold text-secondary text-truncate"),
                    class_="mini-kpi-card mt-3"
                ),
                col_widths={"sm": 12, "md": 6, "lg": 3},
                class_="g-2"
            )
        )

    # -------------------------------------------------------------
    # 2.5 DATAFRAME FILTRADO POR DEPARTAMENTO SELECCIONADO (REACTIVO MEMOIZADO)
    # -------------------------------------------------------------
    @reactive.calc
    def selected_dept_sub_df():
        df = df_react()
        if df.empty or not hasattr(input, "selected_dept"):
            return pd.DataFrame()
        chosen = input.selected_dept()
        if not chosen:
            return pd.DataFrame()
        dept_c, _, _, _ = find_procurement_columns(df)
        if not dept_c or dept_c not in df.columns:
            return pd.DataFrame()
        target = str(chosen).strip().lower()
        dept_clean = df[dept_c].astype(str).str.strip().str.lower()
        return df[dept_clean == target]

    # -------------------------------------------------------------
    # 3. GRÁFICO DE CONTRATISTAS EN EL DEPARTAMENTO
    # -------------------------------------------------------------
    @output
    @render.ui
    def drilldown_contractors_chart():
        sub = selected_dept_sub_df()
        matrix = matrix_df()
        if sub.empty or matrix.empty or not hasattr(input, "selected_dept"):
            return ui.span()

        dept_c, val_c, prov_c, _ = find_procurement_columns(sub)
        if not dept_c or not prov_c or dept_c not in sub.columns or prov_c not in sub.columns:
            return ui.p("Configure columnas válidas de departamento y proveedor.", class_="text-muted")

        chosen = input.selected_dept()

        if val_c and val_c in sub.columns and pd.api.types.is_numeric_dtype(sub[val_c]):
            shares = sub.groupby(prov_c)[val_c].sum()
            tot = shares.sum()
            shares_pct = (shares / tot * 100.0) if tot > 0 else (shares * 0)
        else:
            shares_pct = sub[prov_c].value_counts(normalize=True) * 100.0

        top7 = shares_pct.sort_values(ascending=True).tail(8)
        if top7.empty:
            return ui.p("Sin proveedores registrados.", class_="text-muted")

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=top7.values,
            y=[str(n)[:32] for n in top7.index],
            orientation="h",
            marker=dict(
                color=THEME_PRIMARY,
                line=dict(color="#ffffff", width=1)
            ),
            hovertemplate="<b>%{y}</b><br>Cuota: %{x:.2f}%<extra></extra>"
        ))

        apply_ggplot2_theme(
            fig,
            title=f"Principales Contratistas en {chosen}",
            subtitle="Cuota de mercado sobre el presupuesto total adjudicado (%)",
            xaxis_title="Cuota de Presupuesto (%)",
            height=360,
            margin=dict(t=65, b=45, l=170, r=25),
            x_grid=True,
            y_grid=False
        )

        return ui.HTML(to_ggplot2_html(fig))

    # -------------------------------------------------------------
    # 4. GRÁFICO DE MODALIDADES EN EL DEPARTAMENTO
    # -------------------------------------------------------------
    @output
    @render.ui
    def drilldown_modalities_chart():
        sub = selected_dept_sub_df()
        matrix = matrix_df()
        if sub.empty or matrix.empty or not hasattr(input, "selected_dept"):
            return ui.span()

        dept_c, val_c, _, mod_c = find_procurement_columns(sub)
        if not dept_c or not mod_c or dept_c not in sub.columns or mod_c not in sub.columns:
            return ui.p("Configure la columna de modalidad de contratación.", class_="text-muted")

        chosen = input.selected_dept()

        if val_c and val_c in sub.columns and pd.api.types.is_numeric_dtype(sub[val_c]):
            mod_shares = sub.groupby(mod_c)[val_c].sum().sort_values(ascending=False).head(5)
        else:
            mod_shares = sub[mod_c].value_counts().head(5)

        if mod_shares.empty:
            return ui.p("Sin modalidades registradas.", class_="text-muted")

        slice_colors = [get_modality_color(lbl) for lbl in mod_shares.index]

        fig = go.Figure(data=[go.Pie(
            labels=[str(lbl)[:28] for lbl in mod_shares.index],
            values=mod_shares.values,
            hole=0.48,
            domain=dict(x=[0.0, 0.60]),
            marker=dict(
                colors=slice_colors,
                line=dict(color="#ffffff", width=2)
            ),
            hovertemplate="<b>%{label}</b><br>Participación: %{percent}<extra></extra>"
        )])

        apply_ggplot2_theme(
            fig,
            title=f"Vías de Adjudicación en {chosen}",
            subtitle="Distribución por tipo de proceso y selección",
            height=360,
            margin=dict(t=65, b=30, l=15, r=15),
            show_legend=True,
            legend_orientation="v"
        )
        fig.update_layout(
            legend=dict(
                orientation="v",
                x=0.64,
                y=0.5,
                yanchor="middle",
                bgcolor="rgba(255, 255, 255, 0.95)",
                bordercolor="#e2e8f0",
                borderwidth=1,
                font=dict(size=10)
            )
        )
        fig.update_xaxes(showline=False, ticks="", showgrid=False)
        fig.update_yaxes(showline=False, ticks="", showgrid=False)

        return ui.HTML(to_ggplot2_html(fig))

    # -------------------------------------------------------------
    # 5. MEGACONTRATOS ATÍPICOS DE MAYOR CUANTÍA
    # -------------------------------------------------------------
    @output
    @render.ui
    def drilldown_atypical_container():
        sub = selected_dept_sub_df()
        if sub.empty or not hasattr(input, "selected_dept"):
            return ui.span()

        chosen = input.selected_dept()
        atypical_df = get_department_atypical_contracts(sub, chosen, top_n=6)
        if atypical_df.empty:
            return ui.p("No se registraron contratos individuales atípicos.", class_="text-muted")

        rows = []
        for _, row in atypical_df.iterrows():
            rows.append(
                ui.div(
                    ui.div(
                        ui.span(f"{row['alerta']}", class_=f"{row['alerta_class']} me-2"),
                        ui.span(row['monto_str'], class_="fw-bold font-monospace text-dark fs-6"),
                        class_="d-flex align-items-center mb-1"
                    ),
                    ui.div(f"Contratista: {row['proveedor']}", class_="small fw-semibold text-secondary"),
                    ui.div(f"Modalidad: {row['modalidad']} | Objeto: {row['objeto']}", class_="text-muted small"),
                    class_="p-2 mb-2 bg-white rounded border border-subtle"
                )
            )

        return ui.div(
            ui.div("Contratos de Mayor Cuantía Individual en la Jurisdicción", class_="fw-bold text-primary small mb-2 text-uppercase"),
            *rows
        )

    # -------------------------------------------------------------
    # 6. DICTAMEN Y DIAGNÓSTICO INSTITUCIONAL
    # -------------------------------------------------------------
    @output
    @render.ui
    def drilldown_diagnosis_container():
        matrix = matrix_df()
        if matrix.empty or not hasattr(input, "selected_dept"):
            return ui.span()

        chosen = input.selected_dept()
        sub = matrix[matrix["departamento"] == chosen]
        if sub.empty:
            return ui.span()

        diag = get_department_diagnosis(sub.iloc[0])

        factores_html = "".join([f"<li class='mb-2'>{f}</li>" for f in diag["factores"]])

        return ui.div(
            ui.div("Dictamen Automatizado de Veeduría y Control Fiscal", class_="fw-bold text-primary small mb-2 text-uppercase"),
            ui.div(
                ui.div("Factores Críticos Observados:", class_="fw-bold text-dark small mb-1"),
                ui.HTML(f"<ul class='small text-secondary ps-3 mb-3'>{factores_html}</ul>"),
                ui.div("Recomendación de Política y Control:", class_="fw-bold text-dark small mb-1"),
                ui.p(diag["recomendacion"], class_="small text-secondary mb-0 bg-white p-2 rounded border border-subtle"),
                class_="p-3 bg-light rounded border border-subtle h-100"
            )
        )

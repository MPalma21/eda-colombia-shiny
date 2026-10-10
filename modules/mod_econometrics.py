"""Modulo de Modelado Econometrico y Estimacion de Elasticidades con Heterogeneidad Territorial.

Herramientas econometricas para analisis de politicas y economia:
- Modelos MCO: Log-Log (Elasticidad directa), Lineal (Efecto Marginal) y Semi-Log.
- Segmentacion dinamica por categorias (Departamentos, Estratos, Modalidades, etc.).
- Comparativa de heterogeneidad territorial (Elasticidades por departamento con significancia).
- Estadisticos t, p-valores, errores estandar y coeficientes de determinacion (R² y R² ajustado).
- Interpretacion economica automatizada en lenguaje natural.
"""
from shiny import module, ui, render, reactive
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from services.stats_service import classify_columns
from services.economic_service import (
    estimate_econometric_model,
    estimate_econometric_by_groups
)


@module.ui
def econometrics_ui():
    return ui.div(
        # Tarjeta 1: Estimacion Principal (Muestra Completa o Subgrupo Especifico)
        ui.card(
            ui.card_header(
                ui.div(
                    ui.span("Estimacion Econometrica & Analisis de Elasticidades (MCO)", class_="fw-bold"),
                    ui.span("Relaciones Estructurales · Teoria Micro y Macroeconomica", class_="text-muted", style="font-size: 0.78rem;")
                ),
                class_="d-flex justify-content-between align-items-center"
            ),
            ui.output_ui("econ_controls_ui"),
            ui.output_ui("econ_summary_cards"),
            ui.output_ui("econ_interpretation_box"),
            ui.layout_columns(
                ui.output_ui("econ_regression_plot"),
                ui.output_data_frame("econ_metrics_table"),
                col_widths={"sm": 12, "lg": (7, 5)},
                class_="g-3"
            ),
            full_screen=True,
            class_="mb-3"
        ),
        
        # Tarjeta 2: Heterogeneidad Territorial e Interdepartamental
        ui.card(
            ui.card_header(
                ui.div(
                    ui.span("Heterogeneidad Territorial & Comparativa entre Departamentos / Subgrupos", class_="fw-bold"),
                    ui.span("Sensibilidad y Elasticidades Diferenciales por Region", class_="text-muted", style="font-size: 0.78rem;")
                ),
                class_="d-flex justify-content-between align-items-center"
            ),
            ui.output_ui("econ_heterogeneity_info"),
            ui.layout_columns(
                ui.output_ui("econ_heterogeneity_plot"),
                ui.output_data_frame("econ_heterogeneity_table"),
                col_widths={"sm": 12, "lg": (7, 5)},
                class_="g-3"
            ),
            full_screen=True
        )
    )


@module.server
def econometrics_server(input, output, session, df_react):

    @output
    @render.ui
    def econ_controls_ui():
        df = df_react()
        if df.empty:
            return ui.p("Cargue un conjunto de datos para inicializar el modulo econometrico.", class_="text-muted")

        num_cols, _, cat_cols = classify_columns(df)
        if len(num_cols) < 2:
            return ui.p("Se requieren al menos dos variables cuantitativas continuas para estimar modelos econometricos.", class_="status-warning")

        # Intentar sugerir variables tipicas de Y y X
        y_default = num_cols[0]
        x_default = num_cols[1] if len(num_cols) > 1 else num_cols[0]

        # Sugerir columna de departamento o categoria territorial
        pref_cats = [c for c in cat_cols if any(k in c.lower() for k in ("depa", "muni", "estrato", "sector", "modalidad", "tipo"))]
        cat_choices = ["(Muestra Completa / Sin segmentar)"] + cat_cols
        default_cat = pref_cats[0] if pref_cats else ("(Muestra Completa / Sin segmentar)" if cat_cols else None)

        return ui.div(
            ui.layout_columns(
                ui.input_select(
                    "econ_spec",
                    "Especificacion del Modelo:",
                    choices={
                        "log_log": "Doble Logaritmo (Log-Log) · Elasticidad (%)",
                        "ols_linear": "Lineal Estandar (MCO) · Efecto Marginal Directo",
                        "log_lin": "Semi-Log (Log-Lin) · Semielasticidad (%)"
                    },
                    selected="log_log"
                ),
                ui.input_select("econ_y", "Variable Dependiente (Y):", choices=num_cols, selected=y_default),
                ui.input_select("econ_x", "Variable Explicativa / Independiente (X):", choices=num_cols, selected=x_default),
                col_widths={"sm": 12, "md": 4},
                class_="mb-2 g-2"
            ),
            ui.layout_columns(
                ui.input_select(
                    "econ_segment_col",
                    "Variable de Segmentacion (Departamento / Categoria):",
                    choices=cat_choices,
                    selected=default_cat or "(Muestra Completa / Sin segmentar)"
                ),
                ui.output_ui("econ_category_picker_ui"),
                col_widths={"sm": 12, "md": 6},
                class_="mb-2 g-2"
            )
        )

    @output
    @render.ui
    def econ_category_picker_ui():
        df = df_react()
        if df.empty or not hasattr(input, "econ_segment_col"):
            return ui.span()

        seg_col = input.econ_segment_col()
        if not seg_col or seg_col == "(Muestra Completa / Sin segmentar)" or seg_col not in df.columns:
            return ui.div(
                ui.span("Estimando sobre la muestra nacional agregada (sin filtro de subgrupo).", class_="text-muted", style="font-size: 0.80rem; margin-top: 28px; display: block;")
            )

        # Opciones ordenadas por volumen
        top_vals = df[seg_col].dropna().value_counts().head(35).index.astype(str).tolist()
        choices = ["(Todos los subgrupos / Muestra agregada)"] + top_vals

        return ui.input_select("econ_segment_val", f"Filtrar Subgrupo Especifico ({seg_col}):", choices=choices, selected=choices[0])

    @reactive.calc
    def filtered_df():
        df = df_react()
        if df.empty:
            return pd.DataFrame()

        if hasattr(input, "econ_segment_col") and hasattr(input, "econ_segment_val"):
            seg_col = input.econ_segment_col()
            seg_val = input.econ_segment_val()
            if seg_col and seg_col != "(Muestra Completa / Sin segmentar)" and seg_col in df.columns:
                if seg_val and seg_val != "(Todos los subgrupos / Muestra agregada)":
                    return df[df[seg_col].astype(str) == seg_val]
        return df

    @reactive.calc
    def regression_result():
        df = filtered_df()
        if df.empty or not hasattr(input, "econ_y") or not hasattr(input, "econ_x"):
            return None
        y = input.econ_y()
        x = input.econ_x()
        spec = input.econ_spec() if hasattr(input, "econ_spec") else "log_log"
        if not y or not x or y == x:
            return None
        return estimate_econometric_model(df, y_col=y, x_col=x, model_type=spec)

    @output
    @render.ui
    def econ_summary_cards():
        res = regression_result()
        if not res or not res.get("valido", False):
            return ui.span()

        p_val = res["p_val"]
        sig_class = "badge-status-ok" if p_val < 0.05 else "badge-category"
        param_title = "Elasticidad (β₁)" if res["model_type"] == "log_log" else "Coeficiente (β₁)"

        # Indicador de subgrupo activo
        scope_text = "Muestra nacional agregada"
        if hasattr(input, "econ_segment_val") and input.econ_segment_val() and input.econ_segment_val() != "(Todos los subgrupos / Muestra agregada)":
            scope_text = f"Filtro: {input.econ_segment_val()}"

        return ui.layout_columns(
            ui.value_box(
                param_title,
                f"{res['beta_1']:+.4f}",
                ui.p(f"Error estándar: ±{res['stderr']:.4f}", class_="text-muted mb-0", style="font-size: 0.78rem;"),
                showcase=ui.span(res["sig_stars"], class_=f"badge {sig_class} p-2", style="font-size: 0.76rem;"),
                theme=None,
                class_="kpi-card"
            ),
            ui.value_box(
                "Bondad de Ajuste (R²)",
                f"{res['r2']:.4f}",
                ui.p(f"R² ajustado: {res['r2_adj']:.4f}", class_="text-muted mb-0", style="font-size: 0.78rem;"),
                showcase=ui.span("R²", class_="badge bg-slate-100 text-slate-700 p-2"),
                theme=None,
                class_="kpi-card"
            ),
            ui.value_box(
                "Estadístico t",
                f"{res['t_stat']:+.2f}",
                ui.p(f"p-valor: {res['p_val']:.5f}", class_="text-muted mb-0", style="font-size: 0.78rem;"),
                showcase=ui.span("t-stat", class_="badge bg-slate-100 text-slate-700 p-2"),
                theme=None,
                class_="kpi-card"
            ),
            ui.value_box(
                "Muestra Efectiva (N)",
                f"{res['n_obs']:,}",
                ui.p(scope_text, class_="text-muted mb-0", style="font-size: 0.78rem;"),
                showcase=ui.span("Obs.", class_="badge bg-slate-100 text-slate-700 p-2"),
                theme=None,
                class_="kpi-card"
            ),
            col_widths={"sm": 12, "md": 6, "lg": 3},
            class_="mb-3 g-2"
        )

    @output
    @render.ui
    def econ_interpretation_box():
        res = regression_result()
        if not res:
            return ui.span()
        if not res.get("valido", False):
            return ui.div(
                ui.p(res.get("error", "Error en estimacion econometrica."), class_="status-warning p-2"),
                class_="alert-status-box mb-3"
            )

        subgroup_label = ""
        if hasattr(input, "econ_segment_val") and input.econ_segment_val() and input.econ_segment_val() != "(Todos los subgrupos / Muestra agregada)":
            subgroup_label = f" [Subgrupo: {input.econ_segment_val()}]"

        return ui.div(
            ui.div(
                ui.div(
                    ui.span(f"Interpretacion Economica{subgroup_label}:", class_="fw-bold text-slate-800 me-2"),
                    ui.span(res["interpretacion"], class_="text-slate-700"),
                    class_="d-flex flex-wrap align-items-center"
                ),
                class_="p-3 rounded bg-slate-50 border border-slate-200"
            ),
            class_="mb-3"
        )

    @output
    @render.ui
    def econ_regression_plot():
        res = regression_result()
        if not res or not res.get("valido", False):
            return ui.span()

        subgroup_text = ""
        if hasattr(input, "econ_segment_val") and input.econ_segment_val() and input.econ_segment_val() != "(Todos los subgrupos / Muestra agregada)":
            subgroup_text = f" · {input.econ_segment_val()}"

        fig = go.Figure()

        # Nube de puntos observados
        fig.add_trace(go.Scatter(
            x=res["scatter_x"],
            y=res["scatter_y"],
            mode="markers",
            name="Observaciones",
            marker=dict(color="#0284c7", size=5, opacity=0.45)
        ))

        # Recta de regresión ajustada
        eq_text = f"Y = {res['beta_0']:+.3f} + ({res['beta_1']:+.3f})X"
        fig.add_trace(go.Scatter(
            x=res["line_x"],
            y=res["line_y"],
            mode="lines",
            name=f"Ajuste MCO ({eq_text})",
            line=dict(color="#dc2626", width=2.5)
        ))

        fig.update_layout(
            title=dict(
                text=f"Ajuste Econometrico: {res['y_label']} vs {res['x_label']}{subgroup_text} (R² = {res['r2']:.4f})",
                font=dict(size=13, color="#0f172a")
            ),
            xaxis=dict(title=res["x_label"], gridcolor="#f1f5f9"),
            yaxis=dict(title=res["y_label"], gridcolor="#f1f5f9"),
            height=330,
            margin=dict(t=45, b=45, l=60, r=30),
            plot_bgcolor="white",
            paper_bgcolor="white",
            legend=dict(x=0.03, y=0.95, bgcolor="rgba(255,255,255,0.85)")
        )

        return ui.HTML(fig.to_html(full_html=False, include_plotlyjs="cdn", config={"responsive": True}))

    @output
    @render.data_frame
    def econ_metrics_table():
        res = regression_result()
        if not res or not res.get("valido", False):
            return render.DataGrid(pd.DataFrame(), height="280px")

        param_label = "Elasticidad β₁" if res["model_type"] == "log_log" else "Pendiente β₁"
        table_data = [
            {"Parametro / Metrica": param_label, "Valor": f"{res['beta_1']:+.4f}", "Diagnostico / Significancia": res["sig_stars"]},
            {"Parametro / Metrica": "Constante (Intersepto β₀)", "Valor": f"{res['beta_0']:+.4f}", "Diagnostico / Significancia": "Nivel base"},
            {"Parametro / Metrica": "Error Estandar (SE β₁)", "Valor": f"{res['stderr']:.4f}", "Diagnostico / Significancia": "Precision muestral"},
            {"Parametro / Metrica": "Estadistico t", "Valor": f"{res['t_stat']:+.2f}", "Diagnostico / Significancia": "Rechazo de H0: β₁ = 0"},
            {"Parametro / Metrica": "p-valor (dos colas)", "Valor": f"{res['p_val']:.5f}", "Diagnostico / Significancia": "Probabilidad bajo H0"},
            {"Parametro / Metrica": "Coeficiente R²", "Valor": f"{res['r2']:.4f}", "Diagnostico / Significancia": f"Explica {(res['r2']*100):.1f}% de la varianza"},
            {"Parametro / Metrica": "R² Ajustado", "Valor": f"{res['r2_adj']:.4f}", "Diagnostico / Significancia": "Penalizado por grados de libertad"},
            {"Parametro / Metrica": "Observaciones Efectivas", "Valor": f"{res['n_obs']:,}", "Diagnostico / Significancia": "Tamano muestral"},
        ]
        return render.DataGrid(pd.DataFrame(table_data), filters=False, height="280px")

    # -------------------------------------------------------------
    # 2. HETEROGENEIDAD TERRITORIAL E INTERDEPARTAMENTAL
    # -------------------------------------------------------------
    @reactive.calc
    def heterogeneity_df():
        df = df_react()
        if df.empty or not hasattr(input, "econ_y") or not hasattr(input, "econ_x") or not hasattr(input, "econ_segment_col"):
            return pd.DataFrame()

        y = input.econ_y()
        x = input.econ_x()
        seg_col = input.econ_segment_col()
        spec = input.econ_spec() if hasattr(input, "econ_spec") else "log_log"

        if not seg_col or seg_col == "(Muestra Completa / Sin segmentar)" or seg_col not in df.columns:
            return pd.DataFrame()

        return estimate_econometric_by_groups(df, y_col=y, x_col=x, group_col=seg_col, model_type=spec, min_obs=15, top_n_groups=20)

    @output
    @render.ui
    def econ_heterogeneity_info():
        df = df_react()
        if df.empty:
            return ui.span()
        seg_col = input.econ_segment_col() if hasattr(input, "econ_segment_col") else None
        if not seg_col or seg_col == "(Muestra Completa / Sin segmentar)":
            return ui.p(
                "Seleccione una variable de segmentacion arriba (ej. Departamento, Estrato o Modalidad) para activar el panel comparativo de heterogeneidad territorial.",
                class_="text-muted py-2"
            )
        h_df = heterogeneity_df()
        if h_df.empty:
            return ui.p(
                f"No hay suficientes observaciones por subgrupo en '{seg_col}' (se requieren min. 15 registros por categoria) para estimar modelos comparativos.",
                class_="status-warning py-2"
            )
        param_name = "Elasticidad (β₁)" if (hasattr(input, "econ_spec") and input.econ_spec() == "log_log") else "Coeficiente (β₁)"
        max_group = h_df.iloc[0]["Subgrupo / Departamento"]
        max_val = h_df.iloc[0][param_name]
        min_group = h_df.iloc[-1]["Subgrupo / Departamento"]
        min_val = h_df.iloc[-1][param_name]

        return ui.div(
            ui.span(
                f"Comparando {len(h_df)} subgrupos territoriales. Mayor sensibilidad en ",
                class_="text-slate-600"
            ),
            ui.span(f"{max_group} ({max_val:+.3f})", class_="fw-bold text-slate-800"),
            ui.span(" y menor en ", class_="text-slate-600"),
            ui.span(f"{min_group} ({min_val:+.3f}).", class_="fw-bold text-slate-800"),
            class_="py-2 mb-1"
        )

    @output
    @render.ui
    def econ_heterogeneity_plot():
        h_df = heterogeneity_df()
        if h_df.empty:
            return ui.span()

        param_col = [c for c in h_df.columns if "β₁" in c][0]
        sorted_df = h_df.sort_values(by=param_col, ascending=True)

        fig = px.bar(
            sorted_df,
            x=param_col,
            y="Subgrupo / Departamento",
            orientation="h",
            text=param_col,
            title=f"Comparativa de {param_col} por Subgrupo / Departamento",
            color="R²",
            color_continuous_scale=["#93c5fd", "#1e40af"]
        )
        fig.update_layout(
            height=340,
            margin=dict(t=45, b=45, l=130, r=30),
            plot_bgcolor="white",
            paper_bgcolor="white",
            yaxis=dict(title="")
        )
        fig.update_traces(texttemplate="%{text:+.3f}", textposition="outside")
        return ui.HTML(fig.to_html(full_html=False, include_plotlyjs="cdn", config={"responsive": True}))

    @output
    @render.data_frame
    def econ_heterogeneity_table():
        h_df = heterogeneity_df()
        if h_df.empty:
            return render.DataGrid(pd.DataFrame(), height="340px")
        return render.DataGrid(h_df, filters=False, height="340px")

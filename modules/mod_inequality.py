"""Modulo de Desigualdad y Concentracion de Mercado.

Herramientas de teoria economica:
- Curva de Lorenz interactiva y Coeficiente de Gini.
- Indice Herfindahl-Hirschman (HHI) y ratios de concentracion CR4 y CR8.
- Analisis de deciles y ratio Palma / P90-P10.
"""
from shiny import module, ui, render, reactive
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from services.stats_service import classify_columns
from services.economic_service import (
    compute_lorenz_curve,
    compute_gini_coefficient,
    interpret_gini,
    compute_hhi
)


@module.ui
def inequality_ui():
    return ui.div(
        # Seccion 1: Curva de Lorenz y Coeficiente de Gini
        ui.card(
            ui.card_header(
                ui.div(
                    ui.span("Distribucion y Desigualdad Economica · Curva de Lorenz & Coeficiente de Gini", class_="fw-bold"),
                    ui.span("Teoria de Distribucion del Ingreso y Gasto", class_="text-muted", style="font-size: 0.78rem;")
                ),
                class_="d-flex justify-content-between align-items-center"
            ),
            ui.output_ui("inequality_controls_ui"),
            ui.output_ui("gini_summary_cards"),
            ui.output_ui("lorenz_plot_container"),
            full_screen=True,
            class_="mb-3"
        ),
        
        # Seccion 2: Concentracion de Mercado y Estructura HHI
        ui.card(
            ui.card_header(
                ui.div(
                    ui.span("Concentracion de Mercado & Competencia · Indice Herfindahl-Hirschman (HHI)", class_="fw-bold"),
                    ui.span("Estandares Antimonopolio & Compras Publicas", class_="text-muted", style="font-size: 0.78rem;")
                ),
                class_="d-flex justify-content-between align-items-center"
            ),
            ui.output_ui("hhi_controls_ui"),
            ui.output_ui("hhi_summary_cards"),
            ui.layout_columns(
                ui.output_ui("hhi_plot_container"),
                ui.output_data_frame("hhi_top_table"),
                col_widths={"sm": 12, "lg": (7, 5)},
                class_="g-3"
            ),
            full_screen=True
        )
    )


@module.server
def inequality_server(input, output, session, df_react):

    # -------------------------------------------------------------
    # 1. CONTROLES Y LOGICA DE LORENZ / GINI
    # -------------------------------------------------------------
    @output
    @render.ui
    def inequality_controls_ui():
        df = df_react()
        if df.empty:
            return ui.p("Cargue un conjunto de datos para habilitar el analisis de desigualdad.", class_="text-muted")
        
        num_cols, _, _ = classify_columns(df)
        if not num_cols:
            return ui.p("No se encontraron variables numericas cuantitativas para evaluar desigualdad.", class_="status-warning")
            
        # Sugerir variables monetarias o de puntaje si existen
        preferred = [c for c in num_cols if any(k in c.lower() for k in ("valor", "monto", "precio", "ingreso", "gasto", "punt", "total"))]
        default_var = preferred[0] if preferred else num_cols[0]

        return ui.layout_columns(
            ui.input_select("gini_var", "Variable Cuantitativa de Valor o Monto:", choices=num_cols, selected=default_var),
            ui.input_checkbox("filter_positives", "Analizar solo valores estrictamente positivos (> 0)", value=True),
            col_widths={"sm": 12, "md": 6},
            class_="mb-2 g-2"
        )

    @output
    @render.ui
    def gini_summary_cards():
        df = df_react()
        if df.empty or not hasattr(input, "gini_var"):
            return ui.span()
            
        var = input.gini_var()
        if not var or var not in df.columns:
            return ui.span()
            
        series = df[var].dropna()
        if hasattr(input, "filter_positives") and input.filter_positives():
            series = series[series > 0]
            
        if len(series) < 5:
            return ui.p("Registros positivos insuficientes para calcular distribucion.", class_="status-warning")
            
        gini = compute_gini_coefficient(series)
        interp = interpret_gini(gini)
        
        p10 = float(np.percentile(series, 10))
        p50 = float(np.percentile(series, 50))
        p90 = float(np.percentile(series, 90))
        ratio_p90_p10 = round(p90 / p10, 2) if p10 > 0 else 0.0

        return ui.div(
            ui.layout_columns(
                ui.value_box(
                    "Coeficiente de Gini",
                    f"{gini:.4f}",
                    ui.p(interp["descripcion"], class_="text-muted mb-0", style="font-size: 0.78rem;"),
                    showcase=ui.div(
                        ui.span(interp["nivel"], class_=f"badge {interp['badge_class']} p-2", style="font-size: 0.82rem;")
                    ),
                    theme=None,
                    class_="kpi-card"
                ),
                ui.value_box(
                    "Mediana (P50)",
                    f"{p50:,.2f}",
                    ui.p("Punto medio de la distribucion", class_="text-muted mb-0", style="font-size: 0.78rem;"),
                    showcase=ui.span("50%", class_="badge bg-slate-100 text-slate-700 p-2"),
                    theme=None,
                    class_="kpi-card"
                ),
                ui.value_box(
                    "Disparidad P90 / P10",
                    f"{ratio_p90_p10:.2f}x",
                    ui.p("Veces que el decil 9 supera al decil 1", class_="text-muted mb-0", style="font-size: 0.78rem;"),
                    showcase=ui.span("Ratio", class_="badge bg-slate-100 text-slate-700 p-2"),
                    theme=None,
                    class_="kpi-card"
                ),
                col_widths={"sm": 12, "md": 4},
                class_="mb-3 g-2"
            )
        )

    @output
    @render.ui
    def lorenz_plot_container():
        df = df_react()
        if df.empty or not hasattr(input, "gini_var"):
            return ui.span()
            
        var = input.gini_var()
        if not var or var not in df.columns:
            return ui.span()
            
        series = df[var].dropna()
        if hasattr(input, "filter_positives") and input.filter_positives():
            series = series[series > 0]
            
        if len(series) < 5:
            return ui.span()
            
        pop_share, val_share, gini = compute_lorenz_curve(series, sample_points=120)
        
        fig = go.Figure()
        
        # Linea de perfecta igualdad (diagonal 45 grados)
        fig.add_trace(go.Scatter(
            x=[0, 1],
            y=[0, 1],
            mode="lines",
            name="Perfecta Igualdad (45°)",
            line=dict(color="#94a3b8", dash="dash", width=2)
        ))
        
        # Curva de Lorenz observada
        fig.add_trace(go.Scatter(
            x=pop_share,
            y=val_share,
            mode="lines",
            name=f"Curva de Lorenz (Gini = {gini:.4f})",
            line=dict(color="#1e40af", width=2.5),
            fill="tonexty",
            fillcolor="rgba(30, 64, 175, 0.08)"
        ))
        
        fig.update_layout(
            title=dict(
                text=f"Curva de Lorenz de '{var}' · Coeficiente de Gini = {gini:.4f}",
                font=dict(size=14, color="#0f172a")
            ),
            xaxis=dict(
                title="Proporción Acumulada de la Población / Registros",
                tickformat=".0%",
                range=[0, 1],
                gridcolor="#f1f5f9"
            ),
            yaxis=dict(
                title="Proporción Acumulada del Valor Total",
                tickformat=".0%",
                range=[0, 1],
                gridcolor="#f1f5f9"
            ),
            height=340,
            margin=dict(t=50, b=50, l=60, r=30),
            plot_bgcolor="white",
            paper_bgcolor="white",
            legend=dict(x=0.03, y=0.95, bgcolor="rgba(255,255,255,0.9)")
        )
        
        return ui.HTML(fig.to_html(full_html=False, include_plotlyjs="cdn", config={"responsive": True}))

    # -------------------------------------------------------------
    # 2. CONTROLES Y LOGICA DE HHI (CONCENTRACION)
    # -------------------------------------------------------------
    @output
    @render.ui
    def hhi_controls_ui():
        df = df_react()
        if df.empty:
            return ui.span()
            
        num_cols, _, cat_cols = classify_columns(df)
        if not cat_cols:
            return ui.p("Se requiere al menos una variable categorica (proveedor, entidad, sector) para evaluar concentracion.", class_="status-warning")
            
        # Sugerir proveedores, entidades o contratistas
        pref_cats = [c for c in cat_cols if any(k in c.lower() for k in ("proveedor", "contratista", "entidad", "empresa", "departamento", "sector", "tipo"))]
        default_cat = pref_cats[0] if pref_cats else cat_cols[0]
        
        val_choices = ["(Conteo de Registros)"] + num_cols
        pref_nums = [c for c in num_cols if any(k in c.lower() for k in ("valor", "monto", "precio", "total"))]
        default_val = pref_nums[0] if pref_nums else "(Conteo de Registros)"

        return ui.layout_columns(
            ui.input_select("hhi_cat_var", "Actor Economico / Categoria de Mercado:", choices=cat_cols, selected=default_cat),
            ui.input_select("hhi_val_var", "Ponderacion por Valor (Opcional):", choices=val_choices, selected=default_val),
            col_widths={"sm": 12, "md": 6},
            class_="mb-2 g-2"
        )

    @reactive.calc
    def hhi_data():
        df = df_react()
        if df.empty or not hasattr(input, "hhi_cat_var"):
            return None
        cat = input.hhi_cat_var()
        val = input.hhi_val_var() if hasattr(input, "hhi_val_var") else "(Conteo de Registros)"
        val_col = None if val == "(Conteo de Registros)" else val
        return compute_hhi(df, group_col=cat, val_col=val_col)

    @output
    @render.ui
    def hhi_summary_cards():
        h = hhi_data()
        if not h:
            return ui.span()

        return ui.layout_columns(
            ui.value_box(
                "Indice HHI",
                f"{h['hhi']:,.1f}",
                ui.p(h["descripcion"], class_="text-muted mb-0", style="font-size: 0.78rem;"),
                showcase=ui.span(h["clasificacion"], class_=f"badge {h['badge_class']} p-2", style="font-size: 0.80rem;"),
                theme=None,
                class_="kpi-card"
            ),
            ui.value_box(
                "Concentracion CR4",
                f"{h['cr4']:.1f}%",
                ui.p("Cuota de mercado acumulada de los 4 mayores actores", class_="text-muted mb-0", style="font-size: 0.78rem;"),
                showcase=ui.span("Top 4", class_="badge bg-slate-100 text-slate-700 p-2"),
                theme=None,
                class_="kpi-card"
            ),
            ui.value_box(
                "Concentracion CR8",
                f"{h['cr8']:.1f}%",
                ui.p("Cuota acumulada de los 8 principales oferentes", class_="text-muted mb-0", style="font-size: 0.78rem;"),
                showcase=ui.span("Top 8", class_="badge bg-slate-100 text-slate-700 p-2"),
                theme=None,
                class_="kpi-card"
            ),
            ui.value_box(
                "Total Participantes",
                f"{h['total_actores']:,}",
                ui.p("Entidades o proveedores distintos en el registro", class_="text-muted mb-0", style="font-size: 0.78rem;"),
                showcase=ui.span("Actores", class_="badge bg-slate-100 text-slate-700 p-2"),
                theme=None,
                class_="kpi-card"
            ),
            col_widths={"sm": 12, "md": 6, "lg": 3},
            class_="mb-3 g-2"
        )

    @output
    @render.ui
    def hhi_plot_container():
        h = hhi_data()
        if not h or h["top_df"].empty:
            return ui.span()

        top_df = h["top_df"]
        fig = px.bar(
            top_df,
            x="Cuota (%)",
            y="Actor / Categoria",
            orientation="h",
            text="Cuota (%)",
            title=f"Top 10 Actores por Cuota de Participacion (HHI = {h['hhi']:,.1f})",
            color="Cuota (%)",
            color_continuous_scale=["#bfdbfe", "#1e40af"]
        )
        fig.update_layout(
            yaxis=dict(autorange="reversed"),
            height=300,
            margin=dict(t=40, b=40, l=140, r=40),
            coloraxis_showscale=False,
            plot_bgcolor="white",
            paper_bgcolor="white"
        )
        fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
        return ui.HTML(fig.to_html(full_html=False, include_plotlyjs="cdn", config={"responsive": True}))

    @output
    @render.data_frame
    def hhi_top_table():
        h = hhi_data()
        if not h or h["top_df"].empty:
            return render.DataGrid(pd.DataFrame(), height="280px")
        return render.DataGrid(h["top_df"], filters=False, height="280px")


def p(text: str, **kwargs) -> ui.Tag:
    return ui.p(text, **kwargs)

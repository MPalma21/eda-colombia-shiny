"""Modulo de Brechas Economicas, Territoriales y Socioeconomicas."""
from shiny import module, ui, render, reactive
import pandas as pd
import plotly.express as px
from services.stats_service import classify_columns
from services.economic_service import compute_economic_gaps


@module.ui
def comparisons_ui():
    return ui.card(
        ui.card_header(
            ui.div(
                ui.span("Brechas Socioeconomicas & Disparidades Territoriales", class_="fw-bold"),
                ui.span("Economia Regional & Estratificacion", class_="text-muted", style="font-size: 0.78rem;")
            ),
            class_="d-flex justify-content-between align-items-center"
        ),
        ui.output_ui("comp_controls_ui"),
        ui.output_ui("comp_gap_kpis"),
        ui.layout_columns(
            ui.output_ui("comp_plot_container"),
            ui.output_data_frame("comp_gap_table"),
            col_widths={"sm": 12, "lg": (7, 5)},
            class_="g-3"
        ),
        full_screen=True
    )


@module.server
def comparisons_server(input, output, session, df_react):

    @output
    @render.ui
    def comp_controls_ui():
        df = df_react()
        if df.empty:
            return ui.p("Cargue un dataset para habilitar el analisis de brechas.", class_="text-muted")
        
        num_cols, _, cat_cols = classify_columns(df)
        if not cat_cols or not num_cols:
            return ui.p("Se requiere al menos una variable numerica y una categorica.", class_="status-warning")

        # Sugerir categorias territoriales o de estrato
        pref_cats = [c for c in cat_cols if any(k in c.lower() for k in ("depa", "muni", "estrato", "sector", "region", "tipo", "naturaleza"))]
        default_cat = pref_cats[0] if pref_cats else cat_cols[0]

        pref_nums = [c for c in num_cols if any(k in c.lower() for k in ("valor", "monto", "precio", "punt", "ingreso", "total"))]
        default_num = pref_nums[0] if pref_nums else num_cols[0]

        return ui.layout_columns(
            ui.input_select("cat_group", "Variable de Agrupacion (Departamento / Estrato / Sector):", choices=cat_cols, selected=default_cat),
            ui.input_select("num_target", "Variable Cuantitativa de Comparacion:", choices=num_cols, selected=default_num),
            ui.input_select("comp_style", "Visualizacion:",
                            choices=["Ranking de Promedios (Barras)", "Diagrama de Caja (Box Plot)", "Distribucion (Violin)"]),
            ui.input_numeric("top_categories", "Limite de Grupos:", value=12, min=3, max=30),
            col_widths={"sm": 12, "md": 6, "lg": 3},
            class_="mb-2 g-2"
        )

    @reactive.calc
    def gap_metrics():
        df = df_react()
        if df.empty or not hasattr(input, "cat_group") or not hasattr(input, "num_target"):
            return None
        cat = input.cat_group()
        num = input.num_target()
        if not cat or not num or cat not in df.columns or num not in df.columns:
            return None
        return compute_economic_gaps(df, cat_col=cat, val_col=num, top_n=int(input.top_categories() or 12))

    @output
    @render.ui
    def comp_gap_kpis():
        gaps = gap_metrics()
        if not gaps or not gaps.get("valido", False):
            return ui.span()

        return ui.layout_columns(
            ui.value_box(
                "Grupo Lider (Mayor Promedio)",
                f"{gaps['valor_lider']:,.2f}",
                ui.p(f"Categoria: {gaps['grupo_lider']}", class_="text-muted mb-0", style="font-size: 0.78rem;"),
                showcase=ui.span("Lider", class_="badge badge-status-ok p-2"),
                theme=None,
                class_="kpi-card"
            ),
            ui.value_box(
                "Grupo Rezagado (Menor Promedio)",
                f"{gaps['valor_rezagado']:,.2f}",
                ui.p(f"Categoria: {gaps['grupo_rezagado']}", class_="text-muted mb-0", style="font-size: 0.78rem;"),
                showcase=ui.span("Base", class_="badge badge-category p-2"),
                theme=None,
                class_="kpi-card"
            ),
            ui.value_box(
                "Ratio de Brecha Relativa",
                f"{gaps['ratio_brecha']:.2f}x",
                ui.p("El lider supera al grupo base por este factor", class_="text-muted mb-0", style="font-size: 0.78rem;"),
                showcase=ui.span("Disparidad", class_="badge kpi-missing-mid p-2"),
                theme=None,
                class_="kpi-card"
            ),
            ui.value_box(
                "Brecha Absoluta Media",
                f"{gaps['dif_absoluta']:,.2f}",
                ui.p("Distancia promedio entre extremos", class_="text-muted mb-0", style="font-size: 0.78rem;"),
                showcase=ui.span("Diferencia", class_="badge bg-slate-100 text-slate-700 p-2"),
                theme=None,
                class_="kpi-card"
            ),
            col_widths={"sm": 12, "md": 6, "lg": 3},
            class_="mb-3 g-2"
        )

    @output
    @render.ui
    def comp_plot_container():
        df = df_react()
        if df.empty or not hasattr(input, "num_target") or not hasattr(input, "cat_group"):
            return ui.span()

        num_col = input.num_target()
        cat_col = input.cat_group()
        style = input.comp_style()
        max_cats = int(input.top_categories() or 12)

        if not num_col or not cat_col or num_col not in df.columns or cat_col not in df.columns:
            return ui.span()

        top_keys = df[cat_col].value_counts().head(max_cats).index
        subset = df[df[cat_col].isin(top_keys)].copy()
        subset[cat_col] = subset[cat_col].astype(str)

        palette = ["#1e40af", "#0284c7", "#0f766e", "#4338ca", "#b45309", "#475569"]

        if style == "Ranking de Promedios (Barras)":
            agg = subset.groupby(cat_col, as_index=False)[num_col].mean().sort_values(by=num_col, ascending=True)
            fig = px.bar(
                agg, x=num_col, y=cat_col, orientation="h",
                title=f"Promedio de {num_col} por {cat_col}",
                color=num_col,
                color_continuous_scale=["#bfdbfe", "#1e40af"]
            )
            fig.update_layout(coloraxis_showscale=False)

        elif style == "Diagrama de Caja (Box Plot)":
            fig = px.box(
                subset, x=cat_col, y=num_col, color=cat_col,
                title=f"Distribucion de {num_col} por {cat_col}",
                color_discrete_sequence=palette
            )
            fig.update_xaxes(tickangle=-35)

        else:
            fig = px.violin(
                subset, x=cat_col, y=num_col, color=cat_col, box=True,
                title=f"Densidad de {num_col} por {cat_col}",
                color_discrete_sequence=palette
            )
            fig.update_xaxes(tickangle=-35)

        fig.update_layout(
            height=340,
            margin=dict(t=45, b=50, l=60, r=30),
            plot_bgcolor="white",
            paper_bgcolor="white",
            showlegend=False
        )
        return ui.HTML(fig.to_html(full_html=False, include_plotlyjs="cdn", config={"responsive": True}))

    @output
    @render.data_frame
    def comp_gap_table():
        gaps = gap_metrics()
        if not gaps or not gaps.get("valido", False):
            return render.DataGrid(pd.DataFrame(), height="300px")
        return render.DataGrid(gaps["tabla"], filters=False, height="300px")

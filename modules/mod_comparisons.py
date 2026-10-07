"""Modulo de comparacion categorica vs cuantitativa."""
from shiny import module, ui, render
import pandas as pd
import plotly.express as px
from services.stats_service import classify_columns


@module.ui
def comparisons_ui():
    return ui.card(
        ui.card_header("Comparaciones por Categoria"),
        ui.output_ui("comp_controls_ui"),
        ui.output_ui("comp_plot_container"),
        full_screen=True
    )


@module.server
def comparisons_server(input, output, session, df_react):

    @output
    @render.ui
    def comp_controls_ui():
        df = df_react()
        if df.empty:
            return ui.p("Cargue un dataset para habilitar comparaciones.", class_="text-muted")
        
        num_cols, _, cat_cols = classify_columns(df)
        if not cat_cols or not num_cols:
            return ui.p("Se requiere al menos una variable numerica y una categorica.", class_="status-warning")

        return ui.layout_columns(
            ui.input_select("num_target", "Variable Numerica (Y):", choices=num_cols),
            ui.input_select("cat_group", "Variable Categorica (X):", choices=cat_cols),
            ui.input_select("comp_style", "Tipo de Visualizacion:",
                            choices=["Barras (Promedio)", "Box Plot por Grupo", "Violin por Grupo", "Conteo de Registros"]),
            ui.input_numeric("top_categories", "Maximo de categorias:", value=12, min=3, max=30),
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

        positron_palette = ["#1d4ed8", "#0284c7", "#0f766e", "#4f46e5", "#d97706", "#059669"]

        if style == "Barras (Promedio)":
            agg = subset.groupby(cat_col, as_index=False)[num_col].mean().sort_values(by=num_col, ascending=False)
            fig = px.bar(
                agg, x=cat_col, y=num_col,
                title=f"Promedio de {num_col} segun {cat_col}",
                color=num_col,
                color_continuous_scale="Blues"
            )

        elif style == "Conteo de Registros":
            cnt = subset[cat_col].value_counts().reset_index()
            cnt.columns = [cat_col, "Frecuencia"]
            fig = px.bar(
                cnt, x=cat_col, y="Frecuencia",
                title=f"Conteo de registros segun {cat_col}",
                color="Frecuencia",
                color_continuous_scale="Blues"
            )

        elif style == "Box Plot por Grupo":
            fig = px.box(
                subset, x=cat_col, y=num_col, color=cat_col,
                title=f"Distribucion de {num_col} por {cat_col}",
                color_discrete_sequence=positron_palette
            )

        else:
            fig = px.violin(
                subset, x=cat_col, y=num_col, color=cat_col, box=True,
                title=f"Distribucion de {num_col} por {cat_col}",
                color_discrete_sequence=positron_palette
            )

        fig.update_layout(
            height=480,
            margin=dict(t=50, b=80, l=40, r=40),
            plot_bgcolor="white",
            paper_bgcolor="white",
            showlegend=False
        )
        fig.update_xaxes(tickangle=-30)
        return ui.HTML(fig.to_html(full_html=False, include_plotlyjs="cdn", config={"responsive": True}))

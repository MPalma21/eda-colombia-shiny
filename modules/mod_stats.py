"""Modulo de tablas de inferencia estadistica y descriptiva."""
from shiny import module, ui, render
import pandas as pd
from services.stats_service import (
    classify_columns,
    compute_normality_tests,
    compute_categorical_summary
)


@module.ui
def stats_ui():
    return ui.div(
        ui.card(
            ui.card_header("Estadisticas Descriptivas Cuantitativas"),
            ui.output_ui("num_describe_table"),
            full_screen=True
        ),
        ui.layout_columns(
            ui.card(
                ui.card_header("Prueba de Normalidad Shapiro-Wilk"),
                ui.output_ui("shapiro_table"),
                full_screen=True
            ),
            ui.card(
                ui.card_header("Resumen de Variables Categoricas"),
                ui.output_ui("cat_summary_table"),
                full_screen=True
            ),
            col_widths=[6, 6]
        )
    )


@module.server
def stats_server(input, output, session, df_react):

    @output
    @render.ui
    def num_describe_table():
        df = df_react()
        if df.empty:
            return ui.p("Cargue un dataset para ver tablas descriptivas.", class_="text-muted py-2")
        
        num_cols, _, _ = classify_columns(df)
        if not num_cols:
            return ui.p("No se identificaron variables numericas en el conjunto de datos.", class_="text-muted")

        desc = df[num_cols].describe(percentiles=[0.05, 0.25, 0.5, 0.75, 0.95]).T.round(2)
        desc.insert(0, "Variable", desc.index)

        return ui.div(
            ui.HTML(desc.to_html(index=False, classes="custom-table", border=0)),
            style="overflow-x: auto;"
        )

    @output
    @render.ui
    def shapiro_table():
        df = df_react()
        if df.empty:
            return ui.span()
        
        norm_df = compute_normality_tests(df)
        if norm_df.empty:
            return ui.p("No aplicable para las variables numericas actuales.", class_="text-muted")

        return ui.div(
            ui.HTML(norm_df.to_html(index=False, classes="custom-table", border=0)),
            style="overflow-x: auto;"
        )

    @output
    @render.ui
    def cat_summary_table():
        df = df_react()
        if df.empty:
            return ui.span()
        
        cat_df = compute_categorical_summary(df)
        if cat_df.empty:
            return ui.p("No se identificaron variables categoricas.", class_="text-muted")

        return ui.div(
            ui.HTML(cat_df.to_html(index=False, classes="custom-table", border=0)),
            style="overflow-x: auto;"
        )

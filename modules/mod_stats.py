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
            ui.output_data_frame("num_describe_grid"),
            full_screen=True,
            class_="mb-3"
        ),
        ui.layout_columns(
            ui.card(
                ui.card_header("Prueba de Normalidad Shapiro-Wilk (Muestra n<=5000)"),
                ui.output_data_frame("shapiro_grid"),
                full_screen=True
            ),
            ui.card(
                ui.card_header("Resumen de Variables Categoricas y Modas"),
                ui.output_data_frame("cat_summary_grid"),
                full_screen=True
            ),
            col_widths={"sm": 12, "md": 6},
            class_="g-3"
        )
    )


@module.server
def stats_server(input, output, session, df_react):

    @output
    @render.data_frame
    def num_describe_grid():
        df = df_react()
        if df.empty:
            return render.DataGrid(pd.DataFrame(), height="280px")
        
        num_cols, _, _ = classify_columns(df)
        if not num_cols:
            return render.DataGrid(pd.DataFrame({"Mensaje": ["No se identificaron variables numericas"]}))

        desc = df[num_cols].describe(percentiles=[0.05, 0.25, 0.5, 0.75, 0.95]).T.round(2)
        desc.insert(0, "Variable", desc.index)

        return render.DataGrid(desc, filters=False, height="320px", selection_mode="none")

    @output
    @render.data_frame
    def shapiro_grid():
        df = df_react()
        if df.empty:
            return render.DataGrid(pd.DataFrame(), height="240px")
        
        norm_df = compute_normality_tests(df)
        if norm_df.empty:
            return render.DataGrid(pd.DataFrame({"Mensaje": ["No aplicable para variables numericas actuales"]}))

        return render.DataGrid(norm_df, filters=False, height="260px", selection_mode="none")

    @output
    @render.data_frame
    def cat_summary_grid():
        df = df_react()
        if df.empty:
            return render.DataGrid(pd.DataFrame(), height="240px")
        
        cat_df = compute_categorical_summary(df)
        if cat_df.empty:
            return render.DataGrid(pd.DataFrame({"Mensaje": ["No se identificaron variables categoricas"]}))

        return render.DataGrid(cat_df, filters=False, height="260px", selection_mode="none")

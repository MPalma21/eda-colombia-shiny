"""Modulo para exploracion tabular interactiva con DataGrid nativo."""
from shiny import module, ui, render, reactive
import pandas as pd
from services.stats_service import classify_columns
from services.table_service import filter_table_rows, to_safe_csv_bytes


@module.ui
def table_ui():
    return ui.card(
        ui.card_header("Exploracion de Datos"),
        ui.layout_columns(
            ui.input_text("search_query", "Busqueda global rapida:", placeholder="Filtrar registros por texto..."),
            ui.output_ui("category_filter_ui"),
            ui.input_text("category_value", "Buscar valor de categoría:", placeholder="Texto de la columna elegida; vacío = todas"),
            col_widths={"sm": 12, "md": 4},
            class_="mb-2 g-2"
        ),
        ui.output_ui("table_info_bar"),
        ui.download_button("download_filtered", "Descargar CSV filtrado", class_="btn btn-outline-primary mb-3"),
        ui.output_data_frame("main_data_grid"),
        full_screen=True
    )


@module.server
def table_server(input, output, session, df_react):
    
    @output
    @render.ui
    def category_filter_ui():
        df = df_react()
        if df.empty:
            return ui.span()
        _, _, cat_cols = classify_columns(df)
        if not cat_cols:
            return ui.span()
        
        options = {col: col for col in cat_cols}
        return ui.input_select("category_column", "Columna categórica:", choices=options)

    @reactive.calc
    def filtered_df():
        df = df_react()
        if df.empty:
            return pd.DataFrame()
        
        _, _, cat_cols = classify_columns(df)
        query = (input.search_query() or "").strip()
        column = input.category_column() if cat_cols else ""
        value = (input.category_value() or "").strip()
        return filter_table_rows(df, query, column if column in cat_cols else "", value)

    @output
    @render.download_button(filename="datos_filtrados.csv")
    def download_filtered():
        yield to_safe_csv_bytes(filtered_df())

    @output
    @render.ui
    def table_info_bar():
        df = filtered_df()
        total_len = len(df_react())
        if df.empty:
            return ui.p("No hay registros que coincidan con los criterios de busqueda.", class_="text-muted py-2 mb-0")
        
        return ui.p(
            f"Mostrando {len(df):,} de {total_len:,} filas. Utilice los encabezados de columna para ordenar o filtrar.",
            class_="text-muted small mb-2"
        )

    @output
    @render.data_frame
    def main_data_grid():
        df = filtered_df()
        if df.empty:
            return render.DataGrid(pd.DataFrame(), height="350px")
        
        return render.DataGrid(
            df,
            filters=True,
            selection_mode="rows",
            height="550px",
            width="100%"
        )

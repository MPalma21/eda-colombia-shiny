"""Modulo para exploracion tabular interactiva con DataGrid nativo."""
from shiny import module, ui, render, reactive
import pandas as pd
from services.stats_service import classify_columns


@module.ui
def table_ui():
    return ui.card(
        ui.card_header("Exploracion de Datos"),
        ui.row(
            ui.column(6, ui.input_text("search_query", "Busqueda global rapida:", placeholder="Filtrar registros por texto...")),
            ui.column(6, ui.output_ui("category_filter_ui")),
            class_="mb-2"
        ),
        ui.output_ui("table_info_bar"),
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
        
        main_cat = cat_cols[0]
        options = ["(Todos)"] + df[main_cat].dropna().astype(str).unique()[:50].tolist()
        return ui.input_select("selected_category", f"Filtrar por {main_cat}:", choices=options)

    @reactive.calc
    def filtered_df():
        df = df_react()
        if df.empty:
            return pd.DataFrame()
        
        _, _, cat_cols = classify_columns(df)
        res = df.copy()

        query = (input.search_query() or "").strip()
        if query:
            match_mask = res.astype(str).apply(
                lambda col: col.str.contains(query, case=False, na=False)
            ).any(axis=1)
            res = res[match_mask]

        if cat_cols and hasattr(input, "selected_category"):
            try:
                selected = input.selected_category()
                if selected and selected != "(Todos)":
                    res = res[res[cat_cols[0]].astype(str) == selected]
            except Exception:
                pass

        return res

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

"""Modulo para el control de carga y fuentes de datos abiertos."""
import asyncio
from shiny import module, ui, render, reactive
from shiny.types import SilentException, SilentCancelOutputException
import pandas as pd
from config import SAMPLE_DATASETS, DEFAULT_FETCH_ROWS, DEFAULT_MAX_ROWS
from services.api_service import fetch_dataset
from services.scope_service import apply_analysis_scope
from services.stats_service import classify_columns


@module.ui
def loader_ui():
    return ui.div(
        # Grupo 1: Seleccion de dataset
        ui.div(
            ui.span("Parametros de Consulta", class_="sidebar-section-title"),
            ui.p(
                "Consulte colecciones abiertas publicadas por entidades oficiales del Estado colombiano via SODA API.",
                class_="sidebar-description"
            ),
            class_="mb-3"
        ),
        
        ui.div(
            ui.input_select(
                "sample_ds",
                "Colecciones verificadas:",
                choices=list(SAMPLE_DATASETS.keys()),
            ),
            ui.input_text(
                "resource_id",
                "ID o URL de datos.gov.co:",
                placeholder="Ejemplo: mcec-87by",
                value=""
            ),
            ui.div(
                "Indique el codigo alfanumerico (ej: mcec-87by) o la URL completa.",
                class_="form-text text-muted small mt-n2 mb-3"
            ),
            ui.input_numeric(
                "n_rows",
                "Limite de registros:",
                value=DEFAULT_FETCH_ROWS,
                min=50,
                max=DEFAULT_MAX_ROWS,
                step=500
            ),
            ui.input_select(
                "fetch_mode", "Selección del origen:",
                choices={"first": "Primeros registros por ID", "spread": "Cobertura distribuida (5 bloques)"},
            ),
            ui.input_text("source_query", "Filtrar antes de cargar (texto opcional):", placeholder="Buscar en el recurso completo"),
            ui.p("La busqueda de texto del portal se aplica antes del limite de filas.", class_="form-text text-muted small"),
            ui.input_task_button(
                "btn_load",
                "Cargar y Analizar Datos",
                label_busy="Consultando datos...",
                class_="btn btn-primary w-100 py-2 mt-2 mb-2 btn-load-dataset"
            ),
            ui.output_ui("status_feedback"),
            class_="sidebar-controls-group"
        ),
        ui.output_ui("analysis_scope_ui"),
    )


@module.server
def loader_server(input, output, session):
    """Controlador del modulo de carga.
    
    Retorna tupla reactiva: (df_reactive, metadata_reactive).
    """
    rv_df = reactive.value(pd.DataFrame())
    rv_meta = reactive.value({})
    rv_msg = reactive.value("")
    rv_status = reactive.value("idle")

    @reactive.effect
    @reactive.event(input.sample_ds)
    def _sync_sample():
        chosen = input.sample_ds()
        rid = SAMPLE_DATASETS.get(chosen, "")
        if rid:
            ui.update_text("resource_id", value=rid)

    @ui.bind_task_button(button_id="btn_load")
    @reactive.extended_task
    async def _fetch_task(res_id: str, limit: int, query: str, mode: str):
        return await asyncio.to_thread(fetch_dataset, res_id, limit, query, mode)

    @reactive.effect
    @reactive.event(input.btn_load)
    def _execute_fetch():
        res_id = input.resource_id().strip()
        if not res_id:
            rv_status.set("error")
            rv_msg.set("Por favor ingrese un ID o URL valida.")
            ui.update_task_button("btn_load", state="ready")
            return

        rv_status.set("loading")
        rv_msg.set("Descargando y parseando datos desde API Socrata...")
        limit = int(input.n_rows() or DEFAULT_FETCH_ROWS)
        _fetch_task(res_id, limit, input.source_query() or "", input.fetch_mode())

    @reactive.effect
    def _receive_fetch():
        try:
            df, meta = _fetch_task.result()

            if df.empty:
                rv_df.set(pd.DataFrame())
                rv_meta.set(meta)
                rv_status.set("error")
                rv_msg.set("La consulta no devolvio registros. Revise el filtro o el recurso.")
                return

            rv_df.set(df)
            rv_meta.set(meta)
            rv_status.set("success")
            rv_msg.set(f"Dataset cargado: {len(df):,} filas y {len(df.columns)} columnas.")

        except (SilentException, SilentCancelOutputException):
            return
        except Exception as exc:
            rv_status.set("error")
            rv_msg.set(f"Error en la consulta: {str(exc)[:100]}")

    @output
    @render.ui
    def status_feedback():
        status = rv_status()
        msg = rv_msg()
        if not msg:
            return ui.span()
        
        css_class = {
            "success": "status-success",
            "error": "status-error",
            "loading": "status-warning"
        }.get(status, "")

        return ui.div(
            ui.p(msg, class_=f"{css_class} mb-0", style="font-size: 0.82rem;"),
            class_="alert-status-box mt-2"
        )

    @output
    @render.ui
    def analysis_scope_ui():
        df = rv_df()
        if df.empty:
            return ui.span()
        _, date_cols, _ = classify_columns(df)
        return ui.div(
            ui.span("Alcance del análisis", class_="sidebar-section-title"),
            ui.p("Estos ajustes se aplican a las filas descargadas y a todas las vistas.", class_="sidebar-description"),
            ui.input_select("scope_date_column", "Variable de fecha:", choices={"": "Todas las fechas", **{col: col for col in date_cols}}),
            ui.output_ui("scope_period_ui"),
            ui.input_select("sample_mode", "Registros a analizar:", choices={"all": "Todos los descargados", "sample": "Muestra aleatoria de los descargados"}),
            ui.input_numeric("sample_rows", "Tamaño de la muestra:", value=min(1000, len(df)), min=1, max=len(df)),
            class_="sidebar-controls-group border-top pt-3 mt-3",
        )

    @output
    @render.ui
    def scope_period_ui():
        df = rv_df()
        column = input.scope_date_column()
        if df.empty or not column or column not in df.columns:
            return ui.span()
        dates = pd.to_datetime(df[column], errors="coerce").dropna()
        if dates.empty:
            return ui.span()
        return ui.input_date_range(
            "scope_period", "Período:",
            start=dates.min().date(), end=dates.max().date(),
            min=dates.min().date(), max=dates.max().date(),
            width="100%",
        )

    @reactive.calc
    def scoped_df():
        df = rv_df()
        if df.empty:
            return df
        column = input.scope_date_column() or ""
        period = input.scope_period() if column and hasattr(input, "scope_period") else None
        sample_rows = None
        if input.sample_mode() == "sample":
            sample_rows = max(1, min(int(input.sample_rows() or 1), len(df)))
        return apply_analysis_scope(df, column, period, sample_rows)

    @reactive.calc
    def scoped_meta():
        meta = dict(rv_meta())
        loaded = rv_df()
        meta["_eda_loaded_rows"] = len(loaded)
        if not loaded.empty:
            column = input.scope_date_column() or ""
            period = input.scope_period() if column and hasattr(input, "scope_period") else None
            if column and period:
                meta["_eda_period_label"] = f"{column}: {period[0]} a {period[1]}"
            meta["_eda_sample_active"] = input.sample_mode() == "sample"
        return meta

    return scoped_df, scoped_meta

"""Modulo para el control de carga y fuentes de datos abiertos."""
from shiny import module, ui, render, reactive
import pandas as pd
from config import SAMPLE_DATASETS, DEFAULT_FETCH_ROWS, DEFAULT_MAX_ROWS
from services.api_service import fetch_dataset


@module.ui
def loader_ui():
    return ui.div(
        ui.h5("Fuente de Datos", style="font-size: 0.95rem; font-weight: 600; margin-bottom: 12px;"),
        ui.div(
            "Indique el ID del recurso (ej: gt2j-8ykr) o la URL completa de datos.gov.co, o elija un conjunto de datos sugerido.",
            class_="alert-box alert-info-box"
        ),
        ui.input_select(
            "sample_ds",
            "Dataset sugerido:",
            choices=list(SAMPLE_DATASETS.keys()),
        ),
        ui.input_text(
            "resource_id",
            "ID o URL del recurso:",
            placeholder="Ejemplo: gt2j-8ykr",
            value=""
        ),
        ui.input_numeric(
            "n_rows",
            "Limite de registros:",
            value=DEFAULT_FETCH_ROWS,
            min=50,
            max=DEFAULT_MAX_ROWS,
            step=500
        ),
        ui.input_action_button(
            "btn_load",
            "Cargar Dataset",
            class_="btn btn-primary w-100 mt-2 mb-2"
        ),
        ui.output_ui("status_feedback")
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

    @reactive.effect
    @reactive.event(input.btn_load)
    def _execute_fetch():
        res_id = input.resource_id().strip()
        if not res_id:
            rv_status.set("error")
            rv_msg.set("Por favor ingrese un ID o URL valida.")
            return

        rv_status.set("loading")
        rv_msg.set("Consultando API Socrata...")

        try:
            limit = int(input.n_rows() or DEFAULT_FETCH_ROWS)
            df, meta = fetch_dataset(res_id, limit=limit)

            if df.empty:
                rv_status.set("error")
                rv_msg.set("La API respondio pero no se encontraron registros disponibles.")
                return

            rv_df.set(df)
            rv_meta.set(meta)
            rv_status.set("success")
            rv_msg.set(f"Dataset cargado: {len(df):,} filas y {len(df.columns)} columnas.")

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

        return ui.p(msg, class_=f"{css_class} mt-2 mb-0", style="font-size: 0.82rem;")

    return rv_df, rv_meta

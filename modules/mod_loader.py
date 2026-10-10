"""Modulo para el control de carga y fuentes de datos abiertos (SECOP II).

Depurado para enfocar exclusivamente la auditoria de contratacion publica:
- Seleccion unificada de colecciones de contratacion sin duplicidad de campos.
- Seleccion clara del volumen de contratos a auditar.
- Filtro rapido por territorio o entidad.
- Filtro temporal limpio por periodo de ejecucion o firma.
"""
import asyncio
from shiny import module, ui, render, reactive
from shiny.types import SilentException, SilentCancelOutputException
import pandas as pd
from config import DEFAULT_FETCH_ROWS, DEFAULT_RESOURCE_ID, DATASET_OPTIONS
from services.api_service import fetch_dataset
from services.scope_service import apply_analysis_scope
from services.stats_service import classify_columns


@module.ui
def loader_ui():
    return ui.div(
        # Encabezado de la barra lateral
        ui.div(
            ui.span("Parámetros de Consulta", class_="sidebar-section-title"),
            ui.p(
                "Auditoría oficial de contratación estatal vía API de datos.gov.co.",
                class_="sidebar-description"
            ),
            class_="mb-3"
        ),
        
        # Controles depurados sin redundancia
        ui.div(
            ui.input_select(
                "dataset_source",
                "Fuente de Contratación:",
                choices=DATASET_OPTIONS,
                selected=DEFAULT_RESOURCE_ID
            ),
            ui.output_ui("custom_resource_input_ui"),
            ui.input_select(
                "n_rows",
                "Volumen de Contratos a Auditar:",
                choices={
                    "5000": "5,000 contratos (Rápido)",
                    "10000": "10,000 contratos (Recomendado)",
                    "25000": "25,000 contratos (Amplio)",
                    "50000": "50,000 contratos (Máximo)"
                },
                selected=str(DEFAULT_FETCH_ROWS)
            ),
            ui.input_text(
                "source_query",
                "Filtrar por Territorio o Entidad (opcional):",
                placeholder="Ej. Antioquia, Bogotá, Salud..."
            ),
            ui.input_task_button(
                "btn_load",
                "Cargar y Auditar Contratos",
                label_busy="Descargando SECOP...",
                class_="btn btn-primary w-100 py-2 mt-2 mb-2 btn-load-dataset"
            ),
            ui.output_ui("status_feedback"),
            class_="sidebar-controls-group"
        ),
        ui.output_ui("temporal_filter_ui"),
    )


@module.server
def loader_server(input, output, session):
    """Controlador del modulo de carga simplificado."""
    rv_df = reactive.value(pd.DataFrame())
    rv_meta = reactive.value({})
    rv_msg = reactive.value("")
    rv_status = reactive.value("idle")

    @output
    @render.ui
    def custom_resource_input_ui():
        if input.dataset_source() == "custom":
            return ui.div(
                ui.input_text(
                    "custom_resource_id",
                    "ID o URL de datos.gov.co:",
                    placeholder="Ejemplo: jbjy-vk9h",
                    value=""
                ),
                class_="mb-2"
            )
        return ui.span()

    @ui.bind_task_button(button_id="btn_load")
    @reactive.extended_task
    async def _fetch_task(res_id: str, limit: int, query: str):
        return await asyncio.to_thread(fetch_dataset, res_id, limit, query, "first")

    @reactive.effect
    @reactive.event(input.btn_load)
    def _execute_fetch():
        source = input.dataset_source()
        if source == "custom":
            res_id = input.custom_resource_id().strip() if hasattr(input, "custom_resource_id") else ""
        else:
            res_id = source

        if not res_id:
            rv_status.set("error")
            rv_msg.set("Por favor ingrese un ID o URL válida.")
            ui.update_task_button("btn_load", state="ready")
            return

        rv_status.set("loading")
        rv_msg.set("Descargando contratos desde API Socrata...")
        try:
            limit = int(input.n_rows() or DEFAULT_FETCH_ROWS)
        except Exception:
            limit = DEFAULT_FETCH_ROWS
        _fetch_task(res_id, limit, input.source_query() or "")

    @reactive.effect
    def _receive_fetch():
        try:
            df, meta = _fetch_task.result()

            if df.empty:
                rv_df.set(pd.DataFrame())
                rv_meta.set(meta)
                rv_status.set("error")
                rv_msg.set("La consulta no devolvió registros. Revise el filtro o el recurso.")
                return

            rv_df.set(df)
            rv_meta.set(meta)
            rv_status.set("success")
            rv_msg.set(f"Dataset cargado: {len(df):,} contratos auditados.")

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
    def temporal_filter_ui():
        df = rv_df()
        if df.empty:
            return ui.span()
        _, date_cols, _ = classify_columns(df)
        if not date_cols:
            return ui.span()

        pref_date = [c for c in date_cols if any(k in c.lower() for k in ("firma", "inicio", "crea", "fecha"))]
        default_col = pref_date[0] if pref_date else date_cols[0]

        return ui.div(
            ui.span("Filtro Temporal", class_="sidebar-section-title"),
            ui.p("Acote la auditoría a un período específico:", class_="sidebar-description"),
            ui.input_select("scope_date_column", "Variable de fecha:", choices={col: col for col in date_cols}, selected=default_col),
            ui.output_ui("scope_period_ui"),
            class_="sidebar-controls-group border-top pt-3 mt-3",
        )

    @output
    @render.ui
    def scope_period_ui():
        df = rv_df()
        column = input.scope_date_column() if hasattr(input, "scope_date_column") else ""
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
        column = input.scope_date_column() if hasattr(input, "scope_date_column") else ""
        period = input.scope_period() if column and hasattr(input, "scope_period") else None
        return apply_analysis_scope(df, column, period, None)

    @reactive.calc
    def scoped_meta():
        meta = dict(rv_meta())
        loaded = rv_df()
        meta["_eda_loaded_rows"] = len(loaded)
        if not loaded.empty:
            column = input.scope_date_column() if hasattr(input, "scope_date_column") else ""
            period = input.scope_period() if column and hasattr(input, "scope_period") else None
            if column and period:
                meta["_eda_period_label"] = f"{column}: {period[0]} a {period[1]}"
            meta["_eda_sample_active"] = False
        return meta

    return scoped_df, scoped_meta

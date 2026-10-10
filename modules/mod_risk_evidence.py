"""Modulo de Matriz de Evidencia y Microdatos para Veeduria (Auditoria & Control Fiscal).

Perspectiva 5 del Panel de Riesgo Territorial:
- Matriz completa de evaluacion departamental con semaforos y scores.
- Visor de microdatos de contratos individuales con banderas de riesgo contractual.
- Filtros interactivos por nivel de riesgo y busqueda textual.
- Exportacion segura de datos en CSV (RFC-4180 sanitizado) para entes de control.
"""
from shiny import module, ui, render, reactive
import numpy as np
import pandas as pd
from services.economic_service import (
    compute_procurement_risk_matrix,
    find_procurement_columns,
    format_cop_currency
)
from services.table_service import to_safe_csv_bytes


@module.ui
def risk_evidence_ui():
    return ui.div(
        # Tarjeta 1: Matriz Departamental Consolidada
        ui.card(
            ui.card_header(
                ui.div(
                    ui.span("Matriz Consolidada de Riesgo Territorial · SECOP II", class_="fw-bold"),
                    ui.span("Microdatos Agregados con Semáforos, HHI y Cuotas de Mercado", class_="text-muted", style="font-size: 0.78rem;")
                ),
                class_="d-flex justify-content-between align-items-center"
            ),
            ui.div(
                ui.span("Guía de Auditoría para Veedurías y Control Fiscal: ", class_="fw-bold text-primary small"),
                ui.span("Esta matriz consolida las variables analizadas por jurisdicción. Permite filtrar por semáforo y descargar el expediente completo en CSV para sustentar denuncias formales o informes técnicos de veeduría.", class_="small text-muted"),
                class_="guide-callout mb-3"
            ),
            ui.div(
                ui.div(
                    ui.input_select(
                        "evidence_risk_filter",
                        "Filtrar Matriz por Semáforo:",
                        choices=[
                            "Todos los Niveles",
                            "Solo Alto Riesgo (Críticos)",
                            "Solo Riesgo Moderado",
                            "Solo Bajo Riesgo (Competitivos)"
                        ],
                        selected="Todos los Niveles"
                    ),
                    class_="col-12 col-md-4"
                ),
                ui.div(
                    ui.download_button(
                        "btn_download_matrix",
                        "Descargar Matriz (CSV)",
                        class_="btn btn-outline-primary btn-sm mt-md-4"
                    ),
                    class_="col-12 col-md-3 text-md-end"
                ),
                class_="row align-items-center mb-3 g-2"
            ),
            ui.output_data_frame("evidence_matrix_table"),
            full_screen=True,
            class_="mb-3"
        ),

        # Tarjeta 2: Microdatos de Contratos con Flags de Riesgo
        ui.card(
            ui.card_header(
                ui.div(
                    ui.span("Expediente de Contratos Auditados con Banderas de Alerta", class_="fw-bold"),
                    ui.span("Microdatos a Nivel de Contrato Individual para Veeduría Ciudadana", class_="text-muted", style="font-size: 0.78rem;")
                ),
                class_="d-flex justify-content-between align-items-center"
            ),
            ui.div(
                ui.span("Glosario de Banderas Contractuales: ", class_="fw-bold text-primary small"),
                ui.span("Directa de Alto Monto: Contrato asignado a dedo cuyo valor supera el percentil 75 del territorio (máxima prioridad de revisión). Contratación Directa: Convenio o contrato bajo causal directa ordinaria. Proceso Abierto / Concurso: Licitación pública o puja con pluralidad de oferentes.", class_="small text-muted"),
                class_="guide-callout mb-3"
            ),
            ui.div(
                ui.div(
                    ui.input_text("contract_search", "Buscar en contratos (texto o proveedor):", placeholder="Ej. consorcio, obra, etc."),
                    class_="col-12 col-md-5"
                ),
                ui.div(
                    ui.download_button(
                        "btn_download_contracts",
                        "Descargar Contratos (CSV)",
                        class_="btn btn-outline-primary btn-sm mt-md-4"
                    ),
                    class_="col-12 col-md-3 text-md-end"
                ),
                class_="row align-items-center mb-3 g-2"
            ),
            ui.output_data_frame("evidence_contracts_table"),
            full_screen=True
        )
    )


@module.server
def risk_evidence_server(input, output, session, df_react):

    @reactive.calc
    def full_matrix_df():
        df = df_react()
        if df.empty:
            return pd.DataFrame()
        return compute_procurement_risk_matrix(df, min_contracts_per_dept=1)

    @reactive.calc
    def filtered_matrix_df():
        matrix = full_matrix_df()
        if matrix.empty:
            return matrix

        filt = input.evidence_risk_filter() if hasattr(input, "evidence_risk_filter") else "Todos los Niveles"
        if filt == "Solo Alto Riesgo (Críticos)":
            return matrix[matrix["nivel_riesgo"] == "Alto Riesgo (Crítico)"].copy()
        elif filt == "Solo Riesgo Moderado":
            return matrix[matrix["nivel_riesgo"] == "Riesgo Moderado"].copy()
        elif filt == "Solo Bajo Riesgo (Competitivos)":
            return matrix[matrix["nivel_riesgo"] == "Bajo Riesgo (Competitivo)"].copy()
        return matrix

    # -------------------------------------------------------------
    # 1. TABLA DE LA MATRIZ DE RIESGO
    # -------------------------------------------------------------
    @output
    @render.data_frame
    def evidence_matrix_table():
        matrix = filtered_matrix_df()
        if matrix.empty:
            return pd.DataFrame()

        display_df = matrix[[
            "badge_icon", "departamento", "nivel_riesgo", "score_riesgo",
            "monto_total", "n_contratos", "pct_directa_monto", "hhi",
            "cr4", "top_contratista", "top_cuota"
        ]].copy()

        display_df["monto_total"] = display_df["monto_total"].apply(format_cop_currency)

        display_df.columns = [
            "Alerta", "Departamento", "Nivel de Riesgo", "Score (0-100)",
            "Presupuesto Auditado", "Contratos", "% Directa", "HHI",
            "CR4 (%)", "Top Contratista", "Cuota Top (%)"
        ]

        return render.DataGrid(display_df, filters=True, selection_mode="none")

    @render.download_button(filename="matriz_riesgo_territorial_secop.csv")
    def btn_download_matrix():
        matrix = filtered_matrix_df()
        if matrix.empty:
            return b""
        return to_safe_csv_bytes(matrix)

    # -------------------------------------------------------------
    # 2. MICRODATOS DE CONTRATOS AUDITADOS
    # -------------------------------------------------------------
    @reactive.calc
    def flagged_contracts_df():
        df = df_react()
        if df.empty:
            return pd.DataFrame()

        dept_c, val_c, prov_c, mod_c = find_procurement_columns(df)
        
        # Buscar columna de objeto
        obj_c = None
        for c in df.columns:
            if any(k in c.lower() for k in ("objeto", "descripcion", "detalle")):
                obj_c = c
                break

        val_series = pd.to_numeric(df[val_c], errors="coerce").dropna() if val_c and val_c in df.columns else pd.Series(dtype=float)
        q75 = float(val_series.quantile(0.75)) if not val_series.empty else 0.0

        sample_subset = df.head(1500)
        if sample_subset.empty:
            return pd.DataFrame()

        depts = sample_subset[dept_c].fillna("Territorio N/A").astype(str) if dept_c and dept_c in sample_subset.columns else pd.Series("Territorio N/A", index=sample_subset.index)
        provs = sample_subset[prov_c].fillna("Sin proveedor").astype(str) if prov_c and prov_c in sample_subset.columns else pd.Series("Sin proveedor", index=sample_subset.index)
        vals = pd.to_numeric(sample_subset[val_c], errors="coerce").fillna(0.0) if val_c and val_c in sample_subset.columns else pd.Series(0.0, index=sample_subset.index)
        mods = sample_subset[mod_c].fillna("No especificada").astype(str) if mod_c and mod_c in sample_subset.columns else pd.Series("No especificada", index=sample_subset.index)
        objs = sample_subset[obj_c].fillna("Contrato de obra / prestación de servicios").astype(str).str.slice(0, 80) if obj_c and obj_c in sample_subset.columns else pd.Series("Contrato de obra / prestación de servicios", index=sample_subset.index)

        is_direct = mods.str.lower().str.contains("direct|urgencia|especial|sin concurso", regex=True, na=False)
        cond_high = is_direct & (vals >= q75) & (q75 > 0)
        cond_dir = is_direct & (~cond_high)
        flags = np.select([cond_high, cond_dir], ["Directa de Alto Monto", "Contratación Directa"], default="Proceso Abierto / Concurso")

        res_df = pd.DataFrame({
            "alerta_contrato": flags,
            "departamento": depts,
            "proveedor": provs,
            "monto_raw": vals,
            "monto": vals.map(format_cop_currency),
            "modalidad": mods,
            "objeto": objs
        }, index=sample_subset.index)

        # Filtro de búsqueda textual
        query = input.contract_search().strip() if hasattr(input, "contract_search") else ""
        if query and not res_df.empty:
            mask = res_df.astype(str).apply(
                lambda col: col.str.contains(query, case=False, na=False, regex=False)
            ).any(axis=1)
            res_df = res_df.loc[mask]

        return res_df

    @output
    @render.data_frame
    def evidence_contracts_table():
        c_df = flagged_contracts_df()
        if c_df.empty:
            return pd.DataFrame()

        display_df = c_df[[
            "alerta_contrato", "departamento", "proveedor", "monto", "modalidad", "objeto"
        ]].copy()

        display_df.columns = [
            "Bandera de Alerta", "Departamento", "Contratista", "Monto Contractual", "Modalidad", "Objeto del Contrato"
        ]

        return render.DataGrid(display_df, filters=True, selection_mode="none")

    @render.download_button(filename="microdatos_contratos_auditados_secop.csv")
    def btn_download_contracts():
        c_df = flagged_contracts_df()
        if c_df.empty:
            return b""
        return to_safe_csv_bytes(c_df)

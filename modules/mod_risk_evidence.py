"""Modulo de Matriz de Evidencia y Microdatos para Veeduria (Auditoria & Control Fiscal).

Perspectiva 5 del Panel de Riesgo Territorial:
- Matriz completa de evaluacion departamental con semaforos y scores.
- Visor de microdatos de contratos individuales con banderas de riesgo contractual.
- Filtros interactivos por nivel de riesgo y busqueda textual.
- Exportacion segura de datos en CSV (RFC-4180 sanitizado) para entes de control.
"""
from shiny import module, ui, render, reactive
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
                ui.div(
                    ui.input_select(
                        "evidence_risk_filter",
                        "Filtrar Matriz por Semáforo:",
                        choices=[
                            "Todos los Niveles",
                            "🔴 Solo Alto Riesgo (Críticos)",
                            "🟡 Solo Riesgo Moderado",
                            "🟢 Solo Bajo Riesgo (Competitivos)"
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
        if filt == "🔴 Solo Alto Riesgo (Críticos)":
            return matrix[matrix["nivel_riesgo"] == "Alto Riesgo (Crítico)"].copy()
        elif filt == "🟡 Solo Riesgo Moderado":
            return matrix[matrix["nivel_riesgo"] == "Riesgo Moderado"].copy()
        elif filt == "🟢 Solo Bajo Riesgo (Competitivos)":
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

    @render.download(filename="matriz_riesgo_territorial_secop.csv")
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

        records = []
        val_series = df[val_c].dropna() if val_c and val_c in df.columns and pd.api.types.is_numeric_dtype(df[val_c]) else pd.Series(dtype=float)
        q75 = val_series.quantile(0.75) if not val_series.empty else 0.0

        sample_subset = df.head(1500).copy()

        for _, row in sample_subset.iterrows():
            dept = str(row[dept_c]) if dept_c and dept_c in row and pd.notnull(row[dept_c]) else "Territorio N/A"
            prov = str(row[prov_c]) if prov_c and prov_c in row and pd.notnull(row[prov_c]) else "Sin proveedor"
            val = float(row[val_c]) if val_c and val_c in row and pd.notnull(row[val_c]) else 0.0
            mod = str(row[mod_c]) if mod_c and mod_c in row and pd.notnull(row[mod_c]) else "No especificada"
            obj = str(row[obj_c])[:80] if obj_c and obj_c in row and pd.notnull(row[obj_c]) else "Contrato de obra / prestación de servicios"

            is_direct = any(k in mod.lower() for k in ("direct", "urgencia", "especial", "sin concurso"))
            if is_direct and val >= q75 and q75 > 0:
                flag = "🔴 Directa de Alto Monto"
            elif is_direct:
                flag = "🟡 Contratación Directa"
            else:
                flag = "🟢 Proceso Abierto / Concurso"

            records.append({
                "alerta_contrato": flag,
                "departamento": dept,
                "proveedor": prov,
                "monto_raw": val,
                "monto": format_cop_currency(val),
                "modalidad": mod,
                "objeto": obj
            })

        res_df = pd.DataFrame(records)

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

    @render.download(filename="microdatos_contratos_auditados_secop.csv")
    def btn_download_contracts():
        c_df = flagged_contracts_df()
        if c_df.empty:
            return b""
        return to_safe_csv_bytes(c_df)

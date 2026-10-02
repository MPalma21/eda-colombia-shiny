"""Punto de entrada de la aplicacion Shiny EDA Colombia.

Disenado bajo la arquitectura modular y desacoplada recomendada por Posit PBC:
- Modulos encapsulados (@module)
- Capa de presentacion y servicios independientes
- Grafo reactivo controlado
"""
from pathlib import Path
from shiny import App, ui
from config import WWW_DIR

# Importacion de modulos UI y Server
from modules.mod_loader import loader_ui, loader_server
from modules.mod_summary import summary_ui, summary_server
from modules.mod_table import table_ui, table_server
from modules.mod_distributions import distributions_ui, distributions_server
from modules.mod_correlations import correlations_ui, correlations_server
from modules.mod_comparisons import comparisons_ui, comparisons_server
from modules.mod_timeseries import timeseries_ui, timeseries_server
from modules.mod_stats import stats_ui, stats_server

# -------------------------------------------------------------
# INTERFAZ DE USUARIO (UI ENSAMBLADA)
# -------------------------------------------------------------
app_ui = ui.page_sidebar(
    ui.sidebar(
        loader_ui("loader_mod"),
        width=320,
        bg="#f8fafc"
    ),
    ui.tags.head(
        ui.tags.link(rel="stylesheet", type="text/css", href="styles.css")
    ),
    ui.div(
        ui.h1(
            "EDA Colombia Open Data",
            ui.span("datos.gov.co", class_="badge-tag")
        ),
        ui.p("Analisis Exploratorio de Datos con arquitectura desacoplada para la API Socrata"),
        class_="app-header"
    ),
    ui.navset_tab(
        ui.nav_panel("Resumen", summary_ui("summary_mod")),
        ui.nav_panel("Datos", table_ui("table_mod")),
        ui.nav_panel("Distribuciones", distributions_ui("dist_mod")),
        ui.nav_panel("Correlaciones", correlations_ui("corr_mod")),
        ui.nav_panel("Comparaciones", comparisons_ui("comp_mod")),
        ui.nav_panel("Series de Tiempo", timeseries_ui("ts_mod")),
        ui.nav_panel("Estadisticas", stats_ui("stats_mod")),
        id="main_nav_tabs"
    ),
    title="EDA Datos Abiertos Colombia",
    fillable=True
)

# -------------------------------------------------------------
# CONTROLADOR (SERVER ENSAMBLADO)
# -------------------------------------------------------------
def server(input, output, session):
    df_react, meta_react = loader_server("loader_mod")

    summary_server("summary_mod", df_react=df_react, meta_react=meta_react)
    table_server("table_mod", df_react=df_react)
    distributions_server("dist_mod", df_react=df_react)
    correlations_server("corr_mod", df_react=df_react)
    comparisons_server("comp_mod", df_react=df_react)
    timeseries_server("ts_mod", df_react=df_react)
    stats_server("stats_mod", df_react=df_react)


app = App(app_ui, server, static_assets=WWW_DIR)

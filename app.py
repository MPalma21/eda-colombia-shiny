"""Punto de entrada de la aplicacion Shiny EDA Colombia.

Disenado siguiendo la guia oficial de Posit 'UI & UX Best Practices':
- Navegacion superior limpia con identidad de marca (page_navbar)
- Titulo oficial: Analisis Exploratorio en Datos Abiertos
- Subtitulo descriptivo de plataforma
- Barra lateral retractil con controles de consulta (sidebar)
- Tarjetas con jerarquia visual limpia y soporte de pantalla completa (full_screen=True)
- Footer discreto al pie de pagina (autor y enlaces concentrados exclusivamente aqui)
- Flujo de documento normal (fillable=False) para evitar solapamientos entre tarjetas y footer
- Componentes desacoplados en modulos y servicios
"""
from pathlib import Path
from shiny import App, ui
from config import WWW_DIR

# Modulos analiticos
from modules.mod_loader import loader_ui, loader_server
from modules.mod_summary import summary_ui, summary_server
from modules.mod_table import table_ui, table_server
from modules.mod_distributions import distributions_ui, distributions_server
from modules.mod_correlations import correlations_ui, correlations_server
from modules.mod_comparisons import comparisons_ui, comparisons_server
from modules.mod_timeseries import timeseries_ui, timeseries_server
from modules.mod_stats import stats_ui, stats_server

# Componentes de interfaz
from components.footer import render_app_footer

# -------------------------------------------------------------
# INTERFAZ DE USUARIO (UI ENSAMBLADA)
# -------------------------------------------------------------
app_ui = ui.page_navbar(
    # Destinos principales de navegacion (argumentos posicionales)
    ui.nav_panel("Resumen", summary_ui("summary_mod")),
    ui.nav_panel("Datos", table_ui("table_mod")),
    ui.nav_panel("Distribuciones", distributions_ui("dist_mod")),
    ui.nav_panel("Correlaciones", correlations_ui("corr_mod")),
    ui.nav_panel("Comparaciones", comparisons_ui("comp_mod")),
    ui.nav_panel("Series de Tiempo", timeseries_ui("ts_mod")),
    ui.nav_panel("Estadisticas", stats_ui("stats_mod")),
    
    # Identidad de marca, titulo y subtitulo en el navbar
    title=ui.div(
        ui.tags.img(src="logo.svg", alt="Logo EDA Colombia", height="30px", class_="me-2 flex-shrink-0"),
        ui.div(
            ui.div("Analisis Exploratorio en Datos Abiertos", class_="navbar-app-title"),
            ui.div(ui.HTML("Plataforma analitica interactiva &bull; datos.gov.co"), class_="navbar-app-subtitle"),
            class_="d-flex flex-column justify-content-center"
        ),
        class_="d-flex align-items-center py-1"
    ),
    
    # Panel lateral global para fuentes y seleccion de datos
    sidebar=ui.sidebar(
        loader_ui("loader_mod"),
        width=310,
        bg="#f8fafc",
        open="desktop"
    ),
    
    header=ui.tags.head(
        ui.tags.link(rel="stylesheet", type="text/css", href="styles.css")
    ),
    footer=render_app_footer(),
    fillable=False,
    id="main_navbar"
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

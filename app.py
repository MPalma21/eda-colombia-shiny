"""Punto de entrada de la aplicacion Shiny EDA Colombia.

Disenado siguiendo la guia oficial de Posit 'UI & UX Best Practices':
- Navegacion superior con identidad de marca (page_navbar)
- Titulo oficial: Analisis Exploratorio en Datos Abiertos
- Subtitulo descriptivo de plataforma
- Enlaces de autor y presencia digital (LinkedIn: miguelangelpr, GitHub: MPalma21)
- Barra lateral retractil con controles agrupados (sidebar)
- Tarjetas con jerarquia visual limpia y soporte de pantalla completa (full_screen=True)
- Footer discreto con metadatos tecnicos y enlaces
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

# Constantes SVG
SVG_NAV_LINKEDIN = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="13" height="13" fill="currentColor" class="me-1"><path d="M19 0h-14c-2.761 0-5 2.239-5 5v14c0 2.761 2.239 5 5 5h14c2.762 0 5-2.239 5-5v-14c0-2.761-2.238-5-5-5zm-11 19h-3v-11h3v11zm-1.5-12.268c-.966 0-1.75-.79-1.75-1.764s.784-1.764 1.75-1.764 1.75.79 1.75 1.764-.783 1.764-1.75 1.764zm13.5 12.268h-3v-5.604c0-3.368-4-3.113-4 0v5.604h-3v-11h3v1.765c1.396-2.586 7-2.777 7 2.476v6.759z"/></svg>"""
SVG_NAV_GITHUB = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="13" height="13" fill="currentColor" class="me-1"><path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/></svg>"""

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
    
    # Espaciador para alinear acciones de usuario a la derecha del navbar
    ui.nav_spacer(),
    
    # Enlaces de autor en el navbar superior
    ui.nav_control(
        ui.tags.a(
            ui.HTML(SVG_NAV_LINKEDIN),
            "LinkedIn",
            href="https://www.linkedin.com/in/miguelangelpr",
            target="_blank",
            rel="noopener noreferrer",
            class_="btn btn-sm btn-navbar-link me-2"
        )
    ),
    ui.nav_control(
        ui.tags.a(
            ui.HTML(SVG_NAV_GITHUB),
            "GitHub",
            href="https://github.com/MPalma21",
            target="_blank",
            rel="noopener noreferrer",
            class_="btn btn-sm btn-navbar-link"
        )
    ),
    
    # Identidad de marca, titulo y subtitulo en el navbar
    title=ui.div(
        ui.tags.img(src="logo.svg", alt="Logo EDA Colombia", height="30px", class_="me-2 flex-shrink-0"),
        ui.div(
            ui.div("Analisis Exploratorio en Datos Abiertos", class_="navbar-app-title"),
            ui.div("Plataforma analitica interactiva · datos.gov.co", class_="navbar-app-subtitle"),
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
    fillable=True,
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

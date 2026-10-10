"""Punto de entrada de la aplicacion Shiny EDA Colombia.

Disenado siguiendo la guia oficial de Posit 'UI & UX Best Practices':
- Navegacion superior limpia con identidad de marca (page_navbar)
- Titulo oficial: Analisis Exploratorio en Datos Abiertos
- Subtitulo descriptivo de plataforma
- Barra lateral retractil con controles de consulta (sidebar)
- Tarjetas con jerarquia visual limpia y soporte de pantalla completa (full_screen=True)
- Creditos y enlaces en la barra superior; banner contextual para el recurso
- Flujo de documento normal (fillable=False) para evitar solapamientos entre tarjetas
- Componentes desacoplados en modulos y servicios
"""
from pathlib import Path
from shiny import App, ui, render
from config import WWW_DIR

# Modulos analiticos
from modules.mod_loader import loader_ui, loader_server
from modules.mod_summary import summary_ui, summary_server
from modules.mod_inequality import inequality_ui, inequality_server
from modules.mod_econometrics import econometrics_ui, econometrics_server
from modules.mod_comparisons import comparisons_ui, comparisons_server
from modules.mod_timeseries import timeseries_ui, timeseries_server
from modules.mod_distributions import distributions_ui, distributions_server
from modules.mod_correlations import correlations_ui, correlations_server
from modules.mod_table import table_ui, table_server

# Componentes de interfaz
from components.banner import render_context_banner

# -------------------------------------------------------------
# INTERFAZ DE USUARIO (UI ENSAMBLADA)
# -------------------------------------------------------------
app_ui = ui.page_navbar(
    # Destinos principales de navegacion orientados a analisis economico
    ui.nav_panel("Panorama", summary_ui("summary_mod")),
    ui.nav_panel("Desigualdad & Concentracion", inequality_ui("inequality_mod")),
    ui.nav_panel("Econometria & Elasticidades", econometrics_ui("econ_mod")),
    ui.nav_panel("Brechas & Territorio", comparisons_ui("comp_mod")),
    ui.nav_panel("Series & Precios", timeseries_ui("ts_mod")),
    ui.nav_panel("Distribuciones", distributions_ui("dist_mod")),
    ui.nav_panel("Correlaciones", correlations_ui("corr_mod")),
    ui.nav_panel("Datos", table_ui("table_mod")),
    
    # Identidad de marca, titulo y subtitulo en el navbar
    title=ui.div(
        ui.div(
            ui.tags.img(src="logo.svg", alt="Logo EDA Colombia", class_="navbar-logo flex-shrink-0"),
            ui.div(
                ui.div("Analisis Exploratorio & Economico en Datos Abiertos", class_="navbar-app-title"),
                ui.div(ui.HTML("Observatorio de Inteligencia Economica &bull; datos.gov.co"), class_="navbar-app-subtitle"),
                ui.div(
                    ui.span("Desarrollado por Miguelangel Palma", class_="navbar-author-name"),
                    ui.tags.a("LinkedIn", href="https://www.linkedin.com/in/miguelangelpr", target="_blank", rel="noopener noreferrer"),
                    ui.tags.a("GitHub", href="https://github.com/MPalma21", target="_blank", rel="noopener noreferrer"),
                    ui.tags.a("Posit Connect", href="https://connect.posit.cloud", target="_blank", rel="noopener noreferrer"),
                    class_="navbar-credits",
                ),
                class_="navbar-brand-copy d-flex flex-column justify-content-center"
            ),
            class_="navbar-brand-content d-flex align-items-center"
        ),
        ui.output_ui("global_context_banner"),
        class_="navbar-brand-stack",
    ),
    
    # Panel lateral global para fuentes y seleccion de datos
    sidebar=ui.sidebar(
        loader_ui("loader_mod"),
        width=310,
        bg="#eef3ed",
        open="desktop"
    ),
    
    header=ui.tags.head(ui.tags.link(rel="stylesheet", type="text/css", href="styles.css")),
    fillable=False,
    id="main_navbar"
)

# -------------------------------------------------------------
# CONTROLADOR (SERVER ENSAMBLADO)
# -------------------------------------------------------------
def server(input, output, session):
    df_react, meta_react = loader_server("loader_mod")

    @output
    @render.ui
    def global_context_banner():
        return render_context_banner(df_react(), meta_react())

    summary_server("summary_mod", df_react=df_react, meta_react=meta_react)
    inequality_server("inequality_mod", df_react=df_react)
    econometrics_server("econ_mod", df_react=df_react)
    comparisons_server("comp_mod", df_react=df_react)
    timeseries_server("ts_mod", df_react=df_react)
    distributions_server("dist_mod", df_react=df_react)
    correlations_server("corr_mod", df_react=df_react)
    table_server("table_mod", df_react=df_react)


app = App(app_ui, server, static_assets=WWW_DIR)

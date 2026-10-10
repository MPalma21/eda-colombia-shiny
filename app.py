"""Punto de entrada: Panel de Alertas y Semaforos de Riesgo Territorial.

Observatorio especializado en Contratacion Publica (SECOP II):
- Radar y Semaforos Territoriales: Alertas interdepartamentales, HHI y contratacion directa.
- Auditoria Departamental a Profundidad: Drill-down, contratistas locales, modalidades y diagnostico.
- Concentracion Empresarial & Contratistas Dominantes: Poder de mercado, CR4 y asignacion a dedo.
- Simulador de Politica Economica: Modelo contrafactual de desconcentracion y ahorro fiscal.
- Matriz de Evidencia & Microdatos: Auditoria detallada, flags de riesgo contractual y exportacion CSV.

Desarrollado por Miguelangel Palma siguiendo las guias oficiales de Posit y diseno corporativo.
"""
from pathlib import Path
from shiny import App, ui, render
from config import WWW_DIR

# Modulo de carga de datos SODA / SECOP
from modules.mod_loader import loader_ui, loader_server

# Modulos especializados del Panel de Riesgo Territorial
from modules.mod_risk_radar import risk_radar_ui, risk_radar_server
from modules.mod_risk_drilldown import risk_drilldown_ui, risk_drilldown_server
from modules.mod_risk_contractors import risk_contractors_ui, risk_contractors_server
from modules.mod_simulator import simulator_ui, simulator_server
from modules.mod_risk_evidence import risk_evidence_ui, risk_evidence_server

# Componentes de interfaz
from components.banner import render_context_banner

# -------------------------------------------------------------
# INTERFAZ DE USUARIO (PANEL DE RIESGO TERRITORIAL)
# -------------------------------------------------------------
app_ui = ui.page_navbar(
    # Las 5 perspectivas especializadas del Observatorio de Riesgo
    ui.nav_panel("Radar de Alertas", risk_radar_ui("risk_radar_mod")),
    ui.nav_panel("Auditoría Departamental", risk_drilldown_ui("risk_drill_mod")),
    ui.nav_panel("Contratistas Dominantes", risk_contractors_ui("risk_contractors_mod")),
    ui.nav_panel("Simulador de Reforma", simulator_ui("sim_mod")),
    ui.nav_panel("Matriz & Microdatos", risk_evidence_ui("risk_evidence_mod")),
    
    # Identidad de marca, titulo y subtitulo en el navbar
    title=ui.div(
        ui.div(
            ui.tags.img(src="logo.svg", alt="Logo Riesgo Territorial", class_="navbar-logo flex-shrink-0"),
            ui.div(
                ui.div("Panel de Alertas y Semáforos de Riesgo Territorial", class_="navbar-app-title"),
                ui.div(ui.HTML("Observatorio de Contratación Pública & Competencia &bull; SECOP II &bull; datos.gov.co"), class_="navbar-app-subtitle"),
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
        bg="#f0f4fa",
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

    # Servidores de los 5 modulos de riesgo territorial
    risk_radar_server("risk_radar_mod", df_react=df_react)
    risk_drilldown_server("risk_drill_mod", df_react=df_react)
    risk_contractors_server("risk_contractors_mod", df_react=df_react)
    simulator_server("sim_mod", df_react=df_react)
    risk_evidence_server("risk_evidence_mod", df_react=df_react)


app = App(app_ui, server, static_assets=WWW_DIR)


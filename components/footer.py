"""Componente de pie de pagina (Footer) discreto y profesional.

Sigue las directrices de la guia oficial de UI:
- Version y fecha de actualizacion.
- Enlaces y perfiles profesionales del autor (LinkedIn, GitHub, Posit Connect Cloud).
- Estilo discreto sin invadir el area de analisis.
"""
from shiny import ui

SVG_LINKEDIN = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="13" height="13" fill="currentColor" class="me-1"><path d="M19 0h-14c-2.761 0-5 2.239-5 5v14c0 2.761 2.239 5 5 5h14c2.762 0 5-2.239 5-5v-14c0-2.761-2.238-5-5-5zm-11 19h-3v-11h3v11zm-1.5-12.268c-.966 0-1.75-.79-1.75-1.764s.784-1.764 1.75-1.764 1.75.79 1.75 1.764-.783 1.764-1.75 1.764zm13.5 12.268h-3v-5.604c0-3.368-4-3.113-4 0v5.604h-3v-11h3v1.765c1.396-2.586 7-2.777 7 2.476v6.759z"/></svg>"""

SVG_GITHUB = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="13" height="13" fill="currentColor" class="me-1"><path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/></svg>"""

SVG_POSIT = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="13" height="13" fill="none" stroke="currentColor" stroke-width="2" class="me-1"><circle cx="12" cy="12" r="10"/><path d="M8 12h8M12 8v8"/></svg>"""


def render_app_footer() -> ui.Tag:
    """Retorna un footer limpio y sobrio con los perfiles del autor y metadatos de la app."""
    return ui.tags.footer(
        ui.div(
            # Seccion izquierda: Creditos con espaciado correcto y nombre Miguelangel
            ui.div(
                ui.span("Analisis Exploratorio en Datos Abiertos", class_="fw-semibold text-slate-800 me-2"),
                ui.span("·", class_="text-slate-400 me-2"),
                ui.span("Desarrollado por ", class_="text-slate-500 me-1"),
                ui.span("Miguelangel Palma", class_="fw-semibold text-slate-700"),
                class_="footer-left d-flex align-items-center flex-wrap mb-2 mb-lg-0"
            ),
            
            # Seccion central: Badges discretos
            ui.div(
                ui.span("Python 3.11", class_="footer-badge me-2"),
                ui.span("Shiny for Python", class_="footer-badge me-2"),
                ui.span("datos.gov.co", class_="footer-badge me-2"),
                ui.span("Posit Connect Cloud", class_="footer-badge"),
                class_="footer-center d-flex align-items-center flex-wrap mb-2 mb-lg-0"
            ),
            
            # Seccion derecha: Enlaces directos a perfiles
            ui.div(
                ui.tags.a(
                    ui.HTML(SVG_LINKEDIN),
                    "miguelangelpr",
                    href="https://www.linkedin.com/in/miguelangelpr",
                    target="_blank",
                    rel="noopener noreferrer",
                    class_="footer-link me-3"
                ),
                ui.tags.a(
                    ui.HTML(SVG_GITHUB),
                    "MPalma21",
                    href="https://github.com/MPalma21",
                    target="_blank",
                    rel="noopener noreferrer",
                    class_="footer-link me-3"
                ),
                ui.tags.a(
                    ui.HTML(SVG_POSIT),
                    "Posit Connect Cloud",
                    href="https://connect.posit.cloud",
                    target="_blank",
                    rel="noopener noreferrer",
                    class_="footer-link"
                ),
                class_="footer-right d-flex align-items-center flex-wrap"
            ),
            class_="footer-container d-flex justify-content-between align-items-center flex-wrap py-2 px-3"
        ),
        class_="app-footer border-top mt-auto"
    )

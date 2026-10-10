"""Modal explicativo e institucional con la Guia Metodologica y Marco Normativo.

Disenado para orientar a veedores, investigadores, economistas y servidores publicos.
Zero emojis, tipografia institucional y referencias formales.
"""
from shiny import ui


def show_methodology_modal():
    """Despliega un modal interactivo con la metodologia, formulas y marco normativo."""
    modal = ui.modal(
        ui.div(
            # Seccion 1: Proposito y Enfoque
            ui.div(
                ui.h6("1. Objeto y Alcance del Observatorio", class_="fw-bold text-primary mb-2 text-uppercase", style="font-size: 0.85rem; letter-spacing: 0.05em;"),
                ui.p(
                    "Este panel tiene como objetivo transformar los microdatos oficiales de contratacion del Estado colombiano "
                    "(SECOP II / datos.gov.co) en indicadores objetivos de economia industrial y control fiscal. Permite identificar "
                    "territorios con alta vulnerabilidad a sobrecostos, direccionamiento contractual y practicas restrictivas de la competencia.",
                    class_="small text-secondary mb-3"
                ),
                class_="guide-callout mb-3"
            ),

            # Seccion 2: Criterios Metodologicos y Formulas
            ui.div(
                ui.h6("2. Criterios de Semaforizacion y Metodologia Economica", class_="fw-bold text-primary mb-2 text-uppercase", style="font-size: 0.85rem; letter-spacing: 0.05em;"),
                ui.div(
                    ui.div(
                        ui.div(
                            ui.span("Indice Herfindahl-Hirschman (HHI)", class_="fw-bold text-dark small"),
                            ui.p(
                                "Mide la concentracion del mercado sumando los cuadrados de las cuotas de cada oferente (HHI = Sum s_i^2). "
                                "Rango de 0 a 10,000. Umbrales DOJ/OCDE: Menor a 1,500 indica mercado competitivo; 1,500 a 2,500 concentracion moderada; "
                                "mayor a 2,500 alerta critica de estructura oligopolica o colusion.",
                                class_="small text-muted mb-0"
                            ),
                            class_="p-2 bg-light rounded border border-subtle mb-2"
                        ),
                        ui.div(
                            ui.span("Tasa de Contratacion Directa (%)", class_="fw-bold text-dark small"),
                            ui.p(
                                "Proporcion del presupuesto adjudicado sin concurso abierto ni puja publica. "
                                "La Ley 80 de 1993 exige la licitacion como regla general; tasas superiores al 65% representan "
                                "alerta critica por posible evasion de mecanismos competitivos.",
                                class_="small text-muted mb-0"
                            ),
                            class_="p-2 bg-light rounded border border-subtle mb-2"
                        ),
                        ui.div(
                            ui.span("Score Sintetico de Riesgo Territorial (0 a 100)", class_="fw-bold text-dark small"),
                            ui.p(
                                "Ponderacion estandarizada: Score = 0.55 * (% Directa) + 0.45 * (HHI / 100). "
                                "Permite ranquear jurisdicciones con base en su exposicion simultanea a discrecionalidad y concentracion.",
                                class_="small text-muted mb-0"
                            ),
                            class_="p-2 bg-light rounded border border-subtle mb-2"
                        ),
                        ui.div(
                            ui.span("Ratio de Concentracion CR4", class_="fw-bold text-dark small"),
                            ui.p(
                                "Participacion conjunta de los 4 mayores contratistas de la jurisdiccion. "
                                "Si el CR4 supera el 50%, el mercado territorial se encuentra dominado por un grupo reducido de actores.",
                                class_="small text-muted mb-0"
                            ),
                            class_="p-2 bg-light rounded border border-subtle"
                        ),
                    ),
                    class_="mb-3"
                )
            ),

            # Seccion 3: Marco Normativo Colombiano
            ui.div(
                ui.h6("3. Marco Juridico y Directrices de Control", class_="fw-bold text-primary mb-2 text-uppercase", style="font-size: 0.85rem; letter-spacing: 0.05em;"),
                ui.tags.ul(
                    ui.tags.li(
                        ui.tags.b("Ley 80 de 1993 (Estatuto General de Contratacion): "),
                        "Establece los principios de transparencia, economia y responsabilidad, consagrando la licitacion publica como via ordinaria de seleccion.",
                        class_="mb-1 small text-secondary"
                    ),
                    ui.tags.li(
                        ui.tags.b("Ley 1150 de 2007 (Eficiencia y Transparencia): "),
                        "Define modalidades de seleccion objetiva (licitacion, seleccion abreviada, concurso de meritos y minima cuantia) y restringe la contratacion directa.",
                        class_="mb-1 small text-secondary"
                    ),
                    ui.tags.li(
                        ui.tags.b("Ley 2014 de 2019 (Pliegos Tipo Obligatorios): "),
                        "Mecanismo anticorrupcion que estandariza requisitos habilitantes para evitar 'pliegos sastre' direccionados a proponentes unicos.",
                        class_="mb-1 small text-secondary"
                    ),
                    ui.tags.li(
                        ui.tags.b("Colombia Compra Eficiente (CCE): "),
                        "Agencia rectora encargada de fijar lineamientos de libre competencia y prevencion de colusion en compras publicas.",
                        class_="small text-secondary"
                    ),
                    class_="ps-3 mb-3"
                )
            ),

            # Seccion 4: Ruta de Auditoria en 5 Pasos
            ui.div(
                ui.h6("4. Ruta de Auditoria Recomendada para el Usuario", class_="fw-bold text-primary mb-2 text-uppercase", style="font-size: 0.85rem; letter-spacing: 0.05em;"),
                ui.div(
                    ui.div(
                        ui.span("Paso 1 · Radar de Alertas: ", class_="fw-bold text-dark"),
                        "Identifique los departamentos ubicados en el cuadrante critico (rojo).",
                        class_="small p-2 bg-white rounded border border-subtle mb-1"
                    ),
                    ui.div(
                        ui.span("Paso 2 · Auditoria Departamental: ", class_="fw-bold text-dark"),
                        "Consulte el expediente territorial, los contratos atipicos y el dictamen automatico.",
                        class_="small p-2 bg-white rounded border border-subtle mb-1"
                    ),
                    ui.div(
                        ui.span("Paso 3 · Contratistas Dominantes: ", class_="fw-bold text-dark"),
                        "Detecte que empresas concentran el gasto publico y su porcentaje a dedo.",
                        class_="small p-2 bg-white rounded border border-subtle mb-1"
                    ),
                    ui.div(
                        ui.span("Paso 4 · Simulador de Reforma: ", class_="fw-bold text-dark"),
                        "Cuantifique el ahorro fiscal y la desconcentracion al sustituir asignaciones directas por pliegos tipo.",
                        class_="small p-2 bg-white rounded border border-subtle mb-1"
                    ),
                    ui.div(
                        ui.span("Paso 5 · Matriz & Microdatos: ", class_="fw-bold text-dark"),
                        "Descargue el archivo CSV con banderas de alerta para sustentar informes de veeduria o denuncias.",
                        class_="small p-2 bg-white rounded border border-subtle"
                    ),
                ),
                class_="p-3 bg-light rounded border border-subtle mb-2"
            ),
            class_="modal-guide-body"
        ),
        title=ui.div(
            ui.span("Guia Metodologica, Criterios Regulatorios y Marco Legal", class_="fw-bold text-primary"),
            class_="d-flex align-items-center"
        ),
        size="l",
        easy_close=True,
        footer=ui.modal_button("Entendido y Cerrar")
    )
    ui.modal_show(modal)

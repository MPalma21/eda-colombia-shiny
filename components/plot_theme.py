"""Estilo y plantilla visual unificada en tonalidades de azules para Plotly.

Implementa una estetica monocromatica y analoga en gama de azules inspirada en
la marca corporativa (Royal Cobalt & Midnight Navy) y la Gramatica de Graficos (ggplot2):
- Fondo de trazado suave (#f8fafc) con cuadricula tenue (#e2e8f0).
- Tipografia limpia (sans-serif), jerarquia de titulos y subtitulos alineados a la izquierda.
- Ejes limpios con marcas exteriores y etiquetas legibles.
- Diseno sin solapamiento: leyendas horizontales inferiores y verticales exteriores.
- Sin modebar invasivo (displayModeBar=False para eliminar iconos flotantes sobre titulos).
- Escala tonal de azules para diferenciar categorias, intensidades de riesgo y proyecciones.
"""
from typing import Any
import plotly.graph_objects as go

GGPLOT2_FONT_FAMILY = "system-ui, -apple-system, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif"

# Base Institucional (Azul Cobalto y Midnight Navy de la Marca)
BLUE_MIDNIGHT = "#080c42"   # Azul Marino Profundo / Midnight Navbar
BLUE_NAVY = "#0f172a"       # Azul Tinta Oscuro
BLUE_COBALT = "#1d3190"     # Azul Cobalto Institucional (Marca Miguelangel Palma)
BLUE_SAPPHIRE = "#1e40af"   # Azul Zafiro / Royal
BLUE_ELECTRIC = "#2563eb"   # Azul Electrico Intenso
BLUE_AZURE = "#3b82f6"      # Azul Real Brillante
BLUE_SKY = "#0284c7"        # Azul Cielo
BLUE_ICE = "#93c5fd"        # Azul Hielo Suave
BLUE_MIST = "#bfdbfe"       # Azul Claro Niebla
BLUE_GHOST = "#eff6ff"      # Azul Superficie Tenue

# Semaforo Clasico Ejecutivo (Rojo Carmesi, Ambar Calido, Verde Esmeralda)
SEMAPHORE_RED = "#dc2626"      # Alto Riesgo / Critico / Asignacion Directa
SEMAPHORE_AMBER = "#d97706"    # Riesgo Moderado / Alerta Mixta
SEMAPHORE_GREEN = "#059669"    # Bajo Riesgo / Competitivo / Licitacion Abierta

# Constantes semanticas de color
THEME_PRIMARY = BLUE_COBALT
THEME_CRITICAL = SEMAPHORE_RED
THEME_MODERATE = SEMAPHORE_AMBER
THEME_COMPETITIVE = SEMAPHORE_GREEN
THEME_SECONDARY_BLUE = BLUE_AZURE
THEME_NAVY = BLUE_MIDNIGHT
THEME_SLATE = "#64748b"

# Paleta discreta categorica
GGPLOT2_PALETTE = [
    THEME_PRIMARY,        # #1d3190 (Azul Cobalto)
    THEME_CRITICAL,       # #dc2626 (Rojo Carmesi)
    THEME_COMPETITIVE,    # #059669 (Verde Esmeralda)
    THEME_MODERATE,       # #d97706 (Ambar Calido)
    BLUE_SKY,             # #0284c7 (Azul Cielo)
    "#7c3aed",            # Purpura
    BLUE_MIDNIGHT         # #080c42 (Midnight)
]

# Mapa de semaforo de riesgo oficial
GGPLOT_SEMAPHORE = {
    "Alto Riesgo (Crítico)": THEME_CRITICAL,
    "Riesgo Moderado": THEME_MODERATE,
    "Bajo Riesgo (Competitivo)": THEME_COMPETITIVE,
    "Predominio Directo (Sin Concurso)": THEME_CRITICAL,
    "Mixto / Moderado": THEME_MODERATE,
    "Concurso Competitivo": THEME_COMPETITIVE
}


def get_modality_color(modality_name: str) -> str:
    """Asigna un color semantico intuitivo segun la modalidad de contratacion."""
    m = str(modality_name).lower()
    if any(k in m for k in ("direct", "urgencia", "especial", "sin concurso")):
        return THEME_CRITICAL       # Asignacion a dedo / sin concurso: rojo carmesi
    if any(k in m for k in ("licitac", "concurso", "abierto")):
        return THEME_COMPETITIVE    # Concurso publico abierto: verde esmeralda
    if any(k in m for k in ("abreviad", "subasta")):
        return THEME_PRIMARY        # Seleccion abreviada: azul cobalto institucional
    if any(k in m for k in ("minima", "mínima")):
        return BLUE_SKY             # Minima cuantia: azul cielo
    return THEME_MODERATE           # Otros regimenes: ambar calido


def apply_ggplot2_theme(
    fig: go.Figure,
    title: str | None = None,
    subtitle: str | None = None,
    xaxis_title: str | None = None,
    yaxis_title: str | None = None,
    height: int = 360,
    margin: dict[str, int] | None = None,
    show_legend: bool = False,
    legend_orientation: str = "h",
    x_grid: bool = True,
    y_grid: bool = True,
) -> go.Figure:
    """Aplica el tema visual de ggplot2 (Grammar of Graphics) en gama de azules sin solapamientos."""
    top_margin = 72 if subtitle else (55 if title else 25)
    bottom_margin = 75 if (show_legend and legend_orientation == "h") else (50 if xaxis_title else 30)

    default_margin = dict(
        t=top_margin,
        b=bottom_margin,
        l=55 if yaxis_title else 40,
        r=30
    )
    final_margin = {**default_margin, **(margin or {})}

    title_text = ""
    if title:
        if subtitle:
            title_text = f"<b>{title}</b><br><span style='font-size:11px; font-weight:normal; color:#475569;'>{subtitle}</span>"
        else:
            title_text = f"<b>{title}</b>"

    layout_updates: dict[str, Any] = {
        "font": dict(family=GGPLOT2_FONT_FAMILY, size=11, color="#1e293b"),
        "plot_bgcolor": "#f8fafc",
        "paper_bgcolor": "#ffffff",
        "height": height,
        "margin": final_margin,
        "hoverlabel": dict(
            bgcolor="#ffffff",
            bordercolor="#93c5fd",
            font_size=11.5,
            font_family=GGPLOT2_FONT_FAMILY,
            font_color="#080c42"
        )
    }

    if title_text:
        layout_updates["title"] = dict(
            text=title_text,
            x=0.0,
            xanchor="left",
            y=0.97,
            yanchor="top",
            font=dict(size=13, color="#080c42"),
            pad=dict(b=8)
        )

    if show_legend:
        if legend_orientation == "h":
            layout_updates["legend"] = dict(
                orientation="h",
                yanchor="top",
                y=-0.22,
                xanchor="center",
                x=0.5,
                bgcolor="rgba(255, 255, 255, 0.95)",
                bordercolor="#bfdbfe",
                borderwidth=1,
                font=dict(size=10.5, color="#1e293b")
            )
        else:
            layout_updates["legend"] = dict(
                orientation="v",
                yanchor="middle",
                y=0.5,
                xanchor="left",
                x=1.02,
                bgcolor="rgba(255, 255, 255, 0.95)",
                bordercolor="#bfdbfe",
                borderwidth=1,
                font=dict(size=10.5, color="#1e293b")
            )
    else:
        layout_updates["showlegend"] = False

    fig.update_layout(**layout_updates)

    # Eje X estilo ggplot2: borde suave, marcas exteriores y cuadricula
    x_axes_kwargs: dict[str, Any] = {
        "showline": True,
        "linewidth": 1,
        "linecolor": "#cbd5e1",
        "ticks": "outside",
        "ticklen": 4,
        "tickcolor": "#cbd5e1",
        "showgrid": x_grid,
        "gridcolor": "#e2e8f0" if x_grid else "rgba(0,0,0,0)",
        "gridwidth": 1
    }
    if xaxis_title:
        x_axes_kwargs["title"] = dict(text=xaxis_title, font=dict(size=11, color="#334155"))
    fig.update_xaxes(**x_axes_kwargs)

    # Eje Y estilo ggplot2: borde suave, marcas exteriores y cuadricula
    y_axes_kwargs: dict[str, Any] = {
        "showline": True,
        "linewidth": 1,
        "linecolor": "#cbd5e1",
        "ticks": "outside",
        "ticklen": 4,
        "tickcolor": "#cbd5e1",
        "showgrid": y_grid,
        "gridcolor": "#e2e8f0" if y_grid else "rgba(0,0,0,0)",
        "gridwidth": 1
    }
    if yaxis_title:
        y_axes_kwargs["title"] = dict(text=yaxis_title, font=dict(size=11, color="#334155"))
    fig.update_yaxes(**y_axes_kwargs)

    return fig


def to_ggplot2_html(fig: go.Figure) -> str:
    """Serializa la figura a HTML sin dependencias JS redundantes y sin modebar que cause solapamiento."""
    return fig.to_html(
        include_plotlyjs=False,
        full_html=False,
        config={
            "displayModeBar": False,
            "responsive": True
        }
    )

"""Estilo y plantilla visual unificada inspirada en ggplot2 (Grammar of Graphics) para Plotly.

Proporciona funciones para homologar la estetica visual de R (ggplot2 / theme_minimal / theme_bw):
- Area de trazado con fondo suave y cuadricula tenue (#e2e8f0).
- Tipografia limpia (sans-serif), jerarquia de titulos y subtitulos alineados a la izquierda.
- Ejes limpios con marcas exteriores y etiquetas legibles.
- Diseno sin solapamiento: leyendas horizontales inferiores y verticales exteriores.
- Sin modebar invasivo (displayModeBar=False para eliminar iconos flotantes sobre titulos).
- Paleta semantica coordinada e integrada en toda la aplicacion.
"""
from typing import Any
import plotly.graph_objects as go

GGPLOT2_FONT_FAMILY = "system-ui, -apple-system, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif"

# Paleta unificada institucional y semantica de riesgo
THEME_PRIMARY = "#1d3190"        # Azul Cobalto institucional (marca Miguelangel Palma)
THEME_CRITICAL = "#dc2626"       # Rojo Carmesi (Riesgo Critico / Contratacion Directa)
THEME_MODERATE = "#d97706"       # Ambar (Riesgo Moderado / Procesos Mixtos)
THEME_COMPETITIVE = "#059669"    # Verde Esmeralda (Bajo Riesgo / Licitacion / Ahorro)
THEME_SECONDARY_BLUE = "#0284c7" # Celeste (Seleccion Abreviada / Minima Cuantia)
THEME_NAVY = "#080c42"           # Azul Marino profundo
THEME_SLATE = "#64748b"          # Gris Neutro

# Paleta discreta de categorias estilo ggplot2
GGPLOT2_PALETTE = [
    THEME_PRIMARY,
    THEME_CRITICAL,
    THEME_MODERATE,
    THEME_COMPETITIVE,
    THEME_SECONDARY_BLUE,
    THEME_SLATE,
    THEME_NAVY
]

# Mapa de semaforo de riesgo consistente en toda la aplicacion
GGPLOT_SEMAPHORE = {
    "Alto Riesgo (Crítico)": THEME_CRITICAL,
    "Riesgo Moderado": THEME_MODERATE,
    "Bajo Riesgo (Competitivo)": THEME_COMPETITIVE,
    "Predominio Directo (Sin Concurso)": THEME_CRITICAL,
    "Mixto / Moderado": THEME_MODERATE,
    "Concurso Competitivo": THEME_COMPETITIVE
}


def get_modality_color(modality_name: str) -> str:
    """Asigna un color semantico consistente segun el caracter de la modalidad."""
    m = str(modality_name).lower()
    if any(k in m for k in ("direct", "urgencia", "especial", "sin concurso")):
        return THEME_CRITICAL
    if any(k in m for k in ("licitac", "concurso", "abierto")):
        return THEME_COMPETITIVE
    if any(k in m for k in ("abreviad", "subasta")):
        return THEME_PRIMARY
    if any(k in m for k in ("minima", "mínima")):
        return THEME_SECONDARY_BLUE
    return THEME_MODERATE


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
    """Aplica el tema visual de ggplot2 (Grammar of Graphics) a una figura de Plotly sin solapamientos."""
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
            title_text = f"<b>{title}</b><br><span style='font-size:11px; font-weight:normal; color:#64748b;'>{subtitle}</span>"
        else:
            title_text = f"<b>{title}</b>"

    layout_updates: dict[str, Any] = {
        "font": dict(family=GGPLOT2_FONT_FAMILY, size=11, color="#334155"),
        "plot_bgcolor": "#f8fafc",
        "paper_bgcolor": "#ffffff",
        "height": height,
        "margin": final_margin,
        "hoverlabel": dict(
            bgcolor="#ffffff",
            bordercolor="#cbd5e1",
            font_size=11.5,
            font_family=GGPLOT2_FONT_FAMILY,
            font_color="#0f172a"
        )
    }

    if title_text:
        layout_updates["title"] = dict(
            text=title_text,
            x=0.0,
            xanchor="left",
            y=0.97,
            yanchor="top",
            font=dict(size=13, color="#0f172a"),
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
                bordercolor="#e2e8f0",
                borderwidth=1,
                font=dict(size=10.5)
            )
        else:
            layout_updates["legend"] = dict(
                orientation="v",
                yanchor="middle",
                y=0.5,
                xanchor="left",
                x=1.02,
                bgcolor="rgba(255, 255, 255, 0.95)",
                bordercolor="#e2e8f0",
                borderwidth=1,
                font=dict(size=10.5)
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
        x_axes_kwargs["title"] = dict(text=xaxis_title, font=dict(size=11, color="#475569"))
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
        y_axes_kwargs["title"] = dict(text=yaxis_title, font=dict(size=11, color="#475569"))
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

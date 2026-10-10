"""Estilo y plantilla visual inspirada en ggplot2 (Grammar of Graphics) para Plotly.

Proporciona funciones para homologar la estetica visual de R (ggplot2 / theme_minimal / theme_bw):
- Area de trazado con fondo suave y cuadricula tenue (#e2e8f0).
- Tipografia limpia (sans-serif), jerarquia de titulos y subtitulos alineados a la izquierda.
- Ejes limpios con marcas exteriores y etiquetas legibles.
- Tooltips interactivos con diseno minimalista en tarjetas blancas.
- Paleta semantica institucional alineada con la contratacion publica colombiana.
"""
from typing import Any
import plotly.graph_objects as go

GGPLOT2_FONT_FAMILY = "system-ui, -apple-system, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif"

# Paleta discreta de categorias estilo ggplot2 / Colour Lovers
GGPLOT2_PALETTE = [
    "#1d3190",  # Azul institucional primario
    "#dc2626",  # Coral / Carmesi alerta alta
    "#d97706",  # Ambar / Naranja riesgo moderado
    "#059669",  # Esmeralda / Verde competitivo
    "#0284c7",  # Cyan / Celeste
    "#64748b",  # Pizarra neutro
    "#8b5cf6",  # Violeta
    "#080c42",  # Azul marino profundo
]

# Mapa de semaforo de riesgo
GGPLOT_SEMAPHORE = {
    "Alto Riesgo (Crítico)": "#dc2626",
    "Riesgo Moderado": "#d97706",
    "Bajo Riesgo (Competitivo)": "#059669",
    "Predominio Directo (Sin Concurso)": "#dc2626",
    "Mixto / Moderado": "#d97706",
    "Concurso Competitivo": "#059669"
}


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
    """Aplica el tema visual de ggplot2 (Grammar of Graphics) a una figura de Plotly."""
    default_margin = dict(
        t=55 if title else 25,
        b=45 if xaxis_title else 30,
        l=55 if yaxis_title else 40,
        r=25
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
            y=0.98,
            yanchor="top",
            font=dict(size=13.5, color="#0f172a")
        )

    if show_legend:
        if legend_orientation == "h":
            layout_updates["legend"] = dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="left",
                x=0.0,
                bgcolor="rgba(255, 255, 255, 0.9)",
                bordercolor="#e2e8f0",
                borderwidth=1,
                font=dict(size=10.5)
            )
        else:
            layout_updates["legend"] = dict(
                orientation="v",
                yanchor="middle",
                y=0.5,
                bgcolor="rgba(255, 255, 255, 0.9)",
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

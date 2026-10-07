"""Comprobaciones de la cabecera y el banner contextual."""
import pandas as pd

from app import app_ui
from components.banner import render_context_banner


def test_navbar_contains_author_links_and_context_banner_does_not():
    navbar = str(app_ui)
    html = str(render_context_banner(pd.DataFrame(), {}))
    assert "Explora los datos abiertos de Colombia" in html
    assert "Miguelangel Palma" in navbar
    assert "https://github.com/MPalma21" in navbar
    assert "navbar-credits" in navbar
    assert "Miguelangel Palma" not in html
    assert "navbar-context" in html
    assert "context-banner" not in html


def test_active_banner_explains_loaded_scope():
    df = pd.DataFrame({"valor": [1, 2]})
    html = str(render_context_banner(df, {
        "name": "Serie de prueba", "_eda_total_rows": 20,
        "_eda_query": "Bogotá", "tableAuthor": {"displayName": "Entidad de prueba"},
    }))
    assert "Serie de prueba" in html
    assert "2 de 20 registros" in html
    assert "Filtro de origen: Bogotá" in html
    assert "Miguelangel Palma" not in html


def test_sample_banner_limits_claim_to_downloaded_rows():
    html = str(render_context_banner(pd.DataFrame({"valor": [1]}), {
        "_eda_total_rows": 1000,
        "_eda_loaded_rows": 100,
        "_eda_sample_active": True,
        "_eda_period_label": "fecha: 2024-01-01 a 2024-01-31",
    }))
    assert "100 filas descargadas" in html
    assert "solo entre las filas descargadas" in html
    assert "Período:" in html


def test_distributed_fetch_banner_explains_method():
    html = str(render_context_banner(pd.DataFrame({"valor": [1]}), {
        "_eda_total_rows": 100,
        "_eda_loaded_rows": 1,
        "_eda_fetch_mode": "spread",
    }))
    assert "bloques distribuidos por ID" in html
    assert "no es una muestra aleatoria simple" in html

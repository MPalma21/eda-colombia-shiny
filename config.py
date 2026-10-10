"""Configuracion global de la aplicacion EDA Colombia."""
from pathlib import Path

# Rutas del proyecto
BASE_DIR = Path(__file__).resolve().parent
WWW_DIR = BASE_DIR / "www"

# API datos.gov.co (Socrata)
BASE_API_URL = "https://www.datos.gov.co/resource/{resource_id}.json"
METADATA_API_URL = "https://www.datos.gov.co/api/views/{resource_id}.json"

DEFAULT_MAX_ROWS = 50_000
DEFAULT_FETCH_ROWS = 5_000
API_TIMEOUT_SECONDS = 30

# Colecciones tabulares verificadas para EDA: volumen alto y mezcla de medidas
# numericas con variables categoricas. El selector conserva la entrada manual.
SAMPLE_DATASETS = {
    "Selecciona un dataset de ejemplo...": "",
    "Saber 11 (ICFES) · Puntajes, departamentos y contexto socioeconomico": "rnvb-vnyh",
    "SECOP II · Contratos estatales, montos, modalidades y departamentos": "jbjy-vk9h",
    "SECOP II · Procesos de compra, precios y competencia": "p6dx-8zbt",
    "COVID-19 · Demografia y salud publica territorial": "gt2j-8ykr",
}

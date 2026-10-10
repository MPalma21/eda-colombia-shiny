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
DEFAULT_RESOURCE_ID = "jbjy-vk9h"

# Colecciones tabulares verificadas de contratacion publica (SECOP / datos.gov.co):
SAMPLE_DATASETS = {
    "SECOP II · Contratos Electrónicos, Montos y Departamentos (Recomendado)": "jbjy-vk9h",
    "SECOP II · Procesos de Compra, Licitaciones y Adjudicaciones": "p6dx-8zbt",
    "SECOP I · Contratos Estatales Históricos": "xvdy-7kqu",
    "Ingresar otro ID o URL personalizada de datos.gov.co...": "",
}


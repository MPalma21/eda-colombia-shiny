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

# Datasets mas famosos y consultados de datos.gov.co (100% activos y verificados)
SAMPLE_DATASETS = {
    "Selecciona un dataset de ejemplo...": "",
    "Tasa de Cambio Representativa del Mercado (TRM Historico)": "mcec-87by",
    "SECOP II - Contratos Electronicos del Estado": "jbjy-vk9h",
    "Casos Positivos de COVID-19 en Colombia": "gt2j-8ykr",
    "Codigo Unico de Medicamentos Vigentes (INVIMA)": "i7cb-raxc",
    "SECOP II - Procesos de Contratacion Publica": "p6dx-8zbt",
    "Puestos de Votacion y Censo Electoral (Registraduria)": "iuwx-frrw",
    "Beneficiarios Mas Familias en Accion": "xfif-myr2",
}

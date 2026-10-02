"""Servicio desacoplado para el consumo de datos abiertos de Colombia (datos.gov.co).

Funciones puras de Python sin dependencias de Shiny ni contexto reactivo.
"""
from typing import Any
import requests
import pandas as pd
from config import BASE_API_URL, METADATA_API_URL, API_TIMEOUT_SECONDS, DEFAULT_MAX_ROWS


def extract_resource_id(input_value: str) -> str:
    """Extrae el identificador del recurso Socrata (ej. 'gt2j-8ykr') de una URL o texto plano."""
    val = input_value.strip()
    if not val:
        return ""
    if val.startswith("http"):
        parts = val.rstrip("/").split("/")
        for part in reversed(parts):
            cleaned = part.replace(".json", "").replace(".csv", "")
            if len(cleaned) == 9 and cleaned[4] == "-":
                return cleaned
        return parts[-1].replace(".json", "")
    return val


def fetch_dataset(resource_id: str, limit: int = 5000) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Descarga registros y metadatos de datos.gov.co vía Socrata Open Data API.
    
    Returns:
        tuple[pd.DataFrame, dict]: DataFrame tipado e información de metadatos.
    """
    clean_id = extract_resource_id(resource_id)
    if not clean_id:
        raise ValueError("ID de recurso inválido o vacío.")

    row_limit = min(max(10, limit), DEFAULT_MAX_ROWS)
    data_url = BASE_API_URL.format(resource_id=clean_id)
    
    # 1. Descargar datos
    try:
        resp = requests.get(
            data_url,
            params={"$limit": row_limit, "$offset": 0},
            timeout=API_TIMEOUT_SECONDS
        )
        resp.raise_for_status()
    except requests.exceptions.HTTPError as http_err:
        if resp.status_code == 404:
            raise ValueError(
                f"El recurso '{clean_id}' no existe o fue retirado de datos.gov.co (Error 404: dataset.missing)."
            ) from http_err
        raise

    raw_json = resp.json()
    
    if not raw_json:
        return pd.DataFrame(), {}
    
    df = pd.DataFrame(raw_json)

    # 2. Descargar metadatos descriptivos (opcional / no bloqueante)
    metadata: dict[str, Any] = {}
    try:
        meta_resp = requests.get(
            METADATA_API_URL.format(resource_id=clean_id),
            timeout=10
        )
        if meta_resp.status_code == 200:
            metadata = meta_resp.json()
    except Exception:
        # Metadatos no disponibles no deben bloquear la carga de datos
        pass

    # 3. Conversion e inferencia inteligente de tipos
    for col in df.columns:
        # Intentar numerico primero
        try:
            converted = pd.to_numeric(df[col])
            # Validar que no sean puros NaN si la original no lo era
            if not (converted.isna().all() and not df[col].isna().all()):
                df[col] = converted
                continue
        except (ValueError, TypeError):
            pass

        # Si el nombre de columna sugiere fecha o si es un formato ISO comun
        col_lower = str(col).lower()
        if any(keyword in col_lower for keyword in ["fecha", "date", "vigencia", "periodo", "tiempo"]):
            try:
                df[col] = pd.to_datetime(df[col], errors="coerce")
            except Exception:
                pass

    return df, metadata

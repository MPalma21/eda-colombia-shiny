"""Servicio desacoplado para el consumo de datos abiertos de Colombia (datos.gov.co).

Funciones puras de Python sin dependencias de Shiny ni contexto reactivo.
"""
from typing import Any
import json
import re
from urllib.parse import urlparse
import requests
import pandas as pd
from config import BASE_API_URL, METADATA_API_URL, API_TIMEOUT_SECONDS, DEFAULT_MAX_ROWS


def extract_resource_id(input_value: str) -> str:
    """Extrae el identificador del recurso Socrata (ej. 'gt2j-8ykr') de una URL o texto plano."""
    val = input_value.strip()
    if not val:
        return ""
    if val.startswith(("http://", "https://")):
        parsed = urlparse(val)
        if parsed.scheme != "https" or parsed.hostname not in {"datos.gov.co", "www.datos.gov.co"}:
            raise ValueError("Use una URL HTTPS de datos.gov.co o un ID de recurso.")
        parts = parsed.path.strip("/").split("/")
        if len(parts) < 2:
            raise ValueError("La URL no contiene un ID de recurso válido.")
        val = re.sub(r"\.(json|csv)$", "", parts[-1], flags=re.IGNORECASE)
    if not re.fullmatch(r"[a-z0-9]{4}-[a-z0-9]{4}", val, flags=re.IGNORECASE):
        raise ValueError("El ID debe tener el formato abcd-1234.")
    return val.lower()


def _flatten_structured_value(value: Any) -> Any:
    if isinstance(value, dict):
        return value.get("url") or json.dumps(value, ensure_ascii=False, sort_keys=True)
    if isinstance(value, list):
        return json.dumps(value, ensure_ascii=False)
    return value


def _convert_columns(df: pd.DataFrame, metadata: dict[str, Any]) -> pd.DataFrame:
    """Respeta tipos declarados; evita perder ceros iniciales o fechas inválidas."""
    declared = {
        col.get("fieldName"): col.get("dataTypeName", "").lower()
        for col in metadata.get("columns", [])
        if isinstance(col, dict)
    }
    for col in df.columns:
        # Socrata entrega campos URL y ubicacion como objetos. Las vistas de
        # Shiny y el diagnostico de cardinalidad requieren valores escalares.
        if df[col].map(lambda value: isinstance(value, (dict, list))).any():
            df[col] = df[col].map(_flatten_structured_value)
        kind = declared.get(col, "")
        if kind in {"number", "money", "percent", "double"}:
            converted = pd.to_numeric(df[col], errors="coerce")
            if not (converted.isna() & df[col].notna()).any():
                df[col] = converted
        elif kind in {"calendar_date", "date", "floating_timestamp", "fixed_timestamp"}:
            converted = pd.to_datetime(df[col], errors="coerce")
            if not (converted.isna() & df[col].notna()).any():
                df[col] = converted
        elif not kind:
            values = df[col].dropna().astype(str)
            name = str(col).lower()
            if any(word in name for word in ("fecha", "date", "periodo", "tiempo")):
                converted = pd.to_datetime(df[col], errors="coerce")
                if not (converted.isna() & df[col].notna()).any():
                    df[col] = converted
            elif not any(word in name for word in ("id", "codigo", "código", "nit", "telefono", "teléfono")) and not values.str.match(r"^0\d+").any():
                converted = pd.to_numeric(df[col], errors="coerce")
                if not (converted.isna() & df[col].notna()).any():
                    df[col] = converted
    return df


def _spread_windows(total: int, limit: int) -> list[tuple[int, int]]:
    """Reparte el límite entre bloques ordenados por ID a lo largo del recurso."""
    if total <= limit:
        return [(0, limit)]
    blocks = min(5, limit)
    base, extra = divmod(limit, blocks)
    sizes = [base + (index < extra) for index in range(blocks)]
    return [
        (round(index * (total - size) / (blocks - 1)), size)
        for index, size in enumerate(sizes)
    ]


def fetch_dataset(resource_id: str, limit: int = 5000, query: str = "", selection_mode: str = "first") -> tuple[pd.DataFrame, dict[str, Any]]:
    """Descarga registros y metadatos de datos.gov.co vía Socrata Open Data API.
    
    Returns:
        tuple[pd.DataFrame, dict]: DataFrame tipado e información de metadatos.
    """
    clean_id = extract_resource_id(resource_id)
    if not clean_id:
        raise ValueError("ID de recurso inválido o vacío.")

    row_limit = min(max(10, int(limit)), DEFAULT_MAX_ROWS)
    query = query.strip()
    if selection_mode not in {"first", "spread"}:
        raise ValueError("Modo de selección no válido.")
    if len(query) > 120:
        raise ValueError("El filtro de texto no puede superar 120 caracteres.")
    data_url = BASE_API_URL.format(resource_id=clean_id)
    params = {"$limit": row_limit, "$offset": 0, "$order": ":id"}
    if query:
        params["$q"] = query
    
    def download_page(offset: int, size: int) -> list[dict[str, Any]]:
        page_params = {**params, "$offset": offset, "$limit": size}
        try:
            resp = requests.get(data_url, params=page_params, timeout=API_TIMEOUT_SECONDS)
            resp.raise_for_status()
        except requests.exceptions.HTTPError as http_err:
            if resp.status_code == 404:
                raise ValueError(
                    f"El recurso '{clean_id}' no existe o fue retirado de datos.gov.co (Error 404: dataset.missing)."
                ) from http_err
            raise
        return resp.json()

    count_params = {"$select": "count(*)"}
    if query:
        count_params["$q"] = query
    total_rows = None
    if selection_mode == "spread":
        count_resp = requests.get(data_url, params=count_params, timeout=API_TIMEOUT_SECONDS)
        count_resp.raise_for_status()
        total_rows = int(count_resp.json()[0]["count"])
        windows = _spread_windows(total_rows, row_limit)
        raw_json = [record for offset, size in windows for record in download_page(offset, size)]
    else:
        raw_json = download_page(0, row_limit)
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

    # El conteo es informativo: un error no impide analizar los datos descargados.
    metadata["_eda_query"] = query
    metadata["_eda_limit"] = row_limit
    metadata["_eda_resource_id"] = clean_id
    metadata["_eda_fetch_mode"] = selection_mode
    if selection_mode == "first":
        try:
            count_resp = requests.get(data_url, params=count_params, timeout=API_TIMEOUT_SECONDS)
            count_resp.raise_for_status()
            total_rows = int(count_resp.json()[0]["count"])
        except (requests.RequestException, ValueError, KeyError, IndexError, TypeError):
            pass
    metadata["_eda_total_rows"] = total_rows

    return _convert_columns(df, metadata), metadata

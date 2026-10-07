"""Casos que protegen la carga, los filtros y el alcance del análisis."""
import pandas as pd
import pytest
import requests
from datetime import date

from services.api_service import extract_resource_id, fetch_dataset, _spread_windows
from services.stats_service import classify_columns, sample_scatter_rows, suggest_time_aggregation
from services.scope_service import apply_analysis_scope
from services.table_service import filter_table_rows, to_safe_csv_bytes


class FakeResponse:
    def __init__(self, payload, status=200):
        self.payload = payload
        self.status_code = status

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError("error de API")

    def json(self):
        return self.payload


@pytest.mark.parametrize("value", [
    "https://otro.example/resource/gt2j-8ykr.json",
    "https://www.datos.gov.co.evil.test/d/gt2j-8ykr",
    "../../otro", "gt2j-8ykr/extra", "http://www.datos.gov.co/d/gt2j-8ykr",
])
def test_rejects_invalid_resource_id(value):
    with pytest.raises(ValueError):
        extract_resource_id(value)


def test_fetch_preserves_codes_and_reports_filtered_scope(monkeypatch):
    calls = []

    def fake_get(url, **kwargs):
        calls.append((url, kwargs.get("params")))
        if "/api/views/" in url:
            return FakeResponse({"name": "Ejemplo", "columns": [
                {"fieldName": "codigo", "dataTypeName": "text"},
                {"fieldName": "valor", "dataTypeName": "number"},
                {"fieldName": "fecha", "dataTypeName": "calendar_date"},
            ]})
        if kwargs["params"].get("$select") == "count(*)":
            return FakeResponse([{"count": "42"}])
        return FakeResponse([{"codigo": "0012", "valor": "2.5", "fecha": "2024-01-01"}])

    monkeypatch.setattr("services.api_service.requests.get", fake_get)
    df, meta = fetch_dataset("gt2j-8ykr", limit=10, query="Bogotá")

    assert df.loc[0, "codigo"] == "0012"
    assert df.loc[0, "valor"] == 2.5
    assert pd.api.types.is_datetime64_any_dtype(df["fecha"])
    assert meta["_eda_total_rows"] == 42
    assert meta["_eda_query"] == "Bogotá"
    assert calls[0][1]["$q"] == "Bogotá"
    assert calls[0][1]["$order"] == ":id"
    assert calls[2][1]["$q"] == "Bogotá"


def test_invalid_dates_remain_visible_instead_of_becoming_null(monkeypatch):
    def fake_get(url, **kwargs):
        if "/api/views/" in url:
            return FakeResponse({"columns": [{"fieldName": "fecha", "dataTypeName": "calendar_date"}]})
        if kwargs["params"].get("$select"):
            return FakeResponse([{"count": "2"}])
        return FakeResponse([{"fecha": "2024-01-01"}, {"fecha": "fecha pendiente"}])

    monkeypatch.setattr("services.api_service.requests.get", fake_get)
    df, _ = fetch_dataset("gt2j-8ykr")
    assert df.loc[1, "fecha"] == "fecha pendiente"


def test_fetch_without_metadata_keeps_leading_zero_codes(monkeypatch):
    def fake_get(url, **kwargs):
        if "/api/views/" in url:
            return FakeResponse({}, status=503)
        if kwargs["params"].get("$select"):
            return FakeResponse({}, status=503)
        return FakeResponse([{"codigo_postal": "00123", "monto": "10"}])

    monkeypatch.setattr("services.api_service.requests.get", fake_get)
    df, meta = fetch_dataset("gt2j-8ykr")
    assert df.loc[0, "codigo_postal"] == "00123"
    assert df.loc[0, "monto"] == 10
    assert meta["_eda_total_rows"] is None


def test_empty_data_and_no_numeric_columns(monkeypatch):
    def fake_get(url, **kwargs):
        if "/api/views/" in url:
            return FakeResponse({})
        if kwargs["params"].get("$select"):
            return FakeResponse([{"count": "0"}])
        return FakeResponse([])

    monkeypatch.setattr("services.api_service.requests.get", fake_get)
    df, meta = fetch_dataset("gt2j-8ykr")
    assert df.empty and meta["_eda_total_rows"] == 0
    assert classify_columns(pd.DataFrame({"fecha": pd.to_datetime(["2024-01-01"]), "codigo": ["A"]}))[0] == []


def test_table_search_is_literal_and_export_uses_same_rows():
    df = pd.DataFrame({"texto": ["A (uno)", "A dos", "B (tres)"], "grupo": ["A", "A", "B"]})
    filtered = filter_table_rows(df, "(", "grupo", "A")
    assert filtered["texto"].tolist() == ["A (uno)"]
    assert "A (uno)" in to_safe_csv_bytes(filtered).decode("utf-8-sig")


def test_csv_escapes_untrusted_formula_text():
    df = pd.DataFrame({"valor": ["=1+1", " texto", "@cmd"], "numero": [-2, 3, 4]})
    csv = to_safe_csv_bytes(df).decode("utf-8-sig")
    assert "'=1+1" in csv and "'@cmd" in csv
    assert "-2" in csv


def test_scatter_sample_is_bounded_and_repeatable():
    df = pd.DataFrame({"x": range(2000), "y": range(2000)})
    first = sample_scatter_rows(df, ["x", "y"], max_rows=100)
    second = sample_scatter_rows(df, ["x", "y"], max_rows=100)
    assert len(first) == 100
    pd.testing.assert_frame_equal(first, second)


def test_analysis_scope_filters_period_then_samples_loaded_rows():
    df = pd.DataFrame({
        "fecha": pd.date_range("2024-01-01", periods=100),
        "valor": range(100),
    })
    a = apply_analysis_scope(df, "fecha", (date(2024, 2, 1), date(2024, 2, 29)), 10)
    b = apply_analysis_scope(df, "fecha", (date(2024, 2, 1), date(2024, 2, 29)), 10)
    assert len(a) == 10
    assert a["fecha"].min().date() >= date(2024, 2, 1)
    assert a["fecha"].max().date() <= date(2024, 2, 29)
    pd.testing.assert_frame_equal(a, b)


def test_category_search_uses_any_matching_value():
    df = pd.DataFrame({"region": ["Bogotá", "Bogotá", "Cali"], "sector": ["Salud", "Educación", "Salud"]})
    assert filter_table_rows(df, category_column="sector", category="sal")["region"].tolist() == ["Bogotá", "Cali"]


def test_time_aggregation_suggestion():
    assert suggest_time_aggregation("valor_trm") == "Promedio"
    assert suggest_time_aggregation("cantidad_contratos") == "Suma"


def test_spread_fetch_uses_distant_blocks(monkeypatch):
    offsets = []

    def fake_get(url, **kwargs):
        if "/api/views/" in url:
            return FakeResponse({"columns": []})
        params = kwargs["params"]
        if params.get("$select") == "count(*)":
            return FakeResponse([{"count": "1000"}])
        offsets.append(params["$offset"])
        return FakeResponse([{"valor": str(params["$offset"])}])

    monkeypatch.setattr("services.api_service.requests.get", fake_get)
    df, meta = fetch_dataset("gt2j-8ykr", limit=50, selection_mode="spread")
    assert offsets == [offset for offset, _ in _spread_windows(1000, 50)]
    assert len(set(offsets)) == 5
    assert offsets[-1] > 900
    assert len(df) == 5
    assert meta["_eda_fetch_mode"] == "spread"

"""Filtros de la tabla aplicados también a la exportación."""
import pandas as pd


def filter_table_rows(df: pd.DataFrame, query: str = "", category_column: str = "", category: str = "") -> pd.DataFrame:
    result = df
    query = query.strip()
    if query:
        mask = result.astype(str).apply(
            lambda col: col.str.contains(query, case=False, na=False, regex=False)
        ).any(axis=1)
        result = result.loc[mask]
    if category_column in result.columns and category and category != "(Todos)":
        result = result.loc[result[category_column].astype(str).str.contains(category, case=False, na=False, regex=False)]
    return result


def to_safe_csv_bytes(df: pd.DataFrame) -> bytes:
    """Evita que texto de un recurso externo se ejecute como fórmula al abrir el CSV."""
    exported = df.copy()
    for col in exported.select_dtypes(include=["object", "string"]).columns:
        exported[col] = exported[col].map(
            lambda value: "'" + value if isinstance(value, str) and value.lstrip().startswith(("=", "+", "-", "@")) else value
        )
    return exported.to_csv(index=False).encode("utf-8-sig")

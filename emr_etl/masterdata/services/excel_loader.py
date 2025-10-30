import pandas as pd

from ..schemas import MasterItemRow


def read_excel(path: str, sheet: str | int = 0) -> pd.DataFrame:
    engine = "pyxlsb" if path.lower().endswith(".xlsb") else None
    return pd.read_excel(path, sheet_name=sheet, engine=engine, dtype=str)


def _strip(value) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _normalize_price(value) -> int | None:
    if value is None:
        return None
    raw = str(value).replace(",", "").strip()
    if not raw:
        return None
    try:
        return int(float(raw))
    except Exception:
        return None


def _series_to_raw(row: pd.Series) -> dict[str, str | None]:
    raw: dict[str, str | None] = {}
    for key, value in row.items():
        if pd.isna(value) or str(value).strip() == "":
            raw[str(key)] = None
        else:
            raw[str(key)] = str(value).strip()
    return raw


def map_diagnosis(df: pd.DataFrame) -> list[MasterItemRow]:
    df = df.rename(
        columns={
            "KCD": "code",
            "KOR_NAME": "name",
            "VALID_FROM": "valid_from",
            "VALID_TO": "valid_to",
        }
    )
    rows: list[MasterItemRow] = []
    for _, raw in df.iterrows():
        code = _strip(raw.get("code"))
        name = _strip(raw.get("name"))
        if not code or not name:
            continue
        rows.append(
            MasterItemRow(
                code=code,
                name=name,
                category="DX",
                unit=None,
                price=None,
                raw_fields=_series_to_raw(raw),
            )
        )
    return rows


def map_procedure(df: pd.DataFrame) -> list[MasterItemRow]:
    df = df.rename(
        columns={
            "PROC_CODE": "code",
            "PROC_NAME": "name",
            "PRICE": "price",
            "UNIT": "unit",
        }
    )
    rows: list[MasterItemRow] = []
    for _, raw in df.iterrows():
        code = _strip(raw.get("code"))
        name = _strip(raw.get("name"))
        if not code or not name:
            continue
        rows.append(
            MasterItemRow(
                code=code,
                name=name,
                category="ACT",
                price=_normalize_price(raw.get("price")),
                unit=_strip(raw.get("unit")) or None,
                raw_fields=_series_to_raw(raw),
            )
        )
    return rows


def map_procedure_hira_2025(df: pd.DataFrame) -> list[MasterItemRow]:
    code_col = "수가코드"
    name_col_primary = "산정명칭"
    name_col_fallback = "한글명"
    price_col = "수가금액"
    unit_col = "단위"

    rows: list[MasterItemRow] = []
    for _, raw in df.iterrows():
        code = _strip(raw.get(code_col))
        if not code:
            continue
        name = _strip(raw.get(name_col_primary)) or _strip(raw.get(name_col_fallback))
        rows.append(
            MasterItemRow(
                code=code,
                name=name,
                category="ACT",
                price=_normalize_price(raw.get(price_col)),
                unit=_strip(raw.get(unit_col)) or None,
                raw_fields=_series_to_raw(raw),
            )
        )
    return rows


def map_drug(df: pd.DataFrame) -> list[MasterItemRow]:
    df = df.rename(
        columns={
            "DRUG_CODE": "code",
            "DRUG_NAME": "name",
            "FORM": "unit",
            "PRICE": "price",
        }
    )
    rows: list[MasterItemRow] = []
    for _, raw in df.iterrows():
        code = _strip(raw.get("code"))
        name = _strip(raw.get("name"))
        if not code or not name:
            continue
        rows.append(
            MasterItemRow(
                code=code,
                name=name,
                category="DRG",
                price=_normalize_price(raw.get("price")),
                unit=_strip(raw.get("unit")) or None,
                raw_fields=_series_to_raw(raw),
            )
        )
    return rows

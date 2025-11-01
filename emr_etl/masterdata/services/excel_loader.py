from __future__ import annotations

import pandas as pd

from ..schemas import MasterItemRow


def read_excel(path: str, sheet: str | int = 0) -> pd.DataFrame:
    engine = "pyxlsb" if path.lower().endswith(".xlsb") else None
    return pd.read_excel(path, sheet_name=sheet, engine=engine, dtype=str)


def _strip(value) -> str:
    if value is None:
        return ""
    if pd.isna(value):
        return ""
    return str(value).strip()


def _normalize_price(value) -> int | None:
    if value is None or pd.isna(value):
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
    code_col = _pick_column(df, ["KCD", "상병기호", "진단코드", "CODE"])
    name_col = _pick_column(df, ["KOR_NAME", "한글명", "한글명칭", "명칭"])
    if code_col is None or name_col is None:
        return []

    rows: list[MasterItemRow] = []
    for _, raw in df.iterrows():
        code = _strip(raw.get(code_col))
        name = _strip(raw.get(name_col))
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


def _pick_column(df: pd.DataFrame, candidates: list[str]) -> str | None:
    for column in candidates:
        if column in df.columns:
            return column
    return None


def map_procedure_hira_2025(df: pd.DataFrame) -> list[MasterItemRow]:
    code_col = _pick_column(df, ["수가코드", "코드", "PROC_CODE"]) or "수가코드"
    name_col_primary = _pick_column(df, ["산정명칭", "명칭", "항목명"]) or "산정명칭"
    name_col_fallback = _pick_column(df, ["한글명", "상세명", "한글명칭"])
    price_col = _pick_column(df, ["한방병의원단가", "수가금액", "가격", "단가"])
    unit_col = _pick_column(df, ["단위", "UNIT"])

    rows: list[MasterItemRow] = []
    for _, raw in df.iterrows():
        code = _strip(raw.get(code_col))
        if not code:
            continue
        name = _strip(raw.get(name_col_primary)) or _strip(raw.get(name_col_fallback))
        price_value = raw.get(price_col) if price_col else None
        unit_value = raw.get(unit_col) if unit_col else None
        rows.append(
            MasterItemRow(
                code=code,
                name=name,
                category="ACT",
                price=_normalize_price(price_value),
                unit=_strip(unit_value) or None,
                raw_fields=_series_to_raw(raw),
            )
        )
    return rows


def map_drug(df: pd.DataFrame) -> list[MasterItemRow]:
    code_col = _pick_column(df, ["DRUG_CODE", "약가코드", "제품코드", "코드"])
    name_col = _pick_column(df, ["DRUG_NAME", "약품명", "제품명", "품목명", "명칭"])
    unit_col = _pick_column(df, ["FORM", "단위", "규격"])
    price_col = _pick_column(df, ["PRICE", "상한금액", "약가", "단가", "금액"])
    if code_col is None or name_col is None:
        return []

    rows: list[MasterItemRow] = []
    for _, raw in df.iterrows():
        code = _strip(raw.get(code_col))
        name = _strip(raw.get(name_col))
        if not code or not name:
            continue
        unit_value = raw.get(unit_col) if unit_col else None
        price_value = raw.get(price_col) if price_col else None
        rows.append(
            MasterItemRow(
                code=code,
                name=name,
                category="DRG",
                price=_normalize_price(price_value),
                unit=_strip(unit_value) or None,
                raw_fields=_series_to_raw(raw),
            )
        )
    return rows

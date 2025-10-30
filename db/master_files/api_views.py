import io
import json
from typing import Any, Dict, Iterable, Tuple

import pandas as pd
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db import router, transaction
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from .models import MasterItem, MasterUpload


def _json_error(message: str, status: int = 400) -> JsonResponse:
    """Consistently shape error responses."""
    return JsonResponse({"ok": False, "error": message}, status=status)


def _serialize_master_item(item: MasterItem) -> Dict[str, Any]:
    return {
        "id": item.id,
        "code": item.code,
        "name": item.name,
        "category": item.category,
        "price": item.price,
        "unit": item.unit,
        "raw_fields": item.raw_fields,
    }


def _serialize_master_upload(upload: MasterUpload) -> Dict[str, Any]:
    return {
        "id": upload.id,
        "filename": upload.filename,
        "filetype": upload.filetype,
        "uploaded_at": upload.uploaded_at.isoformat(),
        "total_rows": upload.total_rows,
        "notes": upload.notes,
    }


def _load_json_body(request) -> Dict[str, Any]:
    if not request.body:
        return {}
    try:
        return json.loads(request.body.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        raise ValueError("Request body must be valid JSON")


COLUMN_ALIASES = {
    "code": ["코드", "항목코드", "수가코드", "약가코드", "진단코드", "코드값", "코드번호"],
    "name": ["명칭", "항목명", "품목명", "성분명", "산정명칭", "항목명칭"],
    "price": ["금액", "수가(원)", "약가", "단가", "가격", "가격(원)"],
    "unit": ["단위", "용량", "회수", "횟수", "규격"],
    "category_hint": ["구분", "분류", "급여구분", "항목구분"],
}


def _build_mapping(columns: Iterable[str]) -> Dict[str, str | None]:
    mapping = {"code": None, "name": None, "price": None, "unit": None, "category_hint": None}
    lowered = [str(column).strip().lower() for column in columns]
    for std_key, aliases in COLUMN_ALIASES.items():
        for alias in aliases:
            try:
                idx = lowered.index(str(alias).strip().lower())
            except ValueError:
                continue
            mapping[std_key] = columns[idx]
            break
    return mapping


def _normalize_category(user_category: str, hint_value: str | None) -> str:
    """
    Use the user-selected category first and fall back to weak inference from hint column.
    """
    category = (user_category or "ACT").upper()
    if hint_value:
        hint = str(hint_value).strip()
        if any(token in hint for token in ["약", "Drug", "DRG"]):
            return "DRG"
        if any(token in hint for token in ["진단", "KCD", "DX"]):
            return "DX"
        if any(token in hint for token in ["행위", "수가", "Procedure"]):
            return "ACT"
    return category


def _clean_price(value: Any) -> int | None:
    if pd.isna(value):
        return None
    raw = str(value).replace(",", "").strip()
    if not raw:
        return None
    try:
        return int(float(raw))
    except Exception:
        return None


def _read_file_to_iterator(fobj, ext: str, chunk_size: int = 5000):
    """
    Yield dataframes in chunks so that large uploads stay memory friendly.
    """
    if ext == "csv":
        yield from pd.read_csv(fobj, chunksize=chunk_size, dtype=str, keep_default_na=False)
    elif ext == "xlsx":
        df = pd.read_excel(fobj, dtype=str, engine="openpyxl")
        for i in range(0, len(df), chunk_size):
            yield df.iloc[i : i + chunk_size]
    elif ext == "xlsb":
        df = pd.read_excel(fobj, dtype=str, engine="pyxlsb")
        for i in range(0, len(df), chunk_size):
            yield df.iloc[i : i + chunk_size]
    else:
        raise ValueError(f"Unsupported extension: {ext}")


def _import_master_file(fobj, filename: str, category: str) -> Tuple[MasterUpload, Dict[str, Any]]:
    ext = filename.split(".")[-1].lower()
    if ext not in ("xlsx", "xlsb", "csv"):
        raise ValueError("Only .xlsx, .xlsb, .csv are supported")

    db_alias = router.db_for_write(MasterItem)
    upload = MasterUpload.objects.using(db_alias).create(
        filename=filename,
        filetype=ext,
        total_rows=0,
        notes="",
    )

    total_inserted = 0
    total_updated = 0
    total_rows = 0

    content = fobj.read()

    iterator = _read_file_to_iterator(io.BytesIO(content), ext)
    try:
        first_df = next(iterator)
    except StopIteration:
        raise ValueError("Empty file")
    mapping = _build_mapping(first_df.columns)

    for df in [first_df, *iterator]:
        total_rows += len(df)

        code_col = mapping["code"]
        name_col = mapping["name"]
        price_col = mapping["price"]
        unit_col = mapping["unit"]
        hint_col = mapping["category_hint"]

        records = df.to_dict(orient="records")
        with transaction.atomic(using=db_alias):
            for record in records:
                code = str(record.get(code_col, "")).strip() if code_col else ""
                name = str(record.get(name_col, "")).strip() if name_col else ""
                if not code or not name:
                    continue

                price = _clean_price(record.get(price_col)) if price_col else None
                unit = (str(record.get(unit_col)).strip() or None) if unit_col else None
                normalized_category = _normalize_category(category, record.get(hint_col) if hint_col else None)
                raw_record = {
                    key: (
                        None
                        if (pd.isna(value) or str(value).strip() == "")
                        else str(value)
                    )
                    for key, value in record.items()
                }

                _, created = MasterItem.objects.update_or_create(
                    code=code,
                    category=normalized_category,
                    defaults={
                        "name": name,
                        "price": price,
                        "unit": unit,
                        "raw_fields": raw_record,
                    },
                )
                if created:
                    total_inserted += 1
                else:
                    total_updated += 1

    upload.total_rows = total_rows
    upload.notes = f"inserted={total_inserted}, updated={total_updated}"
    upload.save(using=db_alias)

    stats = {
        "total_rows": total_rows,
        "inserted": total_inserted,
        "updated": total_updated,
        "mapping_used": mapping,
    }
    return upload, stats


@method_decorator(csrf_exempt, name="dispatch")
class MasterItemCollectionView(View):
    http_method_names = ["get", "post", "options"]

    def get(self, request):
        qs = MasterItem.objects.all().order_by("code")

        category = request.GET.get("category")
        if category:
            qs = qs.filter(category=category.upper())

        search = request.GET.get("search")
        if search:
            qs = qs.filter(Q(name__icontains=search) | Q(code__icontains=search))

        page = request.GET.get("page", 1)
        page_size = request.GET.get("page_size") or 25
        try:
            page_size = max(1, min(int(page_size), 100))
        except ValueError:
            return _json_error("page_size must be an integer", status=400)

        paginator = Paginator(qs, page_size)
        try:
            page_obj = paginator.page(page)
        except PageNotAnInteger:
            page_obj = paginator.page(1)
        except EmptyPage:
            page_obj = paginator.page(paginator.num_pages)

        data = [_serialize_master_item(item) for item in page_obj]
        return JsonResponse(
            {
                "ok": True,
                "count": paginator.count,
                "page": page_obj.number,
                "page_size": page_size,
                "results": data,
            }
        )

    def post(self, request):
        try:
            payload = _load_json_body(request)
        except ValueError as exc:
            return _json_error(str(exc), status=400)

        code = (payload.get("code") or "").strip()
        name = (payload.get("name") or "").strip()
        category = (payload.get("category") or "ACT").upper()
        price = payload.get("price")
        unit = payload.get("unit")
        raw_fields = payload.get("raw_fields") or {}

        if not code or not name:
            return _json_error("code and name are required", status=400)

        if category not in dict(MasterItem.CATEGORY_CHOICES):
            return _json_error("invalid category", status=400)

        if price is not None:
            try:
                price = int(price)
            except (TypeError, ValueError):
                return _json_error("price must be numeric", status=400)

        if not isinstance(raw_fields, dict):
            return _json_error("raw_fields must be an object", status=400)

        try:
            item = MasterItem.objects.create(
                code=code,
                name=name,
                category=category,
                price=price,
                unit=unit,
                raw_fields=raw_fields,
            )
        except Exception as exc:
            return _json_error(str(exc), status=400)

        return JsonResponse({"ok": True, "item": _serialize_master_item(item)}, status=201)


@method_decorator(csrf_exempt, name="dispatch")
class MasterItemDetailView(View):
    http_method_names = ["get", "patch", "delete", "options"]

    def get_object(self, pk: int) -> MasterItem:
        return get_object_or_404(MasterItem, pk=pk)

    def get(self, request, pk: int):
        item = self.get_object(pk)
        return JsonResponse({"ok": True, "item": _serialize_master_item(item)})

    def patch(self, request, pk: int):
        item = self.get_object(pk)
        try:
            payload = _load_json_body(request)
        except ValueError as exc:
            return _json_error(str(exc), status=400)

        allowed_fields = {"code", "name", "category", "price", "unit", "raw_fields"}
        dirty = False

        for field, value in payload.items():
            if field not in allowed_fields:
                continue
            if field == "category":
                value = (value or "").upper()
                if value not in dict(MasterItem.CATEGORY_CHOICES):
                    return _json_error("invalid category", status=400)
            if field == "price" and value is not None:
                try:
                    value = int(value)
                except (TypeError, ValueError):
                    return _json_error("price must be numeric", status=400)
            if field == "raw_fields" and value is not None and not isinstance(value, dict):
                return _json_error("raw_fields must be an object", status=400)
            setattr(item, field, value)
            dirty = True

        if dirty:
            item.save(update_fields=list(set(payload.keys()) & allowed_fields))

        return JsonResponse({"ok": True, "item": _serialize_master_item(item)})

    def delete(self, request, pk: int):
        item = self.get_object(pk)
        item.delete()
        return JsonResponse({"ok": True})


@method_decorator(csrf_exempt, name="dispatch")
class MasterUploadCollectionView(View):
    http_method_names = ["get", "post", "options"]

    def get(self, request):
        qs = MasterUpload.objects.all().order_by("-uploaded_at")
        limit = request.GET.get("limit")
        if limit:
            try:
                limit = max(1, min(int(limit), 100))
            except ValueError:
                return _json_error("limit must be an integer", status=400)
            qs = qs[:limit]
        return JsonResponse(
            {"ok": True, "results": [_serialize_master_upload(upload) for upload in qs]}
        )

    def post(self, request):
        upload_file = request.FILES.get("file")
        category = (request.POST.get("category") or "ACT").upper()
        if not upload_file:
            return _json_error("file is required", status=400)
        if category not in dict(MasterItem.CATEGORY_CHOICES):
            return _json_error("invalid category", status=400)

        try:
            upload, stats = _import_master_file(upload_file, upload_file.name, category)
        except ValueError as exc:
            return _json_error(str(exc), status=400)
        except Exception as exc:
            return _json_error(str(exc), status=500)

        body = {"ok": True, "upload": _serialize_master_upload(upload)}
        body.update(stats)
        return JsonResponse(body, status=201)


@method_decorator(csrf_exempt, name="dispatch")
class MasterUploadDetailView(View):
    http_method_names = ["get", "options"]

    def get(self, request, pk: int):
        upload = get_object_or_404(MasterUpload, pk=pk)
        return JsonResponse({"ok": True, "upload": _serialize_master_upload(upload)})

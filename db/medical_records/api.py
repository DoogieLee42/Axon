from __future__ import annotations

import json
from decimal import Decimal, InvalidOperation
from datetime import datetime
from typing import Any, Dict, Iterable

from django.db import transaction
from django.http import HttpRequest, JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone

from db.patients.models import Patient

from .models import ClinicalNote, DiagnosisEntry, Prescription
from .serializers import serialize_note


def _json_error(message: str, status: int = 400) -> JsonResponse:
    return JsonResponse({"ok": False, "error": message}, status=status)


def _to_decimal(value: Any) -> Decimal:
    if value in (None, "", []):
        return Decimal("0")
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return Decimal("0")


def _to_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _ensure_list(payload: Any) -> Iterable:
    if isinstance(payload, list):
        return payload
    return []


def _parse_iso_datetime(value: Any):
    if not value:
        return None
    if not isinstance(value, str):
        return None
    raw = value.strip()
    if not raw:
        return None
    cleaned = raw.replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(cleaned)
    except ValueError:
        return None
    if timezone.is_naive(dt):
        return timezone.make_aware(dt, timezone.get_default_timezone())
    return dt.astimezone(timezone.get_default_timezone())


@csrf_exempt
@require_http_methods(["POST"])
def create_clinical_note(request: HttpRequest, pk: int) -> JsonResponse:
    patient = get_object_or_404(Patient, pk=pk)
    try:
        payload: Dict[str, Any] = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return _json_error("잘못된 JSON 형식입니다.")

    narrative = (payload.get("narrative") or "").strip()
    social_history = (payload.get("socialHistory") or "").strip()
    family_history = (payload.get("familyHistory") or "").strip()
    requested_visit_date = _parse_iso_datetime(payload.get("visitDate"))
    if payload.get("visitDate") and requested_visit_date is None:
        return _json_error("내원일시 형식이 올바르지 않습니다.")

    has_content = any(
        [
            narrative,
            social_history,
            family_history,
            bool(_ensure_list(payload.get("diagnoses"))),
            bool(_ensure_list(payload.get("prescriptions"))),
        ]
    )
    if not has_content:
        return _json_error("기록할 내용이 없습니다.", status=400)

    with transaction.atomic():
        note = ClinicalNote.objects.create(
            patient=patient,
            visit_date=requested_visit_date or timezone.now(),
            chief_complaint=(payload.get("chiefComplaint") or "").strip(),
            s_text=(payload.get("subjective") or "").strip(),
            o_text=(payload.get("objective") or "").strip(),
            a_text=(payload.get("assessment") or "").strip(),
            p_text=(payload.get("plan") or "").strip(),
            narrative=narrative,
            social_history_text=social_history,
            family_history_text=family_history,
        )

        diagnosis_entries = []
        primary_icd = ""
        for entry in _ensure_list(payload.get("diagnoses")):
            if not isinstance(entry, dict):
                continue
            code = (entry.get("code") or "").strip()
            name = (entry.get("name") or "").strip()
            if not code and not name:
                continue
            if not code:
                code = name[:32] or "UNK"
            source = (entry.get("source") or "master").strip() or "master"
            diagnosis_entries.append(
                DiagnosisEntry(
                    note=note,
                    code=code,
                    name=name or code,
                    source=source,
                )
            )
            if not primary_icd and code:
                primary_icd = code

        if diagnosis_entries:
            DiagnosisEntry.objects.bulk_create(diagnosis_entries, ignore_conflicts=True)
            if primary_icd:
                note.primary_icd = primary_icd

        prescription_entries = []
        for entry in _ensure_list(payload.get("prescriptions")):
            if not isinstance(entry, dict):
                continue
            item_type = (entry.get("itemType") or "PROC").upper()
            if item_type not in {"DRUG", "TEST", "PROC"}:
                item_type = "PROC"
            name = (entry.get("name") or "").strip()
            if not name:
                continue
            prescription_entries.append(
                Prescription(
                    note=note,
                    item_type=item_type,
                    code=(entry.get("code") or "").strip(),
                    name=name,
                    qty=_to_decimal(entry.get("qty")),
                    unit=(entry.get("unit") or "").strip(),
                    dose=(entry.get("dose") or "").strip(),
                    freq=(entry.get("freq") or "").strip(),
                    route=(entry.get("route") or "").strip(),
                    days=_to_int(entry.get("days")),
                    specimen=(entry.get("specimen") or "").strip(),
                    priority=(entry.get("priority") or "").strip(),
                    site=(entry.get("site") or "").strip(),
                    anesthesia=(entry.get("anesthesia") or "").strip(),
                    notes=(entry.get("notes") or "").strip(),
                )
            )

        if prescription_entries:
            Prescription.objects.bulk_create(prescription_entries)

        if primary_icd:
            note.save(update_fields=["primary_icd"])

    note = (
        ClinicalNote.objects.filter(pk=note.pk)
        .select_related("vitals", "anthro")
        .prefetch_related("medications", "diagnoses", "allergies", "prescriptions")
        .get()
    )
    return JsonResponse({"ok": True, "note": serialize_note(note)}, status=201)

from __future__ import annotations

import json
from datetime import date
from typing import Any, Dict
from django.http import HttpRequest, JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .models import ExternalDocument, ExternalResult, Patient
from db.medical_records.serializers import (
    serialize_anthropometrics,
    serialize_note,
    serialize_vitals,
)


def _compute_age(birth_date: date) -> int:
    today = date.today()
    age = today.year - birth_date.year - (
        (today.month, today.day) < (birth_date.month, birth_date.day)
    )
    return age


def _serialize_patient(patient: Patient) -> Dict[str, Any]:
    return {
        "id": patient.pk,
        "name": patient.name,
        "gender": patient.gender,
        "birthDate": patient.birth_date.isoformat(),
        "age": _compute_age(patient.birth_date),
        "rrn": patient.rrn,
        "phone": patient.phone,
        "address": patient.address,
        "regNo": patient.reg_no,
        "createdAt": timezone.localtime(patient.created_at).isoformat(),
    }


def _serialize_document(document: ExternalDocument) -> Dict[str, Any]:
    return {
        "id": document.pk,
        "title": document.title,
        "source": document.source,
        "recordedAt": document.recorded_at.isoformat() if document.recorded_at else None,
        "description": document.description,
        "fileUrl": document.file_url,
    }


def _serialize_result(result: ExternalResult) -> Dict[str, Any]:
    return {
        "id": result.pk,
        "name": result.name,
        "provider": result.provider,
        "recordedAt": result.recorded_at.isoformat() if result.recorded_at else None,
        "summary": result.summary,
        "fileUrl": result.file_url,
    }


@require_http_methods(["GET", "POST"])
@csrf_exempt
def patient_collection(request: HttpRequest) -> JsonResponse:
    if request.method == "GET":
        patients = [_serialize_patient(patient) for patient in Patient.objects.order_by("-created_at")]
        return JsonResponse({"results": patients})

    try:
        payload = json.loads(request.body or "{}")
    except json.JSONDecodeError:
        return JsonResponse({"error": "잘못된 JSON 형식입니다."}, status=400)

    required_fields = ["name", "gender", "birthDate", "rrn"]
    missing = [field for field in required_fields if not payload.get(field)]
    if missing:
        return JsonResponse({"error": f"필수 항목 누락: {', '.join(missing)}"}, status=400)

    try:
        birth_date = date.fromisoformat(payload["birthDate"])
    except ValueError:
        return JsonResponse({"error": "생년월일 형식이 올바르지 않습니다."}, status=400)

    gender = payload["gender"].upper()
    valid_genders = {choice[0] for choice in Patient.GENDER_CHOICES}
    if gender not in valid_genders:
        return JsonResponse({"error": "허용되지 않는 성별 코드입니다."}, status=400)

    patient = Patient(
        name=payload["name"].strip(),
        gender=gender,
        birth_date=birth_date,
        rrn=payload["rrn"].strip(),
        phone=payload.get("phone", "").strip(),
        address=payload.get("address", "").strip(),
    )

    try:
        patient.full_clean()
        patient.save()
    except Exception as exc:  # pragma: no cover - serializing validation errors
        return JsonResponse({"error": str(exc)}, status=400)

    return JsonResponse(_serialize_patient(patient), status=201)


@require_http_methods(["GET"])
def patient_detail(request: HttpRequest, pk: int) -> JsonResponse:
    patient = get_object_or_404(Patient, pk=pk)
    notes = (
        patient.clinical_notes.all()
        .select_related("vitals", "anthro")
        .prefetch_related("medications", "diagnoses", "allergies", "prescriptions")
        .order_by("-visit_date")
    )
    serialized_notes = [serialize_note(note) for note in notes[:5]]

    latest_note = notes[0] if notes else None

    documents = [_serialize_document(doc) for doc in patient.external_documents.all()[:5]]
    lab_results = [_serialize_result(result) for result in patient.external_results.all()[:8]]

    response: Dict[str, Any] = {
        "patient": _serialize_patient(patient),
        "notes": serialized_notes,
        "latestVitals": serialize_vitals(getattr(latest_note, "vitals", None)) if latest_note else None,
        "latestAnthropometrics": serialize_anthropometrics(getattr(latest_note, "anthro", None)) if latest_note else None,
        "documents": documents,
        "labResults": lab_results,
    }

    return JsonResponse(response)

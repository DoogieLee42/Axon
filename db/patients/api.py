from __future__ import annotations

import json
from datetime import date
from typing import Any, Dict, Optional
from django.http import HttpRequest, JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .models import ExternalDocument, Patient
from db.medical_records.models import ClinicalNote, Vitals, Anthropometrics


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


def _serialize_vitals(vitals: Optional[Vitals]) -> Optional[Dict[str, Any]]:
    if not vitals:
        return None
    return {
        "systolic": vitals.systolic,
        "diastolic": vitals.diastolic,
        "heartRate": vitals.heart_rate,
        "respRate": vitals.resp_rate,
        "temperatureC": float(vitals.temperature_c) if vitals.temperature_c is not None else None,
        "spo2": vitals.spo2,
        "painScore": vitals.pain_score,
    }


def _serialize_anthro(anthro: Optional[Anthropometrics]) -> Optional[Dict[str, Any]]:
    if not anthro:
        return None
    return {
        "heightCm": float(anthro.height_cm) if anthro.height_cm is not None else None,
        "weightKg": float(anthro.weight_kg) if anthro.weight_kg is not None else None,
        "bmi": float(anthro.bmi) if anthro.bmi is not None else None,
        "waistCm": float(anthro.waist_cm) if anthro.waist_cm is not None else None,
    }


def _serialize_note(note: ClinicalNote) -> Dict[str, Any]:
    return {
        "id": note.pk,
        "visitDate": timezone.localtime(note.visit_date).isoformat(),
        "chiefComplaint": note.chief_complaint,
        "subjective": note.s_text,
        "objective": note.o_text,
        "assessment": note.a_text,
        "plan": note.p_text,
        "primaryIcd": note.primary_icd,
        "medications": [
            {
                "id": medication.pk,
                "name": medication.name,
                "dose": medication.dose,
                "freq": medication.freq,
                "route": medication.route,
                "durationDays": medication.duration_days,
            }
            for medication in note.medications.all()
        ],
        "diagnoses": [
            {
                "id": diagnosis.pk,
                "code": diagnosis.code,
                "name": diagnosis.name,
                "source": diagnosis.source,
                "recordedAt": timezone.localtime(diagnosis.created_at).isoformat(),
            }
            for diagnosis in note.diagnoses.all()
        ],
        "allergies": [
            {
                "id": allergy.pk,
                "substance": allergy.substance,
                "reaction": allergy.reaction,
                "severity": allergy.severity,
                "notes": allergy.notes,
            }
            for allergy in note.allergies.all()
        ],
        "prescriptions": [
            {
                "id": prescription.pk,
                "itemType": prescription.item_type,
                "name": prescription.name,
                "dose": prescription.dose,
                "freq": prescription.freq,
                "days": prescription.days,
                "notes": prescription.notes,
            }
            for prescription in note.prescriptions.all()
        ],
        "vitals": _serialize_vitals(getattr(note, "vitals", None)),
        "anthropometrics": _serialize_anthro(getattr(note, "anthro", None)),
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
    serialized_notes = [_serialize_note(note) for note in notes[:5]]

    latest_note = notes[0] if notes else None

    documents = [_serialize_document(doc) for doc in patient.external_documents.all()[:5]]

    response: Dict[str, Any] = {
        "patient": _serialize_patient(patient),
        "notes": serialized_notes,
        "latestVitals": _serialize_vitals(getattr(latest_note, "vitals", None)) if latest_note else None,
        "latestAnthropometrics": _serialize_anthro(getattr(latest_note, "anthro", None)) if latest_note else None,
        "documents": documents,
    }

    return JsonResponse(response)

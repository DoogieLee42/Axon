from __future__ import annotations

from decimal import Decimal
from typing import Any, Dict, Optional

from django.utils import timezone

from .models import Anthropometrics, ClinicalNote, DiagnosisEntry, MedicationEntry, Prescription, Vitals


def _decimal_to_float(value: Decimal | None) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def serialize_vitals(vitals: Optional[Vitals]) -> Optional[Dict[str, Any]]:
    if not vitals:
        return None
    return {
        "systolic": vitals.systolic,
        "diastolic": vitals.diastolic,
        "heartRate": vitals.heart_rate,
        "respRate": vitals.resp_rate,
        "temperatureC": _decimal_to_float(vitals.temperature_c),
        "spo2": vitals.spo2,
        "painScore": vitals.pain_score,
    }


def serialize_anthropometrics(anthro: Optional[Anthropometrics]) -> Optional[Dict[str, Any]]:
    if not anthro:
        return None
    return {
        "heightCm": _decimal_to_float(anthro.height_cm),
        "weightKg": _decimal_to_float(anthro.weight_kg),
        "bmi": _decimal_to_float(anthro.bmi),
        "waistCm": _decimal_to_float(anthro.waist_cm),
    }


def _serialize_medication(entry: MedicationEntry) -> Dict[str, Any]:
    return {
        "id": entry.pk,
        "code": entry.code,
        "name": entry.name,
        "dose": entry.dose,
        "freq": entry.freq,
        "route": entry.route,
        "durationDays": entry.duration_days,
        "notes": entry.notes,
    }


def _serialize_diagnosis(entry: DiagnosisEntry) -> Dict[str, Any]:
    return {
        "id": entry.pk,
        "code": entry.code,
        "name": entry.name,
        "source": entry.source,
        "recordedAt": timezone.localtime(entry.created_at).isoformat(),
    }


def _serialize_prescription(entry: Prescription) -> Dict[str, Any]:
    return {
        "id": entry.pk,
        "itemType": entry.item_type,
        "code": entry.code,
        "name": entry.name,
        "qty": _decimal_to_float(entry.qty),
        "unit": entry.unit,
        "dose": entry.dose,
        "freq": entry.freq,
        "route": entry.route,
        "days": entry.days,
        "notes": entry.notes,
    }


def serialize_note(note: ClinicalNote) -> Dict[str, Any]:
    return {
        "id": note.pk,
        "visitDate": timezone.localtime(note.visit_date).isoformat(),
        "chiefComplaint": note.chief_complaint,
        "subjective": note.s_text,
        "objective": note.o_text,
        "assessment": note.a_text,
        "plan": note.p_text,
        "primaryIcd": note.primary_icd,
        "narrative": note.narrative,
        "socialHistory": note.social_history_text,
        "familyHistory": note.family_history_text,
        "medications": [_serialize_medication(med) for med in note.medications.all()],
        "diagnoses": [_serialize_diagnosis(diag) for diag in note.diagnoses.all()],
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
        "prescriptions": [_serialize_prescription(order) for order in note.prescriptions.all()],
        "vitals": serialize_vitals(getattr(note, "vitals", None)),
        "anthropometrics": serialize_anthropometrics(getattr(note, "anthro", None)),
    }

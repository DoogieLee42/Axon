"""
Translate EMR clinical notes and prescriptions into claim DTOs that can be
rendered to a SAM file. The collector reads from the main EMR models rather than
the standalone ETL demo models.
"""

from __future__ import annotations

import os
from collections import defaultdict
from datetime import date
from decimal import Decimal
from typing import Dict, Iterable, List, Tuple

from django.db import router
from django.db.models import Prefetch

from db.master_files.models import MasterItem
from db.medical_records.models import ClinicalNote, DiagnosisEntry, Prescription

from .claim_dto import Claim, ClaimLine

PROVIDER_ID = os.getenv("PROVIDER_ID", "11111111")

CATEGORY_BY_ITEM_TYPE = {
    "DRUG": "DRG",
    "PROC": "ACT",
    "TEST": "ACT",  # 검사 항목은 행위(수가) 카테고리로 정규화
}

LINE_TYPE_BY_ITEM_TYPE = {
    "DRUG": "DRUG",
    "PROC": "PROC",
    "TEST": "PROC",
}


def collect_claims(date_from: date | str, date_to: date | str) -> List[Claim]:
    qs = (
        ClinicalNote.objects.select_related("patient")
        .prefetch_related(
            "prescriptions",
            Prefetch("diagnoses", queryset=DiagnosisEntry.objects.order_by("-created_at")),
        )
        .filter(visit_date__date__gte=date_from, visit_date__date__lte=date_to)
        .order_by("visit_date", "id")
    )
    notes = list(qs)
    price_map = _build_price_map(notes)
    return [_note_to_claim(note, price_map) for note in notes]


def collect_claim_for_note(note_id: int) -> Claim | None:
    note = (
        ClinicalNote.objects.select_related("patient")
        .prefetch_related(
            "prescriptions",
            Prefetch("diagnoses", queryset=DiagnosisEntry.objects.order_by("-created_at")),
        )
        .filter(id=note_id)
        .first()
    )
    if not note:
        return None
    price_map = _build_price_map([note])
    return _note_to_claim(note, price_map)


def collect_claim_for_encounter(encounter_id: int) -> Claim | None:
    """
    Backwards-compatible shim: the old ETL demo used Encounter IDs.
    """
    return collect_claim_for_note(encounter_id)


def _build_price_map(notes: Iterable[ClinicalNote]) -> Dict[Tuple[str, str], MasterItem]:
    codes_by_category: Dict[str, set[str]] = defaultdict(set)
    for note in notes:
        for prescription in note.prescriptions.all():
            code = (prescription.code or "").strip()
            if not code:
                continue
            category = CATEGORY_BY_ITEM_TYPE.get(prescription.item_type, "ACT")
            codes_by_category[category].add(code)

    if not codes_by_category:
        return {}

    db_alias = router.db_for_read(MasterItem)
    price_map: Dict[Tuple[str, str], MasterItem] = {}

    for category, codes in codes_by_category.items():
        items = (
            MasterItem.objects.using(db_alias)
            .filter(category=category, code__in=list(codes))
            .only("code", "category", "price")
        )
        for item in items:
            price_map[(item.category, item.code)] = item
    return price_map


def _resolve_amount(prescription: Prescription, price_map: Dict[Tuple[str, str], MasterItem]) -> int | None:
    code = (prescription.code or "").strip()
    if not code:
        return None
    category = CATEGORY_BY_ITEM_TYPE.get(prescription.item_type, "ACT")
    master = price_map.get((category, code))
    if not master or master.price is None:
        return None

    unit_price = Decimal(master.price)

    qty = Decimal(prescription.qty or 0)
    if qty <= 0:
        qty = Decimal(1)

    total = unit_price * qty

    if prescription.item_type == "DRUG":
        days = Decimal(prescription.days or 0)
        if days <= 0:
            days = Decimal(1)
        total *= days

    return int(total)


def _note_to_claim(note: ClinicalNote, price_map: Dict[Tuple[str, str], MasterItem]) -> Claim:
    primary_dx = (note.primary_icd or "").strip()
    sub_dx: List[str] = []

    for diag in note.diagnoses.all():
        code = (diag.code or "").strip()
        if not code:
            continue
        if not primary_dx:
            primary_dx = code
            continue
        if code != primary_dx and code not in sub_dx:
            sub_dx.append(code)

    lines: List[ClaimLine] = []
    for prescription in note.prescriptions.all():
        code = (prescription.code or "").strip()
        if not code:
            continue
        line_type = LINE_TYPE_BY_ITEM_TYPE.get(prescription.item_type, "PROC")
        qty = float(prescription.qty or 0) or 1.0
        days = prescription.days if prescription.item_type == "DRUG" else None
        amount = _resolve_amount(prescription, price_map)
        lines.append(
            ClaimLine(
                line_type=line_type,
                code=code,
                qty=float(qty),
                days=days,
                amount=amount,
            )
        )

    return Claim(
        provider_id=PROVIDER_ID,
        patient_rid=note.patient.reg_no,
        visit_date=note.visit_date.date(),
        primary_dx=primary_dx,
        sub_dx=sub_dx,
        lines=lines,
    )

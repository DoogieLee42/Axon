import json
from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.db import transaction
from django.db.models import Q
from django.shortcuts import redirect, render

from db.master_files.models import MasterItem

from .forms import ClinicalNoteForm
from .models import ClinicalNote, Prescription

def prescriptions_list(request):
    t=request.GET.get('type','').upper()
    q=request.GET.get('q','').strip()
    qs=Prescription.objects.select_related('note','note__patient').all()
    if t in {'DRUG','TEST','PROC'}:
        qs=qs.filter(item_type=t)
    if q:
        qs=qs.filter(Q(name__icontains=q)|Q(code__icontains=q)|Q(note__patient__name__icontains=q)|Q(note__patient__reg_no__icontains=q))
    ctx={'results':qs.order_by('-id')[:300],'type':t,'q':q}
    return render(request,'medical_records/prescriptions.html',ctx)

def clinical_note_create(request):
    form=ClinicalNoteForm(request.POST or None)
    diagnoses=list(MasterItem.objects.using('master_files').filter(category='DX').order_by('code')[:500])
    recent_notes=ClinicalNote.objects.select_related('patient').order_by('-visit_date')[:10]

    if request.method=='POST' and form.is_valid():
        with transaction.atomic():
            note=form.save()
            _sync_prescriptions(note, form.cleaned_data.get('claim_payload'))
        messages.success(request,'임상 노트가 저장되었습니다.')
        return redirect('clinical_note_create')

    ctx={
        'form':form,
        'diagnoses':diagnoses,
        'recent_notes':recent_notes,
    }
    return render(request,'medical_records/note_form.html',ctx)

def _sync_prescriptions(note: ClinicalNote, payload: str | None) -> None:
    try:
        items = json.loads(payload) if payload else []
    except (json.JSONDecodeError, TypeError):
        items = []

    if not isinstance(items, list):
        items = []

    note.prescriptions.all().delete()
    bulk = []

    for entry in items:
        if not isinstance(entry, dict):
            continue
        item_type = (entry.get('type') or 'PROC').upper()
        if item_type not in {'DRUG','PROC','TEST'}:
            item_type = 'PROC'

        code = (entry.get('code') or '').strip()
        name = (entry.get('name') or '').strip()
        if not name:
            continue

        qty = _to_decimal(entry.get('qty'))
        unit = (entry.get('unit') or '').strip()
        dose = (entry.get('dose') or '').strip()
        freq = (entry.get('freq') or '').strip()
        route = (entry.get('route') or '').strip()
        days = _to_int(entry.get('days'))
        notes = (entry.get('notes') or '').strip()

        bulk.append(Prescription(
            note=note,
            item_type=item_type,
            code=code,
            name=name,
            qty=qty,
            unit=unit,
            dose=dose,
            freq=freq,
            route=route,
            days=days,
            specimen=(entry.get('specimen') or '').strip(),
            priority=(entry.get('priority') or '').strip(),
            site=(entry.get('site') or '').strip(),
            anesthesia=(entry.get('anesthesia') or '').strip(),
            notes=notes,
        ))

    if bulk:
        Prescription.objects.bulk_create(bulk)

def _to_decimal(value) -> Decimal:
    if value in (None, '', []):
        return Decimal('0')
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return Decimal('0')

def _to_int(value) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0

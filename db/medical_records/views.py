from django.contrib import messages
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
        form.save()
        messages.success(request,'임상 노트가 저장되었습니다.')
        return redirect('clinical_note_create')

    ctx={
        'form':form,
        'diagnoses':diagnoses,
        'recent_notes':recent_notes,
    }
    return render(request,'medical_records/note_form.html',ctx)

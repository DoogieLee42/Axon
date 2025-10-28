from django.shortcuts import render
from django.db.models import Q
from .models import Patient

def advanced_search(request):
    q=request.GET.get('q','').strip()
    gender=request.GET.get('gender','').strip()
    dob_from=request.GET.get('dob_from','').strip()
    dob_to=request.GET.get('dob_to','').strip()
    qs=Patient.objects.all()
    if q:
        qs=qs.filter(Q(name__icontains=q)|Q(reg_no__icontains=q)|Q(rrn__icontains=q)|Q(phone__icontains=q)|Q(address__icontains=q))
    if gender:
        qs=qs.filter(gender=gender)
    if dob_from:
        qs=qs.filter(birth_date__gte=dob_from)
    if dob_to:
        qs=qs.filter(birth_date__lte=dob_to)
    ctx={'results':qs.order_by('-created_at')[:200],'q':q,'gender':gender,'dob_from':dob_from,'dob_to':dob_to}
    return render(request,'patients/search.html',ctx)

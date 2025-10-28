

# Create your views here.
from django.shortcuts import render

def upload_master_page(request):
    return render(request, 'master/upload.html')

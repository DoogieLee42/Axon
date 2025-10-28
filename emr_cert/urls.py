from django.contrib import admin
from django.urls import include, path
from db.patients.views import advanced_search
from db.medical_records.views import clinical_note_create, prescriptions_list

urlpatterns=[
    path('admin/',admin.site.urls),
    path('patients/search/',advanced_search,name='patients_advanced_search'),
    path('orders/',prescriptions_list,name='prescriptions_list'),
    path('clinical-notes/new/',clinical_note_create,name='clinical_note_create'),
    path('master/',include('db.master_files.urls')),
]

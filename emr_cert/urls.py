from django.contrib import admin
from django.urls import include, path

from db.medical_records.views import clinical_note_create, prescriptions_list
from db.patients.views import advanced_search
from db.patients.api import patient_collection, patient_detail

urlpatterns = [
    path("admin/", admin.site.urls),
    path("patients/search/", advanced_search, name="patients_advanced_search"),
    path("orders/", prescriptions_list, name="prescriptions_list"),
    path("clinical-notes/new/", clinical_note_create, name="clinical_note_create"),
    path("master/", include("db.master_files.urls")),
    path(
        "api/master/",
        include(("db.master_files.api_urls", "master_files_api"), namespace="master_files_api"),
    ),
    path("api/patients/", patient_collection, name="patient_collection"),
    path("api/patients/<int:pk>/", patient_detail, name="patient_detail"),
]

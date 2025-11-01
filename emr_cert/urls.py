from django.contrib import admin
from django.urls import include, path, re_path

from db.medical_records.views import clinical_note_create, prescriptions_list
from db.medical_records.api import create_clinical_note
from db.patients.views import advanced_search
from db.patients.api import patient_collection, patient_detail
from .views import frontend_app

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
    path("api/patients/<int:pk>/notes/", create_clinical_note, name="patient_note_create"),
    path("api/patients/<int:pk>/", patient_detail, name="patient_detail"),
]

# React SPA fallback routes
urlpatterns += [
    path("", frontend_app, name="frontend_index"),
    path("patients", frontend_app, name="frontend_patients_root"),
    path("patients/", frontend_app, name="frontend_patients_trailing"),
    re_path(r"^patients/(?P<path>.*)$", frontend_app, name="frontend_patients_catchall"),
]

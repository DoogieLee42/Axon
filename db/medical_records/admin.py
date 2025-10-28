
from django.contrib import admin
from import_export.admin import ExportActionMixin
from simple_history.admin import SimpleHistoryAdmin
from .models import (
    ClinicalNote, Prescription,
    MedicationEntry, AllergyEntry,
    Vitals, Anthropometrics, SocialHistory, FamilyHistoryEntry
)

class MedicationInline(admin.TabularInline):
    model = MedicationEntry
    extra = 1

class AllergyInline(admin.TabularInline):
    model = AllergyEntry
    extra = 1

class FamilyHistoryInline(admin.TabularInline):
    model = FamilyHistoryEntry
    extra = 1

class VitalsInline(admin.StackedInline):
    model = Vitals
    extra = 0
    max_num = 1

class AnthropometricsInline(admin.StackedInline):
    model = Anthropometrics
    extra = 0
    max_num = 1

class SocialHistoryInline(admin.StackedInline):
    model = SocialHistory
    extra = 0
    max_num = 1

class PrescriptionInline(admin.TabularInline):
    model = Prescription
    extra = 1

@admin.register(ClinicalNote)
class ClinicalNoteAdmin(ExportActionMixin, SimpleHistoryAdmin):
    list_display = ("patient","visit_date","chief_complaint","primary_icd")
    search_fields = ("patient__name","patient__reg_no","primary_icd","chief_complaint","a_text","p_text")
    list_filter = ("visit_date",)
    date_hierarchy = "visit_date"
    inlines = [
        VitalsInline, AnthropometricsInline, SocialHistoryInline,
        MedicationInline, AllergyInline, FamilyHistoryInline, PrescriptionInline
    ]

@admin.register(Prescription)
class PrescriptionAdmin(ExportActionMixin, SimpleHistoryAdmin):
    list_display = ("note","item_type","name","code","qty","unit","dose","freq","route","days","specimen","priority","site","anesthesia")
    search_fields = ("name","code","note__patient__name","note__patient__reg_no")
    list_filter = ("item_type","route","priority")

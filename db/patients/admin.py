from collections import defaultdict

from django import forms
from django.contrib import admin, messages
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect
from django.urls import path, reverse

from import_export.admin import ExportActionMixin
from simple_history.admin import SimpleHistoryAdmin
from auditlog.registry import auditlog

from db.master_files.models import MasterItem
from db.medical_records.forms import ClinicalNoteForm
from db.medical_records.models import (
    ClinicalNote,
    Prescription,
    DiagnosisEntry,
    AllergyEntry,
    Vitals,
    Anthropometrics,
)

from .forms import (
    PrescriptionForm,
    DiagnosisAssignForm,
    DiagnosisEntryForm,
    AllergyEntryForm,
    VitalsForm,
    AnthropometricsForm,
    ExternalDocumentForm,
    ExternalResultForm,
)
from .models import (
    Patient,
    PatientRegistration,
    ExternalDocument,
    ExternalResult,
)


class PatientRegistrationInline(admin.TabularInline):
    model = PatientRegistration
    extra = 0
    can_delete = False
    readonly_fields = ("reg_no", "issued_at")
    ordering = ("-issued_at",)

    def has_add_permission(self, request, obj=None):  # pragma: no cover
        return False

    def has_change_permission(self, request, obj=None):  # pragma: no cover
        return False


@admin.register(Patient)
class PatientAdmin(ExportActionMixin, SimpleHistoryAdmin):
    list_display = ("reg_no", "name", "gender", "birth_date", "phone", "created_at")
    list_display_links = ("reg_no", "name")
    search_fields = ("reg_no", "name", "rrn", "phone", "address")
    list_filter = ("gender", "created_at")
    date_hierarchy = "created_at"
    readonly_fields = ("reg_no",)
    change_form_template = "admin/patients/patient/change_form.html"
    inlines = [PatientRegistrationInline]

    def get_urls(self):  # pragma: no cover
        urls = super().get_urls()
        custom = [
            path(
                "<path:object_id>/duplicate/",
                self.admin_site.admin_view(self.duplicate_view),
                name="patients_patient_duplicate",
            )
        ]
        return custom + urls

    def duplicate_view(self, request, object_id):  # pragma: no cover
        patient = self.get_object(request, object_id)
        if not patient:
            messages.error(request, "선택한 환자를 찾을 수 없습니다.")
            return HttpResponseRedirect(reverse("admin:patients_patient_changelist"))
        if not self.has_add_permission(request):
            raise PermissionDenied
        if request.method != "POST":
            return HttpResponseRedirect(reverse("admin:patients_patient_change", args=[object_id]))

        old_reg = patient.reg_no
        new_reg_no = patient.reissue_registration_number()
        messages.success(request, f"등록번호가 {old_reg} → {new_reg_no} 로 재발급되었습니다.")
        return HttpResponseRedirect(reverse("admin:patients_patient_change", args=[object_id]))

    def changeform_view(self, request, object_id=None, form_url="", extra_context=None):  # pragma: no cover
        extra_context = extra_context or {}
        patient = self.get_object(request, object_id) if object_id else None

        if patient and request.method == "POST" and request.POST.get("_action"):
            response = self._handle_custom_post(request, patient, extra_context)
            if response:
                return response

        if patient:
            extra_context = self._build_patient_context(request, patient, extra_context)

        return super().changeform_view(request, object_id, form_url, extra_context)

    # ------------------------------------------------------------------ custom actions

    def _handle_custom_post(self, request, patient, extra_context):
        action = request.POST.get("_action")
        handlers = {
            "add_clinical_note": self._handle_add_clinical_note,
            "update_clinical_note": self._handle_update_clinical_note,
            "add_prescription": self._handle_add_prescription,
            "update_prescription": self._handle_update_prescription,
            "add_diagnosis": self._handle_add_diagnosis,
            "update_diagnosis": self._handle_update_diagnosis,
            "add_allergy": self._handle_add_allergy,
            "update_allergy": self._handle_update_allergy,
            "add_vitals": self._handle_add_vitals,
            "update_vitals": self._handle_update_vitals,
            "add_anthro": self._handle_add_anthro,
            "update_anthro": self._handle_update_anthro,
            "add_external_document": self._handle_add_external_document,
            "update_external_document": self._handle_update_external_document,
            "add_external_result": self._handle_add_external_result,
            "update_external_result": self._handle_update_external_result,
        }
        handler = handlers.get(action)
        if handler:
            return handler(request, patient, extra_context)
        return None

    def _handle_add_clinical_note(self, request, patient, extra_context):
        form = ClinicalNoteForm(request.POST, patient=patient, prefix="new_note")
        if form.is_valid():
            note = form.save(commit=False)
            note.patient = patient
            note.save()
            messages.success(request, "임상 노트가 추가되었습니다.")
            return HttpResponseRedirect(request.path)
        extra_context["new_note_form"] = form
        return None

    def _handle_update_clinical_note(self, request, patient, extra_context):
        note_id = request.POST.get("note_id")
        note = ClinicalNote.objects.filter(pk=note_id, patient=patient).first()
        if not note:
            messages.error(request, "임상 노트를 찾을 수 없습니다.")
            return HttpResponseRedirect(request.path)
        form = ClinicalNoteForm(request.POST, instance=note, patient=patient, prefix=f"note_{note.pk}")
        if form.is_valid():
            form.save()
            messages.success(request, "임상 노트가 수정되었습니다.")
            return HttpResponseRedirect(request.path)
        extra_context.setdefault("note_update_errors", {})[note.pk] = form
        return None

    def _handle_add_prescription(self, request, patient, extra_context):
        form = PrescriptionForm(request.POST, patient=patient, prefix="new_prescription")
        if form.is_valid():
            prescription = form.save(commit=False)
            if prescription.note.patient_id != patient.pk:
                form.add_error("note", "선택한 임상 노트가 환자와 일치하지 않습니다.")
            else:
                prescription.save()
                messages.success(request, "처방 정보가 추가되었습니다.")
                return HttpResponseRedirect(request.path)
        extra_context["new_prescription_form"] = form
        return None

    def _handle_update_prescription(self, request, patient, extra_context):
        presc_id = request.POST.get("prescription_id")
        prescription = Prescription.objects.select_related("note__patient").filter(pk=presc_id).first()
        if not prescription or prescription.note.patient_id != patient.pk:
            messages.error(request, "처방 정보를 찾을 수 없습니다.")
            return HttpResponseRedirect(request.path)
        form = PrescriptionForm(
            request.POST,
            instance=prescription,
            patient=patient,
            prefix=f"presc_{prescription.pk}",
        )
        if form.is_valid():
            updated = form.save(commit=False)
            if updated.note.patient_id != patient.pk:
                form.add_error("note", "선택한 임상 노트가 환자와 일치하지 않습니다.")
            else:
                updated.save()
                messages.success(request, "처방 정보가 수정되었습니다.")
                return HttpResponseRedirect(request.path)
        extra_context.setdefault("prescription_update_errors", {})[prescription.pk] = form
        return None

    def _handle_add_diagnosis(self, request, patient, extra_context):
        form = DiagnosisAssignForm(request.POST, patient=patient, prefix="new_diag")
        if form.is_valid():
            note = form.cleaned_data["note"]
            try:
                code, name = form.resolve_master()
            except forms.ValidationError as exc:  # type: ignore[attr-defined]
                form.add_error("code", exc)
                extra_context["diagnosis_add_form"] = form
                return None
            DiagnosisEntry.objects.update_or_create(
                note=note,
                code=code,
                defaults={"name": name, "source": "manual"},
            )
            if not note.primary_icd:
                note.primary_icd = code
                note.save(update_fields=["primary_icd"])
            messages.success(request, "진단 정보가 추가되었습니다.")
            return HttpResponseRedirect(request.path)
        extra_context["diagnosis_add_form"] = form
        return None

    def _handle_update_diagnosis(self, request, patient, extra_context):
        diag_id = request.POST.get("diagnosis_id")
        entry = DiagnosisEntry.objects.select_related("note__patient").filter(pk=diag_id).first()
        if not entry or entry.note.patient_id != patient.pk:
            messages.error(request, "진단 정보를 찾을 수 없습니다.")
            return HttpResponseRedirect(request.path)
        form = DiagnosisEntryForm(request.POST, instance=entry, prefix=f"diag_{entry.pk}")
        if form.is_valid():
            code = form.cleaned_data["code"]
            name = form.cleaned_data["name"]
            master = MasterItem.objects.using("master_files").filter(category="DX", code=code).first()
            if master:
                name = master.name
            elif not name:
                form.add_error("code", "진단명을 입력하거나 코드 목록에서 선택하세요.")
                extra_context.setdefault("diagnosis_update_errors", {})[entry.pk] = form
                return None
            entry.code = code
            entry.name = name
            entry.save()
            messages.success(request, "진단 정보가 수정되었습니다.")
            return HttpResponseRedirect(request.path)
        extra_context.setdefault("diagnosis_update_errors", {})[entry.pk] = form
        return None

    def _handle_add_allergy(self, request, patient, extra_context):
        form = AllergyEntryForm(request.POST, patient=patient, prefix="new_allergy")
        if form.is_valid():
            allergy = form.save(commit=False)
            if allergy.note.patient_id != patient.pk:
                form.add_error("note", "선택한 임상 노트가 환자와 일치하지 않습니다.")
            else:
                allergy.save()
                messages.success(request, "알레르기 정보가 추가되었습니다.")
                return HttpResponseRedirect(request.path)
        extra_context["allergy_add_form"] = form
        return None

    def _handle_update_allergy(self, request, patient, extra_context):
        allergy_id = request.POST.get("allergy_id")
        allergy = AllergyEntry.objects.select_related("note__patient").filter(pk=allergy_id).first()
        if not allergy or allergy.note.patient_id != patient.pk:
            messages.error(request, "알레르기 정보를 찾을 수 없습니다.")
            return HttpResponseRedirect(request.path)
        form = AllergyEntryForm(
            request.POST,
            instance=allergy,
            patient=patient,
            prefix=f"allergy_{allergy.pk}",
        )
        if form.is_valid():
            updated = form.save(commit=False)
            if updated.note.patient_id != patient.pk:
                form.add_error("note", "선택한 임상 노트가 환자와 일치하지 않습니다.")
            else:
                updated.save()
                messages.success(request, "알레르기 정보가 수정되었습니다.")
                return HttpResponseRedirect(request.path)
        extra_context.setdefault("allergy_update_errors", {})[allergy.pk] = form
        return None

    def _handle_add_vitals(self, request, patient, extra_context):
        form = VitalsForm(request.POST, patient=patient, prefix="new_vitals")
        if form.is_valid():
            note = form.cleaned_data["note"]
            vitals, created = Vitals.objects.get_or_create(note=note)
            for field in ["systolic", "diastolic", "heart_rate", "resp_rate", "temperature_c"]:
                vitals.__setattr__(field, form.cleaned_data[field])
            vitals.save()
            messages.success(request, "활력징후가 저장되었습니다." if created else "활력징후가 수정되었습니다.")
            return HttpResponseRedirect(request.path)
        extra_context["vitals_add_form"] = form
        return None

    def _handle_update_vitals(self, request, patient, extra_context):
        note_id = request.POST.get("note_id")
        note = ClinicalNote.objects.filter(pk=note_id, patient=patient).first()
        if not note:
            messages.error(request, "임상 노트를 찾을 수 없습니다.")
            return HttpResponseRedirect(request.path)
        vitals = getattr(note, "vitals", None)
        form = VitalsForm(
            request.POST,
            instance=vitals,
            patient=patient,
            prefix=f"vitals_{note.pk}",
        )
        if form.is_valid():
            vitals = form.save(commit=False)
            vitals.note = note
            vitals.save()
            messages.success(request, "활력징후가 수정되었습니다.")
            return HttpResponseRedirect(request.path)
        extra_context.setdefault("vitals_update_errors", {})[note.pk] = form
        return None

    def _handle_add_anthro(self, request, patient, extra_context):
        form = AnthropometricsForm(request.POST, patient=patient, prefix="new_anthro")
        if form.is_valid():
            note = form.cleaned_data["note"]
            anthro, created = Anthropometrics.objects.get_or_create(note=note)
            for field in ["height_cm", "weight_kg"]:
                anthro.__setattr__(field, form.cleaned_data[field])
            anthro.save()
            messages.success(request, "신체계측이 저장되었습니다." if created else "신체계측이 수정되었습니다.")
            return HttpResponseRedirect(request.path)
        extra_context["anthro_add_form"] = form
        return None

    def _handle_update_anthro(self, request, patient, extra_context):
        note_id = request.POST.get("note_id")
        note = ClinicalNote.objects.filter(pk=note_id, patient=patient).first()
        if not note:
            messages.error(request, "임상 노트를 찾을 수 없습니다.")
            return HttpResponseRedirect(request.path)
        anthro = getattr(note, "anthro", None)
        form = AnthropometricsForm(
            request.POST,
            instance=anthro,
            patient=patient,
            prefix=f"anthro_{note.pk}",
        )
        if form.is_valid():
            anthro = form.save(commit=False)
            anthro.note = note
            anthro.save()
            messages.success(request, "신체계측이 수정되었습니다.")
            return HttpResponseRedirect(request.path)
        extra_context.setdefault("anthro_update_errors", {})[note.pk] = form
        return None

    def _handle_add_external_document(self, request, patient, extra_context):
        form = ExternalDocumentForm(request.POST, prefix="new_extdoc")
        if form.is_valid():
            doc = form.save(commit=False)
            doc.patient = patient
            doc.save()
            messages.success(request, "외부 문서가 추가되었습니다.")
            return HttpResponseRedirect(request.path)
        extra_context["external_document_form"] = form
        return None

    def _handle_update_external_document(self, request, patient, extra_context):
        doc_id = request.POST.get("document_id")
        document = ExternalDocument.objects.filter(pk=doc_id, patient=patient).first()
        if not document:
            messages.error(request, "외부 문서를 찾을 수 없습니다.")
            return HttpResponseRedirect(request.path)
        form = ExternalDocumentForm(request.POST, instance=document, prefix=f"extdoc_{document.pk}")
        if form.is_valid():
            form.save()
            messages.success(request, "외부 문서가 수정되었습니다.")
            return HttpResponseRedirect(request.path)
        extra_context.setdefault("external_document_update_errors", {})[document.pk] = form


    def _handle_add_external_result(self, request, patient, extra_context):
        form = ExternalResultForm(request.POST, prefix="new_extresult")
        if form.is_valid():
            result = form.save(commit=False)
            result.patient = patient
            result.save()
            messages.success(request, "외부 검사결과가 추가되었습니다.")
            return HttpResponseRedirect(request.path)
        extra_context["external_result_form"] = form
        return None

    def _handle_update_external_result(self, request, patient, extra_context):
        result_id = request.POST.get("result_id")
        result = ExternalResult.objects.filter(pk=result_id, patient=patient).first()
        if not result:
            messages.error(request, "외부 검사결과를 찾을 수 없습니다.")
            return HttpResponseRedirect(request.path)
        form = ExternalResultForm(request.POST, instance=result, prefix=f"extresult_{result.pk}")
        if form.is_valid():
            form.save()
            messages.success(request, "외부 검사결과가 수정되었습니다.")
            return HttpResponseRedirect(request.path)
        extra_context.setdefault("external_result_update_errors", {})[result.pk] = form
        return None

    # ------------------------------------------------------------------ context builder

    def _build_patient_context(self, request, patient, extra_context):
        extra_context.setdefault(
            "duplicate_button_url",
            reverse("admin:patients_patient_duplicate", args=[patient.pk]),
        )

        notes = list(
            ClinicalNote.objects.filter(patient=patient)
            .select_related("vitals", "anthro", "social")
            .prefetch_related(
                "prescriptions",
                "medications",
                "allergies",
                "family_history",
                "diagnoses",
            )
            .order_by("-visit_date")
        )

        diagnosis_master_items = list(
            MasterItem.objects.using("master_files").filter(category="DX").order_by("code")[:500]
        )

        new_note_form = extra_context.pop("new_note_form", None) or ClinicalNoteForm(
            patient=patient, prefix="new_note"
        )
        new_prescription_form = extra_context.pop("new_prescription_form", None) or PrescriptionForm(
            patient=patient, prefix="new_prescription"
        )
        diagnosis_add_form = extra_context.pop("diagnosis_add_form", None) or DiagnosisAssignForm(
            patient=patient, prefix="new_diag"
        )
        allergy_add_form = extra_context.pop("allergy_add_form", None) or AllergyEntryForm(
            patient=patient, prefix="new_allergy"
        )
        vitals_add_form = extra_context.pop("vitals_add_form", None) or VitalsForm(
            patient=patient, prefix="new_vitals"
        )
        anthro_add_form = extra_context.pop("anthro_add_form", None) or AnthropometricsForm(
            patient=patient, prefix="new_anthro"
        )
        external_document_form = extra_context.pop("external_document_form", None) or ExternalDocumentForm(
            prefix="new_extdoc"
        )
        external_result_form = extra_context.pop("external_result_form", None) or ExternalResultForm(
            prefix="new_extresult"
        )

        note_update_errors = extra_context.pop("note_update_errors", {})
        prescription_update_errors = extra_context.pop("prescription_update_errors", {})
        diagnosis_update_errors = extra_context.pop("diagnosis_update_errors", {})
        allergy_update_errors = extra_context.pop("allergy_update_errors", {})
        vitals_update_errors = extra_context.pop("vitals_update_errors", {})
        anthro_update_errors = extra_context.pop("anthro_update_errors", {})
        external_document_update_errors = extra_context.pop("external_document_update_errors", {})
        external_result_update_errors = extra_context.pop("external_result_update_errors", {})

        note_update_forms = []
        prescription_timeline = []
        for note in notes:
            note_form = note_update_errors.get(note.pk) or ClinicalNoteForm(
                patient=patient, instance=note, prefix=f"note_{note.pk}"
            )
            bundle = {"note": note, "form": note_form}

            med_groups = defaultdict(list)
            for pres in note.prescriptions.all():
                pres_form = prescription_update_errors.get(pres.pk) or PrescriptionForm(
                    patient=patient, instance=pres, prefix=f"presc_{pres.pk}"
                )
                key = pres.name or pres.code or pres.get_item_type_display()
                med_groups[key].append({"object": pres, "form": pres_form})
            prescription_timeline.append(
                {
                    "note": note,
                    "med_groups": [
                        {"name": med_name, "items": items}
                        for med_name, items in sorted(med_groups.items(), key=lambda kv: kv[0])
                    ],
                }
            )

            diagnosis_entries = []
            for diag in note.diagnoses.all():
                form = diagnosis_update_errors.get(diag.pk) or DiagnosisEntryForm(
                    instance=diag, prefix=f"diag_{diag.pk}"
                )
                diagnosis_entries.append({"object": diag, "form": form})

            allergy_entries = []
            for allergy in note.allergies.all():
                form = allergy_update_errors.get(allergy.pk) or AllergyEntryForm(
                    instance=allergy, patient=patient, prefix=f"allergy_{allergy.pk}"
                )
                allergy_entries.append({"object": allergy, "form": form})

            vitals = getattr(note, "vitals", None)
            vitals_form = vitals_update_errors.get(note.pk) or VitalsForm(
                instance=vitals,
                patient=patient,
                prefix=f"vitals_{note.pk}",
            )
            vitals_form.fields['note'].widget = forms.HiddenInput()
            vitals_form.fields['note'].initial = note.pk

            anthro = getattr(note, "anthro", None)
            anthro_form = anthro_update_errors.get(note.pk) or AnthropometricsForm(
                instance=anthro,
                patient=patient,
                prefix=f"anthro_{note.pk}",
            )
            anthro_form.fields['note'].widget = forms.HiddenInput()
            anthro_form.fields['note'].initial = note.pk

            bundle.update(
                {
                    "diagnoses": diagnosis_entries,
                    "allergies": allergy_entries,
                    "vitals": vitals,
                    "anthro": anthro,
                    "vitals_form": vitals_form,
                    "anthro_form": anthro_form,
                }
            )
            note_update_forms.append(bundle)

        external_doc_entries = []
        for doc in ExternalDocument.objects.filter(patient=patient).order_by("-recorded_at", "-created_at", "-pk"):
            form = external_document_update_errors.get(doc.pk) or ExternalDocumentForm(
                instance=doc, prefix=f"extdoc_{doc.pk}"
            )
            external_doc_entries.append({"object": doc, "form": form})

        external_result_entries = []
        for res in ExternalResult.objects.filter(patient=patient).order_by("-recorded_at", "-created_at", "-pk"):
            form = external_result_update_errors.get(res.pk) or ExternalResultForm(
                instance=res, prefix=f"extresult_{res.pk}"
            )
            external_result_entries.append({"object": res, "form": form})

        extra_context.update(
            {
                "patient_summary": {
                    "name": patient.name,
                    "reg_no": patient.reg_no,
                    "rrn": patient.rrn,
                    "gender": patient.get_gender_display(),
                    "birth_date": patient.birth_date,
                    "created_at": patient.created_at,
                    "phone": patient.phone,
                    "address": patient.address,
                },
                "diagnosis_master_items": diagnosis_master_items,
                "new_note_form": new_note_form,
                "note_update_forms": note_update_forms,
                "new_prescription_form": new_prescription_form,
                "patient_prescription_timeline": prescription_timeline,
                "diagnosis_add_form": diagnosis_add_form,
                "allergy_add_form": allergy_add_form,
                "new_vitals_form": vitals_add_form,
                "new_anthro_form": anthro_add_form,
                "external_document_form": external_document_form,
                "external_document_entries": external_doc_entries,
                "external_result_form": external_result_form,
                "external_result_entries": external_result_entries,
                "patient_registration_history": list(
                    patient.registrations.order_by("-issued_at").values("reg_no", "issued_at")
                ),
            }
        )
        return extra_context

auditlog.register(Patient)

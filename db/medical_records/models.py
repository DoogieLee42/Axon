from django.db import models
from django.utils import timezone
from simple_history.models import HistoricalRecords
from db.patients.models import Patient

class ClinicalNote(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="clinical_notes")
    visit_date = models.DateTimeField("내원일시", default=timezone.now)
    chief_complaint = models.CharField("주증상", max_length=200, blank=True)
    s_text = models.TextField("S", blank=True)
    o_text = models.TextField("O", blank=True)
    a_text = models.TextField("A(진단/평가)", blank=True)
    p_text = models.TextField("P(계획)", blank=True)
    primary_icd = models.CharField("KCD/ICD 기본진단코드", max_length=16, blank=True)
    narrative = models.TextField("임상서술", blank=True)
    social_history_text = models.TextField("사회력 요약", blank=True)
    family_history_text = models.TextField("가족력 요약", blank=True)
    history = HistoricalRecords()

    class Meta:
        indexes = [models.Index(fields=["visit_date"]), models.Index(fields=["primary_icd"])]

    def __str__(self): return f"{self.patient.name} - {self.visit_date:%Y-%m-%d %H:%M}"

class MedicationEntry(models.Model):
    note = models.ForeignKey(ClinicalNote, on_delete=models.CASCADE, related_name="medications")
    code = models.CharField("약물코드", max_length=32, blank=True)
    name = models.CharField("약물명", max_length=100)
    dose = models.CharField("1회용량", max_length=50, blank=True)
    freq = models.CharField("1일횟수", max_length=50, blank=True)
    route = models.CharField("경로", max_length=50, blank=True)
    duration_days = models.PositiveIntegerField("기간(일)", default=0)
    notes = models.CharField("비고", max_length=200, blank=True)
    history = HistoricalRecords()

class AllergyEntry(models.Model):
    SEVERITY = [("mild","경증"),("mod","중등도"),("sev","중증")]
    note = models.ForeignKey(ClinicalNote, on_delete=models.CASCADE, related_name="allergies")
    substance = models.CharField("물질/약물", max_length=100)
    reaction = models.CharField("반응", max_length=200, blank=True)
    severity = models.CharField("중증도", max_length=10, choices=SEVERITY, blank=True)
    notes = models.CharField("비고", max_length=200, blank=True)
    history = HistoricalRecords()

class DiagnosisEntry(models.Model):
    note = models.ForeignKey(ClinicalNote, on_delete=models.CASCADE, related_name="diagnoses")
    code = models.CharField("진단코드", max_length=32)
    name = models.CharField("진단명", max_length=255)
    source = models.CharField("출처", max_length=32, default="primary", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at", "-pk"]
        indexes = [
            models.Index(fields=["note", "code"]),
            models.Index(fields=["code"]),
        ]
        unique_together = [("note", "code", "source")]
        verbose_name = "임상 진단"
        verbose_name_plural = "임상 진단"

    def __str__(self):
        return f"{self.code} - {self.name}"

class Vitals(models.Model):
    note = models.OneToOneField(ClinicalNote, on_delete=models.CASCADE, related_name="vitals")
    systolic = models.PositiveIntegerField("수축기 혈압(mmHg)", null=True, blank=True)
    diastolic = models.PositiveIntegerField("이완기 혈압(mmHg)", null=True, blank=True)
    heart_rate = models.PositiveIntegerField("맥박(bpm)", null=True, blank=True)
    resp_rate = models.PositiveIntegerField("호흡수(/분)", null=True, blank=True)
    temperature_c = models.DecimalField("체온(℃)", max_digits=4, decimal_places=1, null=True, blank=True)
    spo2 = models.PositiveIntegerField("산소포화도(%)", null=True, blank=True)
    pain_score = models.PositiveIntegerField("통증점수(0-10)", null=True, blank=True)
    history = HistoricalRecords()

class Anthropometrics(models.Model):
    note = models.OneToOneField(ClinicalNote, on_delete=models.CASCADE, related_name="anthro")
    height_cm = models.DecimalField("신장(cm)", max_digits=5, decimal_places=2, null=True, blank=True)
    weight_kg = models.DecimalField("체중(kg)", max_digits=5, decimal_places=2, null=True, blank=True)
    bmi = models.DecimalField("BMI", max_digits=4, decimal_places=1, null=True, blank=True, editable=False)
    waist_cm = models.DecimalField("허리둘레(cm)", max_digits=5, decimal_places=1, null=True, blank=True)
    history = HistoricalRecords()

    def save(self, *args, **kwargs):
        try:
            if self.height_cm and self.weight_kg and float(self.height_cm) > 0:
                h_m = float(self.height_cm)/100.0
                self.bmi = round(float(self.weight_kg)/(h_m*h_m), 1)
        except Exception:
            pass
        super().save(*args, **kwargs)

class SocialHistory(models.Model):
    SMOKING = [("never","비흡연"),("former","과거흡연"),("current","현재흡연")]
    EXERCISE = [("none","거의안함"),("light","가볍게"),("moderate","중등도"),("vigorous","격렬")]
    note = models.OneToOneField(ClinicalNote, on_delete=models.CASCADE, related_name="social")
    smoking_status = models.CharField("흡연", max_length=10, choices=SMOKING, blank=True)
    alcohol_per_week = models.DecimalField("음주(잔/주)", max_digits=4, decimal_places=1, null=True, blank=True)
    occupation = models.CharField("직업", max_length=100, blank=True)
    exercise_level = models.CharField("운동", max_length=10, choices=EXERCISE, blank=True)
    notes = models.CharField("비고", max_length=200, blank=True)
    history = HistoricalRecords()

class FamilyHistoryEntry(models.Model):
    REL = [("parent","부모"),("sibling","형제자매"),("child","자녀"),("grandparent","조부모"),("other","기타")]
    note = models.ForeignKey(ClinicalNote, on_delete=models.CASCADE, related_name="family_history")
    relative = models.CharField("관계", max_length=20, choices=REL)
    condition = models.CharField("질환/상태", max_length=100)
    age_at_dx = models.PositiveIntegerField("진단나이", null=True, blank=True)
    notes = models.CharField("비고", max_length=200, blank=True)
    history = HistoricalRecords()

class Prescription(models.Model):
    ITEM_TYPES = [("DRUG","약물 처방"),("TEST","검사 처방"),("PROC","처치/수술/기타")]
    note = models.ForeignKey(ClinicalNote, on_delete=models.CASCADE, related_name="prescriptions")
    item_type = models.CharField("유형", max_length=10, choices=ITEM_TYPES)
    code = models.CharField("표준코드", max_length=32, blank=True)
    name = models.CharField("명칭", max_length=100)
    qty = models.DecimalField("총량", max_digits=10, decimal_places=2, default=0)
    unit = models.CharField("단위", max_length=20, blank=True)
    dose = models.CharField("1회용량", max_length=50, blank=True)
    freq = models.CharField("1일횟수", max_length=50, blank=True)
    route = models.CharField("투여경로", max_length=50, blank=True)
    days = models.PositiveIntegerField("일수", default=0)
    specimen = models.CharField("검체", max_length=50, blank=True)
    priority = models.CharField("우선순위", max_length=20, blank=True)
    site = models.CharField("시술부위", max_length=50, blank=True)
    anesthesia = models.CharField("마취", max_length=50, blank=True)
    notes = models.CharField("특기사항", max_length=200, blank=True)
    history = HistoricalRecords()

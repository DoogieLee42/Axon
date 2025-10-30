from django.db import models

class Patient(models.Model):
    rid = models.CharField(max_length=32, unique=True)
    name = models.CharField(max_length=64)
    rrn_masked = models.CharField(max_length=20, blank=True)
    sex = models.CharField(max_length=1, choices=[('M','M'),('F','F')])
    birth = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.rid} {self.name}"

class Encounter(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='encounters')
    visited_at = models.DateTimeField()
    department = models.CharField(max_length=64, blank=True)

    def __str__(self):
        return f"ENC#{self.id} - {self.patient.name} - {self.visited_at}"

class Diagnosis(models.Model):
    encounter = models.ForeignKey(Encounter, on_delete=models.CASCADE, related_name='diagnoses')
    code = models.ForeignKey('masterdata.DiagnosisCode', on_delete=models.PROTECT)
    is_primary = models.BooleanField(default=False)

class Order(models.Model):
    encounter = models.ForeignKey(Encounter, on_delete=models.CASCADE, related_name='orders')
    type = models.CharField(max_length=8, choices=[('DRUG','DRUG'),('PROC','PROC')])
    code_drug = models.ForeignKey('masterdata.DrugCode', null=True, blank=True, on_delete=models.PROTECT)
    code_proc = models.ForeignKey('masterdata.ProcedureCode', null=True, blank=True, on_delete=models.PROTECT)
    qty = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    days = models.IntegerField(null=True, blank=True)

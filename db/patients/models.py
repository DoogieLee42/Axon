from django.apps import apps
from django.db import models
from django.core.exceptions import ValidationError
from simple_history.models import HistoricalRecords
import re, datetime

RRN_RE=re.compile(r'^\d{6}-\d{7}$')
class Patient(models.Model):
    GENDER_CHOICES=[('M','남'),('F','여'),('U','기타')]
    name=models.CharField('이름',max_length=50)
    gender=models.CharField('성별',max_length=1,choices=GENDER_CHOICES)
    birth_date=models.DateField('생년월일')
    rrn=models.CharField('주민등록번호',max_length=14,unique=True)
    phone=models.CharField('전화번호',max_length=20,blank=True)
    address=models.CharField('주소',max_length=200,blank=True)
    reg_no=models.CharField('등록번호',max_length=20,unique=True,editable=False)
    created_at=models.DateTimeField(auto_now_add=True)
    history=HistoricalRecords()
    class Meta:
        indexes=[models.Index(fields=['name']),models.Index(fields=['reg_no']),models.Index(fields=['rrn'])]
    def clean(self):
        from .errors import ERR_INVALID_RRN
        if not RRN_RE.match(self.rrn or ''):
            raise ValidationError({'rrn':ValidationError(ERR_INVALID_RRN.message,code=ERR_INVALID_RRN.code)})
    def save(self,*args,**kwargs):
        if not self.reg_no:
            today=datetime.date.today().strftime('%Y%m%d')
            last=Patient.objects.filter(reg_no__startswith=today).order_by('-reg_no').first()
            seq=int(last.reg_no.split('-')[-1])+1 if last else 1
            self.reg_no=f'{today}-{seq:04d}'
        super().save(*args,**kwargs)
        Registration=apps.get_model('patients','PatientRegistration')
        Registration.objects.get_or_create(patient=self,reg_no=self.reg_no)
    def __str__(self):
        return f"{self.name}({self.reg_no})"

    def reissue_registration_number(self):
        today=datetime.date.today().strftime('%Y%m%d')
        last=Patient.objects.filter(reg_no__startswith=today).order_by('-reg_no').first()
        seq=int(last.reg_no.split('-')[-1])+1 if last else 1
        self.reg_no=f'{today}-{seq:04d}'
        self.save(update_fields=['reg_no'])
        return self.reg_no

class PatientRegistration(models.Model):
    patient=models.ForeignKey(Patient,on_delete=models.CASCADE,related_name='registrations')
    reg_no=models.CharField('등록번호',max_length=20,unique=True)
    issued_at=models.DateTimeField('발급일시',auto_now_add=True)

    class Meta:
        ordering=['-issued_at']
        indexes=[models.Index(fields=['reg_no']),models.Index(fields=['patient','issued_at'])]
        verbose_name='환자 등록번호 이력'
        verbose_name_plural='환자 등록번호 이력'

    def __str__(self):
        return f'{self.reg_no} ({self.patient.name})'


class ExternalDocument(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='external_documents')
    title = models.CharField('문서명', max_length=200)
    source = models.CharField('발급기관', max_length=200, blank=True)
    recorded_at = models.DateField('발급일자', null=True, blank=True)
    description = models.TextField('요약', blank=True)
    file_url = models.URLField('참조 URL', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-recorded_at', '-created_at', '-pk']
        indexes = [
            models.Index(fields=['patient', 'recorded_at']),
            models.Index(fields=['patient', 'created_at']),
        ]
        verbose_name = '외부 의료기관 문서'
        verbose_name_plural = '외부 의료기관 문서'

    def __str__(self):
        return f'{self.title} ({self.patient.name})'


class ExternalResult(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='external_results')
    name = models.CharField('검사명', max_length=200)
    provider = models.CharField('의료기관', max_length=200, blank=True)
    recorded_at = models.DateField('검사일자', null=True, blank=True)
    summary = models.TextField('요약', blank=True)
    file_url = models.URLField('참조 URL', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-recorded_at', '-created_at', '-pk']
        indexes = [
            models.Index(fields=['patient', 'recorded_at']),
            models.Index(fields=['patient', 'created_at']),
        ]
        verbose_name = '외부 검사결과'
        verbose_name_plural = '외부 검사결과'

    def __str__(self):
        return f'{self.name} ({self.patient.name})'

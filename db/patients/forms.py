from django import forms

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

from .models import ExternalDocument, ExternalResult


class PrescriptionForm(forms.ModelForm):
    class Meta:
        model = Prescription
        fields = [
            'note',
            'item_type',
            'name',
            'code',
            'dose',
            'freq',
            'qty',
            'unit',
            'route',
            'days',
            'specimen',
            'priority',
            'notes',
        ]
        widgets = {
            'dose': forms.TextInput(attrs={'placeholder': '예: 500mg'}),
            'freq': forms.TextInput(attrs={'placeholder': '예: 1일 3회'}),
            'qty': forms.NumberInput(attrs={'step': '0.1'}),
            'unit': forms.TextInput(attrs={'placeholder': '정 / 포'}),
            'route': forms.TextInput(attrs={'placeholder': 'PO, IV 등'}),
            'days': forms.NumberInput(attrs={'min': 0}),
            'specimen': forms.TextInput(),
            'priority': forms.TextInput(),
            'notes': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, patient=None, **kwargs):
        self.patient = patient
        super().__init__(*args, **kwargs)
        note_field = self.fields['note']
        if patient is not None:
            note_field.queryset = ClinicalNote.objects.filter(patient=patient).order_by('-visit_date')
        else:
            note_field.queryset = ClinicalNote.objects.none()
        note_field.label = '임상 노트'
        note_field.help_text = '이 처방이 속하는 임상 노트를 선택하세요.'


class DiagnosisAssignForm(forms.Form):
    note = forms.ModelChoiceField(queryset=ClinicalNote.objects.none(), label='임상 노트')
    code = forms.CharField(label='진단 코드', widget=forms.TextInput(attrs={'list': 'diagnosis-codes'}))
    name = forms.CharField(label='진단명', required=False)

    def __init__(self, *args, patient=None, **kwargs):
        self.patient = patient
        super().__init__(*args, **kwargs)
        note_field = self.fields['note']
        if patient is not None:
            note_field.queryset = ClinicalNote.objects.filter(patient=patient).order_by('-visit_date')
        else:
            note_field.queryset = ClinicalNote.objects.none()

    def clean_code(self):
        return (self.cleaned_data.get('code') or '').strip().upper()

    def resolve_master(self):
        code = self.cleaned_data.get('code')
        name = self.cleaned_data.get('name')
        master = None
        if code:
            master = MasterItem.objects.using('master_files').filter(category='DX', code=code).first()
        if master:
            return code, master.name
        if not name:
            raise forms.ValidationError('진단명을 직접 입력하거나 목록에서 선택하세요.')
        return code, name


class DiagnosisEntryForm(forms.ModelForm):
    code = forms.CharField(label='진단 코드', widget=forms.TextInput(attrs={'list': 'diagnosis-codes'}))
    name = forms.CharField(label='진단명')

    class Meta:
        model = DiagnosisEntry
        fields = ['code', 'name']

    def clean_code(self):
        return (self.cleaned_data.get('code') or '').strip().upper()


class AllergyEntryForm(forms.ModelForm):
    class Meta:
        model = AllergyEntry
        fields = ['note', 'substance', 'reaction', 'severity', 'notes']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, patient=None, **kwargs):
        super().__init__(*args, **kwargs)
        note_field = self.fields['note']
        if patient is not None:
            note_field.queryset = ClinicalNote.objects.filter(patient=patient).order_by('-visit_date')
        else:
            note_field.queryset = ClinicalNote.objects.none()
        note_field.label = '임상 노트'


class VitalsForm(forms.ModelForm):
    class Meta:
        model = Vitals
        fields = ['note', 'systolic', 'diastolic', 'heart_rate', 'resp_rate', 'temperature_c']
        widgets = {
            'systolic': forms.NumberInput(attrs={'min': 0}),
            'diastolic': forms.NumberInput(attrs={'min': 0}),
            'heart_rate': forms.NumberInput(attrs={'min': 0}),
            'resp_rate': forms.NumberInput(attrs={'min': 0}),
            'temperature_c': forms.NumberInput(attrs={'step': '0.1'}),
        }

    def __init__(self, *args, patient=None, **kwargs):
        super().__init__(*args, **kwargs)
        note_field = self.fields['note']
        if patient is not None:
            note_field.queryset = ClinicalNote.objects.filter(patient=patient).order_by('-visit_date')
        else:
            note_field.queryset = ClinicalNote.objects.none()
        note_field.label = '임상 노트'
        self.fields['systolic'].label = '수축기 혈압(mmHg)'
        self.fields['diastolic'].label = '이완기 혈압(mmHg)'
        self.fields['heart_rate'].label = '맥박(bpm)'
        self.fields['resp_rate'].label = '호흡수(/분)'
        self.fields['temperature_c'].label = '체온(℃)'
        if self.instance and getattr(self.instance, 'pk', None):
            note_field.widget = forms.HiddenInput()
            note_field.initial = self.instance.note_id


class AnthropometricsForm(forms.ModelForm):
    class Meta:
        model = Anthropometrics
        fields = ['note', 'height_cm', 'weight_kg']
        widgets = {
            'height_cm': forms.NumberInput(attrs={'step': '0.1'}),
            'weight_kg': forms.NumberInput(attrs={'step': '0.1'}),
        }

    def __init__(self, *args, patient=None, **kwargs):
        super().__init__(*args, **kwargs)
        note_field = self.fields['note']
        if patient is not None:
            note_field.queryset = ClinicalNote.objects.filter(patient=patient).order_by('-visit_date')
        else:
            note_field.queryset = ClinicalNote.objects.none()
        note_field.label = '임상 노트'
        self.fields['height_cm'].label = '신장(cm)'
        self.fields['weight_kg'].label = '체중(kg)'
        if self.instance and getattr(self.instance, 'pk', None):
            note_field.widget = forms.HiddenInput()
            note_field.initial = self.instance.note_id


class ExternalDocumentForm(forms.ModelForm):
    class Meta:
        model = ExternalDocument
        fields = ['title', 'source', 'recorded_at', 'description', 'file_url']
        widgets = {
            'recorded_at': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 3}),
            'file_url': forms.URLInput(attrs={'placeholder': 'https://'}),
        }


class ExternalResultForm(forms.ModelForm):
    class Meta:
        model = ExternalResult
        fields = ['name', 'provider', 'recorded_at', 'summary', 'file_url']
        widgets = {
            'recorded_at': forms.DateInput(attrs={'type': 'date'}),
            'summary': forms.Textarea(attrs={'rows': 3}),
            'file_url': forms.URLInput(attrs={'placeholder': 'https://'}),
        }

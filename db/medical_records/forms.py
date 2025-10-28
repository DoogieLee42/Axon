from django import forms

from db.medical_records.models import ClinicalNote


class ClinicalNoteForm(forms.ModelForm):
    note_text = forms.CharField(
        label='임상 노트',
        required=False,
        widget=forms.Textarea(
            attrs={
                'rows': 14,
                'placeholder': (
                    '주증상 및 S/O/A/P, 진단코드를 한 번에 입력하세요.\n'
                    '예)\n'
                    'CC: 두통 3일 지속\n'
                    'S: 3일 전부터 두통 호소\n'
                    'O: BP 120/80, T 37.1\n'
                    'A: 긴장성 두통\n'
                    'P: NSAIDs 처방\n'
                    'KCD/ICD: G44.2 긴장성 두통'
                ),
            }
        ),
    )

    class Meta:
        model = ClinicalNote
        fields = ['patient', 'chief_complaint', 's_text', 'o_text', 'a_text', 'p_text', 'primary_icd']

    def __init__(self, *args, patient=None, **kwargs):
        self._patient = patient
        super().__init__(*args, **kwargs)

        patient_field = self.fields['patient']
        patient_field.label = '환자'
        patient_field.widget.attrs.update({'class': 'patient-select'})
        if patient is not None:
            patient_field.queryset = patient_field.queryset.filter(pk=patient.pk)
            patient_field.initial = patient.pk
            patient_field.widget = forms.HiddenInput()
        else:
            patient_field.queryset = patient_field.queryset.order_by('name')

        for field in ['chief_complaint', 's_text', 'o_text', 'a_text', 'p_text']:
            self.fields[field].widget = forms.HiddenInput()
            self.fields[field].required = False

        self.fields['primary_icd'].widget = forms.HiddenInput()
        self.fields['primary_icd'].required = False

        self.fields['note_text'].initial = self._build_note_text(self.instance)

    def _build_note_text(self, instance):
        if not instance or not instance.pk:
            return ''
        sections = []
        if instance.chief_complaint:
            sections.append(f"CC: {instance.chief_complaint}")
        if instance.s_text:
            sections.append(f"S: {instance.s_text}")
        if instance.o_text:
            sections.append(f"O: {instance.o_text}")
        if instance.a_text:
            sections.append(f"A: {instance.a_text}")
        if instance.p_text:
            sections.append(f"P: {instance.p_text}")
        if instance.primary_icd:
            sections.append(f"KCD/ICD: {instance.primary_icd}")
        return '\n'.join(sections)

    def clean_note_text(self):
        return (self.cleaned_data.get('note_text') or '').strip()

    def _parse_note_text(self, text):
        result = {}
        current_key = None
        lines = [line.rstrip() for line in text.splitlines() if line.strip()]

        for line in lines:
            if ':' in line:
                prefix, content = line.split(':', 1)
                key = prefix.strip().upper()
                value = content.strip()
                if key in {'CC', 'S', 'O', 'A', 'P', 'KCD/ICD'}:
                    current_key = key
                    result[current_key] = value
                    if current_key == 'KCD/ICD':
                        result[current_key] = value.split()[0].upper() if value else ''
                    continue
            if current_key:
                result[current_key] = (result[current_key] + '\n' + line.strip()).strip()
            else:
                result.setdefault('A', '')
                result['A'] = (result['A'] + '\n' + line.strip()).strip()

        if not result.get('KCD/ICD') and self.cleaned_data.get('primary_icd'):
            result['KCD/ICD'] = self.cleaned_data['primary_icd'].upper()
        return result

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self._patient is not None:
            instance.patient = self._patient
        note_text = self.cleaned_data.get('note_text', '')
        parsed = self._parse_note_text(note_text)

        instance.chief_complaint = parsed.get('CC', '')
        instance.s_text = parsed.get('S', '')
        instance.o_text = parsed.get('O', '')
        instance.a_text = parsed.get('A', '')
        instance.p_text = parsed.get('P', '')
        instance.primary_icd = parsed.get('KCD/ICD', self.cleaned_data.get('primary_icd', '')).upper()

        if commit:
            instance.save()
        return instance

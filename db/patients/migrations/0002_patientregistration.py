from django.db import migrations, models
import django.db.models.deletion


def create_initial_registrations(apps, schema_editor):
    Patient = apps.get_model('patients', 'Patient')
    Registration = apps.get_model('patients', 'PatientRegistration')
    bulk = []
    for patient in Patient.objects.all():
        if patient.reg_no and not Registration.objects.filter(reg_no=patient.reg_no).exists():
            bulk.append(Registration(patient=patient, reg_no=patient.reg_no))
    if bulk:
        Registration.objects.bulk_create(bulk)


class Migration(migrations.Migration):

    dependencies = [
        ('patients', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='PatientRegistration',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reg_no', models.CharField(max_length=20, unique=True, verbose_name='등록번호')),
                ('issued_at', models.DateTimeField(auto_now_add=True, verbose_name='발급일시')),
                ('patient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='registrations', to='patients.patient')),
            ],
            options={
                'verbose_name': '환자 등록번호 이력',
                'verbose_name_plural': '환자 등록번호 이력',
                'ordering': ['-issued_at'],
            },
        ),
        migrations.AddIndex(
            model_name='patientregistration',
            index=models.Index(fields=['reg_no'], name='patients_pa_reg_no_hist_idx'),
        ),
        migrations.AddIndex(
            model_name='patientregistration',
            index=models.Index(fields=['patient', 'issued_at'], name='patients_pa_patient_issued_idx'),
        ),
        migrations.RunPython(create_initial_registrations, migrations.RunPython.noop),
    ]

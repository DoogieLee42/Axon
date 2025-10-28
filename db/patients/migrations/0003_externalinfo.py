from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('patients', '0002_patientregistration'),
    ]

    operations = [
        migrations.CreateModel(
            name='ExternalDocument',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200, verbose_name='문서명')),
                ('source', models.CharField(blank=True, max_length=200, verbose_name='발급기관')),
                ('recorded_at', models.DateField(blank=True, null=True, verbose_name='발급일자')),
                ('description', models.TextField(blank=True, verbose_name='요약')),
                ('file_url', models.URLField(blank=True, verbose_name='참조 URL')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('patient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='external_documents', to='patients.patient')),
            ],
            options={
                'verbose_name': '외부 의료기관 문서',
                'verbose_name_plural': '외부 의료기관 문서',
                'ordering': ['-recorded_at', '-created_at', '-pk'],
            },
        ),
        migrations.CreateModel(
            name='ExternalResult',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200, verbose_name='검사명')),
                ('provider', models.CharField(blank=True, max_length=200, verbose_name='의료기관')),
                ('recorded_at', models.DateField(blank=True, null=True, verbose_name='검사일자')),
                ('summary', models.TextField(blank=True, verbose_name='요약')),
                ('file_url', models.URLField(blank=True, verbose_name='참조 URL')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('patient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='external_results', to='patients.patient')),
            ],
            options={
                'verbose_name': '외부 검사결과',
                'verbose_name_plural': '외부 검사결과',
                'ordering': ['-recorded_at', '-created_at', '-pk'],
            },
        ),
        migrations.AddIndex(
            model_name='externaldocument',
            index=models.Index(fields=['patient', 'recorded_at'], name='patients_extdoc_patient_recorded_idx'),
        ),
        migrations.AddIndex(
            model_name='externaldocument',
            index=models.Index(fields=['patient', 'created_at'], name='patients_extdoc_patient_created_idx'),
        ),
        migrations.AddIndex(
            model_name='externalresult',
            index=models.Index(fields=['patient', 'recorded_at'], name='patients_extres_patient_recorded_idx'),
        ),
        migrations.AddIndex(
            model_name='externalresult',
            index=models.Index(fields=['patient', 'created_at'], name='patients_extres_patient_created_idx'),
        ),
    ]

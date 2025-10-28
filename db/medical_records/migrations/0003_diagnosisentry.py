from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('medical_records', '0002_rename_visits_clin_visit_d_d75c4a_idx_medical_rec_visit_d_36d20c_idx_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='DiagnosisEntry',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=32, verbose_name='진단코드')),
                ('name', models.CharField(max_length=255, verbose_name='진단명')),
                ('source', models.CharField(blank=True, default='primary', max_length=32, verbose_name='출처')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('note', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='diagnoses', to='medical_records.clinicalnote')),
            ],
            options={
                'verbose_name': '임상 진단',
                'verbose_name_plural': '임상 진단',
                'ordering': ['-created_at', '-pk'],
            },
        ),
        migrations.AddIndex(
            model_name='diagnosisentry',
            index=models.Index(fields=['note', 'code'], name='medical_rec_note_code_idx'),
        ),
        migrations.AddIndex(
            model_name='diagnosisentry',
            index=models.Index(fields=['code'], name='medical_rec_code_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='diagnosisentry',
            unique_together={('note', 'code', 'source')},
        ),
    ]

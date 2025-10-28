from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('medical_records', '0003_diagnosisentry'),
    ]

    operations = [
        migrations.AlterField(
            model_name='vitals',
            name='systolic',
            field=models.PositiveIntegerField(blank=True, null=True, verbose_name='수축기 혈압(mmHg)')
        ),
        migrations.AlterField(
            model_name='vitals',
            name='diastolic',
            field=models.PositiveIntegerField(blank=True, null=True, verbose_name='이완기 혈압(mmHg)')
        ),
        migrations.AlterField(
            model_name='vitals',
            name='heart_rate',
            field=models.PositiveIntegerField(blank=True, null=True, verbose_name='맥박(bpm)')
        ),
        migrations.AlterField(
            model_name='vitals',
            name='resp_rate',
            field=models.PositiveIntegerField(blank=True, null=True, verbose_name='호흡수(/분)')
        ),
        migrations.AlterField(
            model_name='vitals',
            name='temperature_c',
            field=models.DecimalField(blank=True, decimal_places=1, max_digits=4, null=True, verbose_name='체온(℃)')
        ),
        migrations.AlterField(
            model_name='anthropometrics',
            name='height_cm',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True, verbose_name='신장(cm)')
        ),
        migrations.AlterField(
            model_name='anthropometrics',
            name='weight_kg',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True, verbose_name='체중(kg)')
        ),
    ]

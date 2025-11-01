from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("medical_records", "0008_alter_clinicalnote_visit_date"),
    ]

    operations = [
        migrations.AddField(
            model_name="historicalclinicalnote",
            name="narrative",
            field=models.TextField(blank=True, verbose_name="임상서술"),
        ),
        migrations.AddField(
            model_name="historicalclinicalnote",
            name="social_history_text",
            field=models.TextField(blank=True, verbose_name="사회력 요약"),
        ),
        migrations.AddField(
            model_name="historicalclinicalnote",
            name="family_history_text",
            field=models.TextField(blank=True, verbose_name="가족력 요약"),
        ),
    ]

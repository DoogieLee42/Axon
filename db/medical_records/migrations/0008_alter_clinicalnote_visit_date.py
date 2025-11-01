from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ("medical_records", "0007_clinicalnote_text_fields"),
    ]

    operations = [
        migrations.AlterField(
            model_name="clinicalnote",
            name="visit_date",
            field=models.DateTimeField(default=django.utils.timezone.now, verbose_name="내원일시"),
        ),
    ]

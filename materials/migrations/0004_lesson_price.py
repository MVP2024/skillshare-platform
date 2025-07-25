# Generated by Django 5.2.3 on 2025-07-20 10:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("materials", "0003_alter_course_options_alter_lesson_options"),
    ]

    operations = [
        migrations.AddField(
            model_name="lesson",
            name="price",
            field=models.DecimalField(
                decimal_places=2,
                default=0.0,
                help_text="Укажите стоимость урока",
                max_digits=10,
                verbose_name="Стоимость урока",
            ),
        ),
    ]

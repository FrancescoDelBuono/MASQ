# Generated by Django 3.0.2 on 2020-02-18 16:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('msp', '0006_auto_20200218_1730'),
    ]

    operations = [
        migrations.AlterField(
            model_name='scenario',
            name='validation',
            field=models.FloatField(default=0, null=True),
        ),
    ]

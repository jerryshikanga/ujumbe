# Generated by Django 2.1.1 on 2018-10-28 19:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0003_auto_20181011_2204'),
    ]

    operations = [
        migrations.AddField(
            model_name='accountcharges',
            name='cuurency_code',
            field=models.CharField(default='KES', max_length=5),
        ),
    ]

# Generated by Django 2.1.1 on 2018-10-10 13:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='subscription',
            name='subscription_type',
            field=models.CharField(choices=[('FORECAST', 'forecast'), ('CURRENT', 'current')], default='FORECAST', max_length=50),
        ),
    ]

# Generated by Django 2.1.1 on 2018-10-04 19:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('africastalking', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='incomingmessage',
            name='text',
            field=models.TextField(),
        ),
        migrations.AlterField(
            model_name='outgoingmessages',
            name='text',
            field=models.TextField(),
        ),
    ]
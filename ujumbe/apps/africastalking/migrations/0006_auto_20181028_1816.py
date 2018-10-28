# Generated by Django 2.1.1 on 2018-10-28 18:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('africastalking', '0005_auto_20181028_1808'),
    ]

    operations = [
        migrations.AddField(
            model_name='outgoingmessages',
            name='failure_reason',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='outgoingmessages',
            name='delivery_status',
            field=models.CharField(choices=[('Failed', 'failed'), ('Sent', 'sent'), ('Delivered', 'Delivered'), ('Submitted', 'submitted'), ('Buffered', 'buffered'), ('Rejected', 'rejected'), ('Success', 'success')], default='Submitted', max_length=50),
        ),
    ]
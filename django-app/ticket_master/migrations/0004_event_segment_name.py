# Generated by Django 4.2.6 on 2024-01-17 08:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ticket_master', '0003_remove_classification_venue_event_genre_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='segment_name',
            field=models.CharField(default='', max_length=100),
        ),
    ]

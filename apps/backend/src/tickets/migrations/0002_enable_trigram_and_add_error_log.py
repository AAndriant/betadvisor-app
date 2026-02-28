# Generated migration for enabling PostgreSQL Trigram and adding error logging
from django.contrib.postgres.operations import TrigramExtension
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tickets', '0001_initial'),
    ]

    operations = [
        # Enable PostgreSQL Trigram extension for fuzzy search
        TrigramExtension(),
        
        # Add error logging field for OCR failures
        migrations.AddField(
            model_name='ticket',
            name='ocr_error_log',
            field=models.TextField(blank=True, null=True, help_text='Stores error details when OCR or match linking fails'),
        ),
    ]

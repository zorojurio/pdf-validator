# Generated by Django 4.2.2 on 2024-03-04 00:38

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='PdfDocumentValidator',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('pdf_file', models.FileField(upload_to='pdfs/')),
                ('is_signed', models.BooleanField(default=False)),
                ('is_hashes_valid', models.BooleanField(default=False)),
                ('is_signatures_valid', models.BooleanField(default=False)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='SignatureValidator',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('serial_number', models.CharField(max_length=255)),
                ('hash_valid', models.BooleanField(default=False)),
                ('signature_valid', models.BooleanField(default=False)),
                ('verified_signer', models.BooleanField(default=False)),
                ('message', models.TextField(blank=True, null=True)),
                ('signing_time', models.DateTimeField()),
                ('signature_name', models.CharField(max_length=255)),
                ('signed_by', models.CharField(blank=True, max_length=255, null=True)),
                ('email_of_signer', models.CharField(blank=True, max_length=255, null=True)),
                ('signature_algorithm', models.CharField(blank=True, max_length=255, null=True)),
                ('digest_algorithm', models.CharField(blank=True, max_length=255, null=True)),
                ('message_digest', models.TextField(blank=True, null=True)),
                ('public_key', models.TextField(blank=True, null=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('pdf_document_validator', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='signature_validator.pdfdocumentvalidator')),
            ],
        ),
    ]

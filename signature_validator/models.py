# -*- coding: utf-8 -*-
from django.db import models
from django.urls import reverse

from accounts.models import CustomUser


class PdfDocumentValidator(models.Model):
    """Model to store PDF validation data for the whole document."""

    pdf_file = models.FileField(upload_to="pdfs/", blank=False, null=False)
    is_signed = models.BooleanField(default=False)
    is_hashes_valid = models.BooleanField(default=False)
    is_signatures_valid = models.BooleanField(default=False)
    user = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL, blank=True, null=True
    )
    all_signers_verified = models.BooleanField(default=False)
    distinct_people_signed = models.IntegerField(default=0)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.pdf_file.name

    def get_absolute_url(self):
        """Get absolute URL for the instance."""
        return reverse("signature-validator-view:pdf-result", kwargs={"pk": self.pk})


class SignatureValidator(models.Model):
    """Model to store signature validation data."""

    pdf_document_validator = models.ForeignKey(
        PdfDocumentValidator, on_delete=models.CASCADE
    )
    serial_number = models.CharField(max_length=255)
    hash_valid = models.BooleanField(default=False)
    signature_valid = models.BooleanField(default=False)
    verified_signer = models.BooleanField(default=False)
    message = models.TextField(blank=True, null=True)
    signing_time = models.DateTimeField()
    signature_name = models.CharField(max_length=255)
    signed_by = models.CharField(max_length=255, blank=True, null=True)
    email_of_signer = models.CharField(max_length=255, blank=True, null=True)
    signature_algorithm = models.CharField(max_length=255, blank=True, null=True)
    digest_algorithm = models.CharField(max_length=255, blank=True, null=True)
    message_digest = models.TextField(blank=True, null=True)
    public_key = models.TextField(blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.signature_name

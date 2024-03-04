from django.contrib import admin
from django.forms import BaseInlineFormSet

from .models import SignatureValidator, PdfDocumentValidator


class SignatureValidatorInlineFormSet(BaseInlineFormSet):
    """Custom InlineFormSet to Filter SignatureValidator."""

    def get_queryset(self):
        """Filter Bev registrations as per user's email and by partner."""
        return SignatureValidator.objects.filter(
            pdf_document_validator=self.instance
        )


class SignatureValidatorInline(admin.TabularInline):
    model = SignatureValidator
    fields = ('serial_number', 'hash_valid', 'signature_valid', 'signing_time', 'signature_name')
    readonly_fields = ('hash_valid', 'signature_valid', 'signing_time', 'signature_name')
    formset = SignatureValidatorInlineFormSet
    ordering = ('id',)

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def get_queryset(self, request):
        return super().get_queryset(request)


class PdfDocumentValidatorAdmin(admin.ModelAdmin):
    inlines = [SignatureValidatorInline]
    list_display = ('pk', 'pdf_file', 'is_signed', 'is_hashes_valid', 'is_signatures_valid', 'user',
                    'created', 'updated')
    search_fields = ('pdf_file', 'is_signed', 'is_hashes_valid', 'is_signatures_valid',
                     'user', 'created', 'updated')
    list_filter = ('is_signed', 'is_hashes_valid', 'is_signatures_valid', 'user',
                   'created', 'updated')


admin.site.register(PdfDocumentValidator, PdfDocumentValidatorAdmin)

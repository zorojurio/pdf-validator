from rest_framework import serializers

from accounts.models import CustomUser
from accounts.serializers import UserSerializer
from signature_validator.helpers import PdfSignatureValidator
from signature_validator.models import PdfDocumentValidator, SignatureValidator


class SignatureValidateSerializer(serializers.ModelSerializer):
    """Serializer for signature validator model."""

    class Meta:
        """Meta-class for SignatureValidateSerializer."""

        model = SignatureValidator
        fields = (
            "id",
            "pdf_document_validator",
            "serial_number",
            "hash_valid",
            "signature_valid",
            "signing_time",
            "signature_name",
        )
        read_only_fields = (
            "id", "hash_valid", "serial_number",
            "signature_valid", "signing_time", "signature_name"
        )


class PdfValidateSerializer(serializers.ModelSerializer):
    """Serializer for PDF signature validator model."""
    user = UserSerializer(read_only=True, source="validator_user.user")
    validated_list = SignatureValidateSerializer(
        many=True,
        read_only=True,
        source="signaturevalidator_set"
    )

    class Meta:
        """Meta-class for PdfValidateSerializer."""

        model = PdfDocumentValidator
        fields = (
            "id",
            "user",
            "pdf_file",
            "is_signed",
            "is_hashes_valid",
            "is_signatures_valid",
            "validated_list"
        )
        read_only_fields = ("id", "is_signed", "is_hashes_valid", "is_signatures_valid", "user")

    def create(self, validated_data):
        """Override create method to save logged-in user to signature."""
        pdf_validator = PdfDocumentValidator.objects.create(**validated_data)
        user: CustomUser = self.context.get('user')
        if user and hasattr(user, 'validator_user'):
            pdf_validator.validator_user = user.validator_user
        validator = PdfSignatureValidator(pdf_validator.pdf_file.path)
        validator.validate()
        pdf_validator.is_signed = validator.is_signed
        pdf_validator.is_hashes_valid = validator.is_hashes_valid
        pdf_validator.is_signatures_valid = validator.is_signatures_valid

        # createing related signature validations
        for validated_data in validator.validated_data_list:
            validated_data['pdf_document_validator'] = pdf_validator
            SignatureValidator.objects.create(**validated_data)
        pdf_validator.save()
        return pdf_validator

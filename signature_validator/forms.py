# -*- coding: utf-8 -*-
from django import forms

from accounts.models import SignerUser, CustomUser
from accounts.services.pbs_validation_service import ValidatePublicKey
from signature_validator.services.pdf_validation_service import PdfSignatureValidator
from validator.logger import module_logger
from .models import PdfDocumentValidator, SignatureValidator
from .services.email_service import EmailService

logger = module_logger(__name__)


class PdfValidateForm(forms.ModelForm):
    """Form for validating the PDF file."""

    def __init__(self, *args, **kwargs):
        """Initialize the form with request object."""
        self.request = kwargs.pop("request")
        super(PdfValidateForm, self).__init__(*args, **kwargs)

    class Meta:
        """Meta class for PdfValidateForm."""

        model = PdfDocumentValidator
        fields = ("pdf_file",)

    def clean_pdf_file(self):
        """Validate the PDF file."""
        pdf_file = self.cleaned_data.get("pdf_file")
        if not pdf_file:
            raise forms.ValidationError("PDF file is required.")
        if not pdf_file.name.endswith(".pdf"):
            raise forms.ValidationError("Invalid file format, only PDF is allowed.")
        return pdf_file

    def save(self, commit=True):
        """Override save method to validate PDF."""
        pdf_validator = super().save()
        validator = PdfSignatureValidator(pdf_validator.pdf_file.path)
        validator.validate()
        pdf_validator.is_signed = validator.is_signed
        pdf_validator.is_hashes_valid = validator.is_hashes_valid
        pdf_validator.is_signatures_valid = validator.is_signatures_valid
        # save user
        if self.request.user.is_authenticated:
            pdf_validator.user = self.request.user
        pdf_validator.save()
        emails_to_be_sent = []
        distinct_people_signed = set()

        if self.is_validated_data_available(validator):
            for index, validated_data in enumerate(
                validator.validated_data_list, start=1
            ):
                validated_data["pdf_document_validator"] = pdf_validator
                validated_data["signature_name"] = f"Signature {index}"
                distinct_people_signed.add(validated_data["serial_number"])
                if "public_key" in validated_data:
                    self.validate_and_trim_public_key(validated_data)
                    signature_validator = SignatureValidator.objects.create(
                        **validated_data
                    )
                    self.set_signer_verification(
                        emails_to_be_sent, signature_validator, validated_data
                    )
        self.send_invite_emails(emails_to_be_sent, pdf_validator)
        pdf_validator.all_signers_verified = self.is_all_signers_verified(pdf_validator)
        pdf_validator.distinct_people_signed = len(distinct_people_signed)
        pdf_validator.save()
        return pdf_validator

    @staticmethod
    def is_validated_data_available(validator) -> bool:
        """Check if validated data is available."""
        return (
            validator
            and hasattr(validator, "validated_data_list")
            and validator.validated_data_list
        )

    @staticmethod
    def is_all_signers_verified(pdf_validator) -> bool:
        """Check if all signers are verified."""
        return all(
            [
                signature[0]
                for signature in SignatureValidator.objects.filter(
                    pdf_document_validator=pdf_validator
                ).values_list("verified_signer")
            ]
        )

    @staticmethod
    def validate_and_trim_public_key(validated_data):
        """Validate and trim the public key."""
        validator = ValidatePublicKey(validated_data["public_key"])
        validator.trim_key()
        validated_data["public_key"] = validator.key

    def send_invite_emails(self, emails_to_be_sent, pdf_validator):
        """Send invite emails to the signers."""
        if emails_to_be_sent:
            EmailService.send_invite_email(
                emails_to_be_sent, pdf_validator.pdf_file.path, self.request
            )

    @staticmethod
    def set_signer_verification(emails_to_be_sent, signature_validator, validated_data):
        """Check if the signer exists in the system and set proper messages."""
        user = CustomUser.objects.filter(email=validated_data["email_of_signer"])
        sign_user = SignerUser.objects.filter(
            public_key=validated_data["public_key"], active=True
        )
        if user.exists() and sign_user.exists():
            signature_validator.verified_signer = True
        else:
            PdfValidateForm.set_messages(emails_to_be_sent, signature_validator)
        signature_validator.save()

    @staticmethod
    def set_messages(emails_to_be_sent, signature_validator):
        """Set messages for the signature."""
        if signature_validator.email_of_signer:
            emails_to_be_sent.append(signature_validator.email_of_signer)
            signature_validator.message = (
                f"{signature_validator.email_of_signer} is not registered in the "
                f"system, we have already sent an invitation email, please contact "
                f"signer to signup in the system."
            )
            logger.info("Sending signup invitation email to the signer.")
        else:
            signature_validator.message = (
                f"{signature_validator.email_of_signer} is not provided in the "
                f"signature, please contact signer to create a signature with email"
                f" and personal details."
            )

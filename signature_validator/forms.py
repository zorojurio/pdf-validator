from django import forms

from accounts.services.pbs_validation_service import ValidatePublicKey
from accounts.models import SignerUser, CustomUser
from validator.logger import module_logger
from signature_validator.services.pdf_validation_service import PdfSignatureValidator
from .models import PdfDocumentValidator, SignatureValidator
from .services.email_service import EmailService

logger = module_logger(__name__)


class PdfValidateForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request')
        super(PdfValidateForm, self).__init__(*args, **kwargs)

    class Meta:
        model = PdfDocumentValidator
        fields = (
            "pdf_file",
        )

    def clean_pdf_file(self):
        pdf_file = self.cleaned_data.get('pdf_file')
        if not pdf_file:
            raise forms.ValidationError("PDF file is required.")
        if not pdf_file.name.endswith('.pdf'):
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
        if self.request.user.is_authenticated:
            pdf_validator.user = self.request.user
        pdf_validator.save()
        emails_to_be_sent = []
        distinct_people_signed = set()

        if validator and hasattr(validator, 'validated_data_list') and validator.validated_data_list:
            for index, validated_data in enumerate(validator.validated_data_list, start=1):
                validated_data['pdf_document_validator'] = pdf_validator
                validated_data['signature_name'] = f'Signature {index}'
                distinct_people_signed.add(validated_data['serial_number'])
                if 'public_key' in validated_data:
                    validator = ValidatePublicKey(validated_data['public_key'])
                    validator.trim_key()
                    validated_data['public_key'] = validator.key
                    signature_validator = SignatureValidator.objects.create(**validated_data)
                    user = CustomUser.objects.filter(email=validated_data['email_of_signer'])
                    sign_user = SignerUser.objects.filter(
                        public_key=validated_data['public_key'],
                        active=True
                    )
                    if user.exists() and sign_user.exists():
                        signature_validator.verified_signer = True
                    else:
                        if signature_validator.email_of_signer:
                            emails_to_be_sent.append(signature_validator.email_of_signer)
                            signature_validator.message = (
                                f"{signature_validator.email_of_signer} is not registered in the system, we have "
                                f"already sent an invitation email, please contact signer to signup in the system.")
                            logger.info("Sending signup invitation email to the signer.")
                        else:
                            signature_validator.message = (
                                f"{signature_validator.email_of_signer} is not provided in the signature, please "
                                f"contact signer to create a signature with email and personal details.")
                    signature_validator.save()
        if emails_to_be_sent:
            EmailService.send_invite_email(
                emails_to_be_sent,
                pdf_validator.pdf_file.path,
                self.request)

        pdf_validator.all_signers_verified = all([i[0] for i in
                                                  SignatureValidator.objects.filter(pdf_document_validator=pdf_validator).values_list('verified_signer')])
        pdf_validator.distinct_people_signed = len(distinct_people_signed)
        pdf_validator.save()
        return pdf_validator

import pytest
from django.conf import settings
from django.db.models import QuerySet
from django.urls import reverse

from signature_validator.models import PdfDocumentValidator, SignatureValidator


pytestmark = pytest.mark.django_db


class TestValidateSignatureView:
    """Test the ValidateSignatureView."""

    validate_url = reverse("signature-validator-view:validate-signature")

    def test_get_with_unauthenticated_client(self, client):
        """Test GET request with unauthenticated user."""
        response = client.get(self.validate_url)
        assert response.status_code == 302
        assert response.url == reverse("accounts:login") + "?next=/"

    def test_get_with_authenticated_client(
        self, authenticated_signer_client, activated_user_signer_type
    ):
        """Test GET request with authenticated user."""
        response = authenticated_signer_client.get(self.validate_url)
        assert response.status_code == 200
        assert response.template_name == ["signature_validator/home.html"]
        assert response.context["user"] == activated_user_signer_type
        assert response.context["user"].is_authenticated
        # check if pdf_file is present in form
        assert response.context["form"].fields["pdf_file"]
        # check if pdf_file is required
        assert response.context["form"].fields["pdf_file"].required

    def test_pdf_file_required_when_submitting(self, authenticated_signer_client):
        """Test if pdf_file is required when submitting."""
        response = authenticated_signer_client.post(self.validate_url)
        assert response.status_code == 200
        assert response.context["form"].errors["pdf_file"] == [
            "This field is required."
        ]

    def test_pdf_file_should_be_pdf_when_submitting(
        self, authenticated_signer_client, doc_file
    ):
        """Test if pdf_file should be pdf when submitting."""
        response = authenticated_signer_client.post(
            self.validate_url, {"pdf_file": doc_file}, format="multipart"
        )
        assert response.status_code == 200
        assert response.context["form"].errors["pdf_file"] == [
            "Invalid file format, only PDF is allowed."
        ]

    @pytest.mark.parametrize(
        "pdf_file, signature_count",
        [
            ("Test_File_one_person_one_signature", 1),
            ("test_one_person_three_signatures", 3),
        ],
    )
    def test_validation_of_pdf_file_when_signer_not_verified(
        self,
        authenticated_signer_client,
        activated_user_signer_type,
        mailoutbox,
        pdf_file,
        signature_count,
    ):
        """Test validation of PDF file with one signature."""
        pdf_file_path = f"{settings.TEST_FILES_ROOT}/{pdf_file}.pdf"
        with open(pdf_file_path, "rb") as file:
            response = authenticated_signer_client.post(
                self.validate_url, {"pdf_file": file}, format="multipart"
            )
            assert response.status_code == 302
            pdf_validator: QuerySet[PdfDocumentValidator] = (
                PdfDocumentValidator.objects.filter(user=activated_user_signer_type)
            )
            assert pdf_validator.exists()
            assert pdf_validator.count() == 1

            validator: PdfDocumentValidator = pdf_validator.last()
            assert response.url == validator.get_absolute_url()
            assert validator.is_signed
            assert validator.is_hashes_valid
            assert validator.is_signatures_valid
            assert not validator.all_signers_verified

            assert validator.distinct_people_signed == 1
            assert validator.user == activated_user_signer_type
            assert pdf_file in validator.pdf_file.name

            signatures: QuerySet[SignatureValidator] = (
                SignatureValidator.objects.filter(pdf_document_validator=validator)
            )
            assert signatures.exists()
            assert signatures.count() == signature_count
            signatures: QuerySet[SignatureValidator] = (
                SignatureValidator.objects.filter(pdf_document_validator=validator)
            )
            assert signatures.exists()
            assert signatures.count() == signature_count
            # email should be not be sent to signer of the document as signer already in system
            for signature in signatures:
                assert signature.hash_valid
                assert signature.signature_valid
                assert not signature.verified_signer

            # email should be sent to signer of the document
            assert len(mailoutbox) == 1
            assert mailoutbox[0].subject == "Invitation to PDf Validator"
            assert mailoutbox[0].to == [signature.email_of_signer]

    @pytest.mark.parametrize(
        "pdf_file, signature_count",
        [
            ("Test_File_one_person_one_signature", 1),
            ("test_one_person_three_signatures", 3),
        ],
    )
    def test_validation_of_pdf_file_with_signer_verified(
        self,
        authenticated_signer_client,
        activated_user_signer_type,
        signer,
        mailoutbox,
        pdf_file,
        signature_count,
    ):
        """Test validation of PDF file with one signature."""
        # mailoutbox is cleared, to delete signer actvation email
        mailoutbox.clear()
        pdf_file_path = f"{settings.TEST_FILES_ROOT}/{pdf_file}.pdf"
        with open(pdf_file_path, "rb") as file:
            response = authenticated_signer_client.post(
                self.validate_url, {"pdf_file": file}, format="multipart"
            )
            assert response.status_code == 302
            pdf_validator: QuerySet[PdfDocumentValidator] = (
                PdfDocumentValidator.objects.filter(user=activated_user_signer_type)
            )
            assert pdf_validator.exists()
            assert pdf_validator.count() == 1

            validator: PdfDocumentValidator = pdf_validator.last()
            assert response.url == validator.get_absolute_url()
            assert validator.is_signed
            assert validator.is_hashes_valid
            assert validator.is_signatures_valid
            assert validator.all_signers_verified

            assert validator.distinct_people_signed == 1
            assert validator.user == activated_user_signer_type
            assert pdf_file in validator.pdf_file.name

            signatures: QuerySet[SignatureValidator] = (
                SignatureValidator.objects.filter(pdf_document_validator=validator)
            )
            assert signatures.exists()
            assert signatures.count() == signature_count
            # email should be not be sent to signer of the document as signer already in system
            for signature in signatures:
                assert signature.hash_valid
                assert signature.signature_valid
                assert signature.verified_signer
            # email should be not be sent to signer of the document as signer already in system
            assert len(mailoutbox) == 0
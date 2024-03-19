from django.urls import reverse
import pytest


class TestValidateSignatureView:
    """Test the ValidateSignatureView."""

    validate_url = reverse("signature-validator-view:validate-signature")

    def test_get_with_unauthenticated_client(self, client):
        """Test GET request with unauthenticated user."""
        response = client.get(self.validate_url)
        assert response.status_code == 302
        assert response.url == reverse("accounts:login") + "?next=/"

    @pytest.mark.django_db
    def test_get_with_authenticated_client(
        self, authenticated_signer_client, signer_activated_user
    ):
        """Test GET request with authenticated user."""
        response = authenticated_signer_client.get(self.validate_url)
        assert response.status_code == 200
        assert response.template_name == ["signature_validator/home.html"]
        assert response.context["user"] == signer_activated_user
        assert response.context["user"].is_authenticated
        # check if pdf_file is present in form
        assert response.context["form"].fields["pdf_file"]
        # check if pdf_file is required
        assert response.context["form"].fields["pdf_file"].required

    @pytest.mark.django_db
    def test_pdf_file_required_when_submitting(self, authenticated_signer_client):
        """Test if pdf_file is required when submitting."""
        response = authenticated_signer_client.post(self.validate_url)
        assert response.status_code == 200
        assert response.context["form"].errors["pdf_file"] == [
            "This field is required."
        ]

    @pytest.mark.django_db
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

    @pytest.mark.django_db
    def test_validation_of_pdf_file_with_one_signature(self):
        """Test validation of PDF file with one signature."""
        pass

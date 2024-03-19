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

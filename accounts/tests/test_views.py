from django.urls import reverse
import pytest

from accounts.tests.factories import UserFactory
from django.contrib import auth


class TestCustomLoginView:
    """Test the CustomLoginView."""

    login_url = reverse("accounts:login")

    def test_get_login_request(self, client):
        """Test whether the login page is rendered correctly."""
        response = client.get(self.login_url)
        assert response.status_code == 200
        assert response.template_name == ["accounts/login.html"]

    @pytest.mark.django_db
    def test_invalid_login_credentials(self, client):
        """Test whether the user is logged in."""
        response = client.post(
            self.login_url,
            data={"username": "testuser", "password": "testpassword"},
        )
        assert response.status_code == 200
        assert response.template_name == ["accounts/login.html"]
        assert response.context["form"].errors == {
            "__all__": [
                "Please enter a correct username and password. Note that both fields may be case-sensitive."
            ]
        }

    @pytest.mark.django_db
    def test_valid_login_with_active_user(self, client):
        """Test login with active user."""
        password = "NewPassword@123"
        user = UserFactory.create(
            username="testuser",
        )
        user.set_password(password)
        user.save()
        # user.refresh_from_db()

        response = client.post(
            self.login_url,
            data={"username": user.username, "password": password},
        )
        assert response.status_code == 302
        assert response.url == reverse("signature-validator-view:validate-signature")
        assert response.wsgi_request.user.is_authenticated
        assert response.wsgi_request.user.username == user.username
        assert response.wsgi_request.user.email == user.email
        assert response.wsgi_request.user.first_name == user.first_name
        assert response.wsgi_request.user.last_name == user.last_name
        assert response.wsgi_request.user.user_type == user.user_type
        assert response.wsgi_request.user.is_active == user.is_active

    @pytest.mark.django_db
    def test_valid_login_with_inactive_user(self, client):
        """Test login with inactive user."""
        password = "NewPassword@123"
        user = UserFactory.create(
            username="testuser",
        )
        user.set_password(password)
        user.is_active = False
        user.save()
        # user.refresh_from_db()

        response = client.post(
            self.login_url,
            data={"username": user.username, "password": password},
        )
        assert response.status_code == 200
        assert response.context["form"].errors == {
            "__all__": [
                "Please enter a correct username and password. Note that both fields may be case-sensitive."
            ]
        }
        assert (
            "Please enter a correct username and password"
            in response.content.decode("utf-8")
        )


class TestCustomLogoutView:
    """Test the CustomLogoutView."""

    logout_url = reverse("accounts:logout")

    @pytest.mark.django_db
    def test_logout_of_a_logged_in_user(
        self, authenticated_signer_client, signer_activated_user
    ):
        """Test logout function of a logged-in user."""
        user = auth.get_user(authenticated_signer_client)
        assert user.is_authenticated is True
        response = authenticated_signer_client.post(self.logout_url)
        # checking if a logout redirected to login page
        assert response.url == reverse("accounts:login")
        user = auth.get_user(authenticated_signer_client)
        assert user.is_authenticated is False

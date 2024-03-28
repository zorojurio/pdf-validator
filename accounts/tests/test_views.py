import pytest
from django.apps import apps
from django.conf import settings
from django.contrib import auth
from django.urls import reverse

from accounts.models import CustomUser
from accounts.tests.factories import UserFactory

pytestmark = pytest.mark.django_db


class TestCustomLoginView:
    """Test the CustomLoginView."""

    login_url = reverse("accounts:login")

    def test_get_login_request(self, client):
        """Test whether the login page is rendered correctly."""
        response = client.get(self.login_url)
        assert response.status_code == 200
        assert response.template_name == ["accounts/login.html"]

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
                "Please enter a correct username and password. Note that both fields may "
                "be case-sensitive."
            ]
        }
        assert (
            "Please enter a correct username and password"
            in response.content.decode("utf-8")
        )


class TestCustomLogoutView:
    """Test the CustomLogoutView."""

    logout_url = reverse("accounts:logout")

    def test_logout_of_a_logged_in_user(
        self, authenticated_signer_client, activated_user_signer_type
    ):
        """Test logout function of a logged-in user."""
        user = auth.get_user(authenticated_signer_client)
        assert user.is_authenticated is True
        response = authenticated_signer_client.post(self.logout_url)
        # checking if a logout redirected to login page
        assert response.url == reverse("accounts:login")
        user = auth.get_user(authenticated_signer_client)
        assert user.is_authenticated is False


class TestSignUpView:
    """Test the SignUpView."""

    signup_url = reverse("accounts:signup")

    def test_get_signup_page(self, client):
        """Test whether the signup page is rendered correctly."""
        response = client.get(self.signup_url)
        assert response.status_code == 200
        assert response.template_name == ["accounts/signup.html"]
        # check the form fields are included in the context form
        assert response.context["form"].fields.keys() == {
            "username",
            "first_name",
            "last_name",
            "email",
            "password1",
            "password2",
            "user_type",
        }
        # check the user_type field choices, should be signer and validator
        assert response.context["form"].fields["user_type"].choices == [
            ("signer", "Signer"),
            ("validator", "Validator"),
        ]

    @pytest.mark.parametrize(
        "user_type, related_profile",
        [("signer", "SignerUser"), ("validator", "ValidatorUser")],
    )
    def test_signup(self, client, user_type, related_profile, mailoutbox):
        """Test signup as a signer user and a validator user."""
        username = "testuser-signer"
        response = client.post(
            self.signup_url,
            data={
                "username": username,
                "first_name": "Test",
                "last_name": "User",
                "email": "test-signer@gmail.com",
                "password1": "NewPassword@123",
                "password2": "NewPassword@123",
                "user_type": user_type,
            },
        )
        assert response.status_code == 302
        created_user: CustomUser = CustomUser.objects.filter(username=username).first()
        assert created_user is not None
        assert created_user.username == username
        assert created_user.email == created_user.email
        # newly created user should not be active
        assert created_user.is_active is False
        # newly created user should be a signer
        assert created_user.user_type == getattr(CustomUser.UserType, user_type)
        # check the success url for the redirection
        assert response.url == reverse("accounts:login")
        # user should not be authenticated
        assert response.wsgi_request.user.is_authenticated is False
        # check if related profile is created
        Model = apps.get_model("accounts", related_profile)
        assert Model.objects.filter(user=created_user).exists()
        # check if email is sent to the user
        assert mailoutbox[0].subject == "Activation link has been sent to your email."
        assert mailoutbox[0].to == [created_user.email]
        assert len(mailoutbox) == 1

    @pytest.mark.parametrize(
        "user_type",
        ("signer", "validator"),
    )
    def test_signup_with_existing_username(
        self, client, activated_user_signer_type, user_type
    ):
        """Test signup with an existing username."""
        response = client.post(
            self.signup_url,
            data={
                "username": activated_user_signer_type.username,
                "first_name": "Test",
                "last_name": "User",
                "email": "test-signer@gmail.com",
                "password1": "NewPassword@123",
                "password2": "NewPassword@123",
                "user_type": user_type,
            },
        )
        assert response.status_code == 200
        assert response.context["form"].errors == {
            "username": ["A user with that username already exists."]
        }

    @pytest.mark.parametrize(
        "user_type",
        ("signer", "validator"),
    )
    def test_signup_with_already_existing_email(
        self, client, activated_user_signer_type, user_type
    ):
        """Test signup with an existing email."""
        response = client.post(
            self.signup_url,
            data={
                "username": "testuser-signer",
                "first_name": "Test",
                "last_name": "User",
                "email": activated_user_signer_type.email,
                "password1": "NewPassword@123",
                "password2": "NewPassword@123",
                "user_type": user_type,
            },
        )
        assert response.status_code == 200
        assert response.context["form"].errors == {
            "email": ["User with this Email address already exists."]
        }


class TestSignerUserUpdateView:
    """Test the SignerUserUpdateView."""

    def test_signer_user_update_get_page(
        self,
        authenticated_signer_client,
        signer,
    ):
        """Test whether the signer user update page is rendered correctly."""
        response = authenticated_signer_client.get(
            reverse("accounts:add-signer", kwargs={"pk": signer.pk})
        )
        assert response.status_code == 200
        assert response.template_name == ["accounts/signer.html"]
        # check the form fields are included in the context form
        assert sorted(response.context["form"].fields.keys()) == sorted(
            ["certificate", "nic_image", "nic_number", "profile_image"]
        )

    def test_signer_user_update_invalid_nic(
        self,
        authenticated_signer_client,
        signer,
    ):
        """Test Invalid NIC number."""
        response = authenticated_signer_client.post(
            reverse("accounts:add-signer", kwargs={"pk": signer.pk}),
            data={
                "nic_number": "54422s2",
                "certificate": "test.cer",
                "nic_image": "test.jpg",
            },
            format="multipart",
        )
        assert response.status_code == 200
        assert response.context["form"].errors["nic_number"] == [
            "Invalid National Identity Card Number."
        ]

    def test_signer_user_existing_nic(
        self,
        authenticated_signer_client,
        signer,
        signer2,
    ):
        """Test with existing NIC."""
        signer.public_key = None
        signer2.nic_number = "922971307V"
        signer2.save()
        cert_file_path = "CertExchangechanukachathuranga.fdf"
        with open(settings.TEST_FILES_ROOT + f"/{cert_file_path}", "rb") as fdf_file:
            with open(settings.TEST_FILES_ROOT + "/NIC.pdf", "rb") as nic_image:
                with open(
                    settings.TEST_FILES_ROOT + "/profile-pic.jpg", "rb"
                ) as profile_image:
                    response = authenticated_signer_client.post(
                        reverse("accounts:add-signer", kwargs={"pk": signer.pk}),
                        {
                            "certificate": fdf_file,
                            "nic_number": "922971307V",
                            "nic_image": nic_image,
                            "profile_image": profile_image,
                        },
                        format="multipart",
                    )
                    assert response.status_code == 200
                    assert response.context["form"].errors["nic_number"] == [
                        "This National Identity Card Number is already used, with a different user."
                    ]

    def test_signer_user_existing_public_key(
        self,
        authenticated_signer_client,
        signer,
        signer2,
    ):
        """Test with existing Public key of another signer."""
        cert_file_path = "kavinduLakith.cer"
        with open(settings.TEST_FILES_ROOT + f"/{cert_file_path}", "rb") as fdf_file:
            with open(settings.TEST_FILES_ROOT + "/NIC.pdf", "rb") as nic_image:
                with open(
                    settings.TEST_FILES_ROOT + "/profile-pic.jpg", "rb"
                ) as profile_image:
                    response = authenticated_signer_client.post(
                        reverse("accounts:add-signer", kwargs={"pk": signer.pk}),
                        {
                            "certificate": fdf_file,
                            "nic_number": "922971307V",
                            "nic_image": nic_image,
                            "profile_image": profile_image,
                        },
                        format="multipart",
                    )
                    assert response.status_code == 200
                    assert response.context["form"].errors["certificate"] == [
                        "This certificate is already used, with a different user."
                    ]

    def test_signer_user_update_without_required_feilds(
        self,
        authenticated_signer_client,
        signer,
    ):
        """Test withour required fields."""
        fields = [
            "nic_number",
            "certificate",
            "nic_image",
            "profile_image",
        ]
        response = authenticated_signer_client.post(
            reverse("accounts:add-signer", kwargs={"pk": signer.pk}),
            format="multipart",
        )
        assert response.status_code == 200
        for field in fields:
            assert response.context["form"].errors[field] == ["This field is required."]

    @pytest.mark.parametrize(
        "cert_file_name",
        [
            "CertExchangechanukachathuranga.fdf",
            "CertExchangechanukachathuranga.cer",
            "CertExchangechanukachathuranga.p7c",
        ],
    )
    def test_signer_user_update_for_valid_data_with_different_certs(
        self, authenticated_signer_client, signer, cert_file_name
    ):
        """Test with valid data with different certifications."""
        public_key = signer.public_key
        nic_number = "922971307V"
        nic_image_name = "NIC"
        pp_name = "profile-pic"
        signer.public_key = None
        signer.save()
        with open(settings.TEST_FILES_ROOT + f"/{cert_file_name}", "rb") as cert_file:
            with open(
                settings.TEST_FILES_ROOT + f"/{nic_image_name}.pdf", "rb"
            ) as nic_image:
                with open(
                    settings.TEST_FILES_ROOT + f"/{pp_name}.jpg", "rb"
                ) as profile_image:
                    response = authenticated_signer_client.post(
                        reverse("accounts:add-signer", kwargs={"pk": signer.pk}),
                        {
                            "certificate": cert_file,
                            "nic_number": nic_number,
                            "nic_image": nic_image,
                            "profile_image": profile_image,
                        },
                        format="multipart",
                    )
                    assert response.status_code == 302
                    signer.refresh_from_db()
                    assert signer.public_key == public_key
                    assert signer.nic_number == nic_number
                    assert nic_image_name in signer.nic_image.name
                    assert pp_name in signer.profile_image.name

# -*- coding: utf-8 -*-
from django import forms
from django.contrib.auth.forms import UserCreationForm
import re

from validator.logger import module_logger
from .models import CustomUser, SignerUser
from .services.pbs_extractor_service import PublicKeyExtractor

logger = module_logger(__name__)


class CustomUserCreationForm(UserCreationForm):
    """Custom User Creation Form."""

    user_type = forms.ChoiceField(
        label="User Type",
        choices=CustomUser.UserType.choices,
        initial=CustomUser.UserType.signer,
    )

    class Meta:
        model = CustomUser
        fields = ("username", "email", "user_type", "first_name", "last_name")
        widgets = {
            "password": forms.PasswordInput(),
        }


class SignerUserForm(forms.ModelForm):
    """Signer User ModelForm class."""

    class Meta:
        """Metaclass for SignerUserForm."""

        model = SignerUser
        fields = ("nic_number", "certificate", "nic_image", "profile_image")
        labels = {
            "nic_number": "National Identity Card Number",
            "certificate": "Certificate",
            "nic_image": "National Identity Card Image",
            "profile_image": "Profile Image",
        }

    def __init__(self, *args, **kwargs):
        """Initialize the form with user object."""
        self.user = kwargs.pop("user", None)
        self.calculated_public_key = None
        super().__init__(*args, **kwargs)

    def clean_nic_number(self):
        """Validate the National Identity Card Number."""
        nic_number = self.cleaned_data.get("nic_number")
        if not nic_number:
            raise forms.ValidationError("National Identity Card Number is required.")
        if not re.match(r"^([0-9]{9}[x|X|v|V]|[0-9]{12})$", nic_number):
            raise forms.ValidationError("Invalid National Identity Card Number.")
        if (
            SignerUser.objects.filter(nic_number=nic_number)
            .exclude(user=self.user)
            .exists()
        ):
            raise forms.ValidationError(
                "This National Identity Card Number is already used,"
                " with a different user."
            )
        return nic_number

    def clean_certificate(self):
        """Validate the certificate."""
        certificate = self.cleaned_data.get("certificate")
        if certificate:
            if certificate.name.split(".")[-1] not in ["fdf", "cer", "p7c"]:
                raise forms.ValidationError(
                    "Invalid certificate file type. Only .fdf, .cer, .p7c are allowed."
                )
            try:
                self.calculated_public_key = PublicKeyExtractor(
                    certificate.name, certificate.read()
                ).get_public_key()
            except Exception as e:
                logger.error(f"Error while extracting public key: {e}")
                raise forms.ValidationError("Invalid certificate.")
        else:
            raise forms.ValidationError("Certificate is required.")
        if (
            SignerUser.objects.filter(public_key=self.calculated_public_key)
            .exclude(user=self.user)
            .exists()
        ):
            raise forms.ValidationError(
                "This certificate is already used, with a different user."
            )
        return certificate

    def save(self, commit=True):
        """Override save method to save the calculated public key."""
        instance = super().save()
        if self.calculated_public_key is not None:
            instance.public_key = self.calculated_public_key
        return instance

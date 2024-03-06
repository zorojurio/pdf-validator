from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class CustomUser(AbstractUser):
    """Custom User Model."""

    class UserType(models.TextChoices):
        signer = ('signer', 'Signer')
        validator = ('validator', 'Validator')
    user_type = models.CharField(
        max_length=10,
        choices=UserType.choices,
        default=UserType.validator,
    )
    email = models.EmailField(_("email address"), unique=True)
    is_active = models.BooleanField(
        _("active"),
        default=False,
        help_text=_(
            "Designates whether this user should be treated as active. "
            "Unselect this instead of deleting accounts."
        ),
    )

    def __str__(self):
        return f'{self.username}-{self.email}'


class SignerUser(models.Model):
    public_key = models.TextField(
        unique=True,
        blank=True,
        null=True, help_text="Public key of the Signer")
    nic_number = models.CharField(
        max_length=15,
        help_text="National Identity Card Number of the Signer"
    )
    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="signer_user",
        blank=True,
        null=True
    )
    certificate = models.FileField(
        upload_to='certificates/',
        help_text="Certificate of the Signer"
    )
    nic_image = models.FileField(
        upload_to='nics/',
        help_text="National Identity Card Image of the Signer"
    )
    profile_image = models.FileField(
        upload_to='profile_images/',
        help_text="Profile Image of the Signer"
    )
    verification_email_sent = models.BooleanField(
        default=False,
        help_text="Verification email sent to the signer user"
    )
    active = models.BooleanField(
        default=False,
        help_text="Signer user is active or not"
    )
    rejected = models.BooleanField(
        default=False,
        help_text="Signer user is rejected or not"
    )

    def __str__(self):
        return f'{self.pk}'


class ValidatorUser(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name="validator_user")
    organization = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f'{self.user.username}-{self.user.email}'

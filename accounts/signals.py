import os

from django.conf import settings
from django.core.files import File
from django.core.mail import send_mail
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import SignerUser


@receiver(post_save, sender=SignerUser)
def create_profile(sender, instance, created, **kwargs):
    """Signal to create a QCStock instance when a Product is created."""
    #     You have been verified as a signer
    if not created:
        if instance.active:
            send_mail(
                "Signer Verification",
                "You have been verified as a signer",
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[instance.user.email],
            )
        if instance.rejected:
            send_mail(
                "Signer Verification",
                "You have been rejected as a signer",
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[instance.user.email],
            )

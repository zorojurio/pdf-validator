# -*- coding: utf-8 -*-
from django.conf import settings
from django.core.mail import send_mail
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import SignerUser, CustomUser, ValidatorUser


@receiver(post_save, sender=SignerUser)
def send_verified_or_rejected_email(sender, instance, created, **kwargs):
    """Signal to send email to the signer user when verified or rejected."""
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


@receiver(post_save, sender=CustomUser)
def create_signer_validator_profile(sender, instance, created, **kwargs):
    """Signal to create signer or validator profile when user is created."""
    if created:
        if instance.user_type == CustomUser.UserType.signer:
            signer = SignerUser.objects.create(user=instance)
            signer.verification_email_sent = True
            signer.save()
        elif instance.user_type == CustomUser.UserType.validator:
            ValidatorUser.objects.create(user=instance)

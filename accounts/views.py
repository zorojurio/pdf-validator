# -*- coding: utf-8 -*-
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.core.mail import EmailMessage, mail_admins, send_mail
from django.shortcuts import redirect
from django.template.loader import render_to_string
from django.urls import reverse_lazy, reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.views.generic import UpdateView
from django.views.generic.edit import CreateView
from django_filters.views import FilterView

from validator import settings
from .filters import SignerUserFilter
from .forms import CustomUserCreationForm, SignerUserForm
from .models import CustomUser, SignerUser
from .tokens import account_activation_token


class CustomLoginView(LoginView):
    """Override LoginView to specify template name."""

    template_name = "accounts/login.html"


class SignUpView(CreateView):
    """View for user signup."""

    form_class = CustomUserCreationForm
    template_name = "accounts/signup.html"

    def form_valid(self, form):
        """Save the form and send activation email."""
        user = form.save()

        current_site = self.request.build_absolute_uri("/")[:-1]
        mail_subject = "Activation link has been sent to your email."
        message = render_to_string(
            template_name="accounts/account_activation_email.html",
            context={
                "user": user,
                "domain": current_site,
                "uid": urlsafe_base64_encode(force_bytes(user.pk)),
                "token": account_activation_token.make_token(user),
            },
        )
        to_email = form.cleaned_data.get("email")
        email = EmailMessage(mail_subject, message, to=[to_email])
        email.send()
        messages.success(
            self.request,
            "Please confirm your email address to complete the registration",
        )
        return super().form_valid(form)

    def get_success_url(self):
        """Get the success URL for the view."""
        return reverse_lazy("accounts:login")


class SignerUserView(LoginRequiredMixin, UpdateView):
    """View for adding signer user."""

    form_class = SignerUserForm
    success_url = reverse_lazy("accounts:login")
    template_name = "accounts/signer.html"

    def get_success_url(self):
        """Get the success URL for the view."""
        return reverse_lazy("signature-validator-view:validate-signature")

    def form_valid(self, form):
        """Save the form and send emails to admin and signer."""
        signer_user = form.save(commit=False)
        signer_user.user = self.request.user
        signer_user.save()
        self.request.get_full_path()
        host = self.request.build_absolute_uri("/")[:-1]
        url = reverse(
            viewname="admin:accounts_signeruser_change",
            args=[self.request.user.signer_user.pk],
        )

        if signer_user.public_key:
            # sending emails to admin to verify the signer
            mail_admins(
                subject=f"Check Verification of Signer {self.request.user.username}",
                message=f"A new signer has been joined, please verify and accept. \n"
                f"Username: {self.request.user.username} \n"
                f"Email: {self.request.user.email} \n"
                f"{host + url}",
                fail_silently=False,
            )
            # sending email to the signer about verification process
            send_mail(
                subject="Signer Verification",
                message="Your verification as a signer is under process, we will notify you soon.",
                recipient_list=[self.request.user.email],
                from_email=settings.EMAIL_HOST_USER,
                fail_silently=False,
            )
            messages.warning(
                self.request,
                "Your verification is under process, we will notify you soon.",
            )
        return super().form_valid(form)

    def get_form_kwargs(self):
        """Get the form kwargs for the view to add logged-in user."""
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_queryset(self):
        """Get the queryset for the view."""
        return SignerUser.objects.filter(user=self.request.user)


def activate(request, uidb64, token):
    """Activate the user account."""
    try:
        uid = urlsafe_base64_decode(force_bytes(uidb64).decode("utf-8")).decode("utf-8")
        user = CustomUser.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, CustomUser.DoesNotExist):
        user = None
    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(
            request,
            "Thank you for your email confirmation. "
            "Now you can login to your account.",
        )
        if user.user_type == CustomUser.UserType.signer:
            return redirect(
                reverse_lazy("accounts:add-signer", kwargs={"pk": user.signer_user.pk})
            )
        return redirect(reverse_lazy("accounts:login"))
    else:
        messages.error(request, "Activation link is invalid!")
        return redirect(reverse_lazy("accounts:login"))


class SignerUserListView(FilterView):
    """View for listing all the signers with filters."""

    template_name = "accounts/signer_list.html"
    model = SignerUser
    context_object_name = "signers"
    filterset_class = SignerUserFilter
    paginate_by = 10

    def get_queryset(self):
        """Get the queryset for the view."""
        return SignerUser.objects.filter(active=True)

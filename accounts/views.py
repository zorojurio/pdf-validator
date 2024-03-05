import time

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
from .models import CustomUser, SignerUser, ValidatorUser
from .tokens import account_activation_token


class CustomLoginView(LoginView):
    """Override LoginView to specify template name."""
    template_name = "accounts/login.html"


class SignUpView(CreateView):
    form_class = CustomUserCreationForm
    template_name = 'accounts/signup.html'

    def form_valid(self, form):
        user = form.save()
        if user.user_type == CustomUser.UserType.signer:
            signer = SignerUser.objects.create(user=user)
            signer.verification_email_sent = True
            signer.save()
        elif user.user_type == CustomUser.UserType.validator:
            ValidatorUser.objects.create(user=user)
        current_site = self.request.build_absolute_uri('/')[:-1]
        mail_subject = 'Activation link has been sent to your email.'
        message = render_to_string(template_name='accounts/account_activation_email.html', context={
            'user': user,
            'domain': current_site,
            'uid': urlsafe_base64_encode(force_bytes(user.pk)),
            'token': account_activation_token.make_token(user),
        })
        to_email = form.cleaned_data.get('email')
        email = EmailMessage(
            mail_subject, message, to=[to_email]
        )
        email.send()
        messages.success(
            self.request,
            'Please confirm your email address to complete the registration'
        )
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('accounts:login')


class SignerUserView(LoginRequiredMixin, UpdateView):
    form_class = SignerUserForm
    success_url = reverse_lazy('accounts:login')
    template_name = 'accounts/signer.html'

    def get_success_url(self):
        return reverse_lazy('signature-validator-view:validate-signature')

    def form_valid(self, form):
        signer_user = form.save(commit=False)
        signer_user.user = self.request.user
        signer_user.save()
        self.request.get_full_path()
        host = self.request.build_absolute_uri('/')[:-1]
        url = reverse(
            viewname='admin:accounts_signeruser_change',
            args=[self.request.user.signer_user.pk]
        )

        if signer_user.public_key:
            mail_admins(
                subject=f'Check Verification of Signer {self.request.user.username}',
                message=f"A new signer has been joined, please verify and accept. \n"
                        f"Username: {self.request.user.username} \n"
                        f"Email: {self.request.user.email} \n"
                        f"{host + url}",
                fail_silently=False,
            )
            send_mail(
                subject='Signer Verification',
                message=f"Your verification as a signer is under process, we will notify you soon.",
                recipient_list=[self.request.user.email],
                from_email=settings.EMAIL_HOST_USER,
                fail_silently=False,
            )
            messages.warning(
                self.request,
                "Your verification is under process, we will notify you soon.")
        return super().form_valid(form)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_queryset(self):
        return SignerUser.objects.filter(user=self.request.user)


def activate(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(force_bytes(uidb64).decode('utf-8')).decode('utf-8')
        user = CustomUser.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, CustomUser.DoesNotExist):
        user = None
    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(
            request,
            'Thank you for your email confirmation. Now you can login to your account.'
        )
        if user.user_type == CustomUser.UserType.signer:
            time.sleep(10)
            return redirect(reverse_lazy('accounts:add-signer', kwargs={'pk': user.signer_user.pk}))
        return redirect(reverse_lazy('accounts:login'))
    else:
        messages.error(
            request,
            'Activation link is invalid!'
        )
        return redirect(reverse_lazy('accounts:login'))


class SignerUserListView(FilterView):
    template_name = 'accounts/signer_list.html'
    model = SignerUser
    context_object_name = 'signers'
    filterset_class = SignerUserFilter
    paginate_by = 10

    def get_queryset(self):
        return SignerUser.objects.filter(active=True)


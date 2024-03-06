from django import forms
from django.contrib.auth.forms import UserCreationForm
import re
from .models import CustomUser, SignerUser
from .services.pbs_extractor_service import PublicKeyExtractor


class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'user_type', 'first_name', 'last_name')
        widgets = {
            'password': forms.PasswordInput(),
        }


class SignerUserForm(forms.ModelForm):
    class Meta:
        model = SignerUser
        fields = ('nic_number', 'certificate', 'nic_image', 'profile_image')
        labels = {
            'nic_number': 'National Identity Card Number',
            'certificate': 'Certificate',
            'nic_image': 'National Identity Card Image',
            'profile_image': 'Profile Image',
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.calculated_public_key = None
        super().__init__(*args, **kwargs)

    def clean_nic_number(self):
        nic_number = self.cleaned_data.get('nic_number')
        if not nic_number:
            raise forms.ValidationError("National Identity Card Number is required.")
        if not re.match(r'^([0-9]{9}[x|X|v|V]|[0-9]{12})$', nic_number):
            raise forms.ValidationError("Invalid National Identity Card Number.")
        if SignerUser.objects.filter(nic_number=nic_number).exclude(
                user=self.user
        ).exists():
            raise forms.ValidationError(
                "This National Identity Card Number is already used, with a different user."
            )
        return nic_number

    def clean_certificate(self):
        certificate = self.cleaned_data.get('certificate')
        if certificate:
            if certificate.name.split('.')[-1] not in ['fdf', 'cer', 'p7c']:
                raise forms.ValidationError(
                    f"Invalid certificate file type. Only .fdf, .cer, .p7c are allowed."
                )
            try:
                self.calculated_public_key = PublicKeyExtractor(
                    certificate.name,
                    certificate.read()
                ).get_public_key()
                print(certificate.name, self.calculated_public_key)
            except Exception as e:
                raise forms.ValidationError("Invalid certificate.")
        else:
            raise forms.ValidationError("Certificate is required.")
        if SignerUser.objects.filter(public_key=self.calculated_public_key).exclude(
            user=self.user
        ).exists():
            raise forms.ValidationError(
                "This certificate is already used, with a different user."
            )
        return certificate

    def save(self, commit=True):
        instance = super().save()
        if self.calculated_public_key is not None:
            instance.public_key = self.calculated_public_key
        return instance

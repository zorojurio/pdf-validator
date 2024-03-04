import django_filters
from .models import SignerUser


class SignerUserFilter(django_filters.FilterSet):
    nic_number = django_filters.CharFilter(lookup_expr='contains')
    email = django_filters.CharFilter(lookup_expr='contains', field_name='user__email')
    public_key = django_filters.CharFilter(lookup_expr='contains')

    class Meta:
        model = SignerUser
        fields = ['public_key', 'nic_number', 'email']

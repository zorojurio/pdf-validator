import factory
from django.contrib.auth import get_user_model

from accounts.models import CustomUser


class UserFactory(factory.django.DjangoModelFactory):
    """User model factory."""

    username = factory.Faker("first_name")
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    email = factory.Faker("email")
    user_type = CustomUser.UserType.signer
    is_active = True

    class Meta:
        model = get_user_model()

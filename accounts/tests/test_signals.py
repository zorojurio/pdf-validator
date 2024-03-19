import pytest
from django.apps import apps

from accounts.tests.factories import UserFactory


class TestCustomUserSignal:
    """Test the Custom User signal."""

    @pytest.mark.parametrize(
        "user_type, related_model",
        [
            ("signer", "SignerUser"),
            ("validator", "ValidatorUser"),
        ],
    )
    @pytest.mark.django_db
    def test_signer_user_created(self, user_type, related_model):
        """Test whether the signer user is created or not."""
        user = UserFactory(
            user_type=user_type,
        )
        Model = apps.get_model("accounts", related_model)
        assert Model.objects.filter(user=user).exists()

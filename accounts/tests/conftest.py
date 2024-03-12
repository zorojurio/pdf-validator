import pytest

from accounts.tests.factories import UserFactory


@pytest.fixture
def signer_activated_user():
    """Return an active signer user."""
    return UserFactory(is_active=True, username="signer_activated_user")


@pytest.fixture
def authenticated_signer_client(client, signer_activated_user):
    """Return an active user."""
    client.force_login(signer_activated_user)
    return client

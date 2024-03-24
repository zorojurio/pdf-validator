import pytest

from accounts.models import SignerUser
from accounts.services.pbs_extractor_service import PublicKeyExtractor
from accounts.tests.factories import UserFactory
from validator import settings


@pytest.fixture
def activated_user_signer_type():
    """Return an active signer user."""
    return UserFactory(is_active=True, username="signer_activated_user")


@pytest.fixture
def authenticated_signer_client(client, activated_user_signer_type):
    """Return an active user."""
    client.force_login(activated_user_signer_type)
    return client


@pytest.fixture
def signer(activated_user_signer_type):
    """Return an active signer user with public key."""
    cert_file_path = "CertExchangechanukachathuranga.fdf"
    with open(settings.TEST_FILES_ROOT + f"/{cert_file_path}", "rb") as fdf_file:
        pbs_extractor = PublicKeyExtractor(cert_file_path, fdf_file.read())
        pb_key = pbs_extractor.get_public_key()
    signer: SignerUser = SignerUser.objects.get(user=activated_user_signer_type)
    signer.public_key = pb_key
    signer.active = True
    signer.save()
    return signer

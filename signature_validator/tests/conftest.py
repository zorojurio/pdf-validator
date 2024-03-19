import pytest

from django.core.files.uploadedfile import SimpleUploadedFile


@pytest.fixture
def doc_file():
    """Return a file."""
    doc_file = SimpleUploadedFile(
        "sample.doc", b"Sample Word Document Content", content_type="application/msword"
    )
    return doc_file

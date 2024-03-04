from rest_framework import viewsets
from rest_framework.permissions import AllowAny

from signature_validator.models import SignatureValidator, PdfDocumentValidator
from signature_validator.serializers import PdfValidateSerializer


class PdfValidateViewSet(viewsets.ModelViewSet):
    """Viewset to validate PDF documents."""

    permission_classes = [AllowAny]
    serializer_class = PdfValidateSerializer

    def get_serializer_context(self):
        """Pass the request object to the serializer."""
        context = super().get_serializer_context()
        context.update({"user": self.request.user})
        return context

    def get_queryset(self):
        """Return active signer users."""
        return PdfDocumentValidator.objects.all()

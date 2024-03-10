# -*- coding: utf-8 -*-
from rest_framework import viewsets
from rest_framework.permissions import AllowAny, IsAdminUser

from accounts.models import SignerUser
from accounts.permissions import IsOwnerOrReadOnly
from accounts.serializers import SignerUserSerializer


class SignerUserViewSet(viewsets.ModelViewSet):
    """Viewset for signer user model."""

    permission_classes = []
    serializer_class = SignerUserSerializer

    def get_permissions(self):
        """Handle the permissions for the viewset."""
        if self.action == "create":
            return [AllowAny()]
        else:
            # only admin users and owner of the object can perform the action
            return [IsOwnerOrReadOnly(), IsAdminUser()]

    def get_queryset(self):
        """Return active signer users."""
        return SignerUser.objects.filter(user__is_active=True)

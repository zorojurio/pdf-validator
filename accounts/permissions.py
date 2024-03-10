# -*- coding: utf-8 -*-
from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsSigner(BasePermission):
    """Allows access only to signer type users."""

    def has_permission(self, request, view):
        """Check if the user is a signer and user is authenticated."""
        if request.user and request.user.is_authenticated:
            if request.user.is_signer:
                return True
        return False


class IsValidator(BasePermission):
    """Allows access only to validator type users."""

    def has_permission(self, request, view):
        """Check if the user is a validator and user is authenticated."""
        if request.user and request.user.is_authenticated:
            if request.user.is_validator:
                return True
        return False


class IsOwnerOrReadOnly(BasePermission):
    """Object-level permission to only allow owners of an object to edit it.

    Assumes the model instance has an `owner` attribute.
    """

    def has_object_permission(self, request, view, obj):
        """Check if the user is the owner of the object."""
        if request.method in SAFE_METHODS:
            # so we'll always allow GET, HEAD or OPTIONS requests.
            return True
        # Instance must have an attribute named `owner` if request methods are post, patch, put.
        return obj.owner == request.user

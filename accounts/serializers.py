from rest_framework import serializers

from accounts.models import SignerUser, CustomUser


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = (
            "id",
            "username",
            "email",
            "password",
            "first_name",
            "last_name",
            "is_active",
        )
        extra_kwargs = {"password": {"write_only": True}}
        read_only_fields = ("id", "is_active")


class SignerUserSerializer(serializers.ModelSerializer):
    """Serializer for signer user model."""

    user = UserSerializer()

    class Meta:
        """Meta-class for SignerUserSerializer."""

        model = SignerUser
        fields = (
            "id",
            "public_key",
            "user",
        )
        read_only_fields = ("id",)

    def create(self, validated_data):
        """Create the signer user."""
        user_data = validated_data.pop("user")
        user = CustomUser.objects.create_user(**user_data)
        signer_user = SignerUser.objects.create(user=user, **validated_data)
        return signer_user

# -*- coding: utf-8 -*-
from django.apps import AppConfig


class AccountsConfig(AppConfig):
    """App configuration for accounts."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "accounts"

    def ready(self):
        """Import signals so signals can be used."""
        import accounts.signals  # noqa

# -*- coding: utf-8 -*-
from django.contrib.auth.views import LogoutView
from django.urls import path
from accounts.views import (
    CustomLoginView,
    SignUpView,
    SignerUserView,
    activate,
    SignerUserListView,
)

app_name = "accounts"
urlpatterns = [
    path("login/", CustomLoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("signup/", SignUpView.as_view(), name="signup"),
    path("<int:pk>/add-signer/", SignerUserView.as_view(), name="add-signer"),
    path("activate/<uidb64>/<token>/", activate, name="activate"),
    path("signers/", SignerUserListView.as_view(), name="signers"),
]

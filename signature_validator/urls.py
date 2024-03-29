# -*- coding: utf-8 -*-
from django.urls import path

from signature_validator.views import (
    ValidateSignatureView,
    PDFResultView,
    ValidatedPDFListView,
    ReportView,
)


app_name = "signature-validator-view"
urlpatterns = [
    path("", ValidateSignatureView.as_view(), name="validate-signature"),
    path("pdf-result/<int:pk>/", PDFResultView.as_view(), name="pdf-result"),
    path(
        "pdf-validated_list", ValidatedPDFListView.as_view(), name="validated-pdf-list"
    ),
    path("report", ReportView.as_view(), name="report"),
]

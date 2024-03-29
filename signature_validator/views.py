# -*- coding: utf-8 -*-
from datetime import timedelta

import pdfkit
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.urls import reverse
from django.utils import timezone

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import QuerySet
from django.views.generic import CreateView, DetailView, ListView, TemplateView

from accounts.models import CustomUser, SignerUser

from .forms import PdfValidateForm
from .models import PdfDocumentValidator


class ValidateSignatureView(LoginRequiredMixin, CreateView):
    """View to validate the signature of the PDF."""

    form_class = PdfValidateForm
    template_name = "signature_validator/home.html"

    def get_success_url(self):
        """Get the success URL."""
        return self.object.get_absolute_url()

    def get_form_kwargs(self):
        """Get the form kwargs set request."""
        kwargs = super(ValidateSignatureView, self).get_form_kwargs()
        kwargs["request"] = self.request
        return kwargs


class PDFResultView(LoginRequiredMixin, DetailView):
    """View to show the result of the PDF validation."""

    model = PdfDocumentValidator
    template_name = "signature_validator/pdf_result.html"

    def get_context_data(self, **kwargs):
        """Get the context data to template."""
        context = super().get_context_data(**kwargs)
        context["pdf_restult"] = self.get_object()
        return context


class PDFResultReportView(DetailView):
    """View to show the result of the PDF validation."""

    model = PdfDocumentValidator
    template_name = "signature_validator/pdf_validation_report_with_styles.html"

    def get_context_data(self, **kwargs):
        """Get the context data to template."""
        context = super().get_context_data(**kwargs)
        context["pdf_restult"] = self.get_object()
        return context


class ValidatedPDFListView(LoginRequiredMixin, ListView):
    """View to show the list of validated PDFs."""

    model = PdfDocumentValidator
    template_name = "signature_validator/pdf_list.html"
    context_object_name = "pdf_list"
    paginate_by = 10

    def get_queryset(self):
        """Get the queryset for the view filtered by logged in user."""
        return PdfDocumentValidator.objects.filter(user=self.request.user).order_by(
            "-created"
        )


class ReportView(TemplateView):
    """View to show the report of the validated PDFs."""

    template_name = "signature_validator/report.html"

    def get_context_data(self, **kwargs):
        """Get the context data for the view."""
        context = super().get_context_data(**kwargs)
        validated_pdf: QuerySet[PdfDocumentValidator] = (
            PdfDocumentValidator.objects.all()
        )
        context["pdf_docs_tested"] = validated_pdf.count()
        context["verified_pdf"] = validated_pdf.filter(
            all_signers_verified=True
        ).count()
        context["pdf_not_verified"] = validated_pdf.filter(
            all_signers_verified=False
        ).count()
        context["users_count"] = CustomUser.objects.all().count()
        context["signers_count"] = SignerUser.objects.all().count()
        context["today_date"] = timezone.now().date()
        signed_documents_data = []
        days = []

        for i in range(0, 5):
            current_day = timezone.now() - timedelta(days=i)
            start_of_day = current_day.replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            end_of_day = current_day.replace(
                hour=23, minute=59, second=59, microsecond=999999
            )
            signed_documents_count = PdfDocumentValidator.objects.filter(
                is_signed=True, created__range=(start_of_day, end_of_day)
            ).count()
            signed_documents_data.append(signed_documents_count)
            days.append(str(current_day.date()))
        context["signed_documents_labels"] = days
        context["signed_documents_data"] = signed_documents_data

        users_data = []
        users_label = []
        for i in range(0, 6):
            current_day = timezone.now() - timedelta(days=i)
            start_of_day = current_day.replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            end_of_day = current_day.replace(
                hour=23, minute=59, second=59, microsecond=999999
            )
            users_joined_count = CustomUser.objects.filter(
                is_active=True, date_joined__range=(start_of_day, end_of_day)
            ).count()
            users_data.append(users_joined_count)
            users_label.append(str(current_day.date()))
        context["signed_documents_labels"] = days
        context["signed_documents_data"] = signed_documents_data
        context["users_data"] = users_data
        context["users_label"] = users_label
        return context


@login_required
def generate_pdf_report(request, *args, **kwargs):
    """Generate the PDF report of the validated PDFs."""
    pdf = pdfkit.from_url(
        request.build_absolute_uri(
            reverse(
                "signature-validator-view:pdf-result-report",
                kwargs={"pk": kwargs.get("pk")},
            )
        ),
        False,
    )
    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="report.pdf"'
    return response

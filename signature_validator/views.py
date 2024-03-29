# -*- coding: utf-8 -*-
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import QuerySet
from django.views.generic import CreateView, DetailView, ListView, TemplateView

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

    def get(self, request, *args, **kwargs):
        """Get method for the view."""
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        """Get the context data for the view."""
        context = super().get_context_data(**kwargs)
        validated_pdf: QuerySet[PdfDocumentValidator] = (
            PdfDocumentValidator.objects.all()
        )
        context["pdf_docs_tested"] = validated_pdf.count()
        validated_pdf.filter(all_signers_verified=True)
        return context

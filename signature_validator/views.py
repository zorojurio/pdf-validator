from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView, DetailView, ListView

from .forms import PdfValidateForm
from .models import PdfDocumentValidator


class ValidateSignatureView(LoginRequiredMixin, CreateView):
    form_class = PdfValidateForm
    # success_url = reverse_lazy('accounts:login')
    template_name = "signature_validator/home.html"

    def get_success_url(self):
        return self.object.get_absolute_url()

    def get_form_kwargs(self):
        kwargs = super(ValidateSignatureView, self).get_form_kwargs()
        kwargs["request"] = self.request
        return kwargs


class PDFResultView(LoginRequiredMixin, DetailView):
    model = PdfDocumentValidator
    template_name = "signature_validator/pdf_result.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["pdf_restult"] = self.get_object()
        return context


class ValidatedPDFListView(LoginRequiredMixin, ListView):
    model = PdfDocumentValidator
    template_name = "signature_validator/pdf_list.html"
    context_object_name = "pdf_list"
    paginate_by = 10

    def get_queryset(self):
        return PdfDocumentValidator.objects.filter(user=self.request.user).order_by(
            "-created"
        )

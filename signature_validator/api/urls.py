from rest_framework.routers import DefaultRouter


from signature_validator.api.views import PdfValidateViewSet


router = DefaultRouter()
router.register("signatures", PdfValidateViewSet, "signatures")


urlpatterns = router.urls

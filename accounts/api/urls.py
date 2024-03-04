from rest_framework.routers import DefaultRouter

from accounts.api.views import SignerUserViewSet


router = DefaultRouter()
router.register("signers", SignerUserViewSet, "signers")


urlpatterns = router.urls

from django.urls import path
from rest_framework.routers import DefaultRouter

from users.views import (PaymentCreateAPIView, PaymentListAPIView,
                         ProfileUpdateView, UserViewSet)

app_name = "users"

router = DefaultRouter()
router.register(r"users", UserViewSet, basename="user")

urlpatterns = [
    path("profile/", ProfileUpdateView.as_view(), name="profile-update"),
    path("payments/", PaymentListAPIView.as_view(), name="payment-list"),
    path("payments/create/", PaymentCreateAPIView.as_view(), name="payment-create"),
] + router.urls

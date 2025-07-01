from rest_framework.routers import DefaultRouter
from users.views import UserViewSet, ProfileUpdateView, PaymentListAPIView
from django.urls import path

app_name = "users"

router = DefaultRouter()
router.register(r"users", UserViewSet, basename="user")
router.register(r"payments", PaymentListAPIView, basename="payment")

urlpatterns = [
                  path("profile/", ProfileUpdateView.as_view(), name="profile-update"),
                  path("payments/", PaymentListAPIView.as_view(), name="payment-list"),
              ] + router.urls

from rest_framework.routers import DefaultRouter
from users.views import UserViewSet, ProfileUpdateView
from django.urls import path


app_name = "users"

router = DefaultRouter()
router.register(r"users", UserViewSet, basename="user")

urlpatterns = router.urls

urlpatterns = [
    path("profile/", ProfileUpdateView.as_view(), name="profile-update"),
] + router.urls
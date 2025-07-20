from django.contrib import admin
from django.urls import include, path, re_path
# from rest_framework_simplejwt.views import (TokenObtainPairView,
#                                             TokenRefreshView)
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from skillshare_platform.views import CustomTokenObtainPairView, CustomTokenRefreshView
from django.views.generic import RedirectView

urlpatterns = [
re_path(r'^$', RedirectView.as_view(url='/api/schema/swagger-ui/', permanent=False)),
    path("admin/", admin.site.urls),
    path("api/", include("materials.urls")),
    path("api/", include("users.urls")),
    path(
        "api/token/",
        CustomTokenObtainPairView.as_view(),
        name="token_obtain_pair"
    ),
    path(
        "api/token/refresh/",
        CustomTokenRefreshView.as_view(),
        name="token_refresh",
    ),

    # Пути для документации DRF Spectacular
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/schema/swagger-ui/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
]

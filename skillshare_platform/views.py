from drf_spectacular.utils import extend_schema
from rest_framework_simplejwt.views import (TokenObtainPairView,
                                            TokenRefreshView)


@extend_schema(
    summary="Получение Access и Refresh токенов",
    description="Принимает учетные данные пользователя (email, password) и возвращает Access и Refresh токены для аутентификации.",
)
class CustomTokenObtainPairView(TokenObtainPairView):
    pass


@extend_schema(
    summary="Обновление Access Token",
    description="Принимает Refresh Token и возвращает новый Access Token, если Refresh Token действителен.",
)
class CustomTokenRefreshView(TokenRefreshView):
    pass

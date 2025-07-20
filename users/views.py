from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiTypes

from users.models import Payment, User
from users.permissions import IsOwnerOrModerator
from users.serializers import PaymentSerializer, UserSerializer


@extend_schema(tags=["Users"])
class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet для CRUD операций с пользователями (включая редактирование профиля).
    """

    queryset = User.objects.all()
    serializer_class = UserSerializer

    @extend_schema(
        summary="Создание нового пользователя",
        description="Регистрация нового пользователя (доступно без аутентификации).",
        request=UserSerializer,
        responses={201: UserSerializer, 400: {"description": "Ошибка валидации"}},
        auth=[],
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @extend_schema(
        summary="Получение списка пользователей",
        description="Получает список всех зарегистрированных пользователей (требуется аутентификация).",
        responses={200: UserSerializer(many=True)},
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        summary="Получение деталей пользователя",
        description="Получает подробную информацию о конкретном пользователе. Включает историю платежей для владельца профиля.",
        parameters=[
            OpenApiParameter(name='id', type=OpenApiTypes.INT, description='ID пользователя')
        ],
        responses={
            200: UserSerializer,
            401: {"description": "Неавторизованный доступ"},
            404: {"description": "Пользователь не найден"}
        },
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        summary="Полное обновление данных пользователя",
        description="Полное обновление данных конкретного пользователя. Доступно только владельцу профиля, модератору или администратору.",
        parameters=[
            OpenApiParameter(name='id', type=OpenApiTypes.INT, description='ID пользователя')
        ],
        request=UserSerializer,
        responses={
            200: UserSerializer,
            400: {"description": "Ошибка валидации"},
            401: {"description": "Неавторизованный доступ"},
            403: {"description": "Доступ запрещен"},
            404: {"description": "Пользователь не найден"}
        },
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @extend_schema(
        summary="Частичное обновление данных пользователя",
        description="Частичное обновление данных конкретного пользователя. Доступно только владельцу профиля, модератору или администратору.",
        parameters=[
            OpenApiParameter(name='id', type=OpenApiTypes.INT, description='ID пользователя')
        ],
        request=UserSerializer,
        responses={
            200: UserSerializer,
            400: {"description": "Ошибка валидации"},
            401: {"description": "Неавторизованный доступ"},
            403: {"description": "Доступ запрещен"},
            404: {"description": "Пользователь не найден"}
        },
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(
        summary="Удаление пользователя",
        description="Удаление пользователя. Доступно только владельцу профиля или администратору.",
        parameters=[
            OpenApiParameter(name='id', type=OpenApiTypes.INT, description='ID пользователя')
        ],
        responses={
            204: {"description": "Пользователь успешно удален"},
            401: {"description": "Неавторизованный доступ"},
            403: {"description": "Доступ запрещен (модераторам удаление запрещено)"},
            404: {"description": "Пользователь не найден"}
        },
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)

    def get_permissions(self):
        """
        Создаёт экземпляр и возвращает список разрешений, необходимых для этого представления
        """
        if self.action == "create":
            perm_classes = [AllowAny]
        elif self.action in ["update", "partial_update", "destroy"]:
            # Разрешить обновление/удаление только владельцу профиля, модератору и администратору
            perm_classes = [IsAuthenticated, IsOwnerOrModerator]
        else:  # 'list', 'retrieve'
            # Авторизованные пользователи могут просматривать список и детали любого профиля
            perm_classes = [IsAuthenticated]
        return [permission() for permission in perm_classes]


@extend_schema(tags=["Users"])
class ProfileUpdateView(generics.RetrieveUpdateAPIView):
    """
    APIView для получения и обновления профиля текущего авторизованного пользователя.
    Пользователь может просматривать и редактировать только свой собственный профиль.
    """

    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

    @extend_schema(
        summary="Получение профиля текущего пользователя",
        description="Получает подробную информацию о профиле текущего авторизованного пользователя.",
        responses={200: UserSerializer, 401: {"description": "Неавторизованный доступ"}},
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(
        summary="Полное обновление профиля текущего пользователя",
        description="Полностью обновляет информацию о профиле текущего авторизованного пользователя.",
        request=UserSerializer,
        responses={200: UserSerializer, 400: {"description": "Ошибка валидации"},
                   401: {"description": "Неавторизованный доступ"}},
    )
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)

    @extend_schema(
        summary="Частичное обновление профиля текущего пользователя",
        description="Частично обновляет информацию о профиле текущего авторизованного пользователя.",
        request=UserSerializer(partial=True),
        responses={200: UserSerializer, 400: {"description": "Ошибка валидации"},
                   401: {"description": "Неавторизованный доступ"}},
    )
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)


@extend_schema(tags=["Payments"])
class PaymentListAPIView(generics.ListAPIView):
    """
    APIView для управления платежами с поддержкой фильтрации и сортировки.
    Позволяет:
    - Сортировать по дате оплаты (`payment_date`).
    - Фильтровать по курсу (`paid_course`) и уроку (`paid_lesson`).
    - Фильтровать по способу оплаты (`payment_method`).
    """

    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = {
        "paid_course": ["exact"],
        "paid_lesson": ["exact"],
        "payment_method": ["exact"],
    }
    ordering_fields = ["payment_date"]
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Получение списка платежей",
        description="Получает список всех платежей с возможностью фильтрации по курсу, уроку, способу оплаты и сортировки по дате.",
        parameters=[
            OpenApiParameter(name='paid_course', type=OpenApiTypes.INT, description='Фильтр по ID оплаченного курса',
                             required=False),
            OpenApiParameter(name='paid_lesson', type=OpenApiTypes.INT, description='Фильтр по ID оплаченного урока',
                             required=False),
            OpenApiParameter(name='payment_method', type=OpenApiTypes.STR,
                             description='Фильтр по способу оплаты (cash, transfer, make_qr_code)', required=False,
                             enum=["cash", "transfer", "make_qr_code"]),
            OpenApiParameter(name='ordering', type=OpenApiTypes.STR,
                             description='Порядок сортировки (-payment_date для убывания)', required=False)
        ],
        responses={200: PaymentSerializer(many=True), 401: {"description": "Неавторизованный доступ"}},
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

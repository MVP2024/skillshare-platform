from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated

from users.models import Payment, User
from users.permissions import IsOwnerOrModerator
from users.serializers import PaymentSerializer, UserSerializer


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet для CRUD операций с пользователями (включая редактирование профиля).
    """

    queryset = User.objects.all()
    serializer_class = UserSerializer

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


class ProfileUpdateView(generics.RetrieveUpdateAPIView):
    """
    APIView для получения и обновления профиля текущего авторизованного пользователя.
    Пользователь может просматривать и редактировать только свой собственный профиль.
    """

    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


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

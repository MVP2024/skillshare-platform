from django.shortcuts import render
from rest_framework import viewsets

from users.models import User
from users.serializers import UserSerializer
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import filters
from django_filters.rest_framework import DjangoFilterBackend
from users.models import Payment
from users.serializers import PaymentSerializer


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
        if self.action == 'create':
            perm_classes = [AllowAny]
        else:
            perm_classes = [IsAuthenticated]
        return [permission() for permission in perm_classes]


class ProfileUpdateView(generics.RetrieveUpdateAPIView):
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
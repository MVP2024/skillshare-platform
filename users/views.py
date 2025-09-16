import stripe
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import OpenApiParameter, OpenApiTypes, extend_schema
from rest_framework import filters, generics, status, viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from users.models import Payment, User
from users.permissions import IsOwnerOrModerator
from users.serializers import PaymentCreateSerializer, PaymentSerializer, UserSerializer
from users.services import (
    process_payment_and_create_stripe_session,
    retrieve_stripe_session,
)


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
            OpenApiParameter(
                name="id", type=OpenApiTypes.INT, description="ID пользователя"
            )
        ],
        responses={
            200: UserSerializer,
            401: {"description": "Неавторизованный доступ"},
            404: {"description": "Пользователь не найден"},
        },
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        summary="Полное обновление данных пользователя",
        description="Полное обновление данных конкретного пользователя. Доступно только владельцу профиля, модератору или администратору.",
        parameters=[
            OpenApiParameter(
                name="id", type=OpenApiTypes.INT, description="ID пользователя"
            )
        ],
        request=UserSerializer,
        responses={
            200: UserSerializer,
            400: {"description": "Ошибка валидации"},
            401: {"description": "Неавторизованный доступ"},
            403: {"description": "Доступ запрещен"},
            404: {"description": "Пользователь не найден"},
        },
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @extend_schema(
        summary="Частичное обновление данных пользователя",
        description="Частичное обновление данных конкретного пользователя. Доступно только владельцу профиля, модератору или администратору.",
        parameters=[
            OpenApiParameter(
                name="id", type=OpenApiTypes.INT, description="ID пользователя"
            )
        ],
        request=UserSerializer,
        responses={
            200: UserSerializer,
            400: {"description": "Ошибка валидации"},
            401: {"description": "Неавторизованный доступ"},
            403: {"description": "Доступ запрещен"},
            404: {"description": "Пользователь не найден"},
        },
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(
        summary="Удаление пользователя",
        description="Удаление пользователя. Доступно только владельцу профиля или администратору.",
        parameters=[
            OpenApiParameter(
                name="id", type=OpenApiTypes.INT, description="ID пользователя"
            )
        ],
        responses={
            204: {"description": "Пользователь успешно удален"},
            401: {"description": "Неавторизованный доступ"},
            403: {"description": "Доступ запрещен (модераторам удаление запрещено)"},
            404: {"description": "Пользователь не найден"},
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
        responses={
            200: UserSerializer,
            401: {"description": "Неавторизованный доступ"},
        },
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(
        summary="Полное обновление профиля текущего пользователя",
        description="Полностью обновляет информацию о профиле текущего авторизованного пользователя.",
        request=UserSerializer,
        responses={
            200: UserSerializer,
            400: {"description": "Ошибка валидации"},
            401: {"description": "Неавторизованный доступ"},
        },
    )
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)

    @extend_schema(
        summary="Частичное обновление профиля текущего пользователя",
        description="Частично обновляет информацию о профиле текущего авторизованного пользователя.",
        request=UserSerializer(partial=True),
        responses={
            200: UserSerializer,
            400: {"description": "Ошибка валидации"},
            401: {"description": "Неавторизованный доступ"},
        },
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
            OpenApiParameter(
                name="paid_course",
                type=OpenApiTypes.INT,
                description="Фильтр по ID оплаченного курса",
                required=False,
            ),
            OpenApiParameter(
                name="paid_lesson",
                type=OpenApiTypes.INT,
                description="Фильтр по ID оплаченного урока",
                required=False,
            ),
            OpenApiParameter(
                name="payment_method",
                type=OpenApiTypes.STR,
                description="Фильтр по способу оплаты (cash, transfer, make_qr_code)",
                required=False,
                enum=["cash", "transfer", "make_qr_code"],
            ),
            OpenApiParameter(
                name="ordering",
                type=OpenApiTypes.STR,
                description="Порядок сортировки (-payment_date для убывания)",
                required=False,
            ),
        ],
        responses={
            200: PaymentSerializer(many=True),
            401: {"description": "Неавторизованный доступ"},
        },
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


@extend_schema(tags=["Payments"])
class PaymentCreateAPIView(generics.CreateAPIView):
    """
    API View для создания новой платежной сессии Stripe.
    Принимает course_id или lesson_id и возвращает URL для оплаты.
    """

    serializer_class = PaymentCreateSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Инициировать новый платеж через Stripe",
        description="Создает новую платежную сессию для курса или урока и возвращает URL для оплаты. "
        "Необходимо указать либо 'paid_course', либо 'paid_lesson'.",
        request=PaymentCreateSerializer,
        responses={
            200: PaymentCreateSerializer,
            400: {"description": "Неверные входные данные или ошибка Stripe"},
            401: {"description": "Неавторизованный доступ"},
        },
    )
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        paid_course_id = serializer.validated_data.get("paid_course")
        paid_lesson_id = serializer.validated_data.get("paid_lesson")

        try:
            payment_info = process_payment_and_create_stripe_session(
                user=request.user,
                paid_course_id=paid_course_id.id if paid_course_id else None,
                paid_lesson_id=paid_lesson_id.id if paid_lesson_id else None,
            )
            # Возвращаем данные, которые ожидает PaymentCreateSerializer
            return Response(
                {
                    "payment_id": payment_info["payment_id"],
                    "payment_url": payment_info["payment_url"],
                    "amount": payment_info["amount"],
                    "status": payment_info["status"],
                },
                status=status.HTTP_200_OK,
            )
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(tags=["Stripe Callbacks"])
class StripeSuccessView(APIView):
    """
    Обрабатывает успешные колбэки платежей от Stripe.
    Извлекает сессию Stripe, обновляет локальный статус Payment на 'succeeded'.
    """

    permission_classes = []
    serializer_class = None

    @extend_schema(
        summary="Обработка успешной оплаты Stripe",
        parameters=[
            OpenApiParameter(
                name="session_id",
                type=OpenApiTypes.STR,
                description="ID сессии Stripe Checkout",
                required=True,
            )
        ],
        responses={
            200: OpenApiTypes.OBJECT,  # Используем OpenApiTypes.OBJECT для описания произвольного JSON-объекта
            400: OpenApiTypes.OBJECT,
            500: OpenApiTypes.OBJECT,
        },
    )
    def get(self, request, *args, **kwargs):
        session_id = request.GET.get("session_id")
        if not session_id:
            return Response(
                {"error": "Идентификатор сессии отсутствует."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            stripe_session = retrieve_stripe_session(session_id)

            if stripe_session.payment_status == "paid":
                payment_id = stripe_session.metadata.get("payment_id")
                if not payment_id:
                    return Response(
                        {
                            "error": "Идентификатор платежа отсутствует в метаданных сессии Stripe."
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                payment = get_object_or_404(Payment, id=payment_id)

                if payment.status == "succeeded":
                    # Платеж уже обработан, нет необходимости обновлять снова
                    return Response(
                        {
                            "message": "Платеж уже успешно обработан.",
                            "payment_id": payment.id,
                        },
                        status=status.HTTP_200_OK,
                    )

                payment.status = "succeeded"
                # Очищаем stripe_id и payment_url, так как платеж завершен
                payment.stripe_id = None
                payment.payment_url = None
                payment.save()

                return Response(
                    {"message": "Платёж прошёл успешно!", "payment_id": payment.id},
                    status=status.HTTP_200_OK,
                )
            else:
                # Если payment_status не 'paid', это может означать 'unpaid' или 'no_payment_required'.
                # Для нашего случая, если нас перенаправили сюда, это подразумевает неудачу или отмену.
                payment_id = stripe_session.metadata.get("payment_id")
                if payment_id:
                    payment = get_object_or_404(Payment, id=payment_id)
                    if (
                        payment.status == "pending"
                    ):  # Обновляем только если статус еще "ожидает"
                        payment.status = "failed"
                        payment.save()
                    return Response(
                        {
                            "message": f"Платеж не завершен. Статус: {stripe_session.payment_status}",
                            "payment_id": payment.id,
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                return Response(
                    {
                        "message": f"Платеж не завершен. Статус: {stripe_session.payment_status}"
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        except stripe.error.InvalidRequestError as e:
            return Response(
                {"error": f"Неверный ID сессии Stripe или ошибка API: {e}"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            return Response(
                {"error": f"Произошла непредвиденная ошибка: {e}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


@extend_schema(tags=["Stripe Callbacks"])
class StripeCancelView(APIView):
    """
    Обрабатывает колбэки отмены платежа от Stripe.
    Обновляет локальный статус Payment на 'failed', если он был 'pending'.
    """

    permission_classes = []  # Аутентификация не требуется для колбэков Stripe
    serializer_class = None

    def get(self, request, *args, **kwargs):
        session_id = request.GET.get(
            "session_id"
        )  # Stripe часто отправляет session_id и сюда

        # При желании, можно получить сессию и обновить статус платежа на 'failed'
        if session_id:
            try:
                stripe_session = retrieve_stripe_session(session_id)
                payment_id = stripe_session.metadata.get("payment_id")
                if payment_id:
                    payment = get_object_or_404(Payment, id=payment_id)
                    if payment.status == "pending":
                        payment.status = "failed"
                        payment.save()
            except (stripe.error.InvalidRequestError, Exception) as e:
                # Зарегистрируйте ошибку, но все равно верните сообщение об отмене пользователю/Stripe
                print(
                    f"Ошибка обработки колбэка отмены Stripe для сессии {session_id}: {e}"
                )

        return Response(
            {"message": "Платеж отменен пользователем."}, status=status.HTTP_200_OK
        )

from datetime import timedelta
from django.utils import timezone
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import generics, status, viewsets
from rest_framework.permissions import SAFE_METHODS, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from materials.models import Course, CourseSubscription, Lesson
from materials.paginators import MaterialsPagination
from materials.serializers import CourseSerializer, LessonSerializer
from materials.tasks import send_course_update_notification
from users.permissions import (IsNotModerator, IsOwnerOrModerator,
                               IsOwnerOrSuperuser)


class CourseViewSet(viewsets.ModelViewSet):
    """
    ViewSet для CRUD операций с курсами.
    Обеспечивает, что не-модераторы могут видеть, редактировать и удалять только свои курсы.
    Модераторы и администраторы имеют полный доступ.
    """

    # permission_classes = [IsAuthenticated]
    # queryset = Course.objects.all()
    serializer_class = CourseSerializer
    pagination_class = MaterialsPagination

    def get_queryset(self):
        # Если запрос от DRF Spectacular для генерации схемы, возвращаем пустой QuerySet.
        # Это предотвращает ошибки, связанные с доступом к request.user для анонимного пользователя.
        if getattr(self, "swagger_fake_view", False):
            return Course.objects.none()

        # Если пользователь не является суперпользователем и не входит в группу модераторов,
        # он видит только свои курсы. В противном случае (модератор/админ) видит все курсы.
        if (
            not self.request.user.is_superuser
            and not self.request.user.groups.filter(name="Moderators").exists()
        ):
            return Course.objects.filter(course_user=self.request.user)
        return Course.objects.all()

    def get_permissions(self):
        # Динамическое определение прав доступа в зависимости от действия
        if self.action == "create":
            # Создавать курсы могут только авторизованные пользователи, которые НЕ являются модераторами
            self.permission_classes = [IsAuthenticated, IsNotModerator]

        elif self.action in ["update", "partial_update", "retrieve"]:
            # Обновлять курсы могут владельцы или модераторы
            self.permission_classes = [IsAuthenticated, IsOwnerOrModerator]

        elif self.action == "destroy":
            # Удалять курсы могут только владельцы и администратор (суперпользователь)
            self.permission_classes = [IsAuthenticated, IsOwnerOrSuperuser]

        else:  # list
            # Просматривать список курсов могут все аутентифицированные пользователи.
            # Фильтрация по владельцу для не-модераторов происходит в get_queryset.
            self.permission_classes = [IsAuthenticated]
        return [permission() for permission in self.permission_classes]

    def perform_create(self, serializer):
        """
        При создании курса автоматически привязываем его к текущему авторизованному пользователю.
        """
        serializer.save(course_user=self.request.user)

    def perform_update(self, serializer):
        """
        При обновлении курса, сохраняет изменения и проверяет,
        нужно ли отправить уведомление подписчикам.
        Уведомление отправляется, если с момента последнего уведомления курса
        прошло более четырех часов.
        """
        instance = self.get_object()  # Получаем текущий объект до обновления
        super().perform_update(
            serializer)  # Сохраняем обновленные данные. updated_at обновится автоматически благодаря auto_now=True

        # Проверяем, прошло ли достаточно времени с последнего уведомления.
        # Если updated_at None (впервые обновляется курс) или прошло более 4 часов
        if (
                instance.updated_at is None
                or (timezone.now() - instance.updated_at) >= timedelta(hours=4)
        ):
            # Запускаем асинхронную задачу для отправки уведомлений
            send_course_update_notification.delay(instance.id)
            # Поскольку updated_at имеет auto_now=True, оно уже обновилось при super().perform_update(serializer).
            # Дополнительное сохранение не требуется, если только мы не хотим принудительно установить время.
            # Но для логики "с момента последнего уведомления" auto_now=True подходит хорошо.

    @extend_schema(
        summary="Создание курса",
        description="Позволяет авторизованным пользователям (не модераторам) создавать новые курсы.",
        tags=["Courses"]
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @extend_schema(
        summary="Получение списка курсов",
        description="Получает список курсов. Пользователи видят только свои курсы, модераторы и администраторы — все курсы.",
        tags=["Courses"]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        summary="Получение деталей курса",
        description="Получает подробную информацию о конкретном курсе. Доступно владельцам, модераторам и администраторам.",
        tags=["Courses"]
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        summary="Обновление курса",
        description="Позволяет владельцу или модератору обновить информацию о курсе.",
        tags=["Courses"]
    )
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    @extend_schema(
        summary="Частичное обновление курса",
        description="Позволяет владельцу или модератору частично обновить информацию о курсе.",
        tags=["Courses"]
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @extend_schema(
        summary="Удаление курса",
        description="Позволяет владельцу или администратору удалить курс. Модераторам удаление запрещено.",
        tags=["Courses"]
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)


@extend_schema(
    methods=["GET"],
    summary="Получение списка уроков",
    description="Получает список уроков. Пользователи видят только свои уроки, модераторы и администраторы — все уроки.",
    tags=["Lessons"]
)
@extend_schema(
    methods=["POST"],
    summary="Создание урока",
    description="Позволяет авторизованным пользователям (не модераторам) создавать новые уроки.",
    tags=["Lessons"]
)
class LessonListCreateAPIView(generics.ListCreateAPIView):
    """
    Generic-класс для получения списка уроков и создания нового урока.
    Обеспечивает, что не-модераторы могут видеть только свои уроки и создавать новые.
    """

    # queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    pagination_class = MaterialsPagination

    def get_queryset(self):
        # Если запрос от DRF Spectacular для генерации схемы, возвращаем пустой QuerySet.
        if getattr(self, "swagger_fake_view", False):
            return Lesson.objects.none()

        # Если пользователь не является суперпользователем и не входит в группу модераторов,
        # он видит только свои уроки. В противном случае (модератор/админ) видит все уроки.
        # Уроки фильтруются по полю lesson_user (владелец урока).
        if (
            not self.request.user.is_superuser
            and not self.request.user.groups.filter(name="Moderators").exists()
        ):
            return Lesson.objects.filter(lesson_user=self.request.user)
        return Lesson.objects.all()

    def get_permissions(self):

        # Динамическое определение прав доступа в зависимости от метода запроса
        if self.request.method == "POST":  # Create action
            # Создавать уроки могут только авторизованные пользователи, которые НЕ являются модераторами
            self.permission_classes = [IsAuthenticated, IsNotModerator]

        else:  # GET (list)
            # Просматривать список уроков могут все аутентифицированные пользователи.
            # Фильтрация по владельцу для не-модераторов происходит в get_queryset.
            self.permission_classes = [IsAuthenticated]
        return [permission() for permission in self.permission_classes]

    def perform_create(self, serializer):
        """
        При создании урока автоматически привязываем его к текущему авторизованному пользователю.
        """
        serializer.save(lesson_user=self.request.user)


@extend_schema(
    methods=["GET"],
    summary="Получение деталей урока",
    description="Получает подробную информацию о конкретном уроке. Доступно владельцам, модераторам и администраторам.",
    tags=["Lessons"]
)
@extend_schema(
    methods=["PUT", "PATCH"],
    summary="Обновление урока",
    description="Позволяет владельцу или модератору обновить информацию о уроке.",
    tags=["Lessons"]
)
@extend_schema(
    methods=["DELETE"],
    summary="Удаление урока",
    description="Позволяет владельцу или администратору удалить урок. Модераторам удаление запрещено.",
    tags=["Lessons"]
)
class LessonRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    Generic-класс для получения, обновления и удаления конкретного урока.
    Обеспечивает, что не-модераторы могут просматривать, обновлять и удалять только свои уроки.
    """

    # queryset = Lesson.objects.all()
    serializer_class = LessonSerializer

    def get_queryset(self):
        # Если запрос от DRF Spectacular для генерации схемы, возвращаем пустой QuerySet.
        if getattr(self, "swagger_fake_view", False):
            return Lesson.objects.none()

        # Для действий с одним объектом, также фильтруем queryset, чтобы предотвратить доступ
        # к чужим объектам через прямой URL для не-модераторов.
        if (
            not self.request.user.is_superuser
            and not self.request.user.groups.filter(name="Moderators").exists()
        ):
            return Lesson.objects.filter(lesson_user=self.request.user)
        return Lesson.objects.all()

    def get_permissions(self):

        # Динамическое определение прав доступа в зависимости от метода запроса
        if self.request.method in SAFE_METHODS:  # GET (retrieve)
            # Просматривать конкретный урок могут владельцы или модераторы
            self.permission_classes = [IsAuthenticated, IsOwnerOrModerator]

        elif self.request.method in ["PUT", "PATCH"]:  # Update action
            # Обновлять уроки могут владельцы или модераторы
            self.permission_classes = [IsAuthenticated, IsOwnerOrModerator]

        elif self.request.method == "DELETE":  # Destroy action
            # Удалять уроки могут только владельцы и администратор (суперпользователь)
            self.permission_classes = [IsAuthenticated, IsOwnerOrSuperuser]

        else:  # GET (retrieve)
            # Просматривать уроки могут все аутентифицированные пользователи
            self.permission_classes = [IsAuthenticated]
        return [permission() for permission in self.permission_classes]

    def perform_update(self, serializer):
        """
        При обновлении урока, сохраняет изменения, а затем проверяет,
        нужно ли отправить уведомление подписчикам курса, к которому принадлежит урок.
        Уведомление отправляется, если с момента последнего уведомления курса
        прошло более четырех часов.
        """
        instance = self.get_object()  # Получаем текущий экземпляр урока до обновления
        course_of_lesson = instance.course  # Получаем курс, связанный с этим уроком

        super().perform_update(serializer)  # Сохраняем обновленные данные урока

        # Проверяем, прошло ли достаточно времени с последнего уведомления для КУРСА.
        # Если updated_at None (впервые обновляется курс) или прошло более 4 часов
        if (
                course_of_lesson.updated_at is None
                or (timezone.now() - course_of_lesson.updated_at) >= timedelta(hours=4)
        ):
            # Запускаем асинхронную задачу для отправки уведомлений по КУРСУ
            send_course_update_notification.delay(course_of_lesson.id)

            # Обновляем поле updated_at курса, чтобы сбросить таймер для этого курса.
            # Поскольку updated_at в модели Course имеет auto_now=True, достаточно просто сохранить объект Course,
            # чтобы это поле обновилось до текущего времени.
            course_of_lesson.save()

class CourseSubscriptionView(APIView):
    """
    Управление подпиской на курс.

    POST-запрос требует:
    - course_id - ID курса для подписки

    Возвращает:
    - message - статус операции (добавлена/удалена)
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Подписка/отписка на курс",
        description="Позволяет пользователю подписаться на курс или отписаться, если ужн подписан. Требует `course_id` в теле запроса.",
        request={"application/json": {"course_id": {"type": "integer", "description": "ID курса"}}},
        responses={
            200: {"description": "Успешная операция подписки/отписки"},
            400: {"description": "Неверный запрос (например, отсутствует course_id)"},
            401: {"description": "Неавторизованный доступ"},
            404: {"description": "Курс не найден"}
        },
        tags=["Courses"]
    )

    def post(self, request, *args, **kwargs):
        user = request.user
        course_id = request.data.get('course_id')

        if not course_id:
            return Response({"error": "Параметр 'course_id' обязателен."}, status=status.HTTP_400_BAD_REQUEST)

        course = get_object_or_404(Course, pk=course_id)

        # Проверяем, существует ли подписка, и создаем/удаляем ее
        subscription, created = CourseSubscription.objects.get_or_create(
            user=user,
            course=course
        )

        if not created:
            # Если объект не был создан, значит, он уже существовал, и мы его удаляем
            subscription.delete()
            message = "Подписка удалена"
        else:
            # Если объект был создан, значит, подписки не было, и мы ее добавили
            message = "Подписка добавлена"

        return Response({"message": message}, status=status.HTTP_200_OK)

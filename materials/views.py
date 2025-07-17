from rest_framework import generics, viewsets
from rest_framework.permissions import SAFE_METHODS, IsAuthenticated

from materials.models import Course, Lesson, CourseSubscription
from materials.serializers import CourseSerializer, LessonSerializer
from users.permissions import IsNotModerator, IsOwner, IsOwnerOrModerator, IsOwnerOrSuperuser

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from materials.paginators import MaterialsPagination
from django.shortcuts import get_object_or_404


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


class LessonListCreateAPIView(generics.ListCreateAPIView):
    """
    Generic-класс для получения списка уроков и создания нового урока.
    Обеспечивает, что не-модераторы могут видеть только свои уроки и создавать новые.
    """

    # queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    pagination_class = MaterialsPagination

    def get_queryset(self):
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


class LessonRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    Generic-класс для получения, обновления и удаления конкретного урока.
    Обеспечивает, что не-модераторы могут просматривать, обновлять и удалять только свои уроки.
    """

    # queryset = Lesson.objects.all()
    serializer_class = LessonSerializer

    def get_queryset(self):
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


class CourseSubscriptionView(APIView):
    """
    Управление подпиской на курс.

    POST-запрос требует:
    - course_id - ID курса для подписки

    Возвращает:
    - message - статус операции (добавлена/удалена)
    """
    permission_classes = [IsAuthenticated]

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

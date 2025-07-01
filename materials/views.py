from django.shortcuts import render
from rest_framework import viewsets, generics
from materials.models import Course, Lesson
from materials.serializers import CourseSerializer, LessonSerializer
from rest_framework.permissions import BasePermission, SAFE_METHODS
from rest_framework.permissions import IsAuthenticated


class CourseViewSet(viewsets.ModelViewSet):
    """
    ViewSet для CRUD операций с курсами.
    """
    permission_classes = [IsAuthenticated]
    queryset = Course.objects.all()
    serializer_class = CourseSerializer

    def get_permissions(self):
        if self.action == 'create':
            # Создавать курсы могут только не-модераторы
            self.permission_classes = [IsAuthenticated, IsNotModerator]
        elif self.action in ['update', 'partial_update']:
            # Обновлять курсы могут владельцы или модераторы
            self.permission_classes = [IsAuthenticated, IsOwnerOrModerator]
        elif self.action == 'destroy':
            # Удалять курсы могут только владельцы, которые не являются модераторами
            self.permission_classes = [IsAuthenticated, IsOwner, IsNotModerator]
        else:  # list, retrieve (просмотр)
            # Просматривать курсы могут все аутентифицированные пользователи
            self.permission_classes = [IsAuthenticated]
        return [permission() for permission in self.permission_classes]

    def perform_create(self, serializer):
        serializer.save(course_user=self.request.user)


class LessonListCreateAPIView(generics.ListCreateAPIView):
    """
    Generic-класс для получения списка уроков и создания нового урока.
    """
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer

    def get_permissions(self):
        if self.request.method == 'POST':  # Create action
            # Создавать уроки могут только не-модераторы
            self.permission_classes = [IsAuthenticated, IsNotModerator]
        else:  # GET (list)
            # Просматривать уроки могут все аутентифицированные пользователи
            self.permission_classes = [IsAuthenticated]
        return [permission() for permission in self.permission_classes]


class LessonRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    Generic-класс для получения, обновления и удаления конкретного урока.
    """
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer

    def get_permissions(self):
        if self.request.method in ['PUT', 'PATCH']:  # Update action
            # Обновлять уроки могут владельцы или модераторы
            self.permission_classes = [IsAuthenticated, IsOwnerOrModerator]
        elif self.request.method == 'DELETE':  # Destroy action
            # Удалять уроки могут только владельцы, которые не являются модераторами
            self.permission_classes = [IsAuthenticated, IsOwner, IsNotModerator]
        else:  # GET (retrieve)
            # Просматривать уроки могут все аутентифицированные пользователи
            self.permission_classes = [IsAuthenticated]
        return [permission() for permission in self.permission_classes]


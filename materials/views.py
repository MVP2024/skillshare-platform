from django.shortcuts import render
from rest_framework import viewsets, generics
from materials.models import Course, Lesson
from materials.serializers import CourseSerializer, LessonSerializer
from rest_framework.permissions import BasePermission, SAFE_METHODS


class CourseViewSet(viewsets.ModelViewSet):
    """
    ViewSet для CRUD операций с курсами.
    """
    queryset = Course.objects.all()
    serializer_class = CourseSerializer


class LessonListCreateAPIView(generics.ListCreateAPIView):
    """
    Generic-класс для получения списка уроков и создания нового урока.
    """
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer


class IsOwnerOrReadOnly(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        # Эта строка верна для Lesson, так как владелец через Course
        return obj.course.course_user is not None and obj.course.course_user == request.user


class LessonRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    Generic-класс для получения, обновления и удаления конкретного урока.
    """
    permission_classes = [IsOwnerOrReadOnly]
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer

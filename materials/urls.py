from django.urls import path
from rest_framework.routers import DefaultRouter

from materials.views import (CourseSubscriptionView, CourseViewSet,
                             LessonListCreateAPIView,
                             LessonRetrieveUpdateDestroyAPIView)

app_name = "materials"

router = DefaultRouter()
router.register(r"courses", CourseViewSet, basename="course")

urlpatterns = [
    path("lessons/", LessonListCreateAPIView.as_view(), name="lesson-list-create"),
    path(
        "lessons/<int:pk>/",
        LessonRetrieveUpdateDestroyAPIView.as_view(),
        name="lesson-detail",
    ),
    path('courses/subscribe/', CourseSubscriptionView.as_view(), name='course_subscribe'),
] + router.urls

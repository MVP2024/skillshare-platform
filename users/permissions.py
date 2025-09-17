from rest_framework.permissions import BasePermission

from users.models import User


class IsModerator(BasePermission):
    """
    Пользовательское разрешение, проверяющее, является ли пользователь модератором.
    """

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.groups.filter(name="Moderators").exists()
        )


class IsNotModerator(BasePermission):
    """
    Пользовательское разрешение, проверяющее, что пользователь НЕ является модератором.
    """

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and not request.user.groups.filter(name="Moderators").exists()
        )


class IsOwner(BasePermission):
    """
    Пользовательское разрешение, позволяющее редактировать или удалять объект только его владельцам.
    Предполагается, что экземпляр модели имеет атрибут 'course_user', 'lesson_user' или 'user'.
    Добавлена проверка для самого объекта User.
    """

    def has_object_permission(self, request, view, obj):

        # Для экземпляров модели User, проверяем, является ли объект самим запрашивающим пользователем
        if isinstance(obj, User):
            return obj == request.user

        # Для других моделей (Course, Lesson, Payment), проверяем их соответствующие поля владельца
        if hasattr(obj, "course_user"):
            return obj.course_user == request.user
        elif hasattr(obj, "lesson_user"):
            return obj.lesson_user == request.user
        elif hasattr(obj, "user"):  # Для модели Payment
            return obj.user == request.user
        # Если это урок, проверяем владельца его курса (вторичная проверка, если lesson_user не установлен)
        elif hasattr(obj, "course") and hasattr(obj.course, "course_user"):
            return obj.course.course_user == request.user
        return False


class IsOwnerOrModerator(BasePermission):
    """
    Пользовательское разрешение, позволяющее владельцам или модераторам редактировать объект.
    """

    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:
            return True
        if request.user.is_authenticated:
            return IsOwner().has_object_permission(
                request, view, obj
            ) or IsModerator().has_permission(request, view)
        return False


class IsOwnerOrSuperuser(BasePermission):
    """
    Пользовательское разрешение, позволяющее владельцам или суперпользователям выполнять действие.
    """

    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:
            return True
        if request.user.is_authenticated:
            # Проверяем, является ли пользователь владельцем
            return IsOwner().has_object_permission(request, view, obj)
        return False

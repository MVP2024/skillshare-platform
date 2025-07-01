from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsModerator(BasePermission):
    """
    Пользовательское разрешение, проверяющее, является ли пользователь модератором.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.groups.filter(name='Moderators').exists()


class IsNotModerator(BasePermission):
    """
    Пользовательское разрешение, проверяющее, что пользователь НЕ является модератором.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and not request.user.groups.filter(name='Moderators').exists()


class IsOwner(BasePermission):
    """
    Пользовательское разрешение, позволяющее редактировать или удалять объект только его владельцам.
    Предполагается, что экземпляр модели имеет атрибут 'course_user' или 'user'.
    """
    def has_object_permission(self, request, view, obj):
        # Проверяем, является ли пользователь владельцем
        if hasattr(obj, 'course_user'):
            return obj.course_user == request.user
        elif hasattr(obj, 'user'):
            return obj.user == request.user
        # Если это урок, проверяем владельца его курса
        elif hasattr(obj, 'course') and hasattr(obj.course, 'course_user'):
            return obj.course.course_user == request.user
        return False


class IsOwnerOrModerator(BasePermission):
    """
    Пользовательское разрешение, позволяющее владельцам или модераторам редактировать объект.
    """
    def has_object_permission(self, request, view, obj):
        if request.user and request.user.is_authenticated:
            # Проверяем, является ли пользователь владельцем
            is_owner = IsOwner().has_object_permission(request, view, obj)
            # Проверяем, является ли пользователь модератором
            is_moderator = IsModerator().has_permission(request, view)
            return is_owner or is_moderator
        return False

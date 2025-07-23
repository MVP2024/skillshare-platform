from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from users.models import Payment


class CustomUserAdmin(UserAdmin):
    """
    Пользовательский класс админки для модели User,
    добавляющий колонку с ролями/группами пользователя.
    """

    # Определяем поля, которые будут отображаться в списке пользователей
    # Добавляем 'get_roles' как новую колонку
    list_display = (
        "email",
        "first_name",
        "last_name",
        "is_staff",
        "is_active",
        "get_roles",
    )

    # Определяем поля для поиска
    search_fields = ("email", "first_name", "last_name")

    # Определяем порядок сортировки по умолчанию
    ordering = ("email",)

    # Используем filter_horizontal для удобного управления группами и разрешениями
    filter_horizontal = (
        "groups",
        "user_permissions",
    )

    # Переопределяем fieldsets для страницы изменения пользователя
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (
            "Personal info",
            {"fields": ("first_name", "last_name", "phone", "city", "avatar")},
        ),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )

    # Переопределяем add_fieldsets для страницы создания нового пользователя
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "password", "password2"),
            },
        ),
        (
            "Personal info",
            {"fields": ("first_name", "last_name", "phone", "city", "avatar")},
        ),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
    )

    def get_roles(self, obj):
        """
        Метод для получения и отображения ролей/групп пользователя.
        """
        roles = []
        if obj.is_superuser:
            roles.append("Администратор")

        # Проверяем, является ли пользователь модератором
        if obj.groups.filter(name="Moderators").exists():
            roles.append("Модератор")

        # Получаем названия всех других групп, кроме "Moderators"
        other_groups = obj.groups.exclude(name="Moderators").values_list(
            "name", flat=True
        )
        if other_groups:
            roles.append(f"Группы: {', '.join(other_groups)}")

        if not roles:
            return "Пользователь"  # Если нет специфичных ролей, по умолчанию "Пользователь"
        return ", ".join(roles)

    # Устанавливаем заголовок для новой колонки в админ-панели
    get_roles.short_description = "Роли/Группы"


# Регистрируем модель Payment (регистрация User теперь происходит в users/apps.py)
admin.site.register(Payment)

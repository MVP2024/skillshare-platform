from django.apps import AppConfig


class UsersConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "users"

    def ready(self):
        # Импортируем здесь, чтобы избежать циклического импорта
        from django.contrib import admin

        from users.models import User

        from .admin import CustomUserAdmin

        try:
            # Отменяем регистрацию стандартного UserAdmin
            admin.site.unregister(User)
        except admin.sites.NotRegistered:
            pass  # Модель еще не зарегистрирована, это нормально при первом запуске

        # Регистрируем нашу пользовательскую админку для модели User
        admin.site.register(User, CustomUserAdmin)

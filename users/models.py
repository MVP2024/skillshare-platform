from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """
    Стандартная модель пользователя, использующая email для авторизации
    """
    username = None

    email = models.EmailField(unique=True, verbose_name="Email", help_text="Укажите свой email")
    phone = models.CharField(max_length=35, blank=True, null=True, verbose_name="Телефон",
                             help_text="Укажите свой телефон")
    city = models.CharField(max_length=100, blank=True, null=True, verbose_name="Город", help_text="Укажите свой город")
    avatar = models.ImageField(upload_to="users/avatars_users/", blank=True, null=True, verbose_name="Аватар",
                               help_text="Загрузите свой аватар")

    USERNAME_FIELD = "email"  # устанавливаем email как поля для авторизации
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    def __str__(self):
        return self.email

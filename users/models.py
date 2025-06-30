from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from materials.models import Course, Lesson


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


class Paymant(models.Model):
    """
    Модель платежа.
    Хрнит информацию о транзакциях пользователей за курсы или уроки.
    """
    # Варианты способов оплаты
    PAYMENT_METHOD_CHOICES = [
        ("cash", "Наличные"),
        ("transfer", "Перевод на счет"),
        ("make_qr_code", "Перевод по QR-коду"),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="payments",  # Добавляем related_name для удобства доступа из User
        verbose_name="Пользователь",
        help_text="Пользователь, совершивший платеж",
    )
    payment_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата оплаты",
        help_text="Дата и время совершения платежа",
    )
    paid_course = models.ForeignKey(
        Course,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name="Оплаченный курс",
        help_text="Курс, за который произведена оплата",
    )
    paid_lesson = models.ForeignKey(
        Lesson,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name="Оплаченный урок",
        help_text="Урок, за который произведена оплата",
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Сумма оплаты",
        help_text="Сумма платежа",
    )
    payment_method = models.CharField(
        max_length=10,
        choices=PAYMENT_METHOD_CHOICES,
        verbose_name="Способ оплаты",
        help_text="Способ оплаты (наличные или перевод)",
    )

    class Meta:
        verbose_name = "Платёж"
        verbose_name_plural = "Платежи"

    def __str__(self):
        if self.paid_course:
            return f"Платёж от {self.user.email} за курс '{self.paid_course.title}'"
        elif self.paid_lesson:
            return f"Платеж от {self.user.email} за урок '{self.paid_lesson.title}'"
        return f"Платеж от {self.user.email} на сумму {self.amount}"

    def clean(self):
        """
        Проверяет, что платеж связан либо с курсом, либо с уроком, но не с обоими.
        """
        if self.paid_course and self.paid_lesson:
            raise ValidationError("Платеж не может быть одновременно за курс и за урок.")
        if not self.paid_course and not self.paid_lesson:
            raise ValidationError("Платеж должен быть связан либо с курсом, либо с уроком.")

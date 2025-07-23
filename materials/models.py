from django.conf import settings
from django.db import models
from django.db.models import Sum
from django.utils import timezone


class Course(models.Model):
    """
    Модель курса.
    """

    title = models.CharField(
        max_length=255,
        verbose_name="Название курса",
        help_text="Укажите название курса",
    )
    preview = models.ImageField(
        upload_to="courses/previews/",
        blank=True,
        null=True,
        verbose_name="Превью курса",
        help_text="Укажите картинку превью урока",
    )
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name="Описание курса",
        help_text="Укажите описание курса",
    )
    # course_user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Владелец курса",
    #                                 help_text="Укажите владельца курса")  # удаляется урок вместе с владельцем

    course_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        verbose_name="Владелец курса",
        related_name="courses",
        null=True,
    )
    fixed_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        verbose_name="Фиксированная стоимость",
        help_text="Укажите фиксированную стоимость курса. Если пусто, стоимость будет рассчитана по урокам.",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        null=True,
        blank=True,
        verbose_name="Дата последнего обновления курса",
        help_text="Время последнего обновления курса. Используется для контроля частоты уведомлений."
    )

    @property
    def calculated_price_from_lessons(self):
        """
        Возвращает общую стоимость курса, суммируя цены всех связанных уроков.
        """
        # 'lessons' - это related_name из ForeignKey в модели Lesson
        return self.lessons.aggregate(total_amount=Sum('price'))['total_amount'] or 0.00

    @property
    def actual_price(self):
        """
        Возвращает актуальную стоимость курса: фиксированную, если она задана,
        и больше нуля, иначе - рассчитанную из стоимости уроков.
        """
        # Если fixed_price задан и он больше нуля, используем его
        if self.fixed_price is not None and self.fixed_price > 0:
            return self.fixed_price
        # Иначе используем рассчитанную стоимость по урокам
        return self.calculated_price_from_lessons

    class Meta:
        verbose_name = "Курс"
        verbose_name_plural = "Курсы"
        ordering = ['id']

    def __str__(self):
        return self.title


class Lesson(models.Model):
    """
    Модель урока, связанная с курсом.
    """

    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name="lessons", verbose_name="Курс"
    )
    title = models.CharField(
        max_length=255,
        verbose_name="Название урока",
        help_text="Укажите название урока",
    )
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name="Описание урока",
        help_text="Укажите описание урока",
    )
    preview = models.ImageField(
        upload_to="lessons/previews/",
        blank=True,
        null=True,
        verbose_name="Превью урока",
        help_text="Загрузите картинку превью урока",
    )
    video_link = models.URLField(
        blank=True,
        null=True,
        verbose_name="Ссылка на видео",
        help_text="Укажите ссылку на видео",
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        verbose_name="Стоимость урока",
        help_text="Укажите стоимость урока",
    )
    lesson_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        verbose_name="Владелец урока",
        related_name="lessons",
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = "Урок"
        verbose_name_plural = "Уроки"
        ordering = ['id']

    def __str__(self):
        return f"{self.title} ({self.course.title})"


class CourseSubscription(models.Model):
    """
        Модель подписки пользователя на обновления курса.

        Поля:
        - user: Пользователь, который подписывается
        - course: Курс, на который оформляется подписка
        - created: Дата создания подписки
        """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='subscriptions',
        verbose_name='Пользователь'
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='subscribers',
        verbose_name='Курс'
    )
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Уникальность пары пользователь-курс, чтобы один пользователь не мог подписаться на один курс дважды
        unique_together = ('user', 'course')
        verbose_name = 'Подписка на курс'
        verbose_name_plural = 'Подписки на курсы'

    def __str__(self):
        return f"{self.user} - {self.course}"

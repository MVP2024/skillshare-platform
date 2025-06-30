from django.db import models
from django.core.validators import URLValidator
from django.conf import settings


class Course(models.Model):
    """
    Модель курса.
    """
    title = models.CharField(max_length=255, verbose_name="Название курса", help_text="Укажите название курса")
    preview = models.ImageField(upload_to="courses/previews/", blank=True, null=True, verbose_name="Превью курса",
                                help_text="Укажите картинку превью урока")
    description = models.TextField(blank=True, null=True, verbose_name="Описание курса",
                                   help_text="Укажите описание курса")
    # course_user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Владелец курса",
    #                                 help_text="Укажите владельца курса")  # удаляется урок вместе с владельцем

    course_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, verbose_name="Владелец курса",
                                    related_name="courses",
                                    null=True)  # расскоментируй, чтобы урок оставался, когда владелец удалялся.

    class Meta:
        verbose_name = "Курс"
        verbose_name_plural = "Курсы"

    def __str__(self):
        return self.title


class Lesson(models.Model):
    """
    Модель урока, связанная с курсом.
    """
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="lessons",
        verbose_name="Курс"
    )
    title = models.CharField(max_length=255, verbose_name="Название урока", help_text="Укажите название курса")
    description = models.TextField(blank=True, null=True, verbose_name="Описание урока",
                                   help_text="Укажите описание урока")
    preview = models.ImageField(upload_to="lessons/previews/", blank=True, null=True, verbose_name="Превью урока",
                                help_text="Загрузите картинку превью урока")
    video_link = models.URLField(blank=True, null=True, verbose_name="Ссылка на видео",
                                 help_text="Укажите ссылку на видео")

    class Meta:
        verbose_name = "Урок"
        verbose_name_plural = "Уроки"

    def __str__(self):
        return f"{self.title} ({self.course.title})"

import datetime
import logging

from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone

from materials.models import Course, CourseSubscription
from users.models import User

logger = logging.getLogger(__name__)


@shared_task
def send_course_update_notification(course_id: int):
    """
    Асинхронная задача для отправки уведомлений об обновлении курса
    пользователям, подписанным на этот курс.

    Args:
        course_id (int): ID курса, который был обновлен.
    """
    try:
        course = Course.objects.get(id=course_id)
        # Получаем всех активных подписчиков на данный курс
        subscriptions = CourseSubscription.objects.filter(course=course)

        if not subscriptions.exists():
            logger.info(
                f"Нет активных подписчиков на курс '{course.title}' (ID: {course_id}). Уведомления не отправлены.")
            return

        subject = f"Обновление курса: '{course.title}'"
        message = (
            f"Привет!\n\nКурс '{course.title}' был обновлен.\n\n"
            f"Описание курса: {course.description or 'Нет описания.'}\n\n"
            f"Заходите, чтобы узнать новое! \n\n"
            f"С уважением, Команда SkillShare."
        )
        # Убедитесь, что settings.DEFAULT_FROM_EMAIL настроен в .env или settings.py
        from_email = settings.DEFAULT_FROM_EMAIL
        recipient_list = [sub.user.email for sub in subscriptions if sub.user.email]

        if not recipient_list:
            logger.warning(f"На курсе '{course.title}' (ID: {course_id}) нет подписчиков с валидными email-адресами.")
            return

        logger.info(
            f"Отправка уведомлений об обновлении курса '{course.title}' (ID: {course_id}) для {len(recipient_list)} подписчиков...")

        send_mail(subject, message, from_email, recipient_list, fail_silently=False)

        logger.info(f"Уведомления об обновлении курса '{course.title}' (ID: {course_id}) успешно отправлены.")

    except Course.DoesNotExist:
        logger.error(f"Курс с ID {course_id} не найден. Невозможно отправить уведомление.")
    except Exception as e:
        logger.error(f"Ошибка при отправке уведомлений для курса ID {course_id}: {e}", exc_info=True)


@shared_task
def deactivate_inactive_users():
    """
    Фоновая задача Celery для деактивации пользователей, которые
    не заходили на сайт более одного месяца.
    После деактивации пользователю отправляется уведомление по электронной почте.

    Эта задача запускается Celery Beat по расписанию,
    определенному в настройках Django (CELERY_BEAT_SCHEDULE).
    """
    # Определяем порог неактивного пользователя: текущее время минус 30 дней
    month_ago = timezone.now() - datetime.timedelta(days=30)

    logger.info(f"Начало проверки неактивных пользователей. Порог: {month_ago}")

    # Находим пользователей, которые активны, не являются суперпользователями
    # и их последний вход был раньше, чем месяц назад.
    # Исключаем суперпользователей, чтобы случайно не заблокировать администраторов.
    inactive_users = User.objects.filter(
        is_active=True,
        is_superuser=False,
        last_login__lt=month_ago
    )

    if inactive_users.exists():
        # Собираем email-адреса пользователей перед деактивацией
        deactivated_user_emails = [user.email for user in inactive_users if user.email]
        # Добавим лог с пользователями, которые будут деактивированы
        logger.info(f"Найдены пользователи для деактивации: {deactivated_user_emails}")

        # Обновляем флаг is_active для найденных пользователей
        count = inactive_users.update(is_active=False)
        logger.info(f"Деактивировано {count} неактивных пользователей.")

        # Отправляем уведомления деактивированным пользователям
        subject = "Ваш аккаунт на SkillShare был деактивирован"
        message = (
            "Уважаемый пользователь!\n\n"
            "Ваш аккаунт на платформе SkillShare был деактивирован из-за длительного периода не активности (более 30 дней).\n"
            "Это сделано для обеспечения безопасности и управления ресурсами платформы.\n\n"
            "Если вы хотите восстановить доступ к своему аккаунту, пожалуйста, свяжитесь с нашей службой поддержки по адресу support@skillshare.com.\n\n"
            "С уважением,\n"
            "Команда SkillShare."
        )
        from_email = settings.DEFAULT_FROM_EMAIL

        if deactivated_user_emails:
            try:
                # отправляем письмо каждому пользователю индивидуально
                for email in deactivated_user_emails:
                    send_mail(
                        subject,
                        message,
                        from_email,
                        [email],  # Передаем адрес как список из одного элемента
                        fail_silently=False
                    )
                logger.info(f"Уведомления о деактивации отправлены для {len(deactivated_user_emails)} пользователей.")
            except Exception as e:
                logger.error(f"Ошибка при отправке уведомлений о деактивации пользователей: {e}", exc_info=True)
        else:
            logger.info("Нет email-адресов для отправки уведомлений о деактивации.")
    else:
        logger.info("Не найдено пользователей для деактивации.")

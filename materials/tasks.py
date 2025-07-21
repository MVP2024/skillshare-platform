import datetime
import logging

from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone

from materials.models import Course, CourseSubscription

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
            logger.info(f"Нет активных подписчиков на курс '{course.title}' (ID: {course_id}). Уведомления не отправлены.")
            return

        subject = f"Обновление курса: '{course.title}'"
        message = (
            f"Привет!\n\nКурс '{course.title}' был обновлен.\n\n"
            f"Описание курса: {course.description or 'Нет описания.'}\n\n"
            f"Заходите, чтобы узнать новое! \n\n"
            f"С уважением, Команда SkillShare."
        )
        from_email = settings.DEFAULT_FROM_EMAIL
        recipient_list = [sub.user.email for sub in subscriptions if sub.user.email]

        if not recipient_list:
            logger.warning(f"На курсе '{course.title}' (ID: {course_id}) нет подписчиков с валидными email-адресами.")
            return

        logger.info(f"Отправка уведомлений об обновлении курса '{course.title}' (ID: {course_id}) для {len(recipient_list)} подписчиков...")

        send_mail(subject, message, from_email, recipient_list, fail_silently=False)

        logger.info(f"Уведомления об обновлении курса '{course.title}' (ID: {course_id}) успешно отправлены.")

    except Course.DoesNotExist:
        logger.error(f"Курс с ID {course_id} не найден. Невозможно отправить уведомление.")
    except Exception as e:
        logger.error(f"Ошибка при отправке уведомлений для курса ID {course_id}: {e}", exc_info=True)

from .celery import app as celery_app

# Эта строка гарантирует, что Celery приложение всегда импортируется при запуске Django,
# так что общие задачи могут быть зарегистрированы.
__all__ = ("celery_app",)

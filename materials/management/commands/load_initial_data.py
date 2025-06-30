from django.core.management.base import BaseCommand
from django.core.management import call_command
from pathlib import Path
from django.conf import settings
from materials.models import Course, Lesson
from users.models import User


class Command(BaseCommand):
    help = "Загружает тестовые данные из фикстуры (курсы, уроки, пользователи, платежи)"

    def handle(self, *args, **options):
        self.stdout.write("Удаление данных...")
        Lesson.objects.all().delete()  # Удаляем уроки первыми
        Course.objects.all().delete()  # Затем курсы
        User.objects.all().delete()  # Потом пользователей (каскадно удаляются платежи)
        self.stdout.write(self.style.SUCCESS("Данные удалены."))

        fixture_name = "initial_data.json"
        fixture_path = Path(settings.BASE_DIR) / 'materials' / 'fixtures' / fixture_name

        if fixture_path.exists():
            self.stdout.write("Загрузка фикстуры...")
            call_command("loaddata", fixture_name)
            self.stdout.write(self.style.SUCCESS("Данные загружены."))
        else:
            self.stdout.write(self.style.WARNING(f"Фикстура '{fixture_name}' не найдена."))

from pathlib import Path

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand

from materials.models import Course, Lesson
from users.models import Payment, User


class Command(BaseCommand):
    """
    Команда Django для загрузки начальных тестовых данных в базу данных.
    Перед загрузкой данных, она удаляет существующие записи для предотвращения дублирования.
    Данные загружаются из фикстуры 'initial_data.json', расположенной в 'materials/fixtures/'.
    """

    help = "Загружает тестовые данные из фикстуры (курсы, уроки, пользователи, платежи)"

    def handle(self, *args, **options):
        self.stdout.write("Удаление данных...")
        # Удаляем платежи первыми, чтобы избежать конфликтов
        Payment.objects.all().delete()
        # Удаляем уроки, так как они зависят от курсов
        Lesson.objects.all().delete()
        # Затем удаляем курсы
        Course.objects.all().delete()
        # Потом пользователей (суперпользователя не удаляем)
        User.objects.filter(is_superuser=False).delete()

        self.stdout.write(self.style.SUCCESS("Данные удалены."))

        fixture_name = "initial_data.json"
        # Путь к директории с фикстурами групп
        group_fixtures_dir = Path(settings.BASE_DIR) / "users" / "fixtures"

        # Загрузка всех фикстур групп (ПЕРВЫМИ)
        if group_fixtures_dir.exists():
            group_fixture_files = sorted(group_fixtures_dir.glob("*.json"))
            if group_fixture_files:
                self.stdout.write("Загрузка фикстур групп...")
                for group_file_path in group_fixture_files:
                    group_filename = group_file_path.name
                    self.stdout.write(f"  Загрузка {group_filename}...")
                    call_command("loaddata", group_filename)
                self.stdout.write(self.style.SUCCESS("Все фикстуры групп загружены."))
            else:
                self.stdout.write(
                    self.style.WARNING("Файлы фикстур групп не найдены в 'users/fixtures/'.")
                )
        else:
            self.stdout.write(
                self.style.WARNING("Директория 'users/fixtures/' не найдена.")
            )

        # Загрузка основной фикстуры (ВТОРОЙ)
        fixture_path = Path(settings.BASE_DIR) / "materials" / "fixtures" / fixture_name
        if fixture_path.exists():
            self.stdout.write("Загрузка фикстуры...")
            call_command("loaddata", fixture_name)
            self.stdout.write(self.style.SUCCESS("Данные загружены."))
        else:
            self.stdout.write(
                self.style.WARNING(f"Фикстура '{fixture_name}' не найдена.")
            )

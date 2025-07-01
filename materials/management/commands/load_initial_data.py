from django.core.management.base import BaseCommand
from django.core.management import call_command
from pathlib import Path
from django.conf import settings
from materials.models import Course, Lesson
from users.models import User


class Command(BaseCommand):
    """
        Команда Django для загрузки начальных тестовых данных в базу данных.
        Перед загрузкой данных, она удаляет существующие записи для предотвращения дублирования.
        Данные загружаются из фикстуры 'initial_data.json', расположенной в 'materials/fixtures/'.
    """

    help = "Загружает тестовые данные из фикстуры (курсы, уроки, пользователи, платежи)"

    def handle(self, *args, **options):
        self.stdout.write("Удаление данных...")
        # Удаляем уроки первыми, так как они зависят от курсов
        Lesson.objects.all().delete()

        # Затем удаляем курсы
        Course.objects.all().delete()

        # Потом пользователей (каскадно удаляются связанные платежи)


        # Суперпользователя не удаляем
        User.objects.filter(is_superuser=False).delete()

        self.stdout.write(self.style.SUCCESS("Данные удалены."))

        fixture_name = "initial_data.json"
        # Формируем полный путь к файлу фикстуры
        fixture_path = Path(settings.BASE_DIR) / 'materials' / 'fixtures' / fixture_name

        # Проверяем существование файла фикстуры перед загрузкой
        if fixture_path.exists():
            self.stdout.write("Загрузка фикстуры...")

            # Вызываем встроенную команду Django 'loaddata' для загрузки данных
            call_command("loaddata", fixture_name)
            self.stdout.write(self.style.SUCCESS("Данные загружены."))
        else:
            # Выводим предупреждение, если файл фикстуры не найден
            self.stdout.write(self.style.WARNING(f"Фикстура '{fixture_name}' не найдена."))

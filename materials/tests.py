from unittest.mock import MagicMock, patch
from urllib.error import URLError

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from materials.models import Course, CourseSubscription, Lesson
from materials.validators import validate_youtube_url

User = get_user_model()


class CourseViewSetTest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(email="user@example.com", password="pass")

        # Добавляем создание группы "Moderators", если её нет
        mod_group, created = Group.objects.get_or_create(name="Moderators")
        self.moderator = User.objects.create_user(
            email="mod@example.com", password="pass"
        )
        self.moderator.groups.add(mod_group)
        self.superuser = User.objects.create_superuser(
            email="admin@example.com", password="pass"
        )

    def test_create_course_non_moderator(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(
            reverse("materials:course-list"), {"title": "Test course"}
        )
        self.assertEqual(response.status_code, 201)

    def test_create_course_moderator_forbidden(self):
        self.client.force_authenticate(self.moderator)
        response = self.client.post(
            reverse("materials:course-list"), {"title": "Test course"}
        )
        self.assertEqual(response.status_code, 403)

    def test_update_course_owner(self):
        course = Course.objects.create(title="Course 1", course_user=self.user)
        self.client.force_authenticate(self.user)
        response = self.client.patch(
            reverse("materials:course-detail", args=[course.id]), {"title": "Updated"}
        )
        self.assertEqual(response.status_code, 200)

    def test_update_course_moderator(self):
        course = Course.objects.create(title="Course 1", course_user=self.user)
        self.client.force_authenticate(self.moderator)
        response = self.client.patch(
            reverse("materials:course-detail", args=[course.id]),
            {"title": "Updated by mod"},
        )
        self.assertEqual(response.status_code, 200)

    def test_delete_course_owner_allowed(self):
        course = Course.objects.create(title="Course 1", course_user=self.user)
        self.client.force_authenticate(self.user)
        response = self.client.delete(
            reverse("materials:course-detail", args=[course.id])
        )
        self.assertEqual(response.status_code, 204)

    def test_delete_course_superuser(self):
        course = Course.objects.create(title="Course 1", course_user=self.user)
        self.client.force_authenticate(self.superuser)
        response = self.client.delete(
            reverse("materials:course-detail", args=[course.id])
        )
        self.assertEqual(response.status_code, 204)

    def test_list_courses_non_moderator(self):
        Course.objects.create(title="User Course", course_user=self.user)
        Course.objects.create(title="Other User Course", course_user=self.moderator)

        self.client.force_authenticate(self.user)
        response = self.client.get(reverse("materials:course-list"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["title"], "User Course")

    def test_list_courses_moderator_or_superuser(self):
        Course.objects.create(title="Course 1", course_user=self.user)
        Course.objects.create(title="Course 2", course_user=self.moderator)

        self.client.force_authenticate(self.moderator)
        response = self.client.get(reverse("materials:course-list"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 2)

        self.client.force_authenticate(self.superuser)
        response = self.client.get(reverse("materials:course-list"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 2)


class LessonsCRUDTest(APITestCase):
    def setUp(self):

        # Создаем пользователей с разными ролями
        self.owner_user = User.objects.create_user(
            email="owner@example.com", password="testpassword_owner"
        )
        self.moderator_user = User.objects.create_user(
            email="moderator@example.com", password="testpassword_moderator"
        )
        self.non_owner_user = User.objects.create_user(
            email="non_owner@example.com", password="testpassword_nonowner"
        )
        self.superuser = User.objects.create_superuser(
            email="superuser@example.com", password="testpassword_superuser"
        )

        # Присваиваем модератору группу "Moderators"
        self.moderator_group, created = Group.objects.get_or_create(name="Moderators")
        self.moderator_user.groups.add(self.moderator_group)

        # Создаем курсы и уроки, принадлежащие разным пользователям
        self.course_owner = Course.objects.create(
            title="Курс от владельца", course_user=self.owner_user
        )
        self.lesson_owner = Lesson.objects.create(
            course=self.course_owner,
            title="Урок от владельца",
            video_link="https://youtube.com/watch?v=ownerlesson",
            lesson_user=self.owner_user,
        )

        self.course_non_owner = Course.objects.create(
            title="Курс не владельца", course_user=self.non_owner_user
        )
        self.lesson_non_owner = Lesson.objects.create(
            course=self.course_non_owner,
            title="Урок не владельца",
            video_link="https://youtube.com/watch?v=nonownerles",
            lesson_user=self.non_owner_user,
        )

        # Данные для создания нового урока
        self.new_lesson_data = {
            "course": self.course_owner.id,
            "title": "Вновь созданный урок",
            "video_link": "https://youtube.com/watch?v=newlessonID",
        }

        # URL-адреса для уроков
        self.lessons_list_create_url = reverse("materials:lesson-list-create")
        self.lesson_detail_url = lambda pk: reverse(
            "materials:lesson-detail", kwargs={"pk": pk}
        )

    # Тесты на создание урока
    @patch("materials.validators.urlopen")
    def test_lesson_create_by_owner(
        self, mock_urlopen
    ):  # mock_urlopen передается как аргумент теста

        # Настраиваем мок-объект для urlopen
        mock_response_object = MagicMock()
        mock_response_object.getcode.return_value = (
            200  # Убеждаемся, что getcode() вернет 200 (успех)
        )
        mock_urlopen.return_value = (
            mock_response_object  # urlopen должен возвращать этот мок-объект
        )
        mock_urlopen.side_effect = (
            None  # И убедимся, что сам urlopen не выбрасывает исключений
        )

        self.client.force_authenticate(self.owner_user)
        response = self.client.post(
            self.lessons_list_create_url, self.new_lesson_data, format="json"
        )
        # print(response.status_code) # для отладки
        # print(response.data) # для отладки
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Lesson.objects.count(), 3)

    def test_lesson_create_by_moderator_forbidden(self):
        self.client.force_authenticate(self.moderator_user)
        response = self.client.post(self.lessons_list_create_url, self.new_lesson_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Lesson.objects.count(), 2)  # Новый урок не создан

    def test_lesson_create_unauthenticated(self):
        response = self.client.post(self.lessons_list_create_url, self.new_lesson_data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(Lesson.objects.count(), 2)

    # Тесты на получение (retrieve) урока
    def test_lesson_retrieve_owner(self):
        self.client.force_authenticate(self.owner_user)
        response = self.client.get(self.lesson_detail_url(self.lesson_owner.pk))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], self.lesson_owner.title)

    def test_lesson_retrieve_moderator_own_lesson(self):
        # Создаем урок для модератора, чтобы он был его владельцем
        lesson_by_moderator = Lesson.objects.create(
            course=self.course_owner,  # Может быть любой курс
            title="Урок модератора",
            video_link="https://youtube.com/watch?v=modlessonID",
            lesson_user=self.moderator_user,
        )
        self.client.force_authenticate(self.moderator_user)
        response = self.client.get(self.lesson_detail_url(lesson_by_moderator.pk))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], lesson_by_moderator.title)

    def test_lesson_retrieve_moderator_another_lesson(self):
        self.client.force_authenticate(self.moderator_user)
        response = self.client.get(self.lesson_detail_url(self.lesson_owner.pk))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], self.lesson_owner.title)

    def test_lesson_retrieve_non_owner(self):
        self.client.force_authenticate(self.non_owner_user)
        response = self.client.get(self.lesson_detail_url(self.lesson_owner.pk))
        # Ожидается 404, так как queryset фильтрует объекты по владельцу
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_lesson_retrieve_superuser(self):
        self.client.force_authenticate(self.superuser)
        response = self.client.get(self.lesson_detail_url(self.lesson_owner.pk))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], self.lesson_owner.title)

    def test_lesson_retrieve_unauthenticated(self):
        response = self.client.get(self.lesson_detail_url(self.lesson_owner.pk))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # Тесты на обновление (update) урока
    def test_lesson_update_owner(self):
        updated_data = {"title": "Обновленное владельцем название урока"}
        self.client.force_authenticate(self.owner_user)
        response = self.client.patch(
            self.lesson_detail_url(self.lesson_owner.pk), updated_data
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.lesson_owner.refresh_from_db()
        self.assertEqual(self.lesson_owner.title, updated_data["title"])

    def test_lesson_update_moderator_another_lesson(self):
        updated_data = {"title": "Название урока обновлено модератором"}
        self.client.force_authenticate(self.moderator_user)
        response = self.client.patch(
            self.lesson_detail_url(self.lesson_owner.pk), updated_data
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.lesson_owner.refresh_from_db()
        self.assertEqual(self.lesson_owner.title, updated_data["title"])

    def test_lesson_update_non_owner_forbidden(self):
        updated_data = {"title": "Попытка обновления не владельцем"}
        self.client.force_authenticate(self.non_owner_user)
        response = self.client.patch(
            self.lesson_detail_url(self.lesson_owner.pk), updated_data
        )
        self.assertEqual(
            response.status_code, status.HTTP_404_NOT_FOUND
        )  # Из-за фильтрации в get_queryset
        self.lesson_owner.refresh_from_db()
        self.assertNotEqual(self.lesson_owner.title, updated_data["title"])

    def test_lesson_update_superuser(self):
        updated_data = {"title": "Название урока обновлено суперпользователем"}
        self.client.force_authenticate(self.superuser)
        response = self.client.patch(
            self.lesson_detail_url(self.lesson_owner.pk), updated_data
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.lesson_owner.refresh_from_db()
        self.assertEqual(self.lesson_owner.title, updated_data["title"])

    def test_lesson_update_unauthenticated(self):
        updated_data = {"title": "Попытка обновления без аутентификации"}
        response = self.client.patch(
            self.lesson_detail_url(self.lesson_owner.pk), updated_data
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.lesson_owner.refresh_from_db()
        self.assertNotEqual(self.lesson_owner.title, updated_data["title"])

    # Тесты на удаление (delete) урока
    def test_lesson_delete_owner(self):
        self.client.force_authenticate(self.owner_user)
        response = self.client.delete(self.lesson_detail_url(self.lesson_owner.pk))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Lesson.objects.filter(pk=self.lesson_owner.pk).exists())

    def test_lesson_delete_moderator_forbidden(self):
        self.client.force_authenticate(self.moderator_user)
        response = self.client.delete(self.lesson_detail_url(self.lesson_owner.pk))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(
            Lesson.objects.filter(pk=self.lesson_owner.pk).exists()
        )  # Урок все еще существует

    def test_lesson_delete_non_owner_forbidden(self):
        self.client.force_authenticate(self.non_owner_user)
        response = self.client.delete(self.lesson_detail_url(self.lesson_owner.pk))
        self.assertEqual(
            response.status_code, status.HTTP_404_NOT_FOUND
        )  # Из-за фильтрации в get_queryset
        self.assertTrue(Lesson.objects.filter(pk=self.lesson_owner.pk).exists())

    def test_lesson_delete_superuser(self):
        self.client.force_authenticate(self.superuser)
        response = self.client.delete(self.lesson_detail_url(self.lesson_owner.pk))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Lesson.objects.filter(pk=self.lesson_owner.pk).exists())

    def test_lesson_delete_unauthenticated(self):
        response = self.client.delete(self.lesson_detail_url(self.lesson_owner.pk))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertTrue(Lesson.objects.filter(pk=self.lesson_owner.pk).exists())


class CourseSubscriptionTest(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="user@example.com", password="testpass"
        )
        # Создаем отдельного пользователя для курса, чтобы он не совпадал с self.user
        self.course_owner = User.objects.create_user(
            email="courseowner@example.com", password="testpass"
        )
        self.course = Course.objects.create(
            title="Тестовый курс", course_user=self.course_owner
        )
        self.subscribe_url = reverse("materials:course_subscribe")

    def test_toggle_subscription_add(self):
        """Тест на успешное добавление подписки."""
        self.client.force_authenticate(self.user)
        data = {"course_id": self.course.id}

        # Проверяем, что подписки еще нет
        self.assertFalse(
            CourseSubscription.objects.filter(
                user=self.user, course=self.course
            ).exists()
        )

        response = self.client.post(self.subscribe_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "Подписка добавлена")
        self.assertTrue(
            CourseSubscription.objects.filter(
                user=self.user, course=self.course
            ).exists()
        )

    def test_toggle_subscription_remove(self):
        """Тест на успешное удаление (отмену) подписки."""
        # Сначала создаем подписку, которую будем удалять
        CourseSubscription.objects.create(user=self.user, course=self.course)
        self.assertTrue(
            CourseSubscription.objects.filter(
                user=self.user, course=self.course
            ).exists()
        )

        self.client.force_authenticate(self.user)
        data = {"course_id": self.course.id}

        response = self.client.post(self.subscribe_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["message"], "Подписка удалена")
        self.assertFalse(
            CourseSubscription.objects.filter(
                user=self.user, course=self.course
            ).exists()
        )

    def test_toggle_subscription_unauthenticated(self):
        """Тест на попытку подписки/отписки неавторизованным пользователем."""
        data = {"course_id": self.course.id}
        response = self.client.post(self.subscribe_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertFalse(
            CourseSubscription.objects.filter(
                user=self.user, course=self.course
            ).exists()
        )

    def test_toggle_subscription_invalid_course_id(self):
        """Тест на попытку подписки/отписки с несуществующим ID курса."""
        self.client.force_authenticate(self.user)
        invalid_course_id = self.course.id + 999  # ID, которого точно не существует
        data = {"course_id": invalid_course_id}
        response = self.client.post(self.subscribe_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        # Убедимся, что новая подписка не была создана
        self.assertFalse(
            CourseSubscription.objects.filter(
                user=self.user, course__id=invalid_course_id
            ).exists()
        )

    def test_toggle_subscription_missing_course_id(self):
        """Тест на попытку подписки/отписки без указания course_id в теле запроса."""
        self.client.force_authenticate(self.user)
        data = {}  # Пустой payload
        response = self.client.post(self.subscribe_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"], "Параметр 'course_id' обязателен.")
        self.assertFalse(CourseSubscription.objects.filter(user=self.user).exists())


class ValidatorTest(APITestCase):
    """Тесты для функции validate_youtube_url в materials/validators.py"""

    @patch("materials.validators.urlopen")
    def test_valid_youtube_url(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.getcode.return_value = 200
        mock_urlopen.return_value = mock_response

        valid_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        try:
            validate_youtube_url(valid_url)
        except ValidationError:
            self.fail("validate_youtube_url поднял ValidationError для валидного URL")

    @patch("materials.validators.urlopen")
    def test_youtube_short_url(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.getcode.return_value = 200
        mock_urlopen.return_value = mock_response

        valid_url = "https://youtu.be/dQw4w9WgXcQ"
        try:
            validate_youtube_url(valid_url)
        except ValidationError:
            self.fail("validate_youtube_url поднял ValidationError для короткого URL")

    def test_empty_url_raises_validation_error(self):
        """Проверяем, что пустой URL вызывает ValidationError."""
        with self.assertRaises(ValidationError) as cm:
            validate_youtube_url("")
        self.assertIn("URL слишком длинный или пустой", cm.exception.message)

    def test_too_long_url_raises_validation_error(self):
        """Проверяем, что слишком длинный URL вызывает ValidationError."""
        long_url = (
            "https://www.youtube.com/watch?v=" + "a" * 1020
        )  # Total length > 1024
        with self.assertRaises(ValidationError) as cm:
            validate_youtube_url(long_url)
        self.assertIn("URL слишком длинный или пустой", cm.exception.message)

    def test_non_youtube_url_raises_validation_error(self):
        """Проверяем, что URL, не являющийся YouTube, вызывает ValidationError."""
        invalid_url = "https://www.google.com/search?q=test"
        with self.assertRaises(ValidationError) as cm:
            validate_youtube_url(invalid_url)
        self.assertIn(
            "Можно использовать только ссылки с YouTube", cm.exception.message
        )

    @patch("materials.validators.urlopen")
    def test_youtube_url_unreachable_raises_url_error(self, mock_urlopen):
        """Проверяем, что недоступный URL (URLError) вызывает ValidationError."""
        mock_urlopen.side_effect = URLError("Test URLError")
        url = "https://www.youtube.com/watch?v=some_valid_id"
        with self.assertRaises(ValidationError) as cm:
            validate_youtube_url(url)
        self.assertIn("Не удалось проверить доступность видео", cm.exception.message)

    @patch("materials.validators.urlopen")
    def test_youtube_url_non_200_status_raises_validation_error(self, mock_urlopen):
        """Проверяем, что URL, возвращающий статус не 200, вызывает ValidationError."""
        mock_response_object = MagicMock()
        mock_response_object.getcode.return_value = 404  # Not Found
        mock_urlopen.return_value = mock_response_object
        url = "https://www.youtube.com/watch?v=some_valid_id"
        with self.assertRaises(ValidationError) as cm:
            validate_youtube_url(url)
        self.assertIn("Видео недоступно", cm.exception.message)

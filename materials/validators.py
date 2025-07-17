from django.core.exceptions import ValidationError
import re
from urllib.request import urlopen
from urllib.error import URLError


def validate_youtube_url(value):
    """
        Проверяет, что URL является ссылкой на YouTube.

        Работает с различными форматами YouTube URLs, например:
        - https://www.youtube.com/watch?v=dQw4w9WgXcQ
        - https://youtu.be/dQw4w9WgXcQ
        - https://youtube.com/embed/dQw4w9WgXcQ
        - https://www.youtube.com/v/dQw4w9WgXcQ
        """
    if not value or len(value) > 1024:  # максимальная длина URL
        raise ValidationError("URL слишком длинный или пустой")

    youtube_regex = (
        r'(https?://)?(www\.)?'
        r'(youtube|youtu|youtube-nocookie)\.(com|be)/'
        r'(watch\?v=|embed/|v/|.+\?v=)?([a-zA-Z0-9_-]{11})'
    )

    if not re.match(youtube_regex, value):
        raise ValidationError(f"Использована неверная ссылка '{value}'. Можно использовать только ссылки с YouTube.")

    try:
        response = urlopen(value)
        if response.getcode() != 200:
            raise ValidationError("Видео недоступно")
    except URLError:
        raise ValidationError("Не удалось проверить доступность видео")

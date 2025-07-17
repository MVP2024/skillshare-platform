from django.core.exceptions import ValidationError
import re

def validate_youtube_url(value):
    """
        Проверяет, что URL является ссылкой на YouTube.

        Работает с различными форматами YouTube URLs:
        - class
        - class
        - class
        - class (shortened)
        """
    youtube_regex = (
        r'(https?://)?(www\.)?'
        '(youtube|youtu|youtube-nocookie)\.(com|be)/'
        '(watch\?v=|embed/|v/|.+\?v=)?([^&?\\n]{11})'
    )

    if not re.match(youtube_regex, value):
        raise ValidationError(f"Использована неверная ссылка '{value}'. Можно использовать только ссылки с YouTube.")

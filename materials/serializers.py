from rest_framework import serializers
from materials.validators import validate_youtube_url

from materials.models import Course, Lesson, CourseSubscription


class LessonSerializer(serializers.ModelSerializer):
    video_link = serializers.URLField(validators=[validate_youtube_url])

    class Meta:
        model = Lesson
        fields = "__all__"
        # course_user = serializers.PrimaryKeyRelatedField(source='course_user', read_only=True)


class CourseLessonSerializer(serializers.ModelSerializer):
    """
    Облегченный сериализатор для уроков, используемый при вложении в CourseSerializer.
    """

    class Meta:
        model = Lesson
        fields = ["id", "title"]


class CourseSerializer(serializers.ModelSerializer):
    lessons_count = serializers.SerializerMethodField()
    lessons = CourseLessonSerializer(many=True, read_only=True)
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = "__all__"

    def get_lessons_count(self, obj):
        return obj.lessons.count()

    def get_is_subscribed(self, obj):
        """Проверяет подписку текущего пользователя на курс"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.subscribers.filter(user=request.user).exists()
        return False

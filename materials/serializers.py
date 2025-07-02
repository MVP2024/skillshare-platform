from rest_framework import serializers
from materials.models import Course, Lesson


class LessonSerializer(serializers.ModelSerializer):
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

    class Meta:
        model = Course
        fields = "__all__"

    def get_lessons_count(self, obj):
        return obj.lessons.count()

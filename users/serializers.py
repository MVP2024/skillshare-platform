from rest_framework import serializers
from users.models import User
from users.models import Payment


class PaymentSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели Payment, включающий информацию о пользователе, курсе и уроке.
    Используется для вывода истории платежей в профиле пользователя.
    """
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    paid_course = serializers.PrimaryKeyRelatedField(read_only=True, allow_null=True)
    paid_lesson = serializers.PrimaryKeyRelatedField(read_only=True, allow_null=True)

    class Meta:
        model = Payment
        fields = "__all__"


class UserSerializer(serializers.ModelSerializer):
    """
        Сериализатор для модели User, включающий историю платежей.
        Поля:
        - `payments`: Список всех платежей пользователя (вложенный сериализатор).
    """

    payments = PaymentSerializer(many=True, read_only=True)  # Вложенный сериализатор для платежей

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "phone",
            "city",
            "avatar",
            "first_name",
            "last_name",
            "payments",
        )

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
    password = serializers.CharField(write_only=True, required=False)

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
            "password",
        )
        read_only_fields = ('email',)

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        user = User.objects.create(**validated_data)
        if password is not None:
            user.set_password(password)
            user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        if password is not None:
            instance.set_password(password)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance

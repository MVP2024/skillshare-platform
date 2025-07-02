from rest_framework import serializers

from users.models import Payment, User


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

    payments = PaymentSerializer(
        many=True, read_only=True
    )  # Вложенный сериализатор для платежей
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
            "last_login",
            "payments",
            "password",
        )
        read_only_fields = ("email",)

    def to_representation(self, instance):
        """
        Условно скрывает конфиденциальные поля, если запрашивающий пользователь не является владельцем профиля.
        """
        ret = super().to_representation(instance)
        request = self.context.get("request")

        # Если запрос существует и пользователь аутентифицирован
        if request and request.user.is_authenticated:
            # Если запрашивающий пользователь НЕ является владельцем просматриваемого профиля
            if request.user != instance:
                # Удаляем конфиденциальные поля
                ret.pop("last_name", None)
                ret.pop("payments", None)
                ret.pop("last_login", None)
                # Поле 'password' уже write_only, поэтому оно не будет отображаться при GET-запросах.
        return ret

    def create(self, validated_data):
        password = validated_data.pop("password", None)
        user = User.objects.create(**validated_data)
        if password is not None:
            user.set_password(password)
            user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        if password is not None:
            instance.set_password(password)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance

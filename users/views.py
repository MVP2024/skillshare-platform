from django.shortcuts import render
from rest_framework import viewsets
from users.models import User
from users.serializers import UserSerializer
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet для CRUD операций с пользователями (включая редактирование профиля).
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer


class ProfileUpdateView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

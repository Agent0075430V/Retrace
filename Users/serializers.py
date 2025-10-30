from rest_framework import serializers
from django.contrib.auth.models import User as DjangoUser
from .models import User as ProfileUser, UserProfile


class DjangoUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = DjangoUser
        fields = ['id', 'username', 'email', 'first_name', 'last_name']


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = DjangoUser
        fields = ['id', 'username', 'email', 'password']

    def create(self, validated_data):
        user = DjangoUser.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email'),
            password=validated_data['password']
        )
        return user


class ProfileUserSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='username.username', read_only=True)

    class Meta:
        model = ProfileUser
        fields = ['id', 'username', 'email', 'department', 'phone_number', 'role', 'deleted_status', 'created_at', 'updated_at']


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['id', 'profile_picture', 'bio', 'address', 'created_at', 'updated_at']

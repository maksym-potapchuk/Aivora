from rest_framework import serializers
from .models.user import User


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = (
            'email', 'password',
            'first_name', 'last_name',
            'country', 'city'
        )

    
    def create(self, validated_data):
        password = validated_data.pop('password')

        user = User.objects.create_user(
            password=password,
            is_active=False,
            is_email_verified=False,
            **validated_data
        )
        return user
    

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, min_length=8)



class UserMeSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "uuid", "first_name", "last_name", "email", "phone", "country", "city", "photo", "appointment", "rank", "experience", "role"
        )

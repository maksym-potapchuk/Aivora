from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from .serializers import UserSerializer, ChangePasswordSerializer
from .models import User
from .services import MailConfirmation, PasswordReset, send_email_core
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
import time


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        user: User = authenticate(
            username = request.data.get('email'),
            password = request.data.get('password')
        )

        if not user:
            return Response({'detail': 'User doesn\'t exist'}, status=401)

        if not user.is_email_verified:
            return Response({'detail': 'Email not verified'}, status=403)
        
        if not user.is_active:
            return Response({'detail': 'User is deactivated'}, status=403)
        
        refresh = RefreshToken.for_user(user)

        send_email_core(
            subject="New login into accout",
            message=f"Deat {user.first_name}.\nWe found out that was new login into you account at {time.strftime("%H:%M")} GMT+0",
            recipient=user.email
        )

        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        })
    

class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = UserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.save()
        mail_conf = MailConfirmation(user)
        mail_conf.send_email(request.data.get('email'))

        return Response(
            {'detail': 'Register confirmation was sended to email box'},
            status=status.HTTP_200_OK
        )
    

class EmailConfirmationView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request, token, uid64):
        response = MailConfirmation.verify_email(token, uid64)

        return Response(response)
    

class ChangePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]


    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user: User = request.user
        old_password = serializer.validated_data.get('old_password')
        new_password = serializer.validated_data.get('new_password')

        if not user.check_password(old_password):
            return Response({'detail': 'Old password is incorrect'}, status=400)

        user.set_password(new_password)
        user.save()

        return Response({'detail': 'Password changed successfully'})
    

class PasswordResetView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        try:
            user: User = User.objects.get(email=request.data.get('email'))
        except Exception:
            return {'details': 'User does\'nt exist'}
        password_manager = PasswordReset(user)
        password_manager.send_email(user.email)

        return Response({'detail': 'Password reset confirmation was sended to email box'}, status=200)
    

class PasswordResetConfirmView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, token, uid64):
        response = PasswordReset.reset_password(token, uid64, request.data.get('new_password'))

        return Response(response)






from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from .serializers import UserSerializer, ChangePasswordSerializer, UserMeSerializer
from .models import User
from .services import MailConfirmation, PasswordReset, send_email_core
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.utils.timezone import now
from django.conf import settings


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        user: User = authenticate(
            request,
            username = request.data.get('email'),
            password = request.data.get('password')
        )

        if not user:
            return Response({'detail': 'User doesn\'t exist'}, status=status.HTTP_401_UNAUTHORIZED)

        if not user.is_email_verified:
            return Response({'detail': 'Email not verified'}, status=status.HTTP_403_FORBIDDEN)
        
        if not user.is_active:
            return Response({'detail': 'User is deactivated'}, status=status.HTTP_403_FORBIDDEN)
        
        refresh = RefreshToken.for_user(user)
        response = Response(
            {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            },
            status=status.HTTP_200_OK
        )

        response.set_cookie(
            "access_token",
            str(refresh.access_token),
            httponly=True,
            secure=settings.SECURE_COOKIES,
            samesite="Lax",
        )
        response.set_cookie(
            "refresh_token",
            str(refresh),
            httponly=True,
            secure=settings.SECURE_COOKIES,
            samesite="Lax",
        )

        
        try:
            send_email_core(
                subject="New login into accout",
                message=(
                        f"Dear {user.first_name},\n"
                        f"New login detected at {now().strftime('%H:%M')} UTC"
                    ),
                recipient=user.email
            )
        except Exception:
            pass

        return response
    

class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = UserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.save()
        mail_conf = MailConfirmation(user)
        try:
            mail_conf.send_email(request.data.get('email'))
        except Exception:
            pass

        return Response(
            {'detail': 'Register confirmation was sended to email box'},
            status=status.HTTP_200_OK
        )

class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        refresh = request.COOKIES.get("refresh_token")
        if refresh:
            RefreshToken(refresh).blacklist()

        response = Response({"detail": "logout"})
        response.delete_cookie("access_token")
        response.delete_cookie("refresh_token")
        return response

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
        try:
            password_manager.send_email(user.email)
        except Exception:
            pass

        return Response({'detail': 'Password reset confirmation was sended to email box'}, status=200)
    

class PasswordResetConfirmView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, token, uid64):
        response = PasswordReset.reset_password(token, uid64, request.data.get('new_password'))

        return Response(response)


class UserMeView(APIView):
    permission_classes=[permissions.IsAuthenticated]

    def get(self, request):
        serializer=UserMeSerializer(request.user)

        return Response(serializer.data)
    
    def patch(self, request):
        serializer=UserMeSerializer(
            request.user,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from .serializers import UserSerializer, ChangePasswordSerializer
from .models import User
from .services import MailConfirmation, PasswordReset
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate

class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        print(request.data.get('email'), request.data.get('password'))
        user: User = authenticate(
            username = request.data.get('email'),
            password = request.data.get('password')
        )

        if not user:
            return Response({'detail': 'User does\'nt exist'}, status=401)

        if not user.is_email_verified:
            return Response({'detail': 'Email not verified'}, status=403)
        
        if not user.is_active:
            return Response({'detail': 'User is deactivated'}, status=403)
        
        refresh = RefreshToken.for_user(user)

        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        })
    

class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        print(request.data)
        serializer = UserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.save()
        mail_conf = MailConfirmation(user)
        link = mail_conf.send_email()

        return Response(
            {'detail': f'Check your email to verify account:\\\ {link}'},
            status=status.HTTP_201_CREATED
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
        user: User = User.objects.get(email=request.data.get('email'))
        password_manager = PasswordReset(user)
        link = password_manager.send_email()

        return Response(link, status=200)
    

class PasswordResetConfirmView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, token, uid64):
        response = PasswordReset.reset_password(token, uid64, request.data.get('new_password'))

        return Response(response)






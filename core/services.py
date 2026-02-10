from django.core.mail import send_mail
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from .models import User
from django.urls import reverse
from rest_framework_simplejwt.tokens import RefreshToken
from functools import wraps


class TokenManager:
    def __init__(self, user: User):
        self.user = user

    def create_token(self) -> tuple:
        token = default_token_generator.make_token(self.user)
        uid64 = urlsafe_base64_encode(force_bytes(self.user.uuid))
        return token, uid64

    def send_email(self) -> str:
        token, uid64 = self.create_token()
        return self.get_link(token, uid64)

    def get_link(self, token, uid64) -> str:
        raise NotImplementedError("Define get_link in subclass")


def base64_decoder(func):
        @wraps(func)
        def wrapper(cls, token, uid64, *args, **kwargs):
            try:
                uid = force_str(urlsafe_base64_decode(uid64))
                user: User = User.objects.get(uuid=uid)
            except User.DoesNotExist:
                return {'detail': 'Invalid link', 'status': 400}

            if not default_token_generator.check_token(user, token):
                return {'detail': 'Invalid Token or expired', 'status': 400}

            return func(cls, user, *args, **kwargs)

        return wrapper


class PasswordReset(TokenManager):
    def get_link(self, token, uid64):
        link = reverse(
            'password_reset_confirm',
            kwargs={'uid64': uid64, 'token': token}
        )

        return {'detail': f'Click on the link to confirm action:\n {link}'}
    
    @classmethod
    @base64_decoder
    def reset_password(cls, user: User, new_password):
        user.set_password(new_password)
        user.save()

        return {'detail': 'Password was reset succesfully!'}


class MailConfirmation(TokenManager):
    def get_link(self, token, uid64):
        link = reverse(
            'email_confirmation',
            kwargs={'uid64': uid64, 'token': token}
        )
    
        return {'detail': f'Click on the link to confirm action:\n {link}'}
    
    @classmethod
    @base64_decoder
    def verify_email(cls, user: User) -> dict:
        user.is_active = True
        user.is_email_verified = True
        user.save()

        return {'detail': 'Email confirmed', 'status': 200}
        




from django.urls import path
from .views import (
    RegisterView, EmailConfirmationView, LoginView, ChangePasswordView, PasswordResetConfirmView, PasswordResetView,
    LogoutView, UserMeView
)


urlpatterns = [
    path("auth/register/", RegisterView.as_view(), name="auth_register"),
    path("auth/login/", LoginView.as_view(), name="login"),
    path("auth/login/", LoginView.as_view(), name="login"),
    path("auth/logout/", LogoutView.as_view(), name="logout"),
    path("auth/confirm/<str:token>/<str:uid64>/", EmailConfirmationView.as_view(), name="email_confirmation"),
    path("auth/password/change/", ChangePasswordView.as_view(), name="change_password"),
    path("auth/password/reset/", PasswordResetView.as_view(), name="password_reset"),
    path("auth/password/reset/confirm/<str:token>/<str:uid64>/", PasswordResetConfirmView.as_view(), name="password_reset_confirm"),
    path("account/me/", UserMeView.as_view(), name="account_me"),
]
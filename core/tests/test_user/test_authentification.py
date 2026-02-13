import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

from core.services import PasswordReset

User = get_user_model()


@pytest.fixture
def client():
    """Fixture to get API client for requests"""
    return APIClient()


@pytest.fixture
def test_user():
    return User.objects.create_user(
        first_name='Test',
        last_name='User',
        email='test@example.com',
        password='testpassword',
        country='UA',
        is_active=True,
        is_email_verified=True,
    )

@pytest.fixture
def test_bad_user():
    return User.objects.create_user(
        first_name='Bad',
        last_name='User',
        email='baduser@example.com',
        password='badpassword',
        country='UA',
        is_active=True,
        is_email_verified=False,
    )

@pytest.mark.django_db
class TestAuthentication:

    def test_user_registration(self, client):
        """Test user registration endpoint"""
        data = {
            "first_name": "New",
            "last_name": "User",
            "email": "newuser@example.com",
            "password": "newpassword",
            "country": "UA",
        }
        response = client.post('/api/v1/auth/register/', data)
        assert response.status_code == status.HTTP_200_OK
        assert User.objects.filter(email='newuser@example.com').exists()
        
    def test_user_login(self, client, test_user):
        """Test user login endpoint"""
        data = {
            "email": test_user.email,
            "password": "testpassword",
        }
        response = client.post('/api/v1/auth/login/', data, format='json')
        assert response.status_code == status.HTTP_200_OK

        assert "access_token" in response.cookies
        assert 'refresh_token' in response.cookies

        cookie=response.cookies['access_token']
        assert cookie['httponly'] == True
        assert cookie['samesite'] == 'Lax'
    
    def test_user_login_bad_user(self, client, test_bad_user):
        """Test user login endpoint with bad user"""
        data = {
            "email": test_bad_user.email,
            "password": "badpassword",
        }
        response = client.post('/api/v1/auth/login/', data, format='json')
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.data['detail'] == 'Email not verified'

    def test_user_me(self, client, test_user):
        """Test user me endpoint"""
        client.force_authenticate(user=test_user)
        response = client.get('/api/v1/account/me/')
        assert response.status_code == status.HTTP_200_OK

        assert response.data['email'] == test_user.email
        assert response.data['first_name'] == test_user.first_name
        assert response.data['last_name'] == test_user.last_name

    def test_user_logout(self, client, test_user):
        """Test user logout endpoint"""
        client.force_authenticate(user=test_user)

        response = client.get('/api/v1/auth/logout/')

        assert response.status_code == status.HTTP_204_NO_CONTENT

        for name in ('access_token', 'refresh_token'):
            cookie = response.cookies.get(name)
            assert cookie is None or getattr(cookie, 'value', None) == ''

    def test_change_password(self, client, test_user):
        """Change password with correct old password returns 200 and new password works."""
        client.force_authenticate(user=test_user)
        
        data = {'old_password': 'testpassword', 'new_password': 'newpass123'}

        response = client.post('/api/v1/auth/password/change/', data, format='json')
        # HERE SHOULD BE SOME VALIDATION TO CHANGE PASSWORD (Email verification, etc.)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['detail'] == 'Password changed successfully'
        # Login with new password works
        login_response = client.post(
            '/api/v1/auth/login/',
            {'email': test_user.email, 'password': 'newpass123'},
            format='json',
        )
        assert login_response.status_code == status.HTTP_200_OK

    def test_change_password_wrong_old(self, client, test_user):
        """Change password with wrong old password returns 400."""
        client.force_authenticate(user=test_user)
        data = {'old_password': 'wrong', 'new_password': 'newpass123'}
        response = client.post('/api/v1/auth/password/change/', data, format='json')
        assert response.status_code == 400
        assert response.data['detail'] == 'Old password is incorrect'

    def test_password_reset(self, client, test_user):
        """Request password reset for existing email returns 200 and success message."""
        response = client.post(
            '/api/v1/auth/password/reset/',
            {'email': test_user.email},
            format='json',
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data['detail'] == 'Password reset confirmation was sended to email box'

    def test_password_reset_confirm(self, client, test_user):
        """Confirm reset with valid token sets new password; login with new password works."""
        token, uid64 = PasswordReset(test_user).create_token()
        data = {'new_password': 'newpass123'}
        response = client.post(
            f'/api/v1/auth/password/reset/confirm/{token}/{uid64}/',
            data,
            format='json',
        )
        assert response.status_code == status.HTTP_200_OK
        assert response.data['detail'] == 'Password was reset successfully!'
        login_response = client.post(
            '/api/v1/auth/login/',
            {'email': test_user.email, 'password': 'newpass123'},
            format='json',
        )
        assert login_response.status_code == status.HTTP_200_OK

    def test_password_reset_confirm_invalid_token(self, client, test_user):
        """Confirm reset with invalid token returns error."""
        _, uid64 = PasswordReset(test_user).create_token()
        data = {'new_password': 'newpass123'}
        response = client.post(
            f'/api/v1/auth/password/reset/confirm/invalid-token/{uid64}/',
            data,
            format='json',
        )
        assert response.data['detail'] in ('Invalid Token or expired', 'Invalid link')

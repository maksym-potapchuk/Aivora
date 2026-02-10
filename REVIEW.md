# Aivora Code Review

**Reviewer:** Claude
**Date:** 2026-02-10
**Scope:** Full codebase review — architecture, security, correctness, and code quality
**Branch reviewed:** `feat/auth_model_and_funcs`

---

## Summary

Aivora is a Django REST Framework backend providing user authentication and management with role-based access control. The project is in early development (5 commits) and implements registration, login, email verification, password change, and password reset flows using JWT tokens.

The foundations are reasonable — custom User model with UUID primary key, service layer pattern, DRF conventions — but there are several critical issues that need to be addressed before this code is suitable for any environment beyond local development.

---

## Critical Issues

### 1. Debug `print()` statements leak credentials — `core/views.py:14,41`

```python
# views.py:14 — prints email and password to stdout
print(request.data.get('email'), request.data.get('password'))

# views.py:41 — prints entire request payload
print(request.data)
```

User credentials are written to stdout on every login and registration attempt. In any deployment where logs are collected, this exposes plaintext passwords. These must be removed.

### 2. Unhandled `DoesNotExist` in password reset — `core/views.py:89`

```python
user: User = User.objects.get(email=request.data.get('email'))
```

If the email doesn't exist in the database, this raises `User.DoesNotExist` and returns an unhandled 500 error. This also reveals to an attacker whether an email is registered (user enumeration). Wrap this in a try/except and return a generic response regardless of whether the user exists.

### 3. Emails are never actually sent — `core/services.py:20-22`

```python
def send_email(self) -> str:
    token, uid64 = self.create_token()
    return self.get_link(token, uid64)
```

`send_mail` is imported but never called. The `send_email()` method only generates a link and returns it in the HTTP response. The confirmation/reset links are exposed directly to the caller instead of being delivered via email. This means:
- Anyone who calls the register endpoint gets the verification link in the response body.
- Anyone who calls the password reset endpoint gets the reset link in the response body — this is a **critical security vulnerability** since it allows account takeover without email access.

### 4. No email backend configured — `aivora/settings.py`

There is no `EMAIL_BACKEND`, `EMAIL_HOST`, or related email settings configured in `settings.py`. Even if `send_mail()` were called, it would fail or use Django's default console backend.

---

## Security Concerns

### 5. `DEBUG = True` hardcoded — `aivora/settings.py:27`

Debug mode should never be on in production. This should be driven by an environment variable.

### 6. `ALLOWED_HOSTS` is empty — `aivora/settings.py:29`

An empty `ALLOWED_HOSTS` with `DEBUG=False` will reject all requests. With `DEBUG=True` it allows `localhost` only. This needs to be configured for deployment.

### 7. No CORS configuration

There is no `django-cors-headers` in the dependencies and no CORS middleware. Any frontend on a different origin will be blocked.

### 8. JWT signing key tied to `SECRET_KEY` — `aivora/settings.py:75`

If `SECRET_KEY` is not set in the environment, it will be `None`, and JWT signing will break silently or produce tokens signed with `None`. There is no validation that `SECRET_KEY` is present.

### 9. No password strength validation on reset — `core/services.py:56-58`

`PasswordReset.reset_password()` calls `user.set_password(new_password)` without running Django's password validators. Users could set `"1"` as their new password via the reset flow, bypassing the 8-character minimum enforced on registration.

### 10. Token not invalidated after use

Both the email confirmation token and password reset token remain valid after use until they expire naturally. A password reset link can be reused multiple times.

---

## Bugs and Correctness Issues

### 11. `base64_decoder` swallows the `new_password` argument — `core/services.py:28-42`

The decorator signature is:
```python
def wrapper(cls, token, uid64, *args, **kwargs):
```

But `PasswordResetConfirmView` calls:
```python
PasswordReset.reset_password(token, uid64, request.data.get('new_password'))
```

Inside the decorator, `token` and `uid64` are consumed, and `new_password` ends up in `*args`. The decorated function `reset_password(cls, user, new_password)` then receives `user` from the decorator — but `new_password` is passed through `*args`. This works, but only by accident. If any additional positional argument is added, the mapping will break silently. Use explicit keyword arguments instead.

### 12. Typo in error message — `core/views.py:21`

```python
return Response({'detail': 'User does\'nt exist'}, status=401)
```

"does'nt" should be "doesn't". Also, for a login failure, the message should not reveal whether it was the email or password that was wrong. A generic "Invalid credentials" is more appropriate.

### 13. Typo in model field — `core/models/user.py:51`

```python
experiense = models.PositiveIntegerField(...)
```

"experiense" should be "experience". Since this is a database column name, renaming it later requires a migration. Fix it now while the project is young.

### 14. Escaped backslash in response string — `core/views.py:50`

```python
{'detail': f'Check your email to verify account:\\\ {link}'}
```

The `\\\` produces a literal backslash in the output. This looks like a formatting mistake.

### 15. Typo in error message — `core/models/user.py:10`

```python
raise ValueError("Provide Email filed")
```

"filed" should be "field".

### 16. Typo in success message — `core/services.py:60`

```python
return {'detail': 'Password was reset succesfully!'}
```

"succesfully" should be "successfully".

---

## Architecture and Design

### 17. No test coverage

`core/tests.py` is empty. There are zero tests for any of the authentication flows. At minimum, the following need tests:
- Registration with valid/invalid data
- Login with correct/incorrect credentials
- Email verification with valid/expired/invalid tokens
- Password change with correct/incorrect old password
- Password reset flow end-to-end

### 18. Empty `permissions.py` and `admin.py`

Roles (`admin`, `owner`, `curator`, `student`, `manager`) and ranks (`noob` through `god`) are defined in the model but there are no permission classes that use them. The admin site has no User model registered, so there's no way to manage users through the Django admin.

### 19. No API documentation

No Swagger/OpenAPI schema is configured. For a REST API, auto-generated documentation (via `drf-spectacular` or `drf-yasg`) is important for frontend developers and API consumers.

### 20. No logging configuration

The project uses `print()` instead of Python's `logging` module. A proper logging setup would allow different log levels, structured output, and log routing without code changes.

### 21. Service layer doesn't actually send emails

The `TokenManager` hierarchy (`MailConfirmation`, `PasswordReset`) is structured as if it manages email delivery, but it only generates links. The abstraction is misleading — the name `send_email` implies sending, but it doesn't send anything.

### 22. Missing database index on email

`email` is set to `unique=True` which does create an index in PostgreSQL, so this is actually fine. However, `phone` has no index and no uniqueness constraint — two users could register the same phone number.

### 23. Field length constraints

- `first_name` / `last_name` max 16 characters — too short for many real names
- `phone` max 10 characters — too short for international numbers with country codes (e.g., `+380XXXXXXXXX` is 13 chars)

---

## Positive Observations

- **UUID primary key** — Good choice. Avoids exposing sequential IDs in URLs and APIs.
- **Custom User model from the start** — Changing the user model later in Django is painful. Starting with a custom model is correct.
- **Service layer pattern** — Separating business logic from views is good practice, even if the current implementation is incomplete.
- **`AbstractTimeStampModel`** — Having `created_at`/`updated_at` on all models is useful.
- **`min_length=8` on password serializer** — Basic password length enforcement is in place for registration and change flows.
- **Dependabot configured** — Automated dependency updates are set up.

---

## Recommended Next Steps (Priority Order)

1. **Remove `print()` statements** and configure proper logging
2. **Fix the password reset vulnerability** — do not return reset links in the response body
3. **Add try/except around `User.objects.get()` in password reset**
4. **Implement actual email sending** with an email backend
5. **Fix typos** in model fields (especially `experiense` — requires migration)
6. **Add tests** for all auth flows
7. **Set `DEBUG` from environment variable**
8. **Configure `ALLOWED_HOSTS`** and CORS
9. **Add password validation** to the reset flow
10. **Register User model in Django admin**
11. **Add API documentation** with drf-spectacular

---

*Review generated for commit `0ea2f17`.*

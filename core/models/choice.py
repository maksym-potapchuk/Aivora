from .base import models


class UserRoleChoice(models.TextChoices):
    ADMIN = 'admin', 'Адмін'
    OWNER = 'owner', 'Власник організації'
    СURATOR = 'curator', 'Куратор'
    STUDENT = 'student', 'Студент'
    MANAGER = 'manager', 'Менеджер'


class UserRankChoice(models.TextChoices):
    NOOB = 'noob', 'Noob'
    JUNIOR = 'junior', 'Junior'
    MIDDLE = 'middle', 'Middle'
    SENIOR = 'senior', 'Senior'
    GOD = 'god', 'God'
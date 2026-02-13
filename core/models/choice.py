from .base import models


class UserRoleChoice(models.TextChoices):
    ADMIN = 'admin', 'Admin'
    OWNER = 'owner', 'Organization owner'
    СURATOR = 'curator', 'Curator'
    STUDENT = 'student', 'Student'
    MANAGER = 'manager', 'Manager'


class UserRankChoice(models.TextChoices):
    NOOB = 'noob', 'Noob'
    JUNIOR = 'junior', 'Junior'
    MIDDLE = 'middle', 'Middle'
    SENIOR = 'senior', 'Senior'
    GOD = 'god', 'God'
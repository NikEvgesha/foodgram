from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, username, email, first_name, last_name, password):
        if not email:
            raise ValueError("User must have an email")
        if not username:
            raise ValueError("User must have a username")
        if not password:
            raise ValueError("User must have a password")
        if not first_name:
            raise ValueError("User must have a first name")
        if not last_name:
            raise ValueError("User must have a last name")

        email = self.normalize_email(email)
        username = self.model.normalize_username(username)
        user = self.model(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name)
        user.set_password(password)
        user.save()
        return user

    def create_user(
            self,
            username,
            email,
            first_name,
            last_name,
            password,
            **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(
            username,
            email,
            first_name,
            last_name,
            password)

    def create_superuser(self, username, email, password, **extra_fields):
        if not email:
            raise ValueError("User must have an email")
        if not password:
            raise ValueError("User must have a password")

        user = self.model(
            email=self.normalize_email(email)
        )
        user.set_password(password)
        user.is_admin = True
        user.is_staff = True
        user.save()
        return user


class User(AbstractUser):
    email = models.EmailField(
        'Е-мейл',
        blank=False,
        unique=True,
        max_length=254
    )

    avatar = models.ImageField(
        'Аватар',
        upload_to='avatars/',
        blank=True,
        null=True
    )

    objects = CustomUserManager()

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.username

    @staticmethod
    def has_perm(perm, obj=None):
        return True

    @staticmethod
    def has_module_perms(app_label):
        return True


class Follow(models.Model):

    user = models.ForeignKey(
        User,
        related_name='follower',
        verbose_name="Подписчик",
        on_delete=models.CASCADE,
    )
    author = models.ForeignKey(
        User,
        related_name='followed',
        verbose_name="Автор",
        on_delete=models.CASCADE,
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.UniqueConstraint(
                fields=('user', 'author'),
                name='unique_subscription'
            )
        ]

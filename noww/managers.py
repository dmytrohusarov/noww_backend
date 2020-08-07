from django.contrib.auth.base_user import BaseUserManager


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, phone_number, **extra_fields):
        """
        Creates and saves a User with the given email and password.
        """
        if not phone_number:
            raise ValueError('The given email must be set')
        user = self.model(phone_number=phone_number, **extra_fields)
        user.save(using=self._db)
        return user

    def create_user(self, phone_number, **extra_fields):
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(phone_number, **extra_fields)

    def create_superuser(self, phone_number, **extra_fields):
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(phone_number, **extra_fields)

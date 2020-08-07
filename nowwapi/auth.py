from django.contrib.auth.backends import ModelBackend
from noww.models import User as UserModel


class CustomAuthenticationBackend:

    def authenticate(self, email, password):
        try:
            user = UserModel.objects.get(email=email)
            if user.check_password(password):
                return user
            else:
                return None
        except UserModel.DoesNotExist:
            # logging.getLogger("error_logger").error("user with login %s does not exists " % login)
            return None
        except Exception as e:
            # logging.getLogger("error_logger").error(repr(e))
            return None

    def get_user(self, user_id):
        try:
            user = UserModel.objects.get(id=user_id)
            if user.is_active:
                return user
            return None
        except UserModel.DoesNotExist:
            logging.getLogger("error_logger").error("user with %(user_id)d not found")
            return None

    # def authenticate(self, request, username=None, password=None, **kwargs):
    #     try:
    #         user = User.objects.get(phone_number=username)
    #         pwd_valid = self.check_password(password, user)
    #         user.is_staff = True
    #         user.is_superuser = True
    #         # pwd_valid = user.check_password(password)
    #         if pwd_valid:
    #             return user
    #         return None
    #     except User.DoesNotExist:
    #         return None
    #
    # def get_user(self, user_id):
    #     try:
    #         return User.objects.get(pk=user_id)
    #     except User.DoesNotExist:
    #         return None
    #
    # @staticmethod
    # def check_password(password, user):
    #     return password == user.password

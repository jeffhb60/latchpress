from django.contrib.auth.models import AbstractUser

# Custom user from day one to permit future, backward-compatible fields.
class User(AbstractUser):

    class Meta(AbstractUser.Meta):
        swappable = "AUTH_USER_MODEL"
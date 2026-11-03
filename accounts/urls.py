from django.contrib.auth.views import (
    LoginView, LogoutView, PasswordChangeView, PasswordChangeDoneView,
)
from django.urls import path
from .views import user_create, user_list

urlpatterns = [
    path("login/", LoginView.as_view(template_name="registration/login.html"), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("password/change/", PasswordChangeView.as_view(
        template_name="registration/password_change_form.html",
    ), name="password_change"),
    path("password/changed/", PasswordChangeDoneView.as_view(
        template_name="registration/password_change_done.html",
    ), name="password_change_done"),
    path("users/", user_list, name="user_list"),
    path("users/new/", user_create, name="user_create"),
]
from django.urls import path
from .views import public_post
urlpatterns = [path("<str:slug>/", public_post, name="public_post")]
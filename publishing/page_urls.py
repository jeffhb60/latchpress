from django.urls import path
from .views import public_page
urlpatterns = [path("<str:slug>/", public_page, name="public_page")]
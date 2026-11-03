from django.urls import path
from .views import dashboard, entry_list, entry_new, entry_edit, entry_delete
urlpatterns = [
    path("", dashboard, name="dashboard"),
    path("content/", entry_list, name="entry_list"),
    path("content/new/", entry_new, name="entry_new"),
    path("content/<int:pk>/edit/", entry_edit, name="entry_edit"),
    path("content/<int:pk>/delete/", entry_delete, name="entry_delete"),
]
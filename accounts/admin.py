from django.contrib.admin import AdminSite
from django.contrib.auth.admin import UserAdmin
from .models import User

class OwnerOnlyAdminSite(AdminSite):
    site_header = "LatchPress system administration"
    site_title = "LatchPress administration"
    index_title = "System administration (owners only)"

    def has_permission(self, request):
        user = request.user
        return user.is_active and user.is_authenticated and user.is_superuser

owner_admin_site = OwnerOnlyAdminSite(name="owner_admin")
owner_admin_site.register(User, UserAdmin)

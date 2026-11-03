from django.urls import include, path
from accounts.admin import owner_admin_site
from core.views import HomeView

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("blog/", include("publishing.public_urls")),
    path("pages/", include("publishing.page_urls")),
    path("dashboard/", include("publishing.dashboard_urls")),
    path("accounts/", include("accounts.urls")),
    path("admin/", owner_admin_site.urls),
]
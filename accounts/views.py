from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods

from .forms import OwnerCreateUserForm
from .models import User
from .roles import can_manage_users, enforce, role_for
from publishing.models import AuditEvent

@login_required
@never_cache
@require_http_methods(["GET"])
def user_list(request):
    enforce(can_manage_users(request.user))
    return render(request, "accounts/user_list.html", {
        "users": [(user, role_for(user)) for user in User.objects.prefetch_related("groups").order_by("username")],
    })

@login_required
@never_cache
@require_http_methods(["GET", "POST"])
def user_create(request):
    enforce(can_manage_users(request.user))
    form = OwnerCreateUserForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        AuditEvent.objects.create(
            actor=request.user, action=AuditEvent.Action.USER_CREATED,
            object_type="user", object_id=user.pk, summary=f"Created user {user.username}"
        )
        messages.success(request, "User created.")
        return redirect("user_list")
    return render(request, "accounts/user_form.html", {"form": form})

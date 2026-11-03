# Central authorization policy. Do not authorize using client-provided role names.
from django.core.exceptions import PermissionDenied

ADMINISTRATOR = "Administrator"
EDITOR = "Editor"
AUTHOR = "Author"
CONTRIBUTOR = "Contributor"
SUBSCRIBER = "Subscriber"
ROLE_CHOICES = [(r, r) for r in (ADMINISTRATOR, EDITOR, AUTHOR, CONTRIBUTOR, SUBSCRIBER)]

def role_for(user):
    if not user.is_authenticated or not user.is_active:
        return "Visitor"
    if user.is_superuser:
        return "Owner"
    names = set(user.groups.values_list("name", flat=True))
    valid_roles = {name for name, _ in ROLE_CHOICES}
    # A non-owner may have exactly one CMS role. Unexpected group
    # combinations must never silently grant a higher privilege.
    assigned_roles = names & valid_roles
    if len(assigned_roles) != 1:
        return SUBSCRIBER
    return assigned_roles.pop()

def can_create(user):
    return user.is_authenticated and role_for(user) in {
        "Owner", ADMINISTRATOR, EDITOR, AUTHOR, CONTRIBUTOR
    }

def can_edit(user, entry):
    if not user.is_authenticated:
        return False
    role = role_for(user)
    if role in {"Owner", ADMINISTRATOR, EDITOR}:
        return True
    if role == AUTHOR:
        return entry.author_id == user.pk
    if role == CONTRIBUTOR:
        return entry.author_id == user.pk and entry.status == "draft"
    return False

def can_publish(user):
    return user.is_authenticated and role_for(user) in {
        "Owner", ADMINISTRATOR, EDITOR, AUTHOR
    }

def can_delete(user, entry):
    return can_edit(user, entry)

def can_manage_users(user):
    return user.is_authenticated and user.is_active and user.is_superuser

def enforce(allowed):
    if not allowed:
        raise PermissionDenied("You don't have permission to perform this action.")

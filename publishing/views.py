from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods, require_POST

from accounts.roles import can_create, can_delete, can_edit, can_publish, enforce, role_for
from .forms import EntryForm
from .models import AuditEvent, Entry

def public_post(request, slug):
    entry = get_object_or_404(Entry.objects.public(), kind=Entry.Kind.POST, slug=slug)
    return render(request, "publishing/public_entry.html", {"entry": entry})

def public_page(request, slug):
    entry = get_object_or_404(Entry.objects.public(), kind=Entry.Kind.PAGE, slug=slug)
    return render(request, "publishing/public_entry.html", {"entry": entry})

def visible_content(user):
    entries = Entry.objects.select_related("author")
    if role_for(user) in {"Owner", "Administrator", "Editor"}:
        return entries
    if role_for(user) == "Author":
        return entries.filter(author=user)
    if role_for(user) == "Contributor":
        return entries.filter(author=user, status=Entry.Status.DRAFT)
    return entries.none()

@login_required
@never_cache
@require_http_methods(["GET"])
def dashboard(request):
    entries = visible_content(request.user)
    return render(request, "publishing/dashboard.html", {
        "role": role_for(request.user),
        "total": entries.count(),
        "drafts": entries.filter(status=Entry.Status.DRAFT).count(),
        "published": entries.filter(status=Entry.Status.PUBLISHED).count(),
        "recent": entries[:6],
        "can_create": can_create(request.user),
    })

@login_required
@never_cache
@require_http_methods(["GET"])
def entry_list(request):
    enforce(can_create(request.user))
    return render(request, "publishing/entry_list.html", {
        "entries": visible_content(request.user)[:100],
    })

def record_event(actor, action, entry, summary):
    AuditEvent.objects.create(
        actor=actor, action=action, object_type="entry",
        object_id=entry.pk, summary=summary[:240]
    )

@login_required
@never_cache
@require_http_methods(["GET", "POST"])
def entry_new(request):
    enforce(can_create(request.user))
    form = EntryForm(request.POST or None, user=request.user)
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            entry = form.save(commit=False)
            entry.author = request.user
            if entry.status == Entry.Status.PUBLISHED:
                enforce(can_publish(request.user))
                entry.published_at = timezone.now()
            entry.save()
            record_event(request.user, AuditEvent.Action.CREATED, entry, f"Created {entry.kind}: {entry.title}")
        messages.success(request, "Content saved.")
        return redirect("entry_list")
    return render(request, "publishing/entry_form.html", {"form": form, "heading": "New content"})

@login_required
@never_cache
@require_http_methods(["GET", "POST"])
def entry_edit(request, pk):
    entry = get_object_or_404(Entry, pk=pk)
    enforce(can_edit(request.user, entry))
    # Do not trust direct POST to bypass a contributor's draft-only restriction.
    form = EntryForm(request.POST or None, instance=entry, user=request.user)
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            updated = form.save(commit=False)
            if updated.status == Entry.Status.PUBLISHED and entry.published_at is None:
                enforce(can_publish(request.user))
                updated.published_at = timezone.now()
            elif updated.status == Entry.Status.DRAFT:
                updated.published_at = None
            updated.save()
            record_event(request.user, AuditEvent.Action.UPDATED, updated, f"Updated {updated.kind}: {updated.title}")
        messages.success(request, "Changes saved.")
        return redirect("entry_list")
    return render(request, "publishing/entry_form.html", {"form": form, "heading": "Edit content", "entry": entry})

@login_required
@never_cache
@require_POST
def entry_delete(request, pk):
    entry = get_object_or_404(Entry, pk=pk)
    enforce(can_delete(request.user, entry))
    with transaction.atomic():
        record_event(request.user, AuditEvent.Action.DELETED, entry, f"Deleted {entry.kind}: {entry.title}")
        entry.delete()
    messages.success(request, "Content deleted.")
    return redirect("entry_list")
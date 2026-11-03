from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone

class EntryQuerySet(models.QuerySet):
    def public(self):
        return self.filter(status="published", published_at__lte=timezone.now())

class Entry(models.Model):
    class Kind(models.TextChoices):
        POST = "post", "Post"
        PAGE = "page", "Page"

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PUBLISHED = "published", "Published"

    title = models.CharField(max_length=200)
    kind = models.CharField(max_length=8, choices=Kind.choices, default=Kind.POST)
    slug = models.SlugField(max_length=220, allow_unicode=True)
    body = models.TextField(help_text="Plain text only for this release; HTML is escaped.")
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.DRAFT)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, related_name="entries"
    )
    published_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = EntryQuerySet.as_manager()

    class Meta:
        constraints = [models.UniqueConstraint(fields=["kind", "slug"], name="unique_kind_slug")]
        ordering = ["-updated_at", "-id"]
        indexes = [models.Index(fields=["kind", "status", "published_at"], name="entry_public_idx")]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        if self.kind == self.Kind.PAGE:
            return reverse("public_page", args=[self.slug])
        return reverse("public_post", args=[self.slug])

class AuditEvent(models.Model):
    class Action(models.TextChoices):
        CREATED = "created", "Entry created"
        UPDATED = "updated", "Entry updated"
        DELETED = "deleted", "Entry deleted"
        USER_CREATED = "user_created", "User created"

    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=20, choices=Action.choices)
    object_type = models.CharField(max_length=24)
    object_id = models.PositiveBigIntegerField()
    summary = models.CharField(max_length=240)
    occurred_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-occurred_at", "-id"]
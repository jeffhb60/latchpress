from django import forms
from django.utils.text import slugify
from .models import Entry
from accounts.roles import can_publish

class EntryForm(forms.ModelForm):
    slug = forms.SlugField(
        required=False, max_length=220, allow_unicode=True,
        help_text="Optional. Generated from the title if empty."
    )

    class Meta:
        model = Entry
        fields = ("title", "kind", "slug", "body", "status")
        widgets = {"body": forms.Textarea(attrs={"rows": 14})}

    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        if not can_publish(user):
            self.fields["status"].choices = [(Entry.Status.DRAFT, "Draft")]

    def clean(self):
        cleaned = super().clean()
        title = cleaned.get("title")
        kind = cleaned.get("kind")
        if not title or not kind:
            return cleaned
        slug = cleaned.get("slug") or (self.instance.slug if self.instance.pk else "")
        if not slug:
            base_slug = slugify(title, allow_unicode=True)
            if not base_slug:
                self.add_error("title", "Please provide a title that can form a URL slug.")
                return cleaned
            slug = base_slug[:210]
            index = 2
            while Entry.objects.filter(kind=kind, slug=slug).exclude(pk=self.instance.pk).exists():
                suffix = f"-{index}"
                slug = base_slug[:220-len(suffix)] + suffix
                index += 1
        if Entry.objects.filter(kind=kind, slug=slug).exclude(pk=self.instance.pk).exists():
            self.add_error("slug", "This URL slug is already in use for this content type.")
        cleaned["slug"] = slug
        if cleaned.get("status") == Entry.Status.PUBLISHED and not can_publish(self.user):
            self.add_error("status", "You do not have permission to publish.")
        return cleaned
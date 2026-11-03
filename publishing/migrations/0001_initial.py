# Initial publishing and append-only-style audit event models.
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion

class Migration(migrations.Migration):
    initial = True
    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]

    operations = [
        migrations.CreateModel(
            name="Entry",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=200)),
                ("kind", models.CharField(choices=[("post", "Post"), ("page", "Page")], default="post", max_length=8)),
                ("slug", models.SlugField(allow_unicode=True, max_length=220)),
                ("body", models.TextField(help_text="Plain text only for this release; HTML is escaped.")),
                ("status", models.CharField(choices=[("draft", "Draft"), ("published", "Published")], default="draft", max_length=10)),
                ("published_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("author", models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="entries", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-updated_at", "-id"]},
        ),
        migrations.CreateModel(
            name="AuditEvent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("action", models.CharField(choices=[("created", "Entry created"), ("updated", "Entry updated"), ("deleted", "Entry deleted"), ("user_created", "User created")], max_length=20)),
                ("object_type", models.CharField(max_length=24)),
                ("object_id", models.PositiveBigIntegerField()),
                ("summary", models.CharField(max_length=240)),
                ("occurred_at", models.DateTimeField(auto_now_add=True)),
                ("actor", models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-occurred_at", "-id"]},
        ),
        migrations.AddConstraint(
            model_name="entry",
            constraint=models.UniqueConstraint(fields=("kind", "slug"), name="unique_kind_slug"),
        ),
        migrations.AddIndex(
            model_name="entry",
            index=models.Index(fields=["kind", "status", "published_at"], name="entry_public_idx"),
        )
    ]

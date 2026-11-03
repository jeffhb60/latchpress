from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management import call_command
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from .models import AuditEvent, Entry

User = get_user_model()

class CoreSecurityTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("setup_roles", verbosity=0)
        cls.owner = User.objects.create_superuser("owner", "owner@example.test", "a-very-long-owner-secret")
        for name, role in [
            ("admin_role", "Administrator"),
            ("editor", "Editor"),
            ("author", "Author"),
            ("other_author", "Author"),
            ("contributor", "Contributor"),
            ("subscriber", "Subscriber"),
        ]:
            user = User.objects.create_user(username=name, password="a-very-long-test-secret")
            user.groups.add(Group.objects.get(name=role))
            setattr(cls, name, user)
        cls.draft = Entry.objects.create(
            title="Hidden", slug="hidden", body="private words", author=cls.author,
            kind=Entry.Kind.POST, status=Entry.Status.DRAFT
        )
        cls.published = Entry.objects.create(
            title="Visible", slug="visible", body="Hello <script>alert('x')</script>",
            author=cls.author, kind=Entry.Kind.POST, status=Entry.Status.PUBLISHED,
            published_at=timezone.now()
        )

    def login_as(self, user):
        self.client.force_login(user)

    def test_public_only_sees_published(self):
        self.assertEqual(self.client.get("/blog/hidden/").status_code, 404)
        response = self.client.get("/blog/visible/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "&lt;script&gt;")
        self.assertNotContains(response, "<script>alert", html=False)
        response = self.client.get("/")
        self.assertContains(response, "Visible")
        self.assertNotContains(response, "Hidden")
        self.assertNotContains(response, "private words")

    def test_future_published_at_is_not_public(self):
        future = Entry.objects.create(
            title="Soon", slug="soon", body="later", kind=Entry.Kind.POST,
            author=self.owner, status=Entry.Status.PUBLISHED,
            published_at=timezone.now() + timezone.timedelta(days=1)
        )
        self.assertEqual(self.client.get(future.get_absolute_url()).status_code, 404)

    def test_page_url(self):
        page = Entry.objects.create(
            title="About", slug="about", body="page text", kind=Entry.Kind.PAGE,
            author=self.owner, status=Entry.Status.PUBLISHED,
            published_at=timezone.now()
        )
        self.assertEqual(self.client.get(page.get_absolute_url()).status_code, 200)

    def test_anonymous_redirected_from_dashboard(self):
        resp = self.client.get(reverse("dashboard"))
        self.assertEqual(resp.status_code, 302)
        self.assertIn("login", resp.url)

    def test_subscriber_cannot_access_editor_or_users(self):
        self.login_as(self.subscriber)
        self.assertEqual(self.client.get(reverse("dashboard")).status_code, 200)
        self.assertEqual(self.client.get(reverse("entry_new")).status_code, 403)
        self.assertEqual(self.client.get(reverse("entry_list")).status_code, 403)
        self.assertEqual(self.client.get(reverse("user_list")).status_code, 403)
        self.assertEqual(self.client.get(reverse("user_create")).status_code, 403)

    def test_contributor_may_create_draft_but_not_publish(self):
        self.login_as(self.contributor)
        url = reverse("entry_new")
        payload = {"title": "Proposal", "kind": "post", "slug": "proposal", "body": "Draft.", "status": "draft"}
        resp = self.client.post(url, payload)
        self.assertRedirects(resp, reverse("entry_list"))
        proposal = Entry.objects.get(slug="proposal")
        self.assertEqual(proposal.status, "draft")
        payload["status"] = "published"
        payload["slug"] = "unsafe-published"
        resp = self.client.post(url, payload)
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(Entry.objects.filter(slug="unsafe-published").exists())
        self.assertEqual(self.client.get(reverse("entry_edit", args=[self.published.pk])).status_code, 403)

    def test_authors_cannot_edit_another_users_content(self):
        self.login_as(self.other_author)
        self.assertEqual(self.client.get(reverse("entry_edit", args=[self.draft.pk])).status_code, 403)
        self.assertEqual(self.client.post(reverse("entry_delete", args=[self.draft.pk])).status_code, 403)
        self.assertTrue(Entry.objects.filter(pk=self.draft.pk).exists())

    def test_author_can_publish_own_post(self):
        self.login_as(self.author)
        resp = self.client.post(reverse("entry_new"), {
            "title": "A new story", "kind": "post", "slug": "new-story",
            "body": "Body", "status": "published"
        })
        self.assertEqual(resp.status_code, 302)
        entry = Entry.objects.get(slug="new-story")
        self.assertIsNotNone(entry.published_at)
        self.assertEqual(self.client.get(entry.get_absolute_url()).status_code, 200)
        self.assertTrue(AuditEvent.objects.filter(actor=self.author, object_id=entry.pk).exists())

    def test_editor_can_manage_others_content(self):
        self.login_as(self.editor)
        self.assertEqual(self.client.get(reverse("entry_edit", args=[self.draft.pk])).status_code, 200)

    def test_owner_can_create_non_staff_user(self):
        self.login_as(self.owner)
        resp = self.client.post(reverse("user_create"), {
            "username": "new_writer", "email": "writer@example.test", "role": "Contributor",
            "password1": "something-long-and-reasonably-unique-2026",
            "password2": "something-long-and-reasonably-unique-2026",
        })
        self.assertRedirects(resp, reverse("user_list"))
        user = User.objects.get(username="new_writer")
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertEqual(list(user.groups.values_list("name", flat=True)), ["Contributor"])

    def test_admin_role_cannot_create_users_or_visit_django_admin(self):
        self.login_as(self.admin_role)
        self.assertEqual(self.client.get(reverse("user_create")).status_code, 403)
        response = self.client.get("/admin/")
        self.assertNotEqual(response.status_code, 200)

    def test_delete_requires_post_and_csrf(self):
        self.login_as(self.owner)
        url = reverse("entry_delete", args=[self.draft.pk])
        self.assertEqual(self.client.get(url).status_code, 405)
        strict_client = Client(enforce_csrf_checks=True)
        strict_client.force_login(self.owner)
        self.assertEqual(strict_client.post(url).status_code, 403)
        self.assertTrue(Entry.objects.filter(pk=self.draft.pk).exists())

    def test_default_security_headers(self):
        response = self.client.get("/")
        self.assertIn("object-src 'none'", response["Content-Security-Policy"])
        self.assertEqual(response["X-Frame-Options"], "DENY")

    def test_slugs_unique_within_type(self):
        self.login_as(self.owner)
        for n in range(2):
            self.client.post(reverse("entry_new"), {
                "title": "Repeated title", "kind": "post", "slug": "",
                "body": "Text", "status": "draft"
            })
        self.assertTrue(Entry.objects.filter(slug="repeated-title").exists())
        self.assertTrue(Entry.objects.filter(slug="repeated-title-2").exists())

    def test_multiple_cms_groups_fail_closed(self):
        from accounts.roles import role_for, can_publish
        self.author.groups.add(Group.objects.get(name="Administrator"))
        self.assertEqual(role_for(self.author), "Subscriber")
        self.assertFalse(can_publish(self.author))
        self.login_as(self.author)
        self.assertEqual(self.client.get(reverse("entry_list")).status_code, 403)

    def test_password_change_for_logged_in_user(self):
        self.login_as(self.author)
        response = self.client.post(reverse("password_change"), {
            "old_password": "a-very-long-test-secret",
            "new_password1": "different-strong-password-2026",
            "new_password2": "different-strong-password-2026",
        })
        self.assertRedirects(response, reverse("password_change_done"))
        self.author.refresh_from_db()
        self.assertTrue(self.author.check_password("different-strong-password-2026"))

    def test_get_logout_is_not_allowed(self):
        self.login_as(self.author)
        self.assertEqual(self.client.get(reverse("logout")).status_code, 405)

    def test_normal_editor_cannot_access_owner_admin(self):
        self.login_as(self.editor)
        self.assertNotEqual(self.client.get("/admin/").status_code, 200)

    def test_no_role_cannot_publish(self):
        person = User.objects.create_user(username="norole", password="unshared-complex-password")
        self.login_as(person)
        self.assertEqual(self.client.get(reverse("entry_new")).status_code, 403)

    def test_staff_flag_alone_does_not_grant_cms_privileges(self):
        person = User.objects.create_user(username="staff_only", password="unshared-complex-password", is_staff=True)
        self.login_as(person)
        self.assertEqual(self.client.get(reverse("entry_new")).status_code, 403)
        self.assertNotEqual(self.client.get("/admin/").status_code, 200)
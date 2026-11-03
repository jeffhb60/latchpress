from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand
from django.db import transaction
from django.contrib.contenttypes.models import ContentType

from accounts.roles import ADMINISTRATOR, EDITOR, AUTHOR, CONTRIBUTOR, SUBSCRIBER
from publishing.models import Entry

class Command(BaseCommand):
    help = "Create LatchPress permission groups; idempotent. Run after migrate."

    @transaction.atomic
    def handle(self, *args, **options):
        ct = ContentType.objects.get_for_model(Entry)
        permissions = {
            perm.codename: perm
            for perm in Permission.objects.filter(content_type=ct)
        }
        for role, codes in {
            ADMINISTRATOR: ("add_entry", "change_entry", "delete_entry", "view_entry"),
            EDITOR: ("add_entry", "change_entry", "delete_entry", "view_entry"),
            AUTHOR: ("add_entry", "change_entry", "view_entry"),
            CONTRIBUTOR: ("add_entry", "change_entry", "view_entry"),
            SUBSCRIBER: ()
        }.items():
            group, _ = Group.objects.get_or_create(name=role)
            group.permissions.set([permissions[name] for name in codes])
            self.stdout.write(f"Configured {role}")
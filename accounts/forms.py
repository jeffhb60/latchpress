from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.db import transaction
from .models import User
from .roles import ROLE_CHOICES

class OwnerCreateUserForm(UserCreationForm):
    email = forms.EmailField(required=False)
    role = forms.ChoiceField(choices=ROLE_CHOICES, initial="Subscriber")

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email", "role")

    @transaction.atomic
    def save(self, commit=True):
        if not commit:
            raise ValueError("OwnerCreateUserForm requires commit=True")
        user = super().save(commit=False)
        user.is_staff = False
        user.is_superuser = False
        user.save()
        from django.contrib.auth.models import Group
        group = Group.objects.get(name=self.cleaned_data["role"])
        user.groups.set([group])
        return user
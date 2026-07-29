from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from delivery.models import User


class BootstrapFormMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            css = "form-select" if isinstance(field.widget, forms.Select) else "form-control"
            field.widget.attrs.setdefault("class", css)
            if self.is_bound and self[name].errors:
                field.widget.attrs["class"] += " is-invalid"


class SignUpForm(BootstrapFormMixin, UserCreationForm):
    ROLE_CHOICES = (
        (User.Role.BUYER, User.Role.BUYER.label),
        (User.Role.COURIER, User.Role.COURIER.label),
    )

    first_name = forms.CharField(required=True)
    last_name = forms.CharField(required=True)
    email = forms.EmailField(required=True)
    role = forms.ChoiceField(
        choices=ROLE_CHOICES,
        initial=User.Role.BUYER,
        label="I am a",
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "first_name", "last_name", "email", "role")

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("A user with this email already exists.")
        return email


class BootstrapAuthenticationForm(BootstrapFormMixin, AuthenticationForm):
    pass

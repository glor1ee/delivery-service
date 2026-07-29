from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from delivery.models import Market, Order, Product, User


class BootstrapFormMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            css = "form-select" if isinstance(field.widget, forms.Select) else "form-control"
            field.widget.attrs.setdefault("class", css)

    def full_clean(self):
        super().full_clean()
        for name in self.errors:
            field = self.fields.get(name)
            if field:
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


class OrderForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Order
        fields = ("market",)


class AssignCourierForm(BootstrapFormMixin, forms.ModelForm):
    courier = forms.ModelChoiceField(
        queryset=User.objects.filter(role=User.Role.COURIER).order_by("username"),
        label="Courier",
    )

    class Meta:
        model = Order
        fields = ("courier",)


class MarketForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Market
        fields = ("name",)


class ProductForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Product
        fields = ("market", "name", "price")

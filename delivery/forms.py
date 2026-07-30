from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from delivery.models import Market, Order, Product, User


class BootstrapFormMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_bootstrap_classes()

    def apply_bootstrap_classes(self):
        for field in self.fields.values():
            is_select = isinstance(field.widget, forms.Select)
            css = "form-select" if is_select else "form-control"
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
            raise forms.ValidationError(
                "A user with this email already exists.",
            )
        return email


class BootstrapAuthenticationForm(BootstrapFormMixin, AuthenticationForm):
    pass


class OrderForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Order
        fields = ("market",)


class OrderProductsForm(BootstrapFormMixin, forms.Form):
    def __init__(self, *args, market, **kwargs):
        super().__init__(*args, **kwargs)
        self.market = market
        self.products = list(market.products.order_by("name"))
        for product in self.products:
            self.fields[self.field_name(product)] = forms.IntegerField(
                required=False,
                min_value=0,
                initial=0,
                label=f"{product.name} ({product.price}$)",
            )

        self.apply_bootstrap_classes()

    @staticmethod
    def field_name(product):
        return f"product_{product.pk}"

    def clean(self):
        cleaned = super().clean()
        if not any(cleaned.get(self.field_name(p)) for p in self.products):
            raise forms.ValidationError(
                "Add at least one product to the order.",
            )
        return cleaned

    def selected_items(self):
        items = []
        for product in self.products:
            quantity = self.cleaned_data.get(self.field_name(product))
            if quantity:
                items.append((product, quantity))
        return items


class AssignCourierForm(BootstrapFormMixin, forms.ModelForm):
    courier = forms.ModelChoiceField(
        queryset=(
            User.objects.filter(role=User.Role.COURIER).order_by("username")
        ),
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

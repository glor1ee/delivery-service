from decimal import Decimal

from django.test import TestCase

from delivery.forms import (
    AssignCourierForm,
    MarketForm,
    OrderProductsForm,
    ProductForm,
    SignUpForm,
)
from delivery.models import Market, Product, User


class SignUpFormTest(TestCase):
    def test_valid_form(self):
        form = SignUpForm(
            data={
                "username": "newuser",
                "first_name": "John",
                "last_name": "Doe",
                "email": "john@test.com",
                "role": User.Role.BUYER,
                "password1": "StrongPassword123",
                "password2": "StrongPassword123",
            }
        )

        self.assertTrue(form.is_valid())

    def test_duplicate_email(self):
        User.objects.create_user(
            username="user1",
            password="12345",
            email="john@test.com",
        )

        form = SignUpForm(
            data={
                "username": "newuser",
                "first_name": "John",
                "last_name": "Doe",
                "email": "john@test.com",
                "role": User.Role.BUYER,
                "password1": "StrongPassword123",
                "password2": "StrongPassword123",
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)

    def test_duplicate_username(self):
        User.objects.create_user(
            username="buyer",
            password="12345",
        )

        form = SignUpForm(
            data={
                "username": "buyer",
                "first_name": "John",
                "last_name": "Doe",
                "email": "john@test.com",
                "role": User.Role.BUYER,
                "password1": "StrongPassword123",
                "password2": "StrongPassword123",
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn("username", form.errors)

    def test_passwords_do_not_match(self):
        form = SignUpForm(
            data={
                "username": "buyer",
                "first_name": "John",
                "last_name": "Doe",
                "email": "john@test.com",
                "role": User.Role.BUYER,
                "password1": "StrongPassword123",
                "password2": "AnotherPassword123",
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn("password2", form.errors)


class OrderProductsFormTest(TestCase):
    def setUp(self):
        self.market = Market.objects.create(name="ATB")

        self.product1 = Product.objects.create(
            market=self.market,
            name="Milk",
            price=Decimal("20.00"),
        )

        self.product2 = Product.objects.create(
            market=self.market,
            name="Bread",
            price=Decimal("15.00"),
        )

    def test_form_has_all_products(self):
        form = OrderProductsForm(market=self.market)

        self.assertIn(
            f"product_{self.product1.pk}",
            form.fields,
        )

        self.assertIn(
            f"product_{self.product2.pk}",
            form.fields,
        )

    def test_valid_order(self):
        form = OrderProductsForm(
            market=self.market,
            data={
                f"product_{self.product1.pk}": 3,
                f"product_{self.product2.pk}": 1,
            },
        )

        self.assertTrue(form.is_valid())

    def test_empty_order(self):
        form = OrderProductsForm(
            market=self.market,
            data={
                f"product_{self.product1.pk}": 0,
                f"product_{self.product2.pk}": 0,
            },
        )

        self.assertFalse(form.is_valid())


class AssignCourierFormTest(TestCase):
    def setUp(self):
        self.courier = User.objects.create_user(
            username="courier",
            password="12345",
            role=User.Role.COURIER,
        )

        self.buyer = User.objects.create_user(
            username="buyer",
            password="12345",
            role=User.Role.BUYER,
        )

        self.admin = User.objects.create_superuser(
            username="admin",
            password="12345",
            role=User.Role.ADMIN,
        )

    def test_only_couriers_in_queryset(self):
        form = AssignCourierForm()

        self.assertIn(
            self.courier,
            form.fields["courier"].queryset,
        )

        self.assertNotIn(
            self.buyer,
            form.fields["courier"].queryset,
        )

        self.assertNotIn(
            self.admin,
            form.fields["courier"].queryset,
        )


class MarketFormTest(TestCase):
    def test_valid_form(self):
        form = MarketForm(
            data={
                "name": "ATB",
            }
        )

        self.assertTrue(form.is_valid())

    def test_invalid_form(self):
        form = MarketForm(
            data={
                "name": "",
            }
        )

        self.assertFalse(form.is_valid())


class ProductFormTest(TestCase):
    def setUp(self):
        self.market = Market.objects.create(name="ATB")

    def test_valid_form(self):
        form = ProductForm(
            data={
                "market": self.market.pk,
                "name": "Milk",
                "price": "20.00",
            }
        )

        self.assertTrue(form.is_valid())

    def test_negative_price(self):
        form = ProductForm(
            data={
                "market": self.market.pk,
                "name": "Milk",
                "price": "-1",
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn("price", form.errors)

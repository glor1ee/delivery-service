from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase

from delivery.models import Market, Order, OrderItem, Product, User


class UserModelTest(TestCase):
    def test_is_buyer_property(self):
        user = User.objects.create_user(
            username="buyer",
            password="12345",
            role=User.Role.BUYER,
        )

        self.assertTrue(user.is_buyer)
        self.assertFalse(user.is_courier)
        self.assertFalse(user.is_staff)

    def test_is_courier_property(self):
        user = User.objects.create_user(
            username="courier",
            password="12345",
            role=User.Role.COURIER,
        )

        self.assertTrue(user.is_courier)
        self.assertFalse(user.is_buyer)


class MarketModelTest(TestCase):
    def test_str(self):
        market = Market.objects.create(name="ATB")

        self.assertEqual(str(market), "ATB")


class ProductModelTest(TestCase):
    def setUp(self):
        self.market = Market.objects.create(name="ATB")

    def test_str(self):
        product = Product.objects.create(
            market=self.market,
            name="Milk",
            price=Decimal("10.50"),
        )

        self.assertEqual(
            str(product),
            "Milk (10.50$) Market: ATB",
        )


class OrderModelTest(TestCase):
    def setUp(self):
        self.market = Market.objects.create(name="ATB")

        self.user = User.objects.create_user(
            username="buyer",
            password="12345",
            role=User.Role.BUYER,
        )

        self.order = Order.objects.create(
            market=self.market,
            buyer=self.user,
        )

    def test_total_cost_empty_order(self):
        self.assertEqual(
            self.order.total_cost,
            Decimal("0.00"),
        )

    def test_total_cost(self):
        product = Product.objects.create(
            market=self.market,
            name="Milk",
            price=Decimal("15.00"),
        )

        OrderItem.objects.create(
            order=self.order,
            product=product,
            quantity=3,
        )

        self.assertEqual(
            self.order.total_cost,
            Decimal("45.00"),
        )

    def test_clean_raises_validation_error_when_market_changed(self):
        second_market = Market.objects.create(name="Silpo")

        product = Product.objects.create(
            market=self.market,
            name="Milk",
            price=Decimal("20.00"),
        )

        OrderItem.objects.create(
            order=self.order,
            product=product,
            quantity=1,
        )

        self.order.market = second_market

        with self.assertRaises(ValidationError):
            self.order.clean()


class OrderItemModelTest(TestCase):
    def setUp(self):
        self.market = Market.objects.create(name="ATB")
        self.second_market = Market.objects.create(name="Silpo")

        self.user = User.objects.create_user(
            username="buyer",
            password="12345",
            role=User.Role.BUYER,
        )

        self.order = Order.objects.create(
            market=self.market,
            buyer=self.user,
        )

        self.product = Product.objects.create(
            market=self.market,
            name="Milk",
            price=Decimal("20.00"),
        )

    def test_price_is_copied_from_product(self):
        item = OrderItem.objects.create(
            order=self.order,
            product=self.product,
            quantity=2,
        )

        self.assertEqual(item.price, Decimal("20.00"))

    def test_total_cost(self):
        item = OrderItem.objects.create(
            order=self.order,
            product=self.product,
            quantity=3,
        )

        self.assertEqual(
            item.total_cost,
            Decimal("60.00"),
        )

    def test_clean_raises_validation_error_for_different_market(self):
        another_product = Product.objects.create(
            market=self.second_market,
            name="Bread",
            price=Decimal("15.00"),
        )

        item = OrderItem(
            order=self.order,
            product=another_product,
            quantity=1,
        )

        with self.assertRaises(ValidationError):
            item.clean()

    def test_unique_product_per_order(self):
        OrderItem.objects.create(
            order=self.order,
            product=self.product,
            quantity=1,
        )

        with self.assertRaises(IntegrityError):
            OrderItem.objects.create(
                order=self.order,
                product=self.product,
                quantity=2,
            )
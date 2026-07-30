from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from delivery.models import Market, Order, OrderItem, Product, User


class BaseViewTest(TestCase):
    def setUp(self):
        self.buyer = User.objects.create_user(
            username="buyer",
            password="12345",
            role=User.Role.BUYER,
        )

        self.courier = User.objects.create_user(
            username="courier",
            password="12345",
            role=User.Role.COURIER,
        )

        self.admin = User.objects.create_superuser(
            username="admin",
            password="12345",
            email="admin@test.com",
        )

        self.market = Market.objects.create(name="ATB")
        self.market2 = Market.objects.create(name="Silpo")

        self.product = Product.objects.create(
            market=self.market,
            name="Milk",
            price=Decimal("20.00"),
        )

        self.product2 = Product.objects.create(
            market=self.market,
            name="Bread",
            price=Decimal("15.00"),
        )

        self.order = Order.objects.create(
            market=self.market,
            buyer=self.buyer,
        )

        OrderItem.objects.create(
            order=self.order,
            product=self.product,
            quantity=2,
        )


class IndexViewTest(BaseViewTest):
    def test_not_logged_user_cant_open_couriers_page(self):
        response = self.client.get(reverse("delivery:courier-list"))

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(
            response,
            f"{reverse('login')}?next={reverse('delivery:courier-list')}"
        )

    def test_not_logged_user_cant_open_buyers_page(self):
        response = self.client.get(reverse("delivery:buyer-list"))

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(
            response,
            f"{reverse('login')}?next={reverse('delivery:buyer-list')}"
        )

    def test_not_logged_user_cant_open_orders_page(self):
        response = self.client.get(reverse("delivery:order-list"))

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(
            response,
            f"{reverse('login')}?next={reverse('delivery:order-list')}"
        )

    def test_not_logged_user_cant_open_products_page(self):
        response = self.client.get(reverse("delivery:product-list"))

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(
            response,
            f"{reverse('login')}?next={reverse('delivery:product-list')}"
        )

    def test_not_logged_user_cant_open_markets_page(self):
        response = self.client.get(reverse("delivery:market-list"))

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(
            response,
            f"{reverse('login')}?next={reverse('delivery:market-list')}"
        )


class MarketListViewTest(BaseViewTest):
    def test_market_list(self):
        self.client.force_login(self.buyer)

        response = self.client.get(
            reverse("delivery:market-list")
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "ATB")
        self.assertContains(response, "Silpo")

    def test_market_search(self):
        self.client.force_login(self.buyer)

        response = self.client.get(
            reverse("delivery:market-list"),
            {"q": "ATB"},
        )

        self.assertContains(response, "ATB")
        self.assertNotContains(response, "Silpo")


class MarketDetailViewTest(BaseViewTest):
    def test_market_detail(self):
        self.client.force_login(self.buyer)

        response = self.client.get(
            reverse(
                "delivery:market-detail",
                kwargs={"pk": self.market.pk},
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "ATB")


class ProductListViewTest(BaseViewTest):
    def test_product_list(self):
        self.client.force_login(self.buyer)

        response = self.client.get(
            reverse("delivery:product-list")
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Milk")
        self.assertContains(response, "Bread")

    def test_product_search(self):
        self.client.force_login(self.buyer)

        response = self.client.get(
            reverse("delivery:product-list"),
            {"q": "Milk"},
        )

        self.assertContains(response, "Milk")
        self.assertNotContains(response, "Bread")


class ProductDetailViewTest(BaseViewTest):
    def test_product_detail(self):
        self.client.force_login(self.buyer)

        response = self.client.get(
            reverse(
                "delivery:product-detail",
                kwargs={"pk": self.product.pk},
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Milk")


class OrderListViewTest(BaseViewTest):
    def test_order_list(self):
        self.client.force_login(self.buyer)

        response = self.client.get(
            reverse("delivery:order-list")
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.market.name)

    def test_order_search_by_market(self):
        self.client.force_login(self.buyer)

        response = self.client.get(
            reverse("delivery:order-list"),
            {"q": "ATB"},
        )

        self.assertEqual(response.status_code, 200)

    def test_order_search_by_pk(self):
        self.client.force_login(self.buyer)

        response = self.client.get(
            reverse("delivery:order-list"),
            {"q": str(self.order.pk)},
        )

        self.assertEqual(response.status_code, 200)


class OrderDetailViewTest(BaseViewTest):
    def test_order_detail(self):
        self.client.force_login(self.buyer)

        response = self.client.get(
            reverse(
                "delivery:order-detail",
                kwargs={"pk": self.order.pk},
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Milk")

    def test_owner_can_delete(self):
        self.client.force_login(self.buyer)

        response = self.client.get(
            reverse(
                "delivery:order-detail",
                kwargs={"pk": self.order.pk},
            )
        )

        self.assertTrue(response.context["can_delete"])

    def test_courier_can_take(self):
        self.client.force_login(self.courier)

        response = self.client.get(
            reverse(
                "delivery:order-detail",
                kwargs={"pk": self.order.pk},
            )
        )

        self.assertTrue(response.context["can_take"])

    def test_buyer_cant_take(self):
        self.client.force_login(self.buyer)

        response = self.client.get(
            reverse(
                "delivery:order-detail",
                kwargs={"pk": self.order.pk},
            )
        )

        self.assertFalse(response.context["can_take"])


class MarketCreateViewTest(BaseViewTest):
    def test_admin_can_create_market(self):
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse("delivery:market-create"),
            {"name": "Novus"},
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            Market.objects.filter(name="Novus").exists()
        )

    def test_buyer_cannot_create_market(self):
        self.client.force_login(self.buyer)

        response = self.client.post(
            reverse("delivery:market-create"),
            {"name": "Novus"},
        )

        self.assertEqual(response.status_code, 403)

    def test_courier_cannot_create_market(self):
        self.client.force_login(self.courier)

        response = self.client.post(
            reverse("delivery:market-create"),
            {"name": "Novus"},
        )

        self.assertEqual(response.status_code, 403)


class ProductCreateViewTest(BaseViewTest):
    def test_admin_can_create_product(self):
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse("delivery:product-create"),
            {
                "market": self.market.pk,
                "name": "Water",
                "price": "30.00",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            Product.objects.filter(name="Water").exists()
        )

    def test_buyer_cannot_create_product(self):
        self.client.force_login(self.buyer)

        response = self.client.post(
            reverse("delivery:product-create"),
            {
                "market": self.market.pk,
                "name": "Water",
                "price": "30.00",
            },
        )

        self.assertEqual(response.status_code, 403)

    def test_courier_cannot_create_product(self):
        self.client.force_login(self.courier)

        response = self.client.post(
            reverse("delivery:product-create"),
            {
                "market": self.market.pk,
                "name": "Water",
                "price": "30.00",
            },
        )

        self.assertEqual(response.status_code, 403)


class OrderCreateViewTest(BaseViewTest):
    def test_create_order(self):
        self.client.force_login(self.buyer)

        response = self.client.post(
            reverse("delivery:order-create"),
            {
                "market": self.market.pk,
                f"product_{self.product.pk}": 3,
                f"product_{self.product2.pk}": 2,
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Order.objects.count(), 2)

    def test_invalid_market(self):
        self.client.force_login(self.buyer)

        response = self.client.post(
            reverse("delivery:order-create"),
            {"market": 999},
        )

        self.assertEqual(response.status_code, 302)


class OrderDeleteViewTest(BaseViewTest):
    def test_owner_can_delete(self):
        self.client.force_login(self.buyer)

        response = self.client.post(
            reverse(
                "delivery:order-delete",
                kwargs={"pk": self.order.pk},
            )
        )

        self.assertEqual(response.status_code, 302)
        self.assertFalse(
            Order.objects.filter(pk=self.order.pk).exists()
        )

    def test_admin_can_delete(self):
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse(
                "delivery:order-delete",
                kwargs={"pk": self.order.pk},
            )
        )

        self.assertEqual(response.status_code, 302)

    def test_courier_cannot_delete(self):
        self.client.force_login(self.courier)

        response = self.client.post(
            reverse(
                "delivery:order-delete",
                kwargs={"pk": self.order.pk},
            )
        )

        self.assertEqual(response.status_code, 403)


class OrderTakeViewTest(BaseViewTest):
    def test_take_order(self):
        self.client.force_login(self.courier)

        response = self.client.post(
            reverse(
                "delivery:order-take",
                kwargs={"pk": self.order.pk},
            )
        )

        self.assertEqual(response.status_code, 302)

        self.order.refresh_from_db()

        self.assertEqual(
            self.order.courier,
            self.courier,
        )

    def test_cant_take_taken_order(self):
        self.order.courier = self.courier
        self.order.save()

        courier2 = User.objects.create_user(
            username="courier2",
            password="12345",
            role=User.Role.COURIER,
        )

        self.client.force_login(courier2)

        response = self.client.post(
            reverse(
                "delivery:order-take",
                kwargs={"pk": self.order.pk},
            )
        )

        self.assertEqual(response.status_code, 302)

        self.order.refresh_from_db()

        self.assertEqual(
            self.order.courier,
            self.courier,
        )

    def test_buyer_cant_take_order(self):
        self.client.force_login(self.buyer)

        response = self.client.post(
            reverse("delivery:order-take",
                    kwargs={"pk": self.order.pk},
            )
        )

        self.assertEqual(response.status_code, 403)


class OrderAssignCourierViewTest(BaseViewTest):
    def test_admin_assign_courier(self):
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse(
                "delivery:order-assign-courier",
                kwargs={"pk": self.order.pk},
            ),
            {
                "courier": self.courier.pk,
            },
        )

        self.assertEqual(response.status_code, 302)

        self.order.refresh_from_db()

        self.assertEqual(
            self.order.courier,
            self.courier,
        )


class SignUpViewTest(TestCase):
    def test_signup(self):
        response = self.client.post(
            reverse("delivery:signup"),
            {
                "username": "newuser",
                "first_name": "John",
                "last_name": "Doe",
                "email": "john@test.com",
                "role": User.Role.BUYER,
                "password1": "StrongPassword123",
                "password2": "StrongPassword123",
            },
        )

        self.assertEqual(response.status_code, 302)

        self.assertTrue(
            User.objects.filter(
                username="newuser"
            ).exists()
        )

    def test_authenticated_user_redirected(self):
        user = User.objects.create_user(
            username="user",
            password="12345",
        )

        self.client.force_login(user)

        response = self.client.get(
            reverse("delivery:signup")
        )

        self.assertEqual(response.status_code, 302)

    def test_cant_signup_with_existing_username(self):
        self.client.post(
            reverse("delivery:signup"),
            {
                "username": "buyer",
                "first_name": "John",
                "last_name": "Doe",
                "email": "john@test.com",
                "role": User.Role.BUYER,
                "password1": "StrongPassword123",
                "password2": "StrongPassword123",
            },
        )

        self.assertEqual(
            User.objects.filter(username="buyer").count(),
            1,
        )


class SearchViewTest(BaseViewTest):
    def test_market_search_not_found(self):
        self.client.force_login(self.buyer)

        response = self.client.get(
            reverse("delivery:market-list"),
            {"q": "dfghfdgdg"},
        )

        self.assertEqual(
            len(response.context["market_list"]),
            0,
        )

    def test_product_search_not_found(self):
        self.client.force_login(self.buyer)

        response = self.client.get(
            reverse("delivery:product-list"),
            {"q": "XXXXX"},
        )

        self.assertEqual(
            len(response.context["product_list"]),
            0,
        )

    def test_order_search_not_found(self):
        self.client.force_login(self.buyer)

        response = self.client.get(
            reverse("delivery:order-list"),
            {"q": "XXXXX"},
        )

        self.assertEqual(
            len(response.context["order_list"]),
            0,
        )

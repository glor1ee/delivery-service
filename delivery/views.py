from django.db.models import Count
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.urls import reverse
from django.views import generic

from delivery.models import Market, Order, Product, User


def index(request: HttpRequest) -> HttpResponse:
    buyers = User.objects.filter(role=User.Role.BUYER)
    couriers = User.objects.filter(role=User.Role.COURIER)
    context = {
        "cards": [
            ("Markets", Market.objects.count(), reverse("delivery:market-list")),
            ("Products", Product.objects.count(), reverse("delivery:product-list")),
            ("Orders", Order.objects.count(), reverse("delivery:order-list")),
            ("Buyers", buyers.count(), reverse("delivery:buyer-list")),
            ("Couriers", couriers.count(), reverse("delivery:courier-list")),
        ],
        "latest_orders": (
            Order.objects
            .select_related("market", "buyer", "courier")
            .prefetch_related("items__product")[:8]
        ),
    }
    return render(request, "delivery/index.html", context)


class MarketListView(generic.ListView):
    model = Market
    paginate_by = 10
    queryset = Market.objects.annotate(num_products=Count("products")).order_by("name")


class MarketDetailView(generic.DetailView):
    model = Market
    queryset = Market.objects.prefetch_related("products")


class ProductListView(generic.ListView):
    model = Product
    paginate_by = 10
    queryset = Product.objects.select_related("market")


class ProductDetailView(generic.DetailView):
    model = Product
    queryset = Product.objects.select_related("market")


class OrderListView(generic.ListView):
    model = Order
    paginate_by = 10
    queryset = (
        Order.objects
        .select_related("market", "buyer", "courier")
        .prefetch_related("items__product")
    )


class OrderDetailView(generic.DetailView):
    model = Order
    queryset = (
        Order.objects
        .select_related("market", "buyer", "courier")
        .prefetch_related("items__product")
    )


class BuyerListView(generic.ListView):
    model = User
    paginate_by = 10
    template_name = "delivery/buyer_list.html"
    context_object_name = "buyer_list"
    queryset = (
        User.objects
        .filter(role=User.Role.BUYER)
        .annotate(num_orders=Count("orders"))
        .order_by("username")
    )


class CourierListView(generic.ListView):
    model = User
    paginate_by = 10
    template_name = "delivery/courier_list.html"
    context_object_name = "courier_list"
    queryset = (
        User.objects
        .filter(role=User.Role.COURIER)
        .annotate(num_deliveries=Count("deliveries"))
        .order_by("username")
    )

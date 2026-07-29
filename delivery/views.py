from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse, reverse_lazy
from django.views import generic

from delivery.forms import SignUpForm
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


class MarketListView(LoginRequiredMixin, generic.ListView):
    model = Market
    paginate_by = 10
    queryset = Market.objects.annotate(num_products=Count("products")).order_by("name")


class MarketDetailView(LoginRequiredMixin, generic.DetailView):
    model = Market
    queryset = Market.objects.prefetch_related("products")


class ProductListView(LoginRequiredMixin, generic.ListView):
    model = Product
    paginate_by = 10
    queryset = Product.objects.select_related("market")


class ProductDetailView(LoginRequiredMixin, generic.DetailView):
    model = Product
    queryset = Product.objects.select_related("market")


class OrderListView(LoginRequiredMixin, generic.ListView):
    model = Order
    paginate_by = 10
    queryset = (
        Order.objects
        .select_related("market", "buyer", "courier")
        .prefetch_related("items__product")
    )


class OrderDetailView(LoginRequiredMixin, generic.DetailView):
    model = Order
    queryset = (
        Order.objects
        .select_related("market", "buyer", "courier")
        .prefetch_related("items__product")
    )


class BuyerListView(LoginRequiredMixin, generic.ListView):
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


class CourierListView(LoginRequiredMixin, generic.ListView):
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


class SignUpView(generic.CreateView):
    form_class = SignUpForm
    template_name = "registration/signup.html"
    success_url = reverse_lazy("delivery:index")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect("delivery:index")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)
        messages.success(
            self.request,
            f"Welcome, {self.object.username}! Your account has been created.",
        )
        return response

from decimal import Decimal

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db import transaction
from django.db.models import Count, DecimalField, F, ProtectedError, Sum
from django.db.models.functions import Coalesce
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views import generic

from delivery.forms import (
    AssignCourierForm,
    MarketForm,
    OrderForm,
    OrderProductsForm,
    ProductForm,
    SignUpForm,
)
from delivery.mixins import BuyerRequiredMixin, CourierRequiredMixin, StaffRequiredMixin
from delivery.models import Market, Order, OrderItem, Product, User


def index(request: HttpRequest) -> HttpResponse:
    buyers = User.objects.filter(role=User.Role.BUYER)
    couriers = User.objects.filter(role=User.Role.COURIER)
    context = {
        "cards": [
            {"label": "Markets", "value": Market.objects.count(),
             "url": reverse("delivery:market-list"), "icon": "bi-shop"},
            {"label": "Products", "value": Product.objects.count(),
             "url": reverse("delivery:product-list"), "icon": "bi-box-seam"},
            {"label": "Orders", "value": Order.objects.count(),
             "url": reverse("delivery:order-list"), "icon": "bi-receipt"},
            {"label": "Buyers", "value": buyers.count(),
             "url": reverse("delivery:buyer-list"), "icon": "bi-people"},
            {"label": "Couriers", "value": couriers.count(),
             "url": reverse("delivery:courier-list"), "icon": "bi-bicycle"},
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


class MarketCreateView(StaffRequiredMixin, generic.CreateView):
    model = Market
    form_class = MarketForm
    template_name = "delivery/market_form.html"

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"Market “{self.object.name}” created.")
        return response

    def get_success_url(self):
        return reverse("delivery:market-detail", kwargs={"pk": self.object.pk})


class MarketDeleteView(StaffRequiredMixin, generic.DeleteView):
    model = Market
    template_name = "delivery/market_confirm_delete.html"
    success_url = reverse_lazy("delivery:market-list")

    def form_valid(self, form):
        try:
            return super().form_valid(form)
        except ProtectedError:
            messages.warning(
                self.request,
                f"Can't delete “{self.object.name}” — it still has orders placed at it.",
            )
            return redirect("delivery:market-detail", pk=self.object.pk)


class ProductListView(LoginRequiredMixin, generic.ListView):
    model = Product
    paginate_by = 10
    queryset = Product.objects.select_related("market")


class ProductDetailView(LoginRequiredMixin, generic.DetailView):
    model = Product
    queryset = Product.objects.select_related("market")


class ProductCreateView(StaffRequiredMixin, generic.CreateView):
    model = Product
    form_class = ProductForm

    def get_initial(self):
        initial = super().get_initial()
        market_id = self.request.GET.get("market")
        if market_id and market_id.isdigit():
            initial["market"] = market_id
        return initial

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f"Product “{self.object.name}” created.")
        return response

    def get_success_url(self):
        return reverse("delivery:product-detail", kwargs={"pk": self.object.pk})


class ProductDeleteView(StaffRequiredMixin, generic.DeleteView):
    model = Product
    success_url = reverse_lazy("delivery:product-list")

    def form_valid(self, form):
        try:
            return super().form_valid(form)
        except ProtectedError:
            messages.warning(
                self.request,
                f"Can't delete “{self.object.name}” — it's already part of an order.",
            )
            return redirect("delivery:product-detail", pk=self.object.pk)


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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        order = self.object
        user = self.request.user
        is_owner = user.is_buyer and order.buyer_id == user.pk
        unclaimed = order.courier_id is None

        context["can_delete"] = user.is_staff or (is_owner and unclaimed)
        context["can_take"] = user.is_courier and unclaimed
        context["can_assign_courier"] = user.is_staff
        return context


class OrderCreateView(BuyerRequiredMixin, generic.View):
    template_name = "delivery/order_form.html"

    @staticmethod
    def _market_from(value):
        return Market.objects.filter(pk=value).first() if value and value.isdigit() else None

    def get(self, request):
        market = self._market_from(request.GET.get("market"))
        if market is None:
            return render(request, self.template_name, {"form": OrderForm()})

        products_form = OrderProductsForm(market=market)
        return render(request, self.template_name, {"market": market, "products_form": products_form})

    def post(self, request):
        market = self._market_from(request.POST.get("market"))
        if market is None:
            messages.error(request, "Choose a market first.")
            return redirect("delivery:order-create")

        products_form = OrderProductsForm(request.POST, market=market)
        if products_form.is_valid():
            with transaction.atomic():
                order = Order.objects.create(market=market, buyer=request.user)
                for product, quantity in products_form.selected_items():
                    OrderItem.objects.create(order=order, product=product, quantity=quantity)
            messages.success(
                request,
                f"Order #{order.pk} created with {len(products_form.selected_items())} item(s).",
            )
            return redirect("delivery:order-detail", pk=order.pk)

        return render(request, self.template_name, {"market": market, "products_form": products_form})


class OrderDeleteView(LoginRequiredMixin, UserPassesTestMixin, generic.DeleteView):
    model = Order
    success_url = reverse_lazy("delivery:order-list")

    def test_func(self):
        order = self.get_object()
        user = self.request.user
        if user.is_staff:
            return True
        return user.is_buyer and order.buyer_id == user.pk and order.courier_id is None

    def form_valid(self, form):
        pk = self.object.pk
        response = super().form_valid(form)
        messages.success(self.request, f"Order #{pk} deleted.")
        return response


class OrderAssignCourierView(StaffRequiredMixin, generic.UpdateView):
    model = Order
    form_class = AssignCourierForm
    template_name = "delivery/order_assign_courier.html"

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(
            self.request,
            f"Courier {self.object.courier.username} assigned to order #{self.object.pk}.",
        )
        return response

    def get_success_url(self):
        return reverse("delivery:order-detail", kwargs={"pk": self.object.pk})


class BuyerListView(LoginRequiredMixin, generic.ListView):
    model = User
    paginate_by = 10
    template_name = "delivery/buyer_list.html"
    context_object_name = "buyer_list"
    queryset = (
        User.objects
        .filter(role=User.Role.BUYER)
        .annotate(
            num_orders=Count("orders", distinct=True),
            total_spent=Coalesce(
                Sum(F("orders__items__price") * F("orders__items__quantity")),
                Decimal("0.00"),
                output_field=DecimalField(max_digits=10, decimal_places=2),
            ),
        )
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


class OrderTakeView(CourierRequiredMixin, generic.View):
    def post(self, request, pk):
        updated = Order.objects.filter(pk=pk, courier__isnull=True).update(courier=request.user)
        if updated:
            messages.success(request, f"You are now delivering order #{pk}.")
        else:
            get_object_or_404(Order, pk=pk)  # 404, если заказа вообще нет
            messages.error(request, "This order already has a courier.")
        return redirect("delivery:order-detail", pk=pk)

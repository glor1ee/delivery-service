from django.urls import path

from delivery.views import (
    index,
    MarketListView,
    MarketDetailView,
    MarketCreateView,
    MarketDeleteView,
    ProductListView,
    ProductDetailView,
    ProductCreateView,
    ProductDeleteView,
    OrderListView,
    OrderDetailView,
    OrderCreateView,
    OrderDeleteView,
    OrderAssignCourierView,
    OrderTakeView,
    BuyerListView,
    CourierListView,
    SignUpView,
)


urlpatterns = [
    path("", index, name="index"),
    path("markets/", MarketListView.as_view(), name="market-list"),
    path("markets/create/", MarketCreateView.as_view(), name="market-create"),
    path("markets/<int:pk>/", MarketDetailView.as_view(), name="market-detail"),
    path("markets/<int:pk>/delete/", MarketDeleteView.as_view(), name="market-delete"),
    path("products/", ProductListView.as_view(), name="product-list"),
    path("products/create/", ProductCreateView.as_view(), name="product-create"),
    path("products/<int:pk>/", ProductDetailView.as_view(), name="product-detail"),
    path("products/<int:pk>/delete/", ProductDeleteView.as_view(), name="product-delete"),
    path("orders/", OrderListView.as_view(), name="order-list"),
    path("orders/create/", OrderCreateView.as_view(), name="order-create"),
    path("orders/<int:pk>/", OrderDetailView.as_view(), name="order-detail"),
    path("orders/<int:pk>/delete/", OrderDeleteView.as_view(), name="order-delete"),
    path("orders/<int:pk>/take/", OrderTakeView.as_view(), name="order-take"),
    path(
        "orders/<int:pk>/assign-courier/",
        OrderAssignCourierView.as_view(),
        name="order-assign-courier",
    ),
    path("buyers/", BuyerListView.as_view(), name="buyer-list"),
    path("couriers/", CourierListView.as_view(), name="courier-list"),
    path("signup/", SignUpView.as_view(), name="signup"),
]

app_name = "delivery"

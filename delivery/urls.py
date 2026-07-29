from django.urls import path

from delivery.views import (
    index,
    MarketListView,
    MarketDetailView,
    ProductListView,
    ProductDetailView,
    OrderListView,
    OrderDetailView,
    BuyerListView,
    CourierListView,
)


urlpatterns = [
    path("", index, name="index"),
    path("markets/", MarketListView.as_view(), name="market-list"),
    path("markets/<int:pk>/", MarketDetailView.as_view(), name="market-detail"),
    path("products/", ProductListView.as_view(), name="product-list"),
    path("products/<int:pk>/", ProductDetailView.as_view(), name="product-detail"),
    path("orders/", OrderListView.as_view(), name="order-list"),
    path("orders/<int:pk>/", OrderDetailView.as_view(), name="order-detail"),
    path("buyers/", BuyerListView.as_view(), name="buyer-list"),
    path("couriers/", CourierListView.as_view(), name="courier-list"),
]

app_name = "delivery"

from django.urls import path

from delivery.views import index, OrdersListView


urlpatterns = [
    path("", index, name="index"),
    path("orders/", OrdersListView.as_view(), name="orders-list"),
]

app_name = 'delivery'
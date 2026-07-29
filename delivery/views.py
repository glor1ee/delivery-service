from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.views import generic

from delivery.models import Order


# Create your views here.
def index(request: HttpRequest) -> HttpResponse:
    return render(request, "delivery/index.html")


class OrdersListView(generic.ListView):
    model = Order

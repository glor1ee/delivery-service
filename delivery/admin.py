from django.contrib import admin

from delivery.models import Order, OrderItem, Product, Market, User


admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(Product)
admin.site.register(Market)
admin.site.register(User)
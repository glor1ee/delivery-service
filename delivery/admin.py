from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin


from delivery.models import Market, Order, OrderItem, Product, User


@admin.register(User)
class DeliveryUserAdmin(UserAdmin):
    list_display = (
        "username", "first_name", "last_name", "role", "is_staff",
    )
    list_filter = UserAdmin.list_filter + ("role",)
    fieldsets = UserAdmin.fieldsets + (
        ("Role", {"fields": ("role",)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("Role", {"fields": ("role",)}),
    )


@admin.register(Market)
class MarketAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "market", "price")
    list_filter = ("market",)
    search_fields = ("name",)


class OrderItemInlineFormSet(forms.BaseInlineFormSet):
    """Ловит товар чужого магазина до сохранения: заказа ещё нет,
    магазин уже известен.

    Без этой проверки чужой товар на странице создания доходит до
    OrderItem.save() и роняет админку необработанным ValidationError.
    """

    def clean(self):
        super().clean()
        market_id = getattr(self.instance, "market_id", None)
        if not market_id:
            return
        for form in self.forms:
            if not form.cleaned_data or form.cleaned_data.get("DELETE"):
                continue
            product = form.cleaned_data.get("product")
            if product and product.market_id != market_id:
                order_market = self.instance.market
                form.add_error(
                    "product",
                    f"«{product.name}» is sold by «{product.market.name}», "
                    f"but the order is placed at «{order_market.name}».",
                )


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1
    formset = OrderItemInlineFormSet

    def get_formset(self, request, obj=None, **kwargs):
        request._order_market_id = obj.market_id if obj else None
        return super().get_formset(request, obj, **kwargs)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "product":
            market_id = getattr(request, "_order_market_id", None)
            products = Product.objects.select_related("market")
            # у нового заказа магазина ещё нет — показываем все товары,
            # чужой отсеет OrderItemInlineFormSet.clean()
            kwargs["queryset"] = (
                products.filter(market_id=market_id) if market_id else products
            )
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "market", "buyer", "courier", "created_at")
    list_filter = ("market", "created_at")
    inlines = (OrderItemInline,)


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ("order", "product", "price", "quantity")
    list_filter = ("product__market",)

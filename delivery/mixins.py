from django.contrib.auth.mixins import UserPassesTestMixin
from django.db.models import Q


class SearchMixin:
    search_fields = ()
    search_pk = False
    search_placeholder = "Search"
    search_param = "q"

    def get_search_query(self):
        return self.request.GET.get(self.search_param, "").strip()

    def get_search_filter(self, query):
        condition = Q()
        for field in self.search_fields:
            condition |= Q(**{f"{field}__icontains": query})
        if self.search_pk and query.isdigit():
            condition |= Q(pk=int(query))
        return condition

    def get_queryset(self):
        queryset = super().get_queryset()
        query = self.get_search_query()
        if query and (self.search_fields or self.search_pk):
            queryset = queryset.filter(self.get_search_filter(query))
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["search_query"] = self.get_search_query()
        context["search_param"] = self.search_param
        context["search_placeholder"] = self.search_placeholder
        return context


class BuyerRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_buyer


class CourierRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_courier


class StaffRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_staff

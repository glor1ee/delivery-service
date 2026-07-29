from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.urls import reverse


class Waiter(AbstractUser):
    pass


class Product(models.Model):
    name = models.CharField(max_length=100)


class Order(models.Model):
    market = models.ForeignKey("Market", on_delete=models.CASCADE)
    waiter = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)


class Market(models.Model):
    name = models.CharField(max_length=100)
    product = models.ForeignKey("Product", on_delete=models.CASCADE)

    def __str__(self):
        return self.name
from django.db import models
from pos.models import Product


class InventoryLog(models.Model):

    product = models.ForeignKey(Product, on_delete=models.CASCADE)

    change = models.IntegerField()

    reason = models.CharField(max_length=200)

    created_at = models.DateTimeField(auto_now_add=True)
from pos.models import Sale


def total_sales():

    return Sale.objects.all().count()
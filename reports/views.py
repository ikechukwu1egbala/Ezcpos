from rest_framework.views import APIView
from rest_framework.response import Response
from pos.models import Sale
from django.db.models import Sum


class DailySalesReport(APIView):

    def get(self, request):

        total = Sale.objects.aggregate(total=Sum("total_amount"))

        return Response({
            "total_sales": total["total"] or 0
        })
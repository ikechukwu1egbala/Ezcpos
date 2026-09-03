from rest_framework.exceptions import APIException


class OutOfStock(APIException):

    status_code = 400

    default_detail = "Product out of stock"
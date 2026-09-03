from .models import User


def create_cashier(username, password):

    return User.objects.create_user(
        username=username,
        password=password,
        role="cashier"
    )
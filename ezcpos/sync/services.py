from decimal import Decimal, InvalidOperation

from django.db import transaction
from django.utils import timezone

from .models import SyncOperation

from pos.models import (
    Customer,
    Product,
    Category,
    Location,
    ProductUnit,
)

from expenses.models import Expense, ExpenseCategory

from pos.services import create_sale

from payments.services import (
    process_payment,
    refund_payment,
    process_sales_return,
)


class SyncService:
    """
    Server-side synchronization engine for EZC POS.

    The mobile application can safely retry an operation because
    operation_id is globally unique.

    Business operations are processed through the same server-side
    business services used by the online API.
    """

    @staticmethod
    @transaction.atomic
    def receive_operation(device, user, operation):
        operation_id = operation.get("operation_id")
        entity_type = str(operation.get("entity_type", "")).upper()
        entity_id = operation.get("entity_id")
        operation_type = operation.get("operation_type")
        payload = operation.get("payload") or {}

        if not operation_id:
            raise ValueError("operation_id is required.")

        if not entity_type:
            raise ValueError("entity_type is required.")

        if not entity_id:
            raise ValueError("entity_id is required.")

        if operation_type not in {"create", "update", "delete"}:
            raise ValueError(
                "operation_type must be create, update, or delete."
            )

        if not isinstance(payload, dict):
            raise ValueError("payload must be an object.")

        existing = (
            SyncOperation.objects
            .select_for_update()
            .filter(operation_id=operation_id)
            .first()
        )

        if existing:
            return {
                "operation_id": str(existing.operation_id),
                "status": existing.status,
                "duplicate": True,
                "server_result": existing.server_result,
                "error_message": existing.error_message,
            }

        sync_operation = SyncOperation.objects.create(
            operation_id=operation_id,
            device=device,
            user=user,
            entity_type=entity_type,
            entity_id=str(entity_id),
            operation_type=operation_type,
            payload=payload,
            status="pending",
        )

        try:
            result = SyncService.process_business_operation(
                sync_operation=sync_operation,
            )

            sync_operation.status = "processed"
            sync_operation.server_result = result or {}
            sync_operation.processed_at = timezone.now()
            sync_operation.error_message = ""

            sync_operation.save(
                update_fields=[
                    "status",
                    "server_result",
                    "processed_at",
                    "error_message",
                ]
            )

            return {
                "operation_id": str(sync_operation.operation_id),
                "status": "processed",
                "duplicate": False,
                "server_result": sync_operation.server_result,
                "error_message": "",
            }

        except Exception as exc:
            sync_operation.status = "failed"
            sync_operation.error_message = str(exc)
            sync_operation.processed_at = timezone.now()

            sync_operation.save(
                update_fields=[
                    "status",
                    "error_message",
                    "processed_at",
                ]
            )

            return {
                "operation_id": str(sync_operation.operation_id),
                "status": "failed",
                "duplicate": False,
                "server_result": {},
                "error_message": str(exc),
            }

    @staticmethod
    def process_business_operation(sync_operation):
        handlers = {
            "CUSTOMER": SyncService.handle_customer,
            "PRODUCT": SyncService.handle_product,
            "SALE": SyncService.handle_sale,
            "PAYMENT": SyncService.handle_payment,
            "REFUND": SyncService.handle_refund,
            "RETURN": SyncService.handle_return,
            "EXPENSE": SyncService.handle_expense,
        }

        handler = handlers.get(sync_operation.entity_type)

        if handler is None:
            raise ValueError(
                f"Unsupported sync entity_type: "
                f"{sync_operation.entity_type}"
            )

        return handler(sync_operation)

    # ---------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------

    @staticmethod
    def decimal(value, field_name):
        try:
            value = Decimal(str(value))
        except (InvalidOperation, TypeError, ValueError):
            raise ValueError(
                f"{field_name} must be a valid number."
            )

        return value

    @staticmethod
    def get_category(payload):
        category_id = payload.get("category_id")

        if not category_id:
            return None

        category = Category.objects.filter(id=category_id).first()

        if category is None:
            raise ValueError(
                f"Category {category_id} does not exist."
            )

        return category

    @staticmethod
    def get_location(payload):
        location_id = payload.get("location_id")

        if not location_id:
            return None

        location = (
            Location.objects
            .filter(id=location_id, is_active=True)
            .first()
        )

        if location is None:
            raise ValueError(
                f"Location {location_id} does not exist or is inactive."
            )

        return location

    # ---------------------------------------------------------
    # CUSTOMER
    # ---------------------------------------------------------

    @staticmethod
    def handle_customer(sync_operation):
        payload = sync_operation.payload
        operation_type = sync_operation.operation_type
        entity_id = sync_operation.entity_id

        if operation_type == "create":
            customer = Customer.objects.create(
                name=str(payload.get("name", "")).strip(),
                phone=str(payload.get("phone", "")).strip(),
                address=str(payload.get("address", "")).strip(),
            )

        elif operation_type == "update":
            customer = Customer.objects.filter(id=entity_id).first()

            if customer is None:
                raise ValueError(
                    f"Customer {entity_id} does not exist."
                )

            if "name" in payload:
                customer.name = str(payload["name"]).strip()

            if "phone" in payload:
                customer.phone = str(payload["phone"]).strip()

            if "address" in payload:
                customer.address = str(payload["address"]).strip()

            customer.save()

        elif operation_type == "delete":
            customer = Customer.objects.filter(id=entity_id).first()

            if customer is None:
                return {
                    "entity": "CUSTOMER",
                    "entity_id": entity_id,
                    "deleted": False,
                    "message": "Customer already absent.",
                }

            customer.delete()

            return {
                "entity": "CUSTOMER",
                "entity_id": entity_id,
                "deleted": True,
            }

        else:
            raise ValueError(
                "Unsupported CUSTOMER operation."
            )

        return {
            "entity": "CUSTOMER",
            "entity_id": str(customer.id),
            "operation": operation_type,
            "data": {
                "id": customer.id,
                "name": customer.name,
                "phone": customer.phone,
                "address": customer.address,
            },
        }

    # ---------------------------------------------------------
    # PRODUCT
    # ---------------------------------------------------------

    @staticmethod
    def handle_product(sync_operation):
        payload = sync_operation.payload
        operation_type = sync_operation.operation_type
        entity_id = sync_operation.entity_id

        if operation_type == "create":
            category = SyncService.get_category(payload)

            product = Product.objects.create(
                name=str(payload.get("name", "")).strip(),
                barcode=payload.get("barcode") or None,
                category=category,
                price=SyncService.decimal(
                    payload.get("price", "0"),
                    "price",
                ),
                description=str(
                    payload.get("description", "")
                ).strip(),
                recognition_enabled=payload.get(
                    "recognition_enabled",
                    True,
                ),
            )

        elif operation_type == "update":
            product = Product.objects.filter(id=entity_id).first()

            if product is None:
                raise ValueError(
                    f"Product {entity_id} does not exist."
                )

            if "name" in payload:
                product.name = str(payload["name"]).strip()

            if "barcode" in payload:
                product.barcode = payload["barcode"] or None

            if "category_id" in payload:
                product.category = SyncService.get_category(
                    payload
                )

            if "price" in payload:
                product.price = SyncService.decimal(
                    payload["price"],
                    "price",
                )

            if "description" in payload:
                product.description = str(
                    payload["description"]
                ).strip()

            if "recognition_enabled" in payload:
                product.recognition_enabled = bool(
                    payload["recognition_enabled"]
                )

            product.save()

        elif operation_type == "delete":
            product = Product.objects.filter(id=entity_id).first()

            if product is None:
                return {
                    "entity": "PRODUCT",
                    "entity_id": entity_id,
                    "deleted": False,
                }

            product.delete()

            return {
                "entity": "PRODUCT",
                "entity_id": entity_id,
                "deleted": True,
            }

        else:
            raise ValueError(
                "Unsupported PRODUCT operation."
            )

        return {
            "entity": "PRODUCT",
            "entity_id": str(product.id),
            "operation": operation_type,
            "data": {
                "id": product.id,
                "name": product.name,
                "barcode": product.barcode,
                "category_id": (
                    product.category_id
                    if product.category_id
                    else None
                ),
                "price": str(product.price),
                "description": product.description,
                "recognition_enabled": (
                    product.recognition_enabled
                ),
            },
        }

    # ---------------------------------------------------------
    # SALE
    # ---------------------------------------------------------

    @staticmethod
    def handle_sale(sync_operation):
        payload = sync_operation.payload

        if sync_operation.operation_type != "create":
            raise ValueError(
                "SALE synchronization currently supports create only."
            )

        items = payload.get("items")

        if not items:
            raise ValueError(
                "SALE requires at least one item."
            )

        customer = None

        customer_id = payload.get("customer_id")

        if customer_id:
            customer = Customer.objects.filter(
                id=customer_id
            ).first()

            if customer is None:
                raise ValueError(
                    f"Customer {customer_id} does not exist."
                )

        location = SyncService.get_location(payload)

        discount = SyncService.decimal(
            payload.get("discount", "0.00"),
            "discount",
        )

        sale = create_sale(
            items=items,
            cashier=sync_operation.user,
            customer=customer,
            location=location,
            discount=discount,
        )

        return {
            "entity": "SALE",
            "entity_id": str(sale.id),
            "operation": "create",
            "data": {
                "id": sale.id,
                "subtotal": str(sale.subtotal),
                "discount": str(sale.discount),
                "total_amount": str(sale.total_amount),
            },
        }

    # ---------------------------------------------------------
    # PAYMENT
    # ---------------------------------------------------------

    @staticmethod
    def handle_payment(sync_operation):
        payload = sync_operation.payload

        if sync_operation.operation_type != "create":
            raise ValueError(
                "PAYMENT synchronization currently supports create only."
            )

        sale_id = payload.get("sale_id")

        if not sale_id:
            raise ValueError(
                "PAYMENT requires sale_id."
            )

        amount = SyncService.decimal(
            payload.get("amount"),
            "amount",
        )

        payment_method = payload.get("payment_method")

        if not payment_method:
            raise ValueError(
                "PAYMENT requires payment_method."
            )

        from pos.models import Sale

        sale = Sale.objects.filter(id=sale_id).first()

        if sale is None:
            raise ValueError(
                f"Sale {sale_id} does not exist."
            )

        payment = process_payment(
            sale=sale,
            amount=amount,
            payment_method=payment_method,
            processed_by=sync_operation.user,
            transaction_reference=payload.get(
                "transaction_reference"
            ),
        )

        return {
            "entity": "PAYMENT",
            "entity_id": str(payment.id),
            "operation": "create",
            "data": {
                "id": payment.id,
                "sale_id": payment.sale_id,
                "amount": str(payment.amount),
                "payment_method": payment.payment_method,
                "status": payment.status,
            },
        }

    # ---------------------------------------------------------
    # REFUND
    # ---------------------------------------------------------

    @staticmethod
    def handle_refund(sync_operation):
        payload = sync_operation.payload

        if sync_operation.operation_type != "create":
            raise ValueError(
                "REFUND synchronization currently supports create only."
            )

        payment_id = payload.get("payment_id")

        if not payment_id:
            raise ValueError(
                "REFUND requires payment_id."
            )

        from payments.models import Payment

        payment = Payment.objects.filter(
            id=payment_id
        ).first()

        if payment is None:
            raise ValueError(
                f"Payment {payment_id} does not exist."
            )

        amount = SyncService.decimal(
            payload.get("amount"),
            "amount",
        )

        reason = payload.get("reason")

        if not reason:
            raise ValueError(
                "REFUND requires reason."
            )

        refund = refund_payment(
            payment=payment,
            amount=amount,
            reason=reason,
            processed_by=sync_operation.user,
            reference=payload.get("reference"),
        )

        return {
            "entity": "REFUND",
            "entity_id": str(refund.id),
            "operation": "create",
            "data": {
                "id": refund.id,
                "payment_id": refund.payment_id,
                "amount": str(refund.amount),
                "reason": refund.reason,
            },
        }

    # ---------------------------------------------------------
    # RETURN
    # ---------------------------------------------------------

    @staticmethod
    def handle_return(sync_operation):
        payload = sync_operation.payload

        if sync_operation.operation_type != "create":
            raise ValueError(
                "RETURN synchronization currently supports create only."
            )

        sale_id = payload.get("sale_id")

        if not sale_id:
            raise ValueError(
                "RETURN requires sale_id."
            )

        from pos.models import Sale

        sale = Sale.objects.filter(id=sale_id).first()

        if sale is None:
            raise ValueError(
                f"Sale {sale_id} does not exist."
            )

        items = payload.get("items")

        if not items:
            raise ValueError(
                "RETURN requires at least one item."
            )

        location = SyncService.get_location(payload)

        sales_return = process_sales_return(
            sale=sale,
            items=items,
            location=location,
            reason=payload.get("reason"),
            user=sync_operation.user,
            refund_id=payload.get("refund_id"),
            reference=payload.get("reference"),
        )

        return {
            "entity": "RETURN",
            "entity_id": str(sales_return.id),
            "operation": "create",
            "data": {
                "id": sales_return.id,
                "sale_id": sales_return.sale_id,
                "reason": sales_return.reason,
            },
        }

    # ---------------------------------------------------------
    # EXPENSE
    # ---------------------------------------------------------

    @staticmethod
    def handle_expense(sync_operation):
        payload = sync_operation.payload
        operation_type = sync_operation.operation_type
        entity_id = sync_operation.entity_id

        if operation_type == "create":
            category_id = payload.get("category_id")

            if not category_id:
                raise ValueError(
                    "EXPENSE requires category_id."
                )

            category = ExpenseCategory.objects.filter(
                id=category_id
            ).first()

            if category is None:
                raise ValueError(
                    f"Expense category {category_id} does not exist."
                )

            location = SyncService.get_location(payload)

            expense = Expense.objects.create(
                category=category,
                location=location,
                description=str(
                    payload.get("description", "")
                ).strip(),
                amount=SyncService.decimal(
                    payload.get("amount"),
                    "amount",
                ),
                payment_method=payload.get(
                    "payment_method",
                    "cash",
                ),
                status=payload.get(
                    "status",
                    "paid",
                ),
                reference=str(
                    payload.get("reference", "")
                ).strip(),
                receipt_number=str(
                    payload.get("receipt_number", "")
                ).strip(),
                expense_date=payload.get(
                    "expense_date"
                ),
                recorded_by=sync_operation.user,
            )

        elif operation_type == "update":
            expense = Expense.objects.filter(
                id=entity_id
            ).first()

            if expense is None:
                raise ValueError(
                    f"Expense {entity_id} does not exist."
                )

            if "category_id" in payload:
                category = ExpenseCategory.objects.filter(
                    id=payload["category_id"]
                ).first()

                if category is None:
                    raise ValueError(
                        "Expense category does not exist."
                    )

                expense.category = category

            if "location_id" in payload:
                expense.location = SyncService.get_location(
                    payload
                )

            if "description" in payload:
                expense.description = str(
                    payload["description"]
                ).strip()

            if "amount" in payload:
                expense.amount = SyncService.decimal(
                    payload["amount"],
                    "amount",
                )

            if "payment_method" in payload:
                expense.payment_method = payload[
                    "payment_method"
                ]

            if "status" in payload:
                expense.status = payload["status"]

            if "reference" in payload:
                expense.reference = str(
                    payload["reference"]
                ).strip()

            if "receipt_number" in payload:
                expense.receipt_number = str(
                    payload["receipt_number"]
                ).strip()

            if "expense_date" in payload:
                expense.expense_date = payload[
                    "expense_date"
                ]

            expense.save()

        elif operation_type == "delete":
            expense = Expense.objects.filter(
                id=entity_id
            ).first()

            if expense is None:
                return {
                    "entity": "EXPENSE",
                    "entity_id": entity_id,
                    "deleted": False,
                }

            expense.delete()

            return {
                "entity": "EXPENSE",
                "entity_id": entity_id,
                "deleted": True,
            }

        else:
            raise ValueError(
                "Unsupported EXPENSE operation."
            )

        return {
            "entity": "EXPENSE",
            "entity_id": str(expense.id),
            "operation": operation_type,
            "data": {
                "id": expense.id,
                "amount": str(expense.amount),
                "status": expense.status,
                "payment_method": expense.payment_method,
            },
        }

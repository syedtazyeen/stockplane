from decimal import Decimal
from typing import Any

from faker import Faker


class DataFactory:
    """Generate realistic test payloads with Faker."""

    def __init__(self, faker: Faker) -> None:
        self.faker = faker

    def email(self) -> str:
        return self.faker.unique.email()

    def password(self, length: int = 12) -> str:
        return self.faker.password(length=length, special_chars=False)

    def business_name(self) -> str:
        return self.faker.company()

    def full_name(self) -> str:
        return self.faker.name()

    def sku(self) -> str:
        return self.faker.bothify(text="??-########", letters="ABCDEFGHIJKLMNOPQRSTUVWXYZ")

    def product_name(self) -> str:
        return self.faker.catch_phrase()

    def product_description(self) -> str:
        return self.faker.paragraph(nb_sentences=2)

    def price(self, min_value: float = 1.0, max_value: float = 500.0) -> str:
        return f"{self.faker.pyfloat(min_value=min_value, max_value=max_value, right_digits=2):.2f}"

    def register_payload(self, **overrides: Any) -> dict[str, Any]:
        payload = {
            "email": self.email(),
            "password": self.password(),
            "business_name": self.business_name(),
            "full_name": self.full_name(),
        }
        payload.update(overrides)
        return payload

    def product_payload(self, **overrides: Any) -> dict[str, Any]:
        cost = Decimal(self.price(min_value=1, max_value=100))
        selling = Decimal(self.price(min_value=float(cost), max_value=500))

        payload: dict[str, Any] = {
            "sku": self.sku(),
            "name": self.product_name(),
            "description": self.product_description(),
            "status": "ACTIVE",
            "cost_price": str(cost),
            "selling_price": str(selling),
            "quantity": 0,
        }
        payload.update(overrides)
        return payload

    def phone(self) -> str:
        return self.faker.numerify(text="+1##########")

    def customer_payload(self, **overrides: Any) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "name": self.full_name(),
            "email": self.email(),
            "phone": self.phone(),
            "status": "ACTIVE",
        }
        payload.update(overrides)
        return payload

    def order_payload(self, *, customer_id: str, product_id: str, **overrides: Any) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "customer_id": customer_id,
            "lines": [{"product_id": product_id, "quantity": 1}],
        }
        payload.update(overrides)
        return payload

from datetime import date

from app_mvc.models.discount_model import DiscountModel


class DiscountController:
    def __init__(self, model: DiscountModel) -> None:
        self.model = model

    def list_public_discounts(self, today: date) -> list[dict]:
        return self.model.list_public(today)

    def list_discounts(self) -> list[dict]:
        return self.model.list_all()

    def get_discount(self, discount_id: int) -> dict:
        return self.model.get(discount_id)

    def create_discount(self, data: dict) -> dict:
        return self.model.create(data)

    def update_discount(self, discount_id: int, data: dict) -> dict:
        return self.model.update(discount_id, data)

    def deactivate_discount(self, discount_id: int) -> dict:
        return self.model.deactivate(discount_id)
from app_mvc.models.professional_model import ProfessionalModel


class ProfessionalController:
    def __init__(self, model: ProfessionalModel) -> None:
        self.model = model

    def list_professionals(self, only_active: bool = True) -> list[dict]:
        return self.model.list_all(only_active)

    def get_professional(self, professional_id: int) -> dict:
        return self.model.get(professional_id)

    def create_professional(self, data: dict) -> dict:
        return self.model.create(data)

    def update_professional(self, professional_id: int, data: dict) -> dict:
        return self.model.update(professional_id, data)

    def deactivate_professional(self, professional_id: int) -> dict:
        return self.model.deactivate(professional_id)
from app_mvc.models.service_model import ServiceModel


class ServiceController:
    def __init__(self, model: ServiceModel) -> None:
        self.model = model

    def list_services(
        self,
        only_active: bool = True,
        only_online: bool = True,
    ) -> list[dict]:
        return self.model.list_all(only_active, only_online)

    def get_service(self, service_id: int) -> dict:
        return self.model.get(service_id)

    def get_public_service(self, service_id: int) -> dict:
        return self.model.get_public(service_id)

    def create_service(self, data: dict) -> dict:
        return self.model.create(data)

    def update_service(self, service_id: int, data: dict) -> dict:
        return self.model.update(service_id, data)

    def deactivate_service(self, service_id: int) -> dict:
        return self.model.deactivate(service_id)
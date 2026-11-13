from app_mvc.models.client_model import ClientModel

class ClientController:
    def __init__(self, model: ClientModel):
        self.model = model

    def list_clients(self, only_active: bool = True) -> list[dict]:
        return self.model.list_all(only_active)

    def get_client(self, client_id: int) -> dict:
        return self.model.get(client_id)

    def create_client(self, client_data: dict) -> dict:
        return self.model.create(client_data)

    def update_client(self, client_id: int, client_data: dict) -> dict:
        return self.model.update(client_id, client_data)

    def activate_client(self, client_id: int) -> dict:
        return self.model.change_status(client_id, is_active=True)

    def deactivate_client(self, client_id: int) -> dict:
        return self.model.change_status(client_id, is_active=False)
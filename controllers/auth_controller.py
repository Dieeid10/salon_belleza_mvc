from app_mvc.models.auth_model import AuthModel

class AuthController:
    def __init__(self, model: AuthModel):
        self.model = model

    def login(self, email: str, password: str) -> dict:
        return self.model.login(email, password)

    def refresh(self, refresh_token: str) -> dict:
        return self.model.refresh(refresh_token)
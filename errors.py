class AppError(Exception):
    status_code = 400
    code = "application_error"

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)
class ApplicationBaseError(Exception):
    """
    Базовый класс для доменных исключений.
    """

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class OpenRouterError(ApplicationBaseError):
    """
    Ошибка при взаимодействии с сервисом OpenRouter.ai
    """

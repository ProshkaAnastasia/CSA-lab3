class WrongSelectorError(Exception):
    def __init__(self, message):
        super().__init__(message)

    def __str__(self):
        return f"Ошибка при обработке данных: {self.message}"

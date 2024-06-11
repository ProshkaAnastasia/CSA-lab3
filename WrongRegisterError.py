class WrongRegisterError(Exception):
    def __init__(self, target):
        super().__init__(target)

    def __str__(self):
        return f"Wrong register {self.target}"

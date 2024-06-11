class UnknownLineError(Exception):
    def __str__(self):
        return "Internal error: unknown code line"

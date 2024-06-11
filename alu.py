class ALU:
    max = 2**31 - 1
    min = -(2**31)

    def __init__(self):
        self.left = 0
        self.right = 0
        self.result = 0
        self.flags = {"Z": False, "N": False, "W": False}
        self.operation = 0
        self.operations = {
            "add": self.add,
            "sub": self.sub,
            "mod": self.mod,
            "div": self.div,
            "inc_left": self.inc_left,
            "inc_right": self.inc_right,
            "dec_left": self.dec_left,
            "dec_right": self.dec_right,
            "skip_left": self.skip_left,
            "skip_right": self.skip_right,
        }

    def add(self):
        self.result = self.left + self.right
        if self.result > self.max:
            self.result = self.min + self.result % self.max
            self.flags["W"] = 1
        if self.result < self.min:
            self.result = self.max + 1 - abs(self.result - self.min)
            self.flags["W"] = 1
        self.set_flags()

    def sub(self):
        self.result = self.left - self.right
        if self.result > self.max:
            self.result = self.min + self.result % self.max
            self.flags["W"] = 1
        if self.result < self.min:
            self.result = self.max + 1 - abs(self.result - self.min)
            self.flags["W"] = 1
        self.set_flags()

    def mod(self):
        self.result = self.left % self.right
        self.set_flags()

    def div(self):
        self.result = self.left // self.right
        self.set_flags()

    def inc_left(self):
        self.result = self.left + 1
        self.set_flags()

    def inc_right(self):
        self.result = self.right + 1
        self.set_flags()

    def dec_left(self):
        self.result = self.left - 1
        self.set_flags()

    def dec_right(self):
        self.result = self.right - 1
        self.set_flags()

    def skip_left(self):
        self.result = self.left

    def skip_right(self):
        self.result = self.right

    def configure(self, operation, left, right):
        self.operation = operation
        self.left = left
        self.right = right

    def execute(self, operation):
        self.operations[operation]()

    def set_flags(self):
        self.flags["N"] = self.result < 0
        self.flags["Z"] = self.result == 0

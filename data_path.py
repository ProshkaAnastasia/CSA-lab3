from enum import Enum

from alu import ALU
from isa import registers
from WrongRegisterError import WrongRegisterError
from WrongSelectorError import WrongSelectorError


class Selector(Enum):
    ALU = 0
    MEMORY = 1
    INPUT = 2
    DR = 3
    REGISTER = 4


class DataPath:
    def __init__(self, data, in_buf):
        self.registers = {"r" + str(i): 0 for i in range(4)}
        self.hidden_registers = {
            "dr": 0,
            "ar": 0,
            "sp": 0,
            "ps": {
                "N": False,
                "Z": False,
                "W": False,
                "I": False,
                "IA": True,
                "E": False,
            },
        }
        self.data_memory = data
        self.alu = ALU()
        self.in_ports = [1]
        self.out_ports = [0]
        self.in_buffer = in_buf
        self.out_buffer = {i: [] for i in self.out_ports}
        self.current_in_port = 1
        self.current_out_port = 0

    def mem_write(self):
        self.data_memory[self.hidden_registers["ar"]] = self.hidden_registers["dr"]

    def mem_read(self):
        self.signal_latch_dr(Selector.MEMORY)

    def input(self, port):
        char = ord(self.in_buffer[port].pop(0)[1])
        self.hidden_registers["dr"] = char
        if char == 0:
            self.hidden_registers["ps"]["E"] = True

    def output(self, port):
        char = chr(self.hidden_registers["dr"])
        if char != "\0":
            self.out_buffer[port].append(char)

    def print(self, arg):
        num = str(self.registers[arg])
        for i in range(len(num)):
            self.out_buffer[0].append(num[i])

    def push(self, arg):
        current_sp = self.hidden_registers["sp"]
        self.hidden_registers["sp"] = (
            current_sp - 1 if current_sp > 0 else len(self.data_memory) - 1
        )
        self.hidden_registers["ar"] = self.hidden_registers["sp"]
        self.execute_alu("skip_left", arg, "0")
        self.signal_latch_dr(Selector.ALU)
        self.mem_write()

    def pop(self, arg):
        self.execute_alu("skip_right", "0", "sp")
        self.signal_latch_ar()
        self.mem_read()
        current_sp = self.hidden_registers["sp"]
        self.hidden_registers["sp"] = (
            current_sp + 1 if current_sp < len(self.data_memory) - 1 else 0
        )
        self.execute_alu("skip_right", "0", "dr")
        if arg in self.registers:
            self.signal_latch_register(arg)

    def signal_latch_sp(self):
        self.hidden_registers["sp"] = self.alu.result

    def signal_latch_register(self, target: str):
        if target not in registers:
            raise WrongRegisterError(target)
        self.registers[target] = self.alu.result

    def signal_latch_dr(self, sel):
        if sel not in [Selector.ALU, Selector.MEMORY, Selector.INPUT]:
            raise WrongSelectorError()
        match sel:
            case Selector.ALU:
                self.hidden_registers["dr"] = self.alu.result
            case Selector.MEMORY:
                self.hidden_registers["dr"] = self.data_memory[
                    self.hidden_registers["ar"]
                ]
            case Selector.INPUT:
                self.hidden_registers["dr"] = self.in_buffer[self.current_in_port]

    def signal_latch_ar(self):
        self.hidden_registers["ar"] = self.alu.result

    def left_mux_alu(self, value):
        self.alu.left = value

    def right_mux_alu(self, value):
        self.alu.right = value

    def configure_alu(self, left=0, right=0):
        self.left_mux_alu(left)
        self.right_mux_alu(right)

    def is_number_argument(self, arg: str):
        if arg.isdigit():
            return self.alu.min <= int(arg) and int(arg) <= self.alu.max
        return False

    def setup_alu(self, left: str, right: str):
        if left in self.registers:
            self.left_mux_alu(self.registers[left])
        elif left in self.hidden_registers:
            self.left_mux_alu(self.hidden_registers[left])
        elif self.is_number_argument(left):
            self.left_mux_alu(int(left))
        else:
            self.left_mux_alu(0)
        if right in self.registers:
            self.right_mux_alu(self.registers[right])
        elif right in self.hidden_registers:
            self.right_mux_alu(self.hidden_registers[right])
        elif self.is_number_argument(right):
            self.right_mux_alu(int(right))
        else:
            self.right_mux_alu(0)

    def execute_alu(self, operation, left: str = "0", right: str = "0"):
        self.setup_alu(left, right)
        self.alu.execute(operation)

    def exec_alu(self, operation, left, right):
        self.configure_alu(left, right)
        self.alu.execute(operation)

    def signal_latch_ps(self):
        self.hidden_registers["ps"]["Z"] = self.alu.flags["Z"]
        self.hidden_registers["ps"]["N"] = self.alu.flags["N"]
        self.hidden_registers["ps"]["W"] = self.alu.flags["W"]

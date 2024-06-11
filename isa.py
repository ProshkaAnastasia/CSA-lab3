from __future__ import annotations

import struct
from enum import Enum

DATA_SIZE = 2**11
CODE_SIZE = 2**7


class Opcode(Enum):
    LD = 16
    ST = 32
    MOV = 2
    ADD = 3
    INC = 4
    DEC = 5
    BEQ = 6
    BNE = 7
    JMP = 8
    OUT = 9
    IN = 10
    HLT = 11
    CMP = 12
    PUSH = 13
    POP = 14
    INT = 15
    IRET = 17
    MOD = 18
    DIV = 19
    PRINTI = 20
    VEC = 0
    CALL = 21
    RET = 22
    JNE = 23
    NOP = 24


class Addressing(Enum):
    ABSOLUTE = 0
    RELATIVE = 1


registers: list[str] = [f"r{i}" for i in range(32)]


def check_reg(arg):
    return arg in registers


def check_code_label(arg, labels):
    return arg in labels


def check_data_label(arg, labels):
    return arg in labels


def check_code_address(arg, size):
    return arg in range(size)


def check_data_address(arg, size):
    return arg in range(size)


def check_constant(arg):
    return arg.isdigit()


class ArgType(str, Enum):
    REGISTER = check_reg  # lambda arg: arg in registers
    CODE_LABEL = check_code_label  # lambda arg, labels: arg in labels
    DATA_LABEL = check_data_label  # lambda arg, labels: arg in labels
    CODE_ADDRESS = check_code_address  # lambda arg, code_size: arg in range(code_size)
    DATA_ADDRESS = check_data_address  # lambda arg, data_size: arg in range(data_size)
    CONSTANT = check_constant  # lambda arg: arg.isdigit()

    def __str__(self):
        return self.type


instructions = {
    "vec": {
        "type": Opcode.VEC,
        "args": 1,
        "arg1": [ArgType.CODE_ADDRESS, ArgType.CODE_LABEL],
        "log": lambda addr,
        code,
        args: f"{hex(addr):5}   --   {code}   --   int_vector: handle_addr = {args[0]}",
    },
    "ld": {
        "type": Opcode.LD,
        "args": 2,
        "arg1": [ArgType.REGISTER],
        "arg2": [ArgType.DATA_ADDRESS, ArgType.DATA_LABEL, ArgType.REGISTER],
        "log": lambda addr,
        code,
        args: f"{hex(addr):5}   --   {code}   --   ld:  {args[0]} <- {args[1]}",
    },
    "st": {
        "type": Opcode.ST,
        "args": 2,
        "arg1": [ArgType.REGISTER],
        "arg2": [ArgType.DATA_ADDRESS, ArgType.DATA_LABEL, ArgType.REGISTER],
        "log": lambda addr,
        code,
        args: f"{hex(addr):5}   --   {code}   --   st:  {args[0]} -> {args[1]}",
    },
    "add": {
        "type": Opcode.ADD,
        "args": 3,
        "arg1": [ArgType.REGISTER],
        "arg2": [ArgType.REGISTER],
        "arg3": [ArgType.REGISTER],
        "log": lambda addr,
        code,
        args: f"{hex(addr):5}   --   {code}   --   add: {args[0]} <- {args[1]} + {args[2]}",
    },
    "mod": {
        "type": Opcode.MOD,
        "args": 3,
        "arg1": [ArgType.REGISTER],
        "arg2": [ArgType.REGISTER, ArgType.CONSTANT],
        "arg3": [ArgType.REGISTER, ArgType.CONSTANT],
        "log": lambda addr,
        code,
        args: f"{hex(addr):5}   --   {code}   --   mod: {args[0]} <- {args[1]} % {args[2]}",
    },
    "div": {
        "type": Opcode.DIV,
        "args": 3,
        "arg1": [ArgType.REGISTER],
        "arg2": [ArgType.REGISTER, ArgType.CONSTANT],
        "arg3": [ArgType.REGISTER, ArgType.CONSTANT],
        "log": lambda addr,
        code,
        args: f"{hex(addr):5}   --   {code}   --   div: {args[0]} <- {args[1]} // {args[2]}",
    },
    "inc": {
        "type": Opcode.INC,
        "args": 1,
        "arg1": [ArgType.REGISTER],
        "log": lambda addr,
        code,
        args: f"{hex(addr):5}   --   {code}   --   inc: {args[0]} <- {args[0]} + 1",
    },
    "dec": {
        "type": Opcode.DEC,
        "args": 1,
        "arg1": [ArgType.REGISTER],
        "log": lambda addr,
        code,
        args: f"{hex(addr):5}   --   {code}   --   dec: {args[0]} <- {args[0]} - 1",
    },
    "beq": {
        "type": Opcode.BEQ,
        "args": 1,
        "arg1": [ArgType.CODE_ADDRESS, ArgType.CODE_LABEL],
        "log": lambda addr,
        code,
        args: f"{hex(addr):5}   --   {code}   --   beq: if Z ip <- {args[0]}",
    },
    "bne": {
        "type": Opcode.BNE,
        "args": 1,
        "arg1": [ArgType.CODE_ADDRESS, ArgType.CODE_LABEL],
        "log": lambda addr,
        code,
        args: f"{hex(addr):5}   --   {code}   --   bne: if !Z ip <- {args[0]}",
    },
    "out": {
        "type": Opcode.OUT,
        "args": 2,
        "arg1": [ArgType.REGISTER],
        "arg2": [ArgType.CONSTANT],
        "log": lambda addr,
        code,
        args: f"{hex(addr):5}   --   {code}   --   out: {args[0]} output {int(args[1], 0)}",
    },
    "in": {
        "type": Opcode.IN,
        "args": 2,
        "arg1": [ArgType.REGISTER],
        "arg2": [ArgType.CONSTANT],
        "log": lambda addr,
        code,
        args: f"{hex(addr):5}   --   {code}   --   in:  {args[0]} input {int(args[1], 0)}",
    },
    "printi": {
        "type": Opcode.PRINTI,
        "args": 1,
        "arg1": [ArgType.REGISTER],
        "log": lambda addr,
        code,
        args: f"{hex(addr):5}   --   {code}   --   print int {args[0]}",
    },
    "hlt": {
        "type": Opcode.HLT,
        "args": 0,
        "log": lambda addr, code, args: f"{hex(addr):5}   --   {code}   --   hlt",
    },
    "mov": {
        "type": Opcode.MOV,
        "args": 2,
        "arg1": [ArgType.REGISTER],
        "arg2": [
            ArgType.REGISTER,
            ArgType.CONSTANT,
            ArgType.DATA_LABEL,
            ArgType.CODE_LABEL,
        ],
        "log": lambda addr,
        code,
        args: f"{hex(addr):5}   --   {code}   --   mov: {args[0]} <- {args[1]}",
    },
    "cmp": {
        "type": Opcode.CMP,
        "args": 2,
        "arg1": [ArgType.REGISTER, ArgType.CONSTANT],
        "arg2": [ArgType.REGISTER, ArgType.CONSTANT],
        "log": lambda addr,
        code,
        args: f"{hex(addr):5}   --   {code}   --   cmp: ps <- {args[0]} - {args[1]}",
    },
    "jmp": {
        "type": Opcode.JMP,
        "args": 1,
        "arg1": [ArgType.CODE_ADDRESS, ArgType.CODE_LABEL],
        "log": lambda addr,
        code,
        args: f"{hex(addr):5}   --   {code}   --   jmp: ip <- {args[0]}",
    },
    "jne": {
        "type": Opcode.JNE,
        "args": 1,
        "arg1": [ArgType.CODE_ADDRESS, ArgType.CODE_LABEL],
        "log": lambda addr,
        code,
        args: f"{hex(addr):5}   --   {code}   --   je: if !E ip <- {args[0]}",
    },
    "push": {
        "type": Opcode.PUSH,
        "args": 1,
        "arg1": [ArgType.REGISTER, ArgType.CONSTANT],
        "log": lambda addr,
        code,
        args: f"{hex(addr):5}   --   {code}   --   push: stack <- {args[0]}",
    },
    "pop": {
        "type": Opcode.POP,
        "args": 1,
        "arg1": [ArgType.REGISTER, ArgType.CONSTANT],
        "log": lambda addr,
        code,
        args: f"{hex(addr):5}   --   {code}   --   push: {args[0]} <- stack",
    },
    "int": {
        "type": Opcode.INT,
        "args": 0,
        "log": lambda addr, code, args: f"{hex(addr):5}   --   {code}   --   int",
    },
    "iret": {
        "type": Opcode.IRET,
        "args": 0,
        "log": lambda addr, code, args: f"{hex(addr):5}   --   {code}   --   iret",
    },
    "call": {
        "type": Opcode.CALL,
        "args": 1,
        "arg1": [ArgType.CODE_ADDRESS, ArgType.CODE_LABEL],
        "log": lambda addr,
        code,
        args: f"{hex(addr):5}   --   {code}   --   call {args[0]}",
    },
    "ret": {
        "type": Opcode.RET,
        "args": 0,
        "log": lambda addr, code, args: f"{hex(addr):5}   --   {code}   --   ret",
    },
    "nop": {
        "type": Opcode.NOP,
        "args": 0,
        "log": lambda addr, code, args: f"{hex(addr):5}   --   {code}   --   nop",
    },
}


def read_machine_code(filetype):
    with open(filetype + ".o", "rb") as file:
        data_size = struct.unpack(">I", file.read(4))[0]
        code_size = struct.unpack(">I", file.read(4))[0]
        data = [0] * DATA_SIZE
        code = ["0" * 32] * CODE_SIZE
        for i in range(data_size):
            data[i] = struct.unpack(">I", file.read(4))[0]
        for i in range(code_size):
            command = file.read(4)
            word = ""
            for byte in command:
                word += bin(byte)[2:].zfill(8)
            code[i] = word
        start = struct.unpack(">I", file.read(4))[0]
    return data, code, start


def write_machine_code(filetype, code, log):
    with open(filetype + ".o", "wb") as file:
        file.write(code)
    with open(filetype + ".txt", "w") as file:
        file.write(log)

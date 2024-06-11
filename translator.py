import re
import struct
import sys
from enum import Enum

from isa import (
    CODE_SIZE,
    DATA_SIZE,
    Addressing,
    ArgType,
    Opcode,
    instructions,
    registers,
    write_machine_code,
)
from UnknownLineError import UnknownLineError


class LineType(str, Enum):
    SECTION = 0
    DATA = 1
    COMMAND = 2
    LABEL = 3
    EMPTY = 4
    UNKNOWN = 5


class Section(Enum):
    DATA = ".data"
    CODE = ".text"


class Translator:
    def __init__(self):
        self.code = []
        self.data = []
        self.code_labels = {}
        self.data_labels = {}
        self.current_section = Section.DATA
        self.data_address = 0
        self.code_address = 0
        self.binary_data = b""

    def get_line_type(self, line) -> LineType:
        if re.fullmatch(r"\s*\S*:\s*", line):
            result = LineType.LABEL
        elif re.fullmatch(r"\s*", line):
            result = LineType.EMPTY
        elif self.current_section == Section.CODE:
            result = LineType.COMMAND
        elif re.match(r"\s*section\s+\.(data|text)", line):
            result = LineType.SECTION
        elif re.findall(r"(db|qword|dd)", line):
            result = LineType.DATA
        else:
            result = LineType.UNKNOWN
        return result

    def get_arg_type(self, arg: str) -> set:
        result = []
        if ArgType.REGISTER(arg):
            result.append(ArgType.REGISTER)
        if ArgType.DATA_LABEL(arg, self.data_labels):
            result.append(ArgType.DATA_LABEL)
        if ArgType.CODE_LABEL(arg, self.code_labels):
            result.append(ArgType.CODE_LABEL)
        if ArgType.DATA_ADDRESS(arg, DATA_SIZE):
            result.append(ArgType.DATA_ADDRESS)
        if ArgType.CODE_ADDRESS(arg, CODE_SIZE):
            result.append(ArgType.CODE_ADDRESS)
        if ArgType.CONSTANT(arg):
            result.append(ArgType.CONSTANT)
        return set(result)

    def get_addressing_type(self, arg):
        if re.search(r"\[|\]", arg):
            return Addressing.RELATIVE
        return Addressing.ABSOLUTE

    def parse_section(self, line):
        section = re.search(r"\.\S+", line).group()
        self.current_section = Section(section)

    def parse_label(self, line):
        label = re.search(r"\S+(?=:)", line).group()
        if self.current_section == Section.CODE:
            assert label not in self.code_labels
            if label == "_start":
                self.start = hex(self.code_address)
            self.code_labels[label] = self.code_address
        else:
            assert label not in self.data_labels
            self.data_labels[label] = self.data_address

    def parse_data(self, line):
        sentences = re.findall(r"'.*?'", line)
        line = re.sub(r"'.*?'", "", line)
        line = re.sub(r",", "", line)
        words = line.split()
        words.pop(0)
        for word in words:
            self.data.append(hex(int(word)))
            self.data_address += 1
        for sentence in sentences:
            sentence = re.sub(r"'", "", sentence)
            sentence = re.sub(r"\\n", "\n", sentence)
            for char in sentence:
                self.data.append(hex(ord(char)))
                self.data_address += 1

    def parse_command(self, line):
        line = re.sub(r",", "", line)
        words = line.split()
        command = {}
        command["opcode"] = words[0]
        command["args"] = []
        for i in range(1, len(words)):
            command["args"].append(words[i])
        self.code.append(command)
        self.code_address += 1

    def translate_stage_1(self, text: str):
        lines = text.splitlines()
        for line in lines:
            line = line.split(";")[0]
            line_type = self.get_line_type(line)
            match line_type:
                case LineType.SECTION:
                    self.parse_section(line)
                case LineType.LABEL:
                    self.parse_label(line)
                case LineType.DATA:
                    self.parse_data(line)
                case LineType.COMMAND:
                    self.parse_command(line)
                case LineType.UNKNOWN:
                    raise UnknownLineError()

    def translate_stage_2(self):
        for command in self.code:
            opcode = command["opcode"]
            assert opcode in instructions, f"Command {opcode} does not exist"
            args = instructions[opcode]["args"]
            if len(command["args"]) != 0:
                assert (
                    len(command["args"]) == args
                ), f"Wrong number of arguments for instruction {opcode}: expected {args}"
            for i in range(len(command["args"])):
                arg = command["args"][i]
                a = re.sub(r"\[|#|\]", "", arg)
                key = "arg" + str(i + 1)
                types = self.get_arg_type(a)
                expected_types = instructions[opcode][key]
                cross = types.intersection(expected_types)
                assert len(cross) != 0, f"Wrong argument for command {opcode}"
                arg_type = cross.pop()
                if arg_type == ArgType.CODE_LABEL:
                    command["args"][i] = re.sub(
                        a, hex(self.code_labels[a]), command["args"][i]
                    )
                if arg_type == ArgType.DATA_LABEL:
                    command["args"][i] = re.sub(
                        a, hex(self.data_labels[a]), command["args"][i]
                    )

    def process_addressing(self, command, command_type: Opcode):
        args = command["args"]
        word_bytes = [command_type.value, 0, 0, 0]
        first = int(args[0][1:])
        arg1 = args[1]
        if re.search(r"\[|\]", args[1]):
            word_bytes[1] += 64
            arg1 = re.sub(r"\[|\]", "", args[1])
        if arg1 in registers:
            word_bytes[1] += 128
            second = int(arg1[1:])
        else:
            second = int(args[1], 0)
        result = second + first * 2**11
        word_bytes[3] = result % 2**8
        result = result // 2**8
        word_bytes[2] = result % 2**8
        result = result // 2**8
        word_bytes[1] += result
        return struct.pack(
            "BBBB", word_bytes[0], word_bytes[1], word_bytes[2], word_bytes[3]
        )

    def process_non_addressing(self, command, command_type: Opcode):
        args = command["args"]
        word_bytes = [command_type.value, 0, 0, 0]
        arguments = [0, 0, 0]
        for i in range(len(args)):
            a = re.sub(r"\[|\]|#", "", args[i])
            if a in registers:
                word_bytes[1] += 128 // 2**i
                arguments[i] = int(a[1:])
            else:
                arguments[i] = int(a, 0)
        result = arguments[2] + arguments[1] * 2**7 + arguments[0] * 2**14
        word_bytes[3] = result % 2**8
        result = result // 2**8
        word_bytes[2] = result % 2**8
        result = result // 2**8
        word_bytes[1] += result
        return struct.pack(
            "BBBB", word_bytes[0], word_bytes[1], word_bytes[2], word_bytes[3]
        )

    def process_int_vector(self, command):
        address = int(command["args"][0], 0)
        return struct.pack(">I", address)

    def translate_stage_3(self):
        logging = ""
        binary = struct.pack(">I", len(self.data)) + struct.pack(">I", len(self.code))
        for data in self.data:
            binary += struct.pack(">I", int(data, 0))
        address = 0
        for command in self.code:
            addressing = command["opcode"] in ["ld", "st"]
            command_type: Opcode = instructions[command["opcode"]]["type"]
            if command_type == Opcode.VEC:
                result = self.process_int_vector(command)
            elif addressing:
                result = self.process_addressing(command, command_type)
            else:
                result = self.process_non_addressing(command, command_type)
            logging += (
                instructions[command["opcode"]]["log"](
                    address, result.hex(), command["args"]
                )
                + "\n"
            )
            binary += result
            address += 1
        binary += struct.pack(">I", int(self.start, 0))
        return logging, binary

    def translate(self, text):
        self.translate_stage_1(text)
        self.translate_stage_2()
        return self.translate_stage_3()


def main(source, target):
    t = Translator()
    with open(source, encoding="utf-8") as file:
        text = file.read()
    log, binary = t.translate(text)
    write_machine_code(target, binary, log)


if __name__ == "__main__":
    assert (
        len(sys.argv) == 3
    ), "Wrong arguments: translator.py <input_file> <target_file>"
    _, source, target = sys.argv
    main(source, target)

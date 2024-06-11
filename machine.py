import re
import sys

from control_unit import ControlUnit
from isa import read_machine_code


def read_from_input(data_input):
    with open(data_input, encoding="utf-8") as file:
        data = file.readlines()
    result = {1: []}
    for line in data:
        line = re.sub(r"\(|\)", "", line)
        symbol = re.search(r"(?<=').(?=')", line).group()
        line = re.sub(r"\s", "", line)
        step = line.split(",")[0]
        result[1].append((int(step), symbol))
    last_step = 1 if len(result[1]) == 0 else int(result[1][len(result[1]) - 1][0])
    result[1].append((last_step + 1000, "\0"))
    return result


def main(source, data_input):
    data, code, start = read_machine_code(source)
    data_input = read_from_input(data_input)
    cu = ControlUnit(data, code, data_input, start)
    cu.start()
    print("".join(cu.data_path.out_buffer[0]))


if __name__ == "__main__":
    assert len(sys.argv) == 3, "Wrong arguments: machine.py <source_file> <input_file>"
    _, source, data_input = sys.argv
    main(source, data_input)

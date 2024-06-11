import contextlib
import io
import logging
import os
import tempfile

import pytest

import machine as machine
import translator as translator
from isa import read_machine_code


@pytest.mark.golden_test("golden_tests/*.yml")
def test_translator_asm_and_machine(golden, caplog):
    caplog.set_level(logging.INFO)

    with tempfile.TemporaryDirectory() as tmpdirname:
        source = os.path.join(tmpdirname, "source.txt")
        input_stream = os.path.join(tmpdirname, "input.txt")
        target = os.path.join(tmpdirname, "target")

        with open(source, "w", encoding="utf-8") as file:
            file.write(golden["in_source"])
        with open(input_stream, "w", encoding="utf-8") as file:
            file.write(golden["in_stdin"])

        with contextlib.redirect_stdout(io.StringIO()) as stdout:
            translator.main(source, target)
            machine.main(target, input_stream)

        data, code, start = read_machine_code(target)

        assert str(data) == golden.out["out_data"]
        assert str(code) == golden.out["out_code"]
        assert str(start) == golden.out["out_start"]
        assert stdout.getvalue() == golden.out["out_stdout"]

        if len(caplog.text) >= 124000:
            lines = caplog.text.splitlines()[:1000]
            assert "\n".join(lines) == golden.out["out_log"]
        else:
            assert caplog.text == golden.out["out_log"]

# All functions for LLM

#
# Notes:
#
# All paths in this file should be absolute paths. However, GDB uses
# relative path, so chances are that the LLM will pass a relative path
# to the functions in this file. Therefore, the first thing to do in
# each function is to convert the relative path to an absolute path.
#

import logging
import os
import re
from tools.tools import (
    gdb_backtrace,
    gdb_frame,
    gdb_print,
    gdb_restart,
    gdb_start,
    lsp_get_function,
    lsp_get_symbol_definition,
    lsp_get_symbol_summary,
)
from tools.file_utils import file_get_content, file_get_decorated_content
from tools.lsp_integration import lsp_instance, lsp_to_abs_path, uri_to_path

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(logging.FileHandler("function.log", mode="w"))


######################################################################
# Help functions (not called by LLM)


def _to_abs_path(filename):
    """
    Convert a relative path to an absolute path. It is used by LSP functions to
    convert the relative file path in GDB to an absolute path in LSP working
    directory.
    """
    return lsp_to_abs_path(filename)


def _uri_to_path(uri):
    return uri_to_path(uri)


######################################################################
# GDB tool functions
started = False


def run_program() -> str:
    """
    Run the program to be debugged.
    If the program exited normally, return a good message.
    Otherwise, return formatted crash site and backtrace.
    """
    global started

    logger.info("CALL> run_program")

    if not started:
        response = gdb_start()
        started = True
    else:
        response = gdb_restart()

    if "exited normally" in response:
        return "[PASSED] Program exited normally."

    error = "\n".join(response.split("\n")[-3:-1])
    message = f"[FAILED] Program crashed with error:\n{error}\n"
    message += f"The stack trace is as follows with format #<frame number> in <function> (<args>) at <file>:<line>"

    backtrace = gdb_backtrace()
    # Hope this regex works.
    pattern = re.compile(
        r"#\s*(\d+)\s+0x[0-9a-fA-F]+\s+in\s+(\w+)\s*\(([^)]*)\)\s+at\s+(\S+):(\d+)"
    )
    for line in backtrace.split("\n"):
        matches = pattern.search(line)
        if matches is not None:
            frame_number = matches.group(1)
            function = matches.group(2)
            args = matches.group(3)
            filename = matches.group(4)
            line = matches.group(5)
            message += f"\n#{frame_number} in {function} ({args}) at {filename}:{line}"
    message += "\n"

    logger.info(message)

    return message


def print_value(expression: str) -> str:
    """
    Print the value of an expression in the current context.
    """
    logger.info(f"CALL> print_value({expression})")

    expression = str(expression)

    response = gdb_print(expression)
    # TODO: handle error response

    logger.info(response)

    return response


def switch_frame(frame: int) -> str:
    """
    Switch to a different stack frame.
    """
    logger.info(f"CALL> switch_frame({frame})")
    frame = int(frame)

    response = gdb_frame(frame)
    frame = response.split("\n")[0]

    pattern = re.compile(
        r"#\s*(\d+)\s+0x[0-9a-fA-F]+\s+in\s+(\w+)\s*\(([^)]*)\)\s+at\s+(\S+):(\d+)"
    )
    matches = pattern.search(frame)
    if matches is None:
        logger.error(f"Invalid frame: {frame}")
        return "Invalid frame number."

    function = matches.group(2)
    filename = _to_abs_path(matches.group(4))
    line = matches.group(5)

    message = f"Switched to frame {frame}, function {function} at {filename}:{line}.\n"
    message += file_get_content(filename, int(line), int(line))

    logger.info(message)

    return message


######################################################################
# LSP tool functions


def definition(filename: str, line: int, symbol: str) -> str:
    """
    Get the definition of a symbol at a given position.
    It only gives the one-line definition location.
    """
    logger.info(f"CALL> definition({filename}, {line}, {symbol})")

    filename = str(filename)
    line = int(line)
    symbol = str(symbol)

    filename = _to_abs_path(filename)
    definition = lsp_get_symbol_definition(filename, line, symbol)
    if definition == "":
        definition = f"Symbol {symbol} not found in {filename} around line {line}."
    # TODO: handle definition not found

    logger.info(definition)

    return definition


def summary(filename: str, line: int, symbol: str) -> str:
    """
    Get the summary of a symbol at a given position.
    It uses the "hover" feature of LSP.
    """
    logger.info(f"CALL> summary({filename}, {line}, {symbol})")
    filename = str(filename)
    line = int(line)
    symbol = str(symbol)

    filename = _to_abs_path(filename)
    summary = lsp_get_symbol_summary(filename, line, symbol)
    if summary == "":
        summary = f"Symbol {symbol} not found in {filename} around line {line}."

    logger.info(summary)

    return summary


def function_body(filename: str, function: str) -> str:
    """
    Get the body of a function.
    """
    logger.info(f"CALL> function_body({filename}, {function})")
    filename = str(filename)
    function = str(function)

    filename = _to_abs_path(filename)
    body = lsp_get_function(filename, function)
    if body == "":
        body = f"Function {function} not found in {filename}."

    logger.info(body)

    return body


######################################################################
# Miscellaneous functions
def get_file_content(filename: str, start_line: int, end_line: int) -> str:
    """
    Get the content of a file from start_line to end_line (both inclusive).
    It returns the content with decorated line number.
    """
    logger.info(f"CALL> get_file_content({filename}, {start_line}, {end_line})")
    filename = str(filename)
    start_line = int(start_line)
    end_line = int(end_line)

    filename = _to_abs_path(filename)
    content = file_get_decorated_content(filename, start_line, end_line)
    message = f"Content of {filename} from line {start_line} to {end_line}:\n{content}"

    logger.info(message)

    return message


FIX_LOCATION_OUTPUT = "locations.txt"


def set_confirm_output(filename):
    """
    Set the output file for the confirmed bug locations.
    This is not a function called by LLM. It's a configuration function.
    """
    global FIX_LOCATION_OUTPUT
    FIX_LOCATION_OUTPUT = filename


def confirm(locations: list[str]) -> str:
    """
    Confirm the locations of the bug.
    """
    logger.info(f"CALL> confirm({locations})")

    content = ""
    if locations is None or len(locations) == 0:
        content = "No bug."
    else:
        for location in locations:
            content += f"{location}\n"
    with open(FIX_LOCATION_OUTPUT, "w") as f:
        f.write(content)

    return "Confirmed. TERMINATE"

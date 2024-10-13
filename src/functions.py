# All functions for LLM

#
# Notes:
#
# All paths in this file should be absolute paths. However, GDB uses
# relative path, so chances are that the LLM will pass a relative path
# to the functions in this file. Therefore, the first thing to do in
# each function is to convert the relative path to an absolute path.
#

import json
import logging
import os
import re
from typing import List
from consts import LOCALIZATION_OUTPUT, PATCH_OUTPUT
from prompt import FL_AFTER_RUN_TO_LINE
from tools.tools import (
    editor_backup_file,
    editor_insert_after,
    editor_replace,
    editor_restore_file,
    gdb_backtrace,
    gdb_frame,
    gdb_print,
    gdb_run,
    gdb_run_to_line,
    lsp_get_function,
    lsp_get_symbol_definition,
    lsp_get_symbol_summary,
)
from tools.file_utils import file_get_content, file_get_decorated_content
from tools.lsp_integration import lsp_to_abs_path, uri_to_path

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

expected_func = None


def set_expected_function(function):
    global expected_func
    expected_func = function


def run_program() -> str:
    """
    Run the program to be debugged.
    If the program exited normally, return a good message.
    Otherwise, return formatted crash site and backtrace.
    """
    logger.info("CALL> run_program")

    response = gdb_run()

    if "exited normally" in response:
        message = "[PASSED] Program exited normally."
        logger.info(message)
        return message

    print(response)

    message = "Program crashed with error.\n"
    message += "\n".join(response.split("\n")[-3:-1])
    message += f"\nThe stack trace is as follows with format #<frame number> in <function> (<args>) at <file>:<line>\n"

    backtrace = gdb_backtrace()
    # Hope this regex works.
    pattern = re.compile(
        r"#\s*(\d+)\s+0x[0-9a-fA-F]+\s+in\s+(\w+)\s*\(([^)]*)\)\s+at\s+(\S+):(\d+)"
    )

    expected_frame = None
    for line in backtrace.split("\n"):
        matches = pattern.search(line)
        if matches is not None:
            frame_number = matches.group(1)
            function = matches.group(2)
            args = matches.group(3)
            filename = matches.group(4)
            line = matches.group(5)
            message += f"\n#{frame_number} in {function} ({args}) at {filename}:{line}"

            if expected_func is not None and expected_func in function:
                expected_frame = frame_number
            elif expected_frame is None:
                expected_frame = frame_number

            if frame_number > 10:
                message += "\nMore than 10 frames, stopping here."
    message += "\n"

    if expected_frame is not None:
        if expected_func is not None:
            message += f"The program crashed in function `{expected_func}` at frame {expected_frame} at line given below.\n"
        else:
            message += f"The program crashed at frame {expected_frame}.\n"
        old = logger.level
        logger.setLevel(logging.CRITICAL)  # supress switch_frame log
        message += switch_frame(expected_frame)
        logger.setLevel(old)

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
        return "Invalid frame number, please switch to another valid frame."

    function = matches.group(2)
    filename = _to_abs_path(matches.group(4))
    line = matches.group(5)

    message = f"Switched to frame {frame}, function {function} at {filename}:{line}.\n"
    message += file_get_decorated_content(filename, int(line), int(line))

    logger.info(message)

    return message


def run_to_line(filename: str, line: int) -> str:
    """
    Run the program to the given line by setting a breakpoint.
    FIXME: A special case is recursive function, where this only stops at
    the first call.
    """
    logger.info(f"CALL> run_to_line({filename}, {line})")

    filename = str(filename)
    line = int(line)

    filename = _to_abs_path(filename)
    response = gdb_run_to_line(filename, line)

    if "Breakpoint" in response:
        message = f"Program stopped at {filename}:{line}."
        message += "\n".join(response.split("\n")[-3:-1])
    else:
        message = f"Program crashed before {filename}:{line}."
        message += "\n".join(response.split("\n")[-3:-1])
    message += "\n"
    message += FL_AFTER_RUN_TO_LINE
    message += "\n"
    message += "Currently available stack frames:\n"
    backtrace = gdb_backtrace()
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


def confirm_location(locations: List[str], root_cause: str) -> str:
    """
    Confirm the locations of the bug.
    """
    logger.info(f"CALL> confirm_location({locations}, {root_cause})")

    content = {"root_cause": root_cause, "locations": locations}
    with open(LOCALIZATION_OUTPUT, "w") as f:
        f.write(json.dumps(content, indent=4))

    message = "Confirmed, respond with TERMINATE"

    logger.info(message)

    return message


validate_callback = None


def set_validate_callback(callback):
    global validate_callback
    validate_callback = callback


patch_count = 0


def confirm_patch(patch: dict) -> str:
    """
    Confirm the locations of the bug.
    """
    global patch_count

    logger.info(f"CALL> confirm_patch({patch})")

    with open(PATCH_OUTPUT, "w") as f:
        f.write(json.dumps(patch, indent=4))

    response = validate_callback()
    if response == None:
        message = "Valid, respond with TERMINATE"
        logger.info(message)
        return message

    patch_count += 1
    if patch_count >= 3:
        # fake a valid response
        with open(PATCH_OUTPUT, "w") as f:
            patch = {"failed": f"Failed to generate patch after {patch_count} times"}
            f.write(json.dumps(patch, indent=4))
        message = "Valid, respond with TERMINATE"
        logger.info(message)

    message = f"The patch is not valid, please generate another patch. The reason is that: {response}"
    logger.info(message)
    return message


######################################################################
# Editor functions
# These functions are not called by LLM.


def apply_patch():
    with open(PATCH_OUTPUT, "r") as f:
        patch = json.load(f)

    if not ("filename" in patch and "patch" in patch):
        return False, "Invalid patch format"

    filename = _to_abs_path(patch["filename"])
    content = patch["patch"]

    if not os.path.exists(filename):
        return False, f"File {filename} not found"
    editor_backup_file(filename)

    if "line" in patch:
        # addition
        line = patch["line"]
        editor_insert_after(filename, line, content)
    elif "start" in patch and "end" in patch:
        # modification
        start = patch["start"]
        end = patch["end"]
        editor_replace(filename, start, end, content)
    else:
        return False, "Invalid patch format"

    return True, None


def undo_patch():
    with open(PATCH_OUTPUT, "r") as f:
        patch = json.load(f)

    if not ("filename" in patch):
        return False, "Invalid patch format"

    filename = _to_abs_path(patch["filename"])
    editor_restore_file(filename)

    return True, None

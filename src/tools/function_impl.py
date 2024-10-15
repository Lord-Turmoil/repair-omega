import os
import re
from tools.lsp_integration import lsp_to_abs_path


def to_abs_path(logger, filename):
    """
    Convert a relative path to an absolute path. It is used by LSP functions to
    convert the relative file path in GDB to an absolute path in LSP working
    directory.
    """
    path, cwd = lsp_to_abs_path(filename)
    if os.path.exists(path):
        return path
    basename = os.path.basename(filename)
    # search for the file under cwd
    for root, _, files in os.walk(cwd):
        if basename in files:
            return os.path.join(root, basename)
    # failed to find the file
    logger.error(f"File {filename} not found under {cwd}")
    return filename


def parse_stackframe(frame):
    pattern_1 = re.compile(
        r"#\s*(\d+)\s+0x[0-9a-fA-F]+\s+in\s+(\w+)\s*\(([^)]*)\)\s+at\s+(\S+):(\d+)"
    )
    pattern_2 = re.compile(r"#(\d+)\s+(\w+)\s*\((.*?)\)\s+at\s+([\w\.\-]+):(\d+)")

    matches = pattern_1.search(frame)
    if matches is None:
        matches = pattern_2.search(frame)
    if matches is None:
        return None, None, None, None, None
    frame_number = matches.group(1)
    function = matches.group(2)
    args = matches.group(3)
    filename = matches.group(4)
    line = matches.group(5)

    return int(frame_number), function, args, filename, int(line)


def _parse_address_sanitizer_stackframe(frame):
    pattern = re.compile(
        r"#(\d+)\s+(0x[0-9a-fA-F]+)\s+in\s+(\w+)\s+([\w/.\-]+):(\d+):(\d+)"
    )
    matches = pattern.search(frame)
    if matches is None:
        return None, None, None, None
    frame_number = matches.group(1)
    function = matches.group(3)
    filename = matches.group(4)
    line = matches.group(5)
    return int(frame_number), function, filename, int(line)


def _parse_undefined_sanitizer_stackframe(frame):
    pattern = re.compile(r"^([^:]+):(\d+):(\d+):\sruntime error:\s(.+)$")
    matches = pattern.search(frame)
    if matches is None:
        return None, None, None
    filename = matches.group(1)
    line = matches.group(2)
    message = matches.group(4)

    return filename, int(line), message


def _extract_address_sanitizer_error(logger, response, expected_func):
    # find the first error
    pos1 = response.find("==ERROR")
    if pos1 == -1:
        message = "Sanitizer error message not found."
        logger.error(message)
        return None, None, message

    # find the first frame
    pos2 = response.find("#0", pos1)
    if pos2 == -1:
        message = "Sanitizer frame not found."
        logger.error(message)
        return None, None, message

    message = response[pos1:pos2].replace("\n", "").strip()

    message += f"\n\nThe stack trace is as follows with format #<frame number> in <function> at <file>:<line>"
    backtrace = response[pos2:].split("\n")
    expected_frame = None
    expected_filename = None
    expected_line = None
    for trace in backtrace:
        if trace == "":
            # error will end with an empty line
            break
        frame_number, function, filename, line = _parse_address_sanitizer_stackframe(
            trace
        )
        if frame_number is None:
            continue
        message += f"\n#{frame_number} in {function} at {filename}:{line}"
        if expected_func is not None and expected_func in function:
            expected_frame = frame_number
            expected_filename = filename
            expected_line = line
        elif expected_frame is None:
            expected_frame = frame_number
            expected_filename = filename
            expected_line = line
        if frame_number > 20:
            message += "\nMore than 20 frames, stopping here."

    return expected_filename, expected_line, message


def _extract_undefined_sanitizer_error(logger, response, expected_func):
    for line in response.split("\n"):
        expected_filename, expected_line, message = (
            _parse_undefined_sanitizer_stackframe(line)
        )
        if expected_filename is not None:
            return expected_filename, expected_line, message
    return None, None, None


def extract_sanitizer_error(logger, response, expected_func):
    expected_filename, expected_line, message = _extract_address_sanitizer_error(
        logger, response, expected_func
    )
    if expected_filename is None:
        expected_filename, expected_line, message = _extract_undefined_sanitizer_error(
            logger, response, expected_func
        )
    return expected_filename, expected_line, message

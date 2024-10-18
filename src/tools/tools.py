from tools.gdb_integration import gdb_instance
from tools.file_utils import (
    file_get_decorated_content,
    file_get_content,
    file_get_line_count,
)
from tools.lsp_integration import lsp_instance, uri_to_path

######################################################################
# LSP functions


def _get_fuzzy_position(filename, lineno, symbol):
    FUZZY_RANGE = 10
    line_count = file_get_line_count(filename)

    lines_to_search = [lineno]
    for i in range(1, FUZZY_RANGE + 1):
        if lineno - i > 0:
            lines_to_search.append(lineno - i)
        if lineno + i <= line_count:
            lines_to_search.append(lineno + i)
    for i in lines_to_search:
        line = file_get_content(filename, i, i)
        pos = line.find(symbol)
        if pos != -1:
            # replace tabs with spaces
            char = pos + len(symbol) + 1
            return i, char
    return None, None


def lsp_get_symbol_definition(filename, lineno, symbol):
    """
    Get the definition of a symbol at a given position.
    Will perform a fuzzy search around the line.
    """
    lsp = lsp_instance()
    line, char = _get_fuzzy_position(filename, lineno, symbol)
    if line is None:
        return f"Symbol {symbol} not found in {filename} around line {lineno}."
    response = lsp.definition(filename, line, char)
    if response is None:
        return (
            f"Definition of {symbol} not available in {filename} around line {lineno}."
        )
    file = uri_to_path(response["uri"])
    start_line = response["range"]["start"]["line"] + 1
    end_line = response["range"]["end"]["line"] + 1
    return file_get_decorated_content(file, start_line, end_line)


def lsp_get_symbol_summary(filename, lineno, symbol):
    """
    Get the hover information of a symbol at a given position.
    Will perform a fuzzy search around the line.
    """
    lsp = lsp_instance()
    line, char = _get_fuzzy_position(filename, lineno, symbol)
    if line is None:
        return f"Symbol {symbol} not found in {filename} around line {lineno}."
    response = lsp.summary(filename, line, char)
    if response is None:
        return f"Summary of {symbol} not available in {filename} around line {lineno}."
    return response["contents"]["value"]


def lsp_get_function(filename, function):
    """
    Get the function definition.
    """
    lsp = lsp_instance()
    symbols = lsp.document_symbol(filename)
    body = ""
    size = 0
    for symbol in symbols:
        if symbol["name"] == function:
            start_line = symbol["location"]["range"]["start"]["line"] + 1
            end_line = symbol["location"]["range"]["end"]["line"] + 1
            if end_line - start_line + 1 > size:
                size = end_line - start_line
                body = file_get_decorated_content(filename, start_line, end_line)
    return body


######################################################################
# GDB functions


def gdb_run():
    gdb = gdb_instance()
    if gdb.is_running():
        gdb.kill()
    return gdb.run()


def gdb_run_sanitizer():
    return gdb_instance().run_sanitizer()


def gdb_backtrace():
    return gdb_instance().backtrace()


def gdb_frame(frame):
    return gdb_instance().frame(frame)


def gdb_run_to_line(file, line, to_line=None):
    """
    In case the line is not reachable, specify to_line to add breakpoints
    to every line from line to to_line.
    """
    gdb = gdb_instance()
    if gdb.is_running():
        gdb.kill()

    gdb.set_breakpoint(file, line)
    if to_line is not None:
        for i in range(line + 1, to_line + 1):
            gdb.set_breakpoint(file, i)
    response = gdb.run()
    gdb.clear_breakpoints()

    return response


def gdb_print(expression):
    return gdb_instance().print(expression)


######################################################################
# Editor functions

FILE_BACKUPS = {}


def editor_backup_file(filename: str) -> None:
    """
    Backup the given file.
    """
    global FILE_BACKUPS
    with open(filename, "r") as f:
        FILE_BACKUPS[filename] = f.read()


def editor_restore_file(filename: str) -> None:
    """
    Restore the given file.
    """
    content = FILE_BACKUPS.get(filename, None)
    if content is None:
        raise FileNotFoundError(f"File {filename} not found in backups.")
    with open(filename, "w") as f:
        f.write(content)


def editor_replace(
    filename: str, start_line: int, end_line: int, new_content: str
) -> None:
    """
    Replace lines from start_line to end_line (inclusive) with new_content.
    """
    with open(filename, "r") as f:
        lines = f.readlines()
    new_lines = [line + "\n" for line in new_content.split("\n")]
    lines = lines[: start_line - 1] + new_lines + lines[end_line:]
    with open(filename, "w") as f:
        f.write("".join(lines))


def editor_insert_after(filename: str, line: int, new_content: str) -> None:
    """
    Insert new_content after the given line.
    """
    with open(filename, "r") as f:
        lines = f.readlines()
    new_lines = [line + "\n" for line in new_content.split("\n")]
    lines = lines[:line] + new_lines + lines[line:]
    with open(filename, "w") as f:
        f.write("".join(lines))

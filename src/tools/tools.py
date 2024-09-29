from tools.gdb_integration import gdb_instance
from tools.file_utils import file_get_decorated_content, file_get_content
from tools.lsp_integration import lsp_instance

######################################################################
# LSP functions


def lsp_get_symbol_definition(filename, line, symbol):
    """
    Get the definition of a symbol at a given position.
    Will perform a fuzzy search around the line.
    """
    lsp = lsp_instance()
    content = file_get_content(filename, line - 3, line + 3)
    for i, line in enumerate(content.split("\n"), max(1, line - 3)):
        pos = line.find(symbol)
        if pos != -1:
            response = lsp.definition(filename, i, pos + 1)
            start_line = response["range"]["start"]["line"] + 1
            end_line = response["range"]["end"]["line"] + 1
            return file_get_decorated_content(filename, start_line, end_line)
    return ""


def lsp_get_symbol_summary(filename, line, symbol):
    """
    Get the hover information of a symbol at a given position.
    Will perform a fuzzy search around the line.
    """
    lsp = lsp_instance()
    content = file_get_content(filename, line - 3, line + 3)
    for i, line in enumerate(content.split("\n"), max(1, line - 3)):
        pos = line.find(symbol)
        if pos != -1:
            response = lsp.summary(filename, i, pos + 1)
            return response["contents"]["value"]
    return ""


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


def gdb_start():
    gdb = gdb_instance()
    gdb.start()
    return gdb.run()


def gdb_restart():
    gdb = gdb_instance()
    gdb.kill()
    return gdb.run()


def gdb_backtrace():
    return gdb_instance().backtrace()


def gdb_frame(frame):
    return gdb_instance().frame(frame)


def gdb_print(expression):
    return gdb_instance().print(expression)

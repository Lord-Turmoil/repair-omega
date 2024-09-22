import json
import os
import subprocess

from tools.file_utils import get_file_content


def _to_lsp_request(id, method, params):
    request = {"jsonrpc": "2.0", "id": id, "method": method}
    if params:
        request["params"] = params

    content = json.dumps(request)
    header = f"Content-Length: {len(content)}\r\n\r\n"
    return (header + content).encode("utf-8")


def _to_lsp_notification(method, params):
    request = {"jsonrpc": "2.0", "method": method}
    if params:
        request["params"] = params

    content = json.dumps(request)
    header = f"Content-Length: {len(content)}\r\n\r\n"
    return (header + content).encode("utf-8")


def _parse_lsp_response(id, file):
    while True:
        header = {}
        while True:
            line = file.readline().decode("utf-8").strip()
            if not line:
                break
            key, value = line.split(":", 1)
            header[key.strip()] = value.strip()

        content = file.read(int(header["Content-Length"])).decode("utf-8")
        response = json.loads(content)
        if "id" in response and response["id"] == id:
            return response


def path_to_uri(path):
    return f"file://{path}"


def uri_to_path(uri):
    return uri[7:]


def is_lsp_available(executable="clangd"):
    try:
        lsp = subprocess.run(
            [executable, "--version"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return lsp.returncode == 0
    except FileNotFoundError:
        return False


class LspController:
    def __init__(
        self,
        executable="clangd",
        cwd=os.getcwd(),
        stderr=subprocess.DEVNULL,
    ) -> None:
        self.id = 0
        self.cwd = cwd
        self._process = subprocess.Popen(
            [executable],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=stderr,
            cwd=cwd,
        )
        self.initialize()

    def initialize(self):
        self.id += 1
        request = _to_lsp_request(self.id, "initialize", {"processId": os.getpid()})
        self._process.stdin.write(request)
        self._process.stdin.flush()
        return _parse_lsp_response(self.id, self._process.stdout)

    def didOpen(self, filename):
        """
        Open a file in the language server.
        """
        _, ext = os.path.splitext(filename)
        languageId = "c" if ext == ".c" else "cpp"

        with open(filename, "r") as file:
            text = file.read()

        notification = _to_lsp_notification(
            "textDocument/didOpen",
            {
                "textDocument": {
                    "uri": path_to_uri(filename),
                    "languageId": languageId,
                    "text": text,
                }
            },
        )
        self._process.stdin.write(notification)
        self._process.stdin.flush()

        # notification has no response
        return None

    def didClose(self, filename):
        """
        Close a file in the language server.
        Should use this and didOpen in pair.
        """
        notification = _to_lsp_notification(
            "textDocument/didClose",
            {"textDocument": {"uri": path_to_uri(filename)}},
        )
        self._process.stdin.write(notification)
        self._process.stdin.flush()

    def definition(self, filename, line, character):
        """
        Get the definition of a symbol at a given position.
        Must call didOpen on the file before calling this method.
        """
        self.id += 1
        request = _to_lsp_request(
            self.id,
            "textDocument/definition",
            {
                "textDocument": {"uri": path_to_uri(filename)},
                "position": {
                    "line": line - 1,
                    "character": character - 1,
                },
            },
        )
        self._process.stdin.write(request)
        self._process.stdin.flush()
        return _parse_lsp_response(self.id, self._process.stdout)

    def hover(self, filename, line, character):
        """
        Get the hover information at a given position.
        """
        self.id += 1
        request = _to_lsp_request(
            self.id,
            "textDocument/hover",
            {
                "textDocument": {"uri": path_to_uri(filename)},
                "position": {
                    "line": line - 1,
                    "character": character - 1,
                },
            },
        )
        self._process.stdin.write(request)
        self._process.stdin.flush()
        return _parse_lsp_response(self.id, self._process.stdout)

    def documentSymbol(self, filename):
        """
        Get all symbols in the document. It only get top-level symbols such as
        functions and classes.
        """
        self.id += 1
        request = _to_lsp_request(
            self.id,
            "textDocument/documentSymbol",
            {"textDocument": {"uri": path_to_uri(filename)}},
        )
        self._process.stdin.write(request)
        self._process.stdin.flush()
        return _parse_lsp_response(self.id, self._process.stdout)

    def exit(self):
        self._process.terminate()


class LspWrapper:
    def __init__(self, executable="clangd", cwd=os.getcwd()):
        if not is_lsp_available(executable):
            raise FileNotFoundError(f"{executable} is not available")
        self._controller = LspController(executable, cwd)

    def definition(self, filename, line, character):
        self._controller.didOpen(filename)
        response = self._controller.definition(filename, line, character)
        self._controller.didClose(filename)

        if len(response["result"]) == 0:
            return None
        return response["result"][0]

    def summary(self, filename, line, character):
        self._controller.didOpen(filename)
        response = self._controller.hover(filename, line, character)
        self._controller.didClose(filename)

        return response["result"]

    def document_symbol(self, filename):
        self._controller.didOpen(filename)
        response = self._controller.documentSymbol(filename)
        self._controller.didClose(filename)

        return response["result"]

    def exit(self):
        self._controller.exit()


class LspWrapperFactory:
    def __init__(self, executable="clangd", cwd=os.getcwd()) -> None:
        self._executable = executable
        self._cwd = cwd
        self._instance: LspWrapper = None

    def _create(self):
        return LspWrapper(self._executable, self._cwd)

    def get(self):
        if self._instance is None:
            self._instance = self._create()
        return self._instance

    def respawn(self):
        self._instance.exit()
        self._instance = None


######################################################################
# LSP instance management
LSP_FACTORY = None


def lsp_init(executable="clangd", cwd=os.getcwd()):
    global LSP_FACTORY
    if LSP_FACTORY is not None:
        LSP_FACTORY.respawn()
    LSP_FACTORY = LspWrapperFactory(executable, cwd)
    return LSP_FACTORY


def lsp_instance():
    if LSP_FACTORY is not None:
        return LSP_FACTORY.get()
    raise Exception("LSP not initialized")


def lsp_respawn():
    if LSP_FACTORY is None:
        raise Exception("LSP not initialized")
    LSP_FACTORY.respawn()


def lsp_exit():
    lsp_respawn()

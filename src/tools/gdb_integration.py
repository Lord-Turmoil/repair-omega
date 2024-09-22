from pygdbmi.gdbcontroller import GdbController
import os


def _parse_gdb_output(output):
    response = ""
    for message in output:
        if message["type"] == "console":
            response += message["payload"]
    return response


class GdbWrapper:
    def __init__(self, executable, cwd=os.getcwd()) -> None:
        self._controller = GdbController()
        self._executable = os.path.join(cwd, executable)
        self._cwd = cwd

    def start(self):
        return _parse_gdb_output(
            self._controller.write(f"-file-exec-and-symbols {self._executable}")
        )

    def run(self):
        return _parse_gdb_output(self._controller.write("run"))

    def backtrace(self):
        return _parse_gdb_output(self._controller.write("backtrace"))

    def frame(self, frame):
        return _parse_gdb_output(self._controller.write(f"frame {frame}"))

    def print(self, expression):
        return _parse_gdb_output(self._controller.write(f"print {expression}"))

    def kill(self):
        return self._controller.write("kill")

    def exit(self):
        self.kill()
        self._controller.exit()

    def to_abs_path(self, filename):
        if not filename.startswith(self._cwd):
            return os.path.join(self._cwd, filename)
        return filename


class GdbWrapperFactory:
    def __init__(self, executable, cwd=os.getcwd()) -> None:
        self._executable = executable
        self._cwd = cwd
        self._instance: GdbWrapper = None

    def _create(self):
        return GdbWrapper(self._executable, self._cwd)

    def get(self):
        if self._instance is None:
            self._instance = self._create()
        return self._instance

    def respawn(self):
        self._instance.exit()
        self._instance = None


######################################################################
# GDB instance management

GDB_FACTORY = None


def gdb_init(executable, cwd=os.getcwd()):
    global GDB_FACTORY
    if GDB_FACTORY is not None:
        GDB_FACTORY.respawn()
    GDB_FACTORY = GdbWrapperFactory(executable, cwd)


def gdb_instance():
    if GDB_FACTORY is not None:
        return GDB_FACTORY.get()
    raise Exception("GDB not initialized")


def gdb_respawn():
    if GDB_FACTORY is None:
        raise Exception("GDB not initialized")
    GDB_FACTORY.respawn()


def gdb_exit():
    gdb_respawn()


def gdb_to_abs_path(filename):
    gdb_instance().to_abs_path(filename)

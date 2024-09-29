import logging
from typing import Dict, List
from pygdbmi.gdbcontroller import GdbController
import os

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(logging.FileHandler("gdb.log", "w"))


def _parse_gdb_output(output):
    response = ""
    for message in output:
        if message["type"] == "console":
            response += message["payload"]
    return response


class GdbWrapper:
    def __init__(
        self, executable, args: List[str], env: Dict[str, str], cwd=os.getcwd()
    ) -> None:
        assert os.path.exists(cwd)
        assert os.path.exists(executable)

        self._controller = GdbController()
        self._executable = executable
        self._args = args
        self._env = env
        self._cwd = cwd

    def _execute(self, cmd):
        logger.info(cmd)
        output = _parse_gdb_output(self._controller.write(cmd))
        logger.info(output)
        return output

    def start(self):
        return self._execute(f"-file-exec-and-symbols {self._executable}")

    def run(self):
        for key, value in self._env.items():
            self._execute(f"set environment {key}={value}")
        cmd = "run"
        for arg in self._args:
            cmd += f" {arg}"
        return self._execute(cmd)

    def backtrace(self):
        return self._execute("backtrace")

    def frame(self, frame):
        return self._execute(f"frame {frame}")

    def print(self, expression):
        return self._execute(f"print {expression}")

    def kill(self):
        return self._execute("kill")

    def exit(self):
        self.kill()
        self._controller.exit()


class GdbWrapperFactory:
    def __init__(
        self, executable, args: List[str], env: Dict[str, str], cwd=os.getcwd()
    ) -> None:
        self._executable = executable
        self._args = args
        self._env = env
        self._cwd = cwd
        self._instance: GdbWrapper = None

    def _create(self):
        return GdbWrapper(self._executable, self._args, self._env, self._cwd)

    def get(self):
        if self._instance is None:
            self._instance = self._create()
        return self._instance

    def respawn(self):
        if self._instance is not None:
            self._instance.exit()
        self._instance = None


######################################################################
# GDB instance management

GDB_FACTORY = None


def gdb_init(executable, args=[], env={}, cwd=os.getcwd()):
    global GDB_FACTORY
    if GDB_FACTORY is not None:
        GDB_FACTORY.respawn()
    GDB_FACTORY = GdbWrapperFactory(executable, args, env, cwd)


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

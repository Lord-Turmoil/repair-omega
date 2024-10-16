import logging
from arguments import parse_args_validate
from functions import run_program, set_run_mode
from tools.lsp_integration import lsp_exit, lsp_init
from tools.gdb_integration import gdb_exit, gdb_init
import subprocess
import coloredlogs

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())
logger.addHandler(logging.FileHandler("validate.log", "w"))
coloredlogs.install(level="DEBUG", logger=logger)


def test_build(profile):
    build = subprocess.run(
        profile["build"],
        cwd=profile["sandbox"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
    )
    if build.returncode == 0:
        return True, ""
    logger.error("Failed to build project")

    return False, build.stderr.decode("utf-8")


def test_run(profile):
    result = run_program()
    if "[PASSED]" in result:
        return True, ""
    return False, result


def validate(profile):
    """
    Validate the patch by building the project.
    """
    logger.info("Validating patch")

    status, result = test_build(profile)
    if status:
        status, result = test_run(profile)
        if status:
            return None
        else:
            result = f"The program still crashes: {result}"
            logger.error(result)
    else:
        result = f"Patch is syntactically invalid: {result}"
        logger.error(result)

    return result


if __name__ == "__main__":
    args, profile, _ = parse_args_validate()

    logger.info("Initializing GDB")
    gdb_init(
        profile["run"],
        profile["args"],
        profile["env"],
        profile["work"],
    )
    logger.info("Initializing LSP")
    lsp_init(cwd=profile["sandbox"])

    set_run_mode(profile["mode"])

    message = validate(profile)
    result = ""
    if message is None:
        logger.info("Patch is valid")
        result = "valid"
    else:
        logger.error(f"Patch is invalid: {message}")
        result = "invalid"
    with open("vd.log", "w") as f:
        f.write(result)

    gdb_exit()
    lsp_exit()

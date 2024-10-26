import os
import shutil

from agent.functions import set_run_mode, test_build, test_run, validate
from shared.arguments import parse_args_validate
from shared.utils import get_logger
from tools.gdb_integration import gdb_exit, gdb_init
from tools.lsp_integration import lsp_exit, lsp_init

logger = get_logger(__name__, log_file="validate.log")


def keep_log(profile):
    if not os.path.exists(f"log/{profile['profile']}"):
        os.makedirs(f"log/{profile['profile']}")
    shutil.copyfile("validate.log", f"log/{profile['profile']}/validate.log")


def validate_patch(profile):
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
        logger.error(f"{result}: {message}")


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

    message = validate_patch(profile)
    result = ""
    if message is None:
        logger.info("Patch is valid")
        result = "valid"
    else:
        logger.error(f"Patch is invalid: {message}")
        result = "invalid"
    with open("validate.lock", "w") as f:
        f.write(result)

    logger.info("Exiting GDB")
    gdb_exit()
    logger.info("Exiting LSP")
    lsp_exit()

    if args.keep:
        keep_log(profile)

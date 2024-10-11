import json
import logging
import os
from arguments import parse_args_pg
from consts import PATCH_INPUT, PATCH_OUTPUT, PATCH_SNAPSHOT
from functions import apply_patch, run_program, set_validate_callback, undo_patch
from tools.gdb_integration import gdb_exit, gdb_init
from tools.lsp_integration import lsp_exit, lsp_init
from agent import agent_init_pg
import shutil
import subprocess
from prompt import PG_CONSTRAINT, PG_INITIAL_MESSAGE

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())
logger.addHandler(logging.FileHandler("pg.log", "w"))


def load_locations(profile):
    with open(PATCH_INPUT, "r") as f:
        locations = json.load(f)
    return locations


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

    status, message = apply_patch()
    if not status:
        logger.error(f"Failed to apply patch: {message}")
        return message

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

    status, message = undo_patch()
    if not status:
        logger.error(f"Failed to undo patch: {message}")
        return message

    return result


def keep_log(profile):
    if not os.path.exists(f"log/{profile['profile']}"):
        os.makedirs(f"log/{profile['profile']}")

    shutil.copyfile(PATCH_SNAPSHOT, f"log/{profile['profile']}/{PATCH_SNAPSHOT}")
    shutil.copyfile("pg.log", f"log/{profile['profile']}/pg.log")
    shutil.copyfile("function.log", f"log/{profile['profile']}/pg_function.log")
    shutil.copyfile(PATCH_OUTPUT, f"log/{profile['profile']}/{PATCH_OUTPUT}")


if __name__ == "__main__":
    args, profile, llm_config = parse_args_pg()

    # log of essential information
    snapshot = {"profile": profile}

    locations = load_locations(profile)
    snapshot["locations"] = locations

    logger.info("Initializing GDB")
    gdb_init(
        profile["run"],
        profile["args"],
        profile["env"],
        profile["work"],
    )

    logger.info("Initializing LSP")
    lsp_init(cwd=profile["sandbox"])

    logger.info("Initializing agent")
    assistant, user_proxy, system_message = agent_init_pg(llm_config)

    logger.info("Initiating chat")
    initial = PG_INITIAL_MESSAGE.format(locations["root_cause"])
    for location in locations["locations"]:
        initial += "\n" + location
    if profile["constraint"]:
        initial += "\n" + PG_CONSTRAINT.format(profile["constraint"])

    # set validate callback
    set_validate_callback(lambda: validate(profile))

    chat_result = None
    try:
        chat_result = user_proxy.initiate_chat(
            assistant,
            message=initial,
        )
    except Exception as e:
        logger.error(f"Chat terminated with exception: {e}")
    finally:
        # keep the log even if the chat aborts
        chat_log = {"system": system_message}
        if chat_result:
            chat_log["history"] = chat_result.chat_history
            chat_log["cost"] = chat_result.cost
        else:
            chat_log["history"] = "Chat aborted"
            chat_log["cost"] = "N/A"

        snapshot["dialog"] = chat_log

        with open(PATCH_OUTPUT, "r") as f:
            patch = f.read()
        snapshot["patch"] = json.loads(patch)

        with open(PATCH_SNAPSHOT, "w") as f:
            f.write(json.dumps(snapshot, indent=4))

        if args.keep:
            keep_log(profile)

    # Terminate GDB and LSP.
    gdb_exit()
    lsp_exit()

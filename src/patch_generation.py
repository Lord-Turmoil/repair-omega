import json
import os
import shutil

from agent.agent import agent_init_pg
from agent.functions import set_validate_callback, validate
from shared.arguments import parse_args_pg
from shared.consts import PATCH_INPUT, PATCH_OUTPUT, PATCH_SNAPSHOT
from shared.prompt import PG_CONSTRAINT, PG_INITIAL_MESSAGE
from shared.utils import get_duration, get_logger
from tools.gdb_integration import gdb_exit, gdb_init
from tools.lsp_integration import lsp_exit, lsp_init

logger = get_logger(__name__, log_file="pg.log")


def load_locations():
    if not os.path.exists(PATCH_INPUT):
        logger.error("No fix locations provided")
        exit(1)

    with open(PATCH_INPUT, "r") as f:
        locations = json.load(f)

    if locations["root_cause"] is None or len(locations["locations"]) == 0:
        logger.error("No need for patching")
        exit(0)

    return locations


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

    locations = load_locations()
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
    assistant, user_proxy, system_message = agent_init_pg(llm_config, profile)

    logger.info("Initiating chat")
    initial = PG_INITIAL_MESSAGE.format(
        locations["root_cause"], "\n".join(locations["locations"])
    )
    if profile["constraint"]:
        initial += "\n" + PG_CONSTRAINT.format(profile["constraint"])

    # set validate callback
    set_validate_callback(lambda: validate(logger, profile))

    chat_result = None
    try:
        chat_result = user_proxy.initiate_chat(
            assistant,
            message=initial,
        )
        print("")
    except Exception as e:
        logger.error(f"Chat terminated with exception: {e}")
        snapshot["error"] = str(e)
    finally:
        logger.info("Chat terminated")
        # keep the log even if the chat aborts
        chat_log = {"system": system_message}
        if chat_result:
            chat_log["history"] = chat_result.chat_history
            chat_log["cost"] = chat_result.cost
        else:
            chat_log["history"] = "Chat aborted"
            chat_log["cost"] = "N/A"

        snapshot["dialog"] = chat_log

        if os.path.exists(PATCH_OUTPUT):
            with open(PATCH_OUTPUT, "r") as f:
                patch = f.read()
        else:
            patch = {"failed": "Failed to generate patch, see snapshot['error']"}
        snapshot["patch"] = json.loads(patch)

        snapshot["duration"] = "{:.2f}s".format(get_duration(profile))
        with open(PATCH_SNAPSHOT, "w") as f:
            f.write(json.dumps(snapshot, indent=4))

    # Terminate GDB and LSP.
    logger.info("Exiting GDB")
    gdb_exit()
    logger.info("Exiting LSP")
    lsp_exit()

    if args.keep:
        keep_log(profile)

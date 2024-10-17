import json
import logging
import os
from arguments import parse_args_co
from consts import CO_OUTPUT, CO_SNAPSHOT
from functions import function_body, get_full_path, set_validate_callback
from tools.gdb_integration import gdb_exit, gdb_init
from patch_generation import validate
from tools.lsp_integration import lsp_exit, lsp_init
from agent import agent_init_co
import shutil
from prompt import CO_CONSTRAINT, CO_INITIAL_MESSAGE
import coloredlogs

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())
logger.addHandler(logging.FileHandler("co.log", "w"))
coloredlogs.install(level="DEBUG", logger=logger)


def keep_log(profile):
    if not os.path.exists(f"log/{profile['profile']}"):
        os.makedirs(f"log/{profile['profile']}")

    shutil.copyfile(CO_SNAPSHOT, f"log/{profile['profile']}/{CO_SNAPSHOT}")
    shutil.copyfile("co.log", f"log/{profile['profile']}/co.log")
    shutil.copyfile("function.log", f"log/{profile['profile']}/co_function.log")
    shutil.copyfile(CO_OUTPUT, f"log/{profile['profile']}/{CO_OUTPUT}")


if __name__ == "__main__":
    args, profile, llm_config = parse_args_co()

    # log of essential information
    snapshot = {"profile": profile}

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
    assistant, user_proxy, system_message = agent_init_co(llm_config, profile)

    assert profile["file"]
    assert profile["function"]

    filename = get_full_path(profile["file"])
    function = function_body(filename, profile["function"])

    logger.info("Initiating chat")
    initial = CO_INITIAL_MESSAGE.format(filename, function)
    if profile["constraint"]:
        initial += "\n" + CO_CONSTRAINT.format(profile["constraint"])

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

        with open(CO_OUTPUT, "r") as f:
            patch = f.read()
        snapshot["patch"] = json.loads(patch)

        with open(CO_SNAPSHOT, "w") as f:
            f.write(json.dumps(snapshot, indent=4))

    logger.info("Exiting GDB")
    gdb_exit()
    logger.info("Exiting LSP")
    lsp_exit()

    if args.keep:
        keep_log(profile)

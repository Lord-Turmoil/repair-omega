import json
import os
import shutil

from agent.agent import agent_init_fl
from shared.arguments import parse_args_fl
from shared.consts import LOCALIZATION_OUTPUT, LOCALIZATION_SNAPSHOT
from shared.prompt import FL_CONSTRAINT, FL_IGNORE_LOCATIONS, FL_INITIAL_MESSAGE
from shared.utils import get_duration, get_logger
from tools.gdb_integration import gdb_exit, gdb_init
from tools.lsp_integration import lsp_exit, lsp_init

logger = get_logger(__name__, log_file="fl.log")


def load_locations():
    if not os.path.exists(LOCALIZATION_OUTPUT):
        logger.error("No fix locations provided")
        exit(1)

    with open(LOCALIZATION_OUTPUT, "r") as f:
        locations = json.load(f)

    if locations["root_cause"] is None or len(locations["locations"]) == 0:
        logger.warning("No need for fix localization")
        exit(0)

    return locations


def keep_log(profile):
    if not os.path.exists(f"log/{profile['profile']}"):
        os.makedirs(f"log/{profile['profile']}")

    shutil.copyfile(
        LOCALIZATION_SNAPSHOT, f"log/{profile['profile']}/{LOCALIZATION_SNAPSHOT}"
    )
    shutil.copyfile("fl.log", f"log/{profile['profile']}/fl.log")
    shutil.copyfile("function.log", f"log/{profile['profile']}/fl_function.log")
    shutil.copyfile("gdb.log", f"log/{profile['profile']}/gdb.log")
    shutil.copyfile(
        LOCALIZATION_OUTPUT, f"log/{profile['profile']}/{LOCALIZATION_OUTPUT}"
    )


if __name__ == "__main__":
    args, profile, llm_config = parse_args_fl()

    # log of essential information
    snapshot = {"profile": profile}

    locations = None
    if profile["rerun"]:
        logger.warning("Rerun requested")
        locations = load_locations()

    if not os.path.exists(profile["run"]):
        logger.error(f"Executable {profile['run']} not found, forget to build?")
        exit(1)

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
    assistant, user_proxy, system_message = agent_init_fl(llm_config, profile)

    logger.info("Initiating chat")
    initial = FL_INITIAL_MESSAGE
    if profile["constraint"] is not None:
        initial += "\n" + FL_CONSTRAINT.format(profile["constraint"])
    if locations is not None:
        ignored = "\n".join(locations["locations"])
        initial += "\n" + FL_IGNORE_LOCATIONS.format(ignored)

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
        if chat_result is not None:
            chat_log["history"] = chat_result.chat_history
            chat_log["cost"] = chat_result.cost
        else:
            chat_log["history"] = "Chat aborted"
            chat_log["cost"] = "N/A"

        snapshot["dialog"] = chat_log

        if os.path.exists(LOCALIZATION_OUTPUT):
            with open(LOCALIZATION_OUTPUT, "r") as f:
                locations = json.load(f)
        else:
            locations = {
                "root_cause": None,
                "locations": [],
                "error": "Failed to generate fix locations, see snapshot['error']",
            }
        snapshot["locations"] = locations

        snapshot["duration"] = "{:.2f}s".format(get_duration(profile))
        with open(LOCALIZATION_SNAPSHOT, "w") as f:
            f.write(json.dumps(snapshot, indent=4))

    # Terminate GDB and LSP.
    logger.info("Exiting GDB")
    gdb_exit()
    logger.info("Exiting LSP")
    lsp_exit()

    if args.keep:
        keep_log(profile)

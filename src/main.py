import json
import logging
import os
from arguments import parse_args
from functions import set_confirm_output
from prompt import CONSTRAINT, INITIAL_MESSAGE, SYSTEM_MESSAGE_WITHOUT_DBG
from tools.lsp_integration import lsp_exit, lsp_init
from tools.gdb_integration import gdb_exit, gdb_init
from agent import agent_init
import shutil
import subprocess
from prompt import SYSTEM_MESSAGE_WITH_DBG

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())
logger.addHandler(logging.FileHandler("log.log", "w"))


def prepare_sandbox(profile):
    if os.path.exists(profile["sandbox"]):
        shutil.rmtree(profile["sandbox"])
    shutil.copytree(profile["project"], profile["sandbox"])


def prepare_work(profile):
    if os.path.exists(profile["work"]):
        shutil.rmtree(profile["work"])
    os.makedirs(profile["work"])
    if profile["init"]:
        for root, _, files in os.walk(profile["init"]):
            for file in files:
                shutil.copy2(os.path.join(root, file), profile["work"])


def build_project(profile):
    build = subprocess.run(
        profile["build"],
        cwd=profile["sandbox"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
    )
    if build.returncode != 0:
        logger.error("Failed to build project")
        logger.error(build.stderr.decode("utf-8"))
        exit(1)


def keep_log(profile):
    if not os.path.exists(f"log/{profile['profile']}"):
        os.makedirs(f"log/{profile['profile']}")
    shutil.copyfile("dialog.json", f"log/{profile['profile']}/dialog.json")
    shutil.copyfile("log.log", f"log/{profile['profile']}/log.log")
    shutil.copyfile("function.log", f"log/{profile['profile']}/function.log")
    shutil.copyfile("gdb.log", f"log/{profile['profile']}/gdb.log")
    shutil.copyfile(profile["output"], f"log/{profile['profile']}/locations.txt")


if __name__ == "__main__":
    args, profile, llm_config = parse_args()
    logger.info(json.dumps(profile, indent=4))

    if args.dry:
        logger.info("Preparing sandbox for dry run")
        prepare_sandbox(profile)

    logger.info("Building project")
    build_project(profile)

    logger.info("Preparing work directory")
    prepare_work(profile)

    if not os.path.exists(profile["run"]):
        logger.error(f"Run file {profile['run']} not found")
        exit(1)

    if args.build_only:
        logger.info("Build only specified, exiting")
        exit(0)

    logger.info("Initializing GDB")
    gdb_init(
        profile["run"],
        profile["args"],
        profile["env"],
        profile["breakpoints"],
        profile["work"],
    )
    logger.info("Initializing LSP")
    lsp_init(cwd=profile["sandbox"])

    logger.info("Initializing agent")
    system_message = (
        SYSTEM_MESSAGE_WITH_DBG if profile["debug"] else SYSTEM_MESSAGE_WITHOUT_DBG
    )
    assistant, user_proxy = agent_init(llm_config, system_message)

    logger.info("Initiating chat")
    set_confirm_output(profile["output"])
    initial = INITIAL_MESSAGE
    if profile["constraint"]:
        initial += "\n" + CONSTRAINT.format(profile["constraint"])
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
        chat_log = {}
        if chat_result:
            chat_log["dialog"] = chat_result.chat_history
            chat_log["cost"] = chat_result.cost
        else:
            chat_log["dialog"] = "Chat aborted"
            chat_log["cost"] = "N/A"
        with open("dialog.json", "w") as f:
            f.write(json.dumps(chat_log, indent=4))
        if args.keep:
            keep_log(profile)

    # Terminate GDB and LSP.
    gdb_exit()
    lsp_exit()

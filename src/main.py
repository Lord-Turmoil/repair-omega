import json
import logging
import os
from arguments import parse_args
from functions import set_confirm_output
from prompt import CONSTRAINT, INITIAL_MESSAGE
from tools.lsp_integration import lsp_exit, lsp_init
from tools.gdb_integration import gdb_exit, gdb_init
from agent import agent_init
import shutil
import subprocess

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


def keep_log():
    if not os.path.exists("log"):
        os.makedirs("log")
    shutil.copyfile("function.log", f"log/{profile['profile']}.function.log")
    shutil.copyfile("log.log", f"log/{profile['profile']}.log.log")


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

    logger.info("Initializing GDB")
    gdb_init(profile["run"], profile["args"], profile["env"], profile["work"])
    logger.info("Initializing LSP")
    lsp_init(cwd=profile["sandbox"])

    logger.info("Initializing agent")
    assistant, user_proxy = agent_init(llm_config)

    logger.info("Initiating chat")
    set_confirm_output(profile["output"])
    initial = INITIAL_MESSAGE
    if profile["constraint"]:
        initial += "\n" + CONSTRAINT.format(profile["constraint"])
    try:
        chat_result = user_proxy.initiate_chat(
            assistant,
            message=initial,
        )
    except Exception as e:
        logger.error(f"Chat terminated with exception: {e}")
    finally:
        # keep the log even if the chat aborts
        if args.keep:
            keep_log()

    # Terminate GDB and LSP.
    gdb_exit()
    lsp_exit()

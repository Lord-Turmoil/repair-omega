import json
import logging
import os
import shutil
import subprocess
from arguments import parse_args_fl
from consts import LOCALIZATION_OUTPUT, LOCALIZATION_SNAPSHOT
from tools.lsp_integration import lsp_exit, lsp_init
from tools.gdb_integration import gdb_exit, gdb_init
from agent import agent_init_fl
from prompt import FL_CONSTRAINT, FL_INITIAL_MESSAGE

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())
logger.addHandler(logging.FileHandler("fl.log", "w"))


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

    shutil.copyfile(LOCALIZATION_SNAPSHOT, f"log/{profile['profile']}/{LOCALIZATION_SNAPSHOT}")
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
        profile["work"],
    )
    logger.info("Initializing LSP")
    lsp_init(cwd=profile["sandbox"])

    logger.info("Initializing agent")
    assistant, user_proxy, system_message = agent_init_fl(llm_config, profile["debug"])

    logger.info("Initiating chat")
    initial = FL_INITIAL_MESSAGE
    if profile["constraint"]:
        initial += "\n" + FL_CONSTRAINT.format(profile["constraint"])
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

        with open(LOCALIZATION_OUTPUT, "r") as f:
            locations = f.read().split("\n")
        snapshot["locations"] = [line for line in locations if line.strip() != ""]

        with open(LOCALIZATION_SNAPSHOT, "w") as f:
            f.write(json.dumps(snapshot, indent=4))

        if args.keep:
            keep_log(profile)

    # Terminate GDB and LSP.
    gdb_exit()
    lsp_exit()
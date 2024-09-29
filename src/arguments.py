import argparse
import logging
import os
from autogen.agentchat.conversable_agent import json
import yaml


def load_config(filename="config.yaml"):
    config = {}

    entries = ["base_url", "api_key", "model"]

    with open(filename, "r") as f:
        CONFIG = yaml.load(f, Loader=yaml.FullLoader)
    try:
        select = CONFIG["llm"]["select"]
        for profile in CONFIG["llm"]["profiles"]:
            if profile["name"] == select:
                for entry in entries:
                    if entry in profile:
                        config[entry] = profile[entry]
    except KeyError:
        raise KeyError("Config file is not valid")

    return config


def load_profile(filename):
    if not filename.endswith(".json"):
        filename += ".json"
    if not os.path.exists(filename):
        filename = os.path.join("profile.d", filename)
    if not os.path.exists(filename):
        raise FileNotFoundError(f"Profile {filename} not found")
    with open(filename, "r") as f:
        profile = json.load(f)
    if "args" not in profile:
        profile["args"] = []
    if "env" not in profile:
        profile["env"] = {}
    return profile


def parse_args():
    parser = argparse.ArgumentParser(
        prog="Omega",
        description="LLM with Debugger and Language Server",
        epilog="Enjoy the program! :)",
    )
    parser.add_argument(
        "-c", "--config", type=str, default="config.yaml", help="Configuration file"
    )
    parser.add_argument(
        "-p",
        "--profile",
        type=str,
        required=True,
        help="Project profile",
    )

    args = parser.parse_args()

    profile = load_profile(args.profile)
    llm_config = load_config(args.config)

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    logger.addHandler(logging.StreamHandler())
    logger.info(f"Profile: {json.dumps(profile, indent=2)}")

    return args, profile, llm_config

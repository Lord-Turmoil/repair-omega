import argparse
import json
import os
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


def _contains(profile, key):
    if not key in profile:
        return False
    if profile[key] is None:
        return False
    if isinstance(profile[key], str) and profile[key] == "":
        return False
    return True


def load_profile(filename):
    if not filename.endswith(".json"):
        filename += ".json"
    if not os.path.exists(filename):
        filename = os.path.join("profile.d", filename)
    if not os.path.exists(filename):
        raise FileNotFoundError(f"Profile {filename} not found")
    with open(filename, "r") as f:
        profile = json.load(f)

    for key in ["project", "build", "run"]:
        if key not in profile:
            raise KeyError(f"Profile {filename} missing required key {key}")

    profile["project"] = os.path.abspath(profile["project"])

    if not _contains(profile, "sandbox"):
        profile["sandbox"] = ".sandbox"
    profile["sandbox"] = os.path.abspath(profile["sandbox"])
    profile["run"] = os.path.join(profile["sandbox"], profile["run"])

    if not _contains(profile, "work"):
        profile["work"] = ".work"
    profile["work"] = os.path.abspath(profile["work"])

    if not _contains(profile, "init"):
        profile["init"] = None
    else:
        profile["init"] = os.path.join(profile["sandbox"], profile["init"])

    if not _contains(profile, "output"):
        profile["output"] = os.path.abspath("locations.txt")

    if not _contains(profile, "args"):
        profile["args"] = []
    if not _contains(profile, "env"):
        profile["env"] = {}
    if not _contains(profile, "constraint"):
        profile["constraint"] = None

    # add profile identifier
    if not _contains(profile, "profile"):
        profile["profile"] = os.path.splitext(os.path.basename(filename))[0]

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
    parser.add_argument(
        "-k",
        "--keep",
        action="store_true",
        required=False,
        default=False,
        help="Keep the log after execution",
    )
    parser.add_argument(
        "-d",
        "--dry",
        action="store_true",
        required=False,
        default=True,
        help="Dry run",
    )

    args = parser.parse_args()

    profile = load_profile(args.profile)
    llm_config = load_config(args.config)
    profile["profile"] += f"-{llm_config['model']}"
    if profile["constraint"]:
        profile["profile"] += "-c"

    return args, profile, llm_config

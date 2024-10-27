import argparse
import datetime
import json
import os

import yaml


def _contains(profile, key):
    if not key in profile:
        return False
    if profile[key] is None:
        return False
    if isinstance(profile[key], str) and profile[key] == "":
        return False
    return True


def _load_llm_config(filename="config.yaml"):
    config = {}

    entries = ["base_url", "api_key", "model", "price"]

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


def _load_profile(filename):
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

    if not _contains(profile, "pre-build"):
        profile["pre-build"] = None

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

    if not _contains(profile, "args"):
        profile["args"] = []
    if not _contains(profile, "env"):
        profile["env"] = {}
    if not _contains(profile, "lib"):
        profile["lib"] = {}
    for key, value in profile["lib"].items():
        if key == "LD_LIBRARY_PATH":
            profile["lib"][key] = os.path.join(profile["sandbox"], value)
        # write linker options to env
        profile["env"][key] = profile["lib"][key]

    if not _contains(profile, "constraint"):
        profile["constraint"] = None
    if not _contains(profile, "function"):
        profile["function"] = None

    if not _contains(profile, "mode"):
        profile["mode"] = "gdb"

    # add profile identifier
    if not _contains(profile, "profile"):
        profile["profile"] = os.path.splitext(os.path.basename(filename))[0]

    # get current system time
    profile["timestamp"] = str(datetime.datetime.now())

    return profile


def _parse_args(parser):
    args = parser.parse_args()
    args_dict = vars(args)

    profile = _load_profile(args.profile)
    llm_config = _load_llm_config(args.config)

    if "no_constraint" in args_dict:
        if args.no_constraint:
            # force disable constraint
            profile["constraint"] = None
    if "rerun" in args_dict:
        profile["rerun"] = args.rerun

    profile["profile"] += f"-{llm_config['model']}"
    if profile["constraint"] is None:
        profile["profile"] += "-nc"

    return args, profile, llm_config


def parse_args_fl():
    """
    -c, --config: configuration file
    -p, --profile: project profile
    --keep: keep the log after execution
    --no-constraint: disable constraint
    """
    parser = argparse.ArgumentParser(
        prog="Fix Localization",
        description="Perform fix localization",
        epilog="Enjoy the program! :)",
    )
    parser.add_argument(
        "-c",
        "--config",
        type=str,
        required=False,
        default="config.yaml",
        help="Configuration file",
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
        "--no-constraint",
        action="store_true",
        required=False,
        default=False,
        help="Disable constraint",
    )
    parser.add_argument(
        "--rerun",
        action="store_true",
        required=False,
        default=False,
        help="Rerun the localization process",
    )

    return _parse_args(parser)


def parse_args_pg():
    """
    -c, --config: configuration file
    -p, --profile: project profile
    --keep: keep the log after execution
    --no-constraint: disable constraint
    """
    parser = argparse.ArgumentParser(
        prog="Patch Generation",
        description="Perform patch generation",
        epilog="Enjoy the program! :)",
    )
    parser.add_argument(
        "-c",
        "--config",
        type=str,
        required=False,
        default="config.yaml",
        help="Configuration file",
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
        "--no-constraint",
        action="store_true",
        required=False,
        default=False,
        help="Disable constraint",
    )

    return _parse_args(parser)


def parse_args_co():
    """
    -c, --config: configuration file
    -p, --profile: project profile
    --keep: keep the log after execution
    --no-constraint: disable constraint
    """
    parser = argparse.ArgumentParser(
        prog="Chat Only",
        description="Perform chat only patch generation",
        epilog="Enjoy the program! :)",
    )
    parser.add_argument(
        "-c",
        "--config",
        type=str,
        required=False,
        default="config.yaml",
        help="Configuration file",
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
        "--no-constraint",
        action="store_true",
        required=False,
        default=False,
        help="Disable constraint",
    )

    return _parse_args(parser)


def parse_args_build():
    """
    -p, --profile: project profile
    """
    parser = argparse.ArgumentParser(
        prog="Build",
        description="Prepare workspace",
        epilog="Enjoy the program! :)",
    )

    parser.add_argument(
        "-p",
        "--profile",
        type=str,
        required=True,
        help="Project profile",
    )

    args = parser.parse_args()
    profile = _load_profile(args.profile)

    return args, profile, None


def parse_args_validate():
    """
    -c, --config: configuration file
    -p, --profile: project profile
    --keep: keep the log after execution
    """
    parser = argparse.ArgumentParser(
        prog="Validation",
        description="Validate the patch",
        epilog="Enjoy the program! :)",
    )
    parser.add_argument(
        "-c",
        "--config",
        type=str,
        required=False,
        default="config.yaml",
        help="Configuration file",
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
        "--no-constraint",
        action="store_true",
        required=False,
        default=False,
        help="Disable constraint",
    )

    return _parse_args(parser)

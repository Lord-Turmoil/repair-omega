import os
import subprocess

from shared.arguments import parse_args_build
from shared.utils import copy_dir_content, ensure_empty_dir, get_logger

logger = get_logger(__name__)


def _prepare_sandbox(profile):
    ensure_empty_dir(profile["sandbox"])
    copy_dir_content(profile["project"], profile["sandbox"])


def _prepare_work(profile):
    ensure_empty_dir(profile["work"])
    if profile["init"]:
        copy_dir_content(profile["init"], profile["work"])


def _build_project(profile):
    if profile["pre-build"] is not None:
        pre_build = subprocess.run(
            profile["pre-build"],
            cwd=profile["sandbox"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
        )
        if pre_build.returncode != 0:
            logger.error("Failed to pre-build project")
            logger.error(pre_build.stderr.decode("utf-8"))
            return False

    build = subprocess.run(
        profile["build"],
        cwd=profile["sandbox"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
    )
    if build.returncode != 0:
        logger.error("Failed to build project")
        logger.error(build.stderr.decode("utf-8"))
        return False

    return True


if __name__ == "__main__":
    args, profile, _ = parse_args_build()

    logger.info("Preparing sandbox")
    _prepare_sandbox(profile)

    logger.info("Preparing work directory")
    _prepare_work(profile)

    logger.info("Building project")
    if not _build_project(profile):
        logger.error("Failed to build project")
        exit(1)

    if not os.path.exists(profile["run"]):
        logger.warning(f"Executable {profile['run']} not found")

    logger.info("Build complete")

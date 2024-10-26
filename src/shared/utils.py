import datetime
import logging
import os
import shutil

import coloredlogs


def get_logger(name, level=logging.INFO, log_file=None):
    log_formatter = logging.Formatter(
        "%(asctime)s %(levelname)s %(filename)s:%(lineno)d %(message)s",
        datefmt="%d/%m/%Y %H:%M:%S",
    )

    logger = logging.getLogger(name)
    logger.setLevel(level)

    if log_file is not None:
        file_handler = logging.FileHandler(log_file, "w")
        file_handler.setFormatter(log_formatter)
        file_handler.setLevel(level)
        logger.addHandler(file_handler)
    logger.addHandler(logging.StreamHandler())

    coloredlogs.install(level=level, logger=logger)

    return logger


def get_duration(profile):
    """
    get duration in seconds from profile
    """
    timestamp = datetime.datetime.strptime(profile["timestamp"], "%Y-%m-%d %H:%M:%S.%f")
    duration = datetime.datetime.now() - timestamp
    return duration.total_seconds()


def ensure_empty_dir(directory: str):
    """
    Ensure that the directory is empty.
    """
    if not os.path.exists(directory):
        os.makedirs(directory)
        return
    # delete all files and directories under directory
    for root, _, files in os.walk(directory):
        for file in files:
            os.remove(os.path.join(root, file))
        for directory in os.listdir(root):
            shutil.rmtree(os.path.join(root, directory))


def copy_dir_content(src: str, dest: str):
    """
    Copy the content of src directory to dest directory while keeping
    directory structure in dest.
    """
    for root, _, files in os.walk(src):
        for file in files:
            src_file = os.path.join(root, file)
            dest_file = os.path.join(dest, os.path.relpath(src_file, src))
            dest_dir = os.path.dirname(dest_file)
            if not os.path.exists(dest_dir):
                os.makedirs(dest_dir)
            shutil.copy2(src_file, dest_file)

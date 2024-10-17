import os
import shutil


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

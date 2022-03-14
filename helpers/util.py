import os
import subprocess


def adb_connected():
    return subprocess.call("adb get-state", shell=True) == 0


def command(string: str):
    return subprocess.check_output(string.split(" ")).decode()


def download_dir():
    directory = os.environ['HOME']
    if 'termux' in directory:
        directory += "/storage/shared/Download"
    else:
        directory += "/Downloads"
    directory += "/fdroid-cli"
    if not os.path.exists(directory):
        os.makedirs(directory)
    return directory

import os
import subprocess
import zipfile


def adb_connected():
    return subprocess.call("adb get-state>/dev/null", shell=True) == 0


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


def verify_apk(path: str, size: int):
    return os.stat(path).st_size == size and zipfile.is_zipfile(path)

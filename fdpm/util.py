import configparser
import os
import platform
import subprocess
import zipfile

import requests
from tqdm import tqdm


def adb_connected():
    """
    :return: Returns true if adb get-state call is ok
    """
    return subprocess.call("adb get-state>/dev/null", shell=True) == 0


def command(string: str) -> str:
    """
    :param string: console command
    :return: command output
    """
    return subprocess.check_output(string.split(" ")).decode()


def download_dir() -> str:
    """
    :return: Path to download apks to
    """
    directory = os.environ['HOME']
    if 'termux' in directory:
        directory = os.path.expanduser("~/storage/downloads")
    else:
        directory = os.path.expanduser("~/Downloads")
    directory = ''.join([directory, "/fdpm"])
    if not os.path.exists(directory):
        os.makedirs(directory)
    return directory


def share_dir() -> str:
    """
    :return: Path to store indexes and cache
    """
    if platform.system() == "Windows":
        directory = os.path.expanduser("~/Documents/fdpm")
        if not os.path.exists(directory):
            os.makedirs(directory)
        return directory
    if 'PREFIX' not in os.environ:
        return f"{os.environ['HOME']}/.local/share/fdpm"
    if 'termux' in os.environ['PREFIX']:
        return f"{os.environ['PREFIX']}/share/fdpm"


def verify_apk(path: str, size: int) -> bool:
    """
    :param path: path of apl
    :param size: expected size
    :return: Returns true if apk file is valid zip and matches given size
    """
    return os.stat(path).st_size == size and zipfile.is_zipfile(path)


def download(url: str, file_path: str = "") -> None:
    """
    Download from given url
    :param file_path:
    :param url: Url for apk
    """
    file_name = f"{url.split('/')[-1]}"
    file_path = (
        f"{file_path}/{file_name}"
        if file_path
        else f"{download_dir()}/{file_name}"
    )

    response = requests.get(url, stream=True)
    file_size = response.headers.get('content-length')

    # handle if no content length present
    if file_size is None:
        with open(file_path, "wb") as f:
            f.write(response.content)
        return

    # avoid re-download if file is already downloaded
    if (
        file_name.endswith(".apk")
        and os.path.exists(file_path)
        and verify_apk(file_path, int(file_size))
    ):
        return

    # make dirs
    if not os.path.exists(os.path.dirname(file_path)):
        os.makedirs(os.path.dirname(file_path))

    # download with progress bar
    with open(file_path, "wb") as f:
        file_size = int(file_size)
        pbar = tqdm(total=file_size,
                    desc=url.split("/")[-1],
                    leave=False, colour='green')
        for data in response.iter_content(chunk_size=4096):
            f.write(data)
            pbar.update(len(data))
        pbar.close()


def get(coll: any, key: str, fallback="") -> any:
    """
    Safely get value from collection
    :param coll: any object
    :param key: key string
    :param fallback: fallback value if key not in collection
    :return:
    """
    return coll[key] if key in coll else fallback


def cache_put(section: str, key: str, value: str):
    """
    Puts key, value pair in section
    :param section: section name
    :param key: key string
    :param value: value string
    """
    config_file = configparser.ConfigParser()
    config_file.optionxform = str
    if not config_file.has_section(section):
        config_file.add_section(section)
    config_file.read(f"{share_dir()}/cache")
    config_file.set(section, key, value)
    with open(f"{share_dir()}/cache", 'w') as configfileObj:
        config_file.write(configfileObj)
        configfileObj.flush()
        configfileObj.close()


def cache_get(section: str, key: str):
    """
    Returns value for given key in section
    :param section: section name
    :param key: key name
    :return: value string
    """
    config_file = configparser.ConfigParser()
    config_file.optionxform = str
    if os.path.exists(f"{share_dir()}/cache"):
        config_file.read(f"{share_dir()}/cache")
        return config_file.get(section, key, fallback=None)
    return None


def cache_get_all(section: str) -> list:
    """

    :param section:
    :return: all keys from section
    """
    config_file = configparser.ConfigParser()
    config_file.optionxform = str
    if os.path.exists(f"{share_dir()}/cache"):
        config_file.read(f"{share_dir()}/cache")
        return config_file.options(section)
    return []

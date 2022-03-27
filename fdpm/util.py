import configparser
import os
import subprocess
import zipfile

import certifi
import urllib3
from tqdm import tqdm


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


def share_dir():
    if 'PREFIX' in os.environ:
        if 'termux' in os.environ['PREFIX']:
            return f"{os.environ['PREFIX']}/share/fdpm"
    else:
        return f"{os.environ['HOME']}/.local/share/fdpm"


def verify_apk(path: str, size: int):
    return os.stat(path).st_size == size and zipfile.is_zipfile(path)


def download(url: str, file_path: str = "") -> None:
    """
    Download from given url
    :param file_path:
    :param url: Url for apk
    """
    file_size_dl = 0
    block_sz = 8192
    file_name = f"{url.split('/')[-1]}"
    if not file_path:
        file_path = f"{download_dir()}/{file_name}"
    else:
        file_path = f"{file_path}/{file_name}"
    http = urllib3.PoolManager(
        cert_reqs='CERT_REQUIRED',
        ca_certs=certifi.where()
    )
    r = http.request('GET', url, preload_content=False)

    if "Content-Length" in r.headers:
        file_size = int(r.headers["Content-Length"])
    else:
        f = open(file_path, "wb")
        while True:
            buffer = r.read(block_sz)
            if not buffer:
                break
            f.write(buffer)
        return

    if file_name.endswith(".apk"):
        if os.path.exists(file_path) and verify_apk(file_path, file_size):
            return
    if not os.path.exists(os.path.dirname(file_path)):
        os.makedirs(os.path.dirname(file_path))

    f = open(file_path, "wb")
    pbar = tqdm(total=file_size,
                desc=url.split("/")[-1].split(".")[-1].capitalize(),
                leave=False, colour='green')
    while True:
        buffer = r.read(block_sz)
        if not buffer:
            break
        file_size_dl += len(buffer)
        f.write(buffer)
        pbar.update(len(buffer))
    pbar.close()
    f.close()


def get(coll, key, fallback=""):
    return coll[key] if key in coll else fallback


def cache_put(section, key, value):
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


def cache_get(section, key):
    config_file = configparser.ConfigParser()
    config_file.optionxform = str
    if os.path.exists(f"{share_dir()}/cache"):
        config_file.read(f"{share_dir()}/cache")
        return config_file.get(section, key, fallback=None)
    return None


def cache_get_all(section):
    config_file = configparser.ConfigParser()
    config_file.optionxform = str
    if os.path.exists(f"{share_dir()}/cache"):
        config_file.read(f"{share_dir()}/cache")
        return config_file.options(section)
    return None

import os
import subprocess
from multiprocessing.pool import ThreadPool

import certifi
import urllib3
from tqdm import tqdm

from helpers.util import download_dir, adb_connected, command, verify_apk
from models.fdroid import suggested_version, latest_version, version_code
from models.user import installed_packages


def download(url: str) -> None:
    """
    Download from given url
    :param url: Url for apk
    """
    file_name = f"{url.split('/')[-1]}"
    http = urllib3.PoolManager(
        cert_reqs='CERT_REQUIRED',
        ca_certs=certifi.where()
    )
    r = http.request('GET', url, preload_content=False)
    file_size = int(r.headers["Content-Length"])
    file_size_dl = 0
    block_sz = 8192
    apk_path = f"{download_dir()}/{file_name}"
    if os.path.exists(apk_path) and verify_apk(apk_path, file_size):
        return
    f = open(apk_path, "wb")
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


def download_multiple(urls: list) -> None:
    """
    Download apk from given urls parallely
    :param urls: List of url
    """
    pbar = tqdm(total=len(urls), desc="Downloading apk", colour='blue')
    results = ThreadPool(4).imap_unordered(download, urls)
    for _ in results:
        pbar.update(1)
    pbar.close()


def suggested_outdated(id_: str) -> int:
    """
    Returns newer 'suggested' version if available, 0 otherwise
    :param id_: Package name
    :return: Newer 'suggested' version if available, 0 otherwise
    """
    version = suggested_version(id_)
    if installed_package_version(id_) < version:
        return version
    else:
        return 0


def latest_outdated(id_: str):
    """
    Returns newer 'latest' version if available, 0 otherwise
    :param id_: Package name
    :return: Newer 'latest' version if available, 0 otherwise
    """
    version = latest_version(id_)
    if installed_package_version(id_) < latest_version(id_):
        return version
    return 0


def outdated_packages(suggested: bool = True) -> list:
    """
    Returns list of outdated packages
    :param suggested: Package versions. True=suggested, False=latest
    :return: List of outdated packages
    """
    packages = []
    for package_id in installed_packages('fdroid.cli'):
        if suggested:
            new_version = suggested_outdated(package_id)
            if new_version:
                packages.append(f"https://f-droid.org/repo/{package_id}_{new_version}.apk")
        if not suggested and latest_outdated(package_id):
            new_version = latest_outdated(package_id)
            if new_version:
                packages.append(f"https://f-droid.org/repo/{package_id}_{new_version}.apk")
    return packages


def installed_package_version(id_: str) -> int:
    """
    Returns installed package version for package name
    :param id_: Package name
    :return: Installed package version if found, 0 otherwise
    """
    if adb_connected():
        try:
            output = command(f"adb shell dumpsys package {id_} | grep versionName")
            version_name = output.strip("\n").split("=")[1]
            return version_code(id_, version_name)
        except subprocess.CalledProcessError as e:
            print(f"Failed to check package version for '{id_}'", e.output)
    return 0


def apk_url(id_: str):
    """
    Get apk url of suggested version for given package name
    :param id_: List of package names
    :return: list[str]:
    """
    code = suggested_version(id_)
    file_name = f"{id_}_{code}.apk"
    url = f"https://f-droid.org/repo/{file_name}"
    return url


def apk_urls(ids: list) -> list[str]:
    """
    Get apk url of suggested version for given package names
    :param ids: List of package names
    :return: list[str]:
    """
    __urls = []
    pbar = tqdm(total=len(ids), desc="Getting url for apk", colour='blue')
    results = ThreadPool(4).imap_unordered(apk_url, ids)
    for r in results:
        __urls.append(r)
        pbar.update(1)
    pbar.close()
    return __urls


def install_all(ids: list) -> None:
    """
    Installs app with given url
    :param ids: List of package names to install
    :return:None
    """
    package_urls = apk_urls(ids)
    download_multiple(package_urls)
    if adb_connected():
        results = ThreadPool(4).imap_unordered(install, package_urls)
        with tqdm(total=len(ids), desc=f"Installing apk", colour='blue') as pbar:
            for _ in results:
                pbar.update(1)
        pbar.close()


def install(url: str) -> (str, bool):
    """
    Installs app with given url
    :param url: APK file url
    :return:(str, bool): package name, install status
    """
    file_name = url.split("/")[-1]
    id_ = file_name.replace(".apk", "")
    install_reason = "--install-reason 4"
    user = f"--user 0"
    installer = "-i kshib.fdroid.cli"
    params = f"{install_reason} {user} {installer}"
    try:
        output = command(f"adb install {params} {download_dir()}/{file_name}")
        return id_, "Success" in output
    except subprocess.CalledProcessError as e:
        print(f"Failed to install'{id_}'", e.output)
        return id_, False


def uninstall(id_: str) -> (str, bool):
    """
    Uninstalls app with given package name
    :param id_: Package names of app to uninstall
    :return:(str, bool): package name, uninstall status
    """
    user = f"--user 0"
    params = f"{user} {id_}"
    try:
        output = command(f"adb uninstall {params}")
        return id_, "Success" in output
    except subprocess.CalledProcessError as e:
        print(f"Failed to uninstall' {id_}'", e.output)
    return id_, False


def uninstall_all(ids: list) -> None:
    """
    Uninstalls all apps in given package names list
    :param ids: List of package names of apps to uninstall
    :return:None
    """
    if adb_connected():
        pbar = tqdm(total=len(ids), desc="Uninstalling app", colour='blue')
        results = ThreadPool(4).imap_unordered(uninstall, ids)
        for _ in results:
            pbar.update(1)
        pbar.close()

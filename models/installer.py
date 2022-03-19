import subprocess
from multiprocessing.pool import ThreadPool

import certifi
import requests
import urllib3

from helpers.util import download_dir, adb_connected, command
from models.fdroid import suggested_version, latest_version, version_code, search
from models.package import Package
from models.user import installed_packages, package_installed

download_status = {}


def download(package: Package, code: int = 0) -> None:
    """
    Download package to default download directory

    :param package: Package
    :type package: Package
    :param code: Version code of the package to download
    :type code: int
    """
    if code == 0:
        code = suggested_version(package)
    file_name = f"{package.id_}_{code}.apk"
    url = f"https://f-droid.org/repo/{file_name}"

    http = urllib3.PoolManager(
        cert_reqs='CERT_REQUIRED',
        ca_certs=certifi.where()
    )
    r = http.request('GET', url, preload_content=False)
    file_size = int(r.headers["Content-Length"])
    file_size_dl = 0
    block_sz = 8192
    download_status[file_name] = (file_size_dl, file_size)
    f = open(f"{download_dir()}/{file_name}", "wb")
    while True:
        buffer = r.read(block_sz)
        if not buffer:
            break
        file_size_dl += len(buffer)
        f.write(buffer)
        status = "{}".format(int(file_size_dl * 100. // file_size))
        download_status[file_name] = (status, file_size)
    f.close()


def download_multiple(urls):
    results = ThreadPool(3).imap_unordered(download, urls)
    for r in results:
        pass


def suggested_outdated(package: Package) -> bool:
    """
    :param package: Package
    :type package: Package
    :return: True if version for given package is lower than the suggested version
    """
    return installed_package_version(package) < suggested_version(package)


def latest_outdated(package):
    """
    :param package: Package
    :type package: Package
    :return: True if version for given package is lower than the latest version
    """
    return installed_package_version(package) < latest_version(package)


def outdated_packages(suggested: bool = True) -> list[Package]:
    """
    :param suggested: Use suggested version? Latest otherwise
    :type suggested: bool
    :return: Returns list of outdated packages
    """
    packages = []
    for package in installed_packages('fdroid.cli'):
        if suggested and suggested_outdated(package):
            packages.append(package)
        if not suggested and latest_outdated(package):
            packages.append(package)
    return packages


def update_outdated_packages(suggested=True) -> list[Package]:
    """
    Downloads and installs outdated packages

    :param suggested: Use suggested version? Latest otherwise
    :type suggested: bool
    :return: List of packages failed to install
    """
    packages = []
    for package in outdated_packages():
        if suggested:
            code = suggested_version(package)
        else:
            code = latest_version(package)
        download(package, code)
        success = install(package, code)
        if not success:
            packages.append(package)
    return packages


def installed_package_version(package: Package) -> int:
    """
    :param package: Package
    :type package: Package
    :return: Installed package version
    """
    if adb_connected():
        try:
            output = command(f"adb shell dumpsys package {package.id_} | grep versionName")
            version_name = output.strip("\n").split("=")[1]
            return version_code(package, version_name)
        except subprocess.CalledProcessError as e:
            print(f"Failed to check package version for '{package.name}'", e.output)
    return -1


def search_install(query: str) -> bool:
    """
    Searches packages matching given query and installs first result
    :param query: Search term
    :type query: Package
    :return: True if install was successful
    """
    results = search(query)
    if results:
        return install(results[0])


def install_multiple(packages: list[Package], code: int = 0, user: int = 0) -> bool:
    """
    Install package

    :param packages: Package
    :param code: Version of package to install
    :param user: User id. 0 by default (main user)
    :return: True if install was successful
    """
    urls=[]
    for package in packages:
        if code == 0:
            if code == -1:
                return False
        if package_installed(package):
            return False
        file_name = f"{package.id_}_{code}.apk"
        url = f"https://f-droid.org/repo/{file_name}"
        urls.append(url)
    download_multiple(urls)
    for package in packages:
        if adb_connected():
            file_name = f"{package.id_}_{code}.apk"
            pkg_id = f"--pkg {package.id_}"
            install_reason = "--install-reason 4"
            user = f"--user {user}"
            installer = "-i kshib.fdroid.cli"
            params = f"{pkg_id} {install_reason} {user} {installer}"
            try:
                output = command(f"adb install {params} {file_name}")
                return "Success" in output
            except subprocess.CalledProcessError as e:
                print(f"Failed to check package version for '{package.name}'", e.output)
        return False


def install(package: Package, code: int = 0, user: int = 0) -> bool:
    """
    Install package

    :param package: Package
    :param code: Version of package to install
    :param user: User id. 0 by default (main user)
    :return: True if install was successful
    """
    if code == 0:
        code = suggested_version(package)
        if code == -1:
            return False
    if package_installed(package):
        return False
    dl_dir = download_dir()
    download(package, code)
    file_name = f"{dl_dir}/{package.id_}_{code}.apk"
    if adb_connected():
        pkg_id = f"--pkg {package.id_}"
        install_reason = "--install-reason 4"
        user = f"--user {user}"
        installer = "-i kshib.fdroid.cli"
        params = f"{pkg_id} {install_reason} {user} {installer}"
        try:
            output = command(f"adb install {params} {file_name}")
            return "Success" in output
        except subprocess.CalledProcessError as e:
            print(f"Failed to check package version for '{package.name}'", e.output)
    return False


def uninstall(package: Package, user=0):
    """
    Uninstall package

    :param package: Package
    :param user: User id. 0 by default (main user)
    :return: True if install was successful
    """
    if adb_connected():
        user = f"--user {user}"
        id_ = f"{package.id_}"
        params = f"{user} {id_}"
        try:
            output = command(f"adb uninstall {params}")
            return "Success" in output
        except subprocess.CalledProcessError as e:
            print(f"Failed to uninstall'{package.name}'", e.output)
    return False

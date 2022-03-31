import json
import os
import shutil
import subprocess
import time
import zipfile
from multiprocessing.pool import ThreadPool

import requests
from tqdm import tqdm

from fdpm.util import download, share_dir, get, adb_connected, \
    command, download_dir, cache_put, cache_get, cache_get_all


class User:

    @staticmethod
    def installed_packages(installer_keyword, user=0) -> list:
        """
        :param installer_keyword: Package installer, can be partial package name
        :param user: User id, 0 by default
        :return: List of package names for installed apps
        """
        packages = []
        if adb_connected():
            try:
                output = command(f"adb shell pm list packages -3 -i --user {user}")
                for package_info in output.split("\n"):
                    package_info_split = package_info.strip().split("  ")
                    package_id = package_info_split[0].replace("package:", "")
                    if len(package_info_split) > 1:
                        installer = package_info_split[1].split("=")[1]
                        if installer_keyword in installer:
                            packages.append(package_id)
            except subprocess.CalledProcessError as e:
                print("Failed to check package version for", e.output)
        return packages

    @staticmethod
    def cpu() -> str:
        """
        :return: returns cpu abi
        """
        if adb_connected():
            try:
                cpu = cache_get("USER", "cpu")
                if cpu:
                    return cpu
                cpu = command("adb shell getprop ro.product.cpu.abi")
                cache_put("USER", "cpu", cpu)
                return cpu
            except subprocess.CalledProcessError as e:
                print("Failed to cpu type for", e.output)

    @staticmethod
    def sdk():
        """
        :return: returns sdk version
        """
        if adb_connected():
            try:
                sdk = cache_get("USER", "sdk")
                if sdk:
                    return sdk
                sdk = command("adb shell getprop ro.build.version.sdk")
                cache_put("USER", "sdk", sdk)
                return sdk
            except subprocess.CalledProcessError as e:
                print("Failed to sdk version for", e.output)

    @staticmethod
    def android() -> bool:
        """
        :return: returns True if user is using android
        """
        return "android" in str(os.environ).lower()


class Repo:

    def __init__(self):
        self.dl_dir = f"{share_dir()}/repos"
        self.data = {}
        self.name = "F-Droid"
        self.subscribe(self.name)
        self.load(self.name)

    def load(self, repo: str):
        """
        Downloads repo index and reads it
        :param repo: Full repo name as specified in repo.json

        https://gitlab.com/AuroraOSS/auroradroid/-/raw/master/app/src/main/assets/repo.json
        """

        if not os.path.exists(self.dl_dir):
            os.makedirs(self.dl_dir)
        repo_url = "https://f-droid.org/repo"
        index_file = f'{self.dl_dir}/{repo}/index-v1.json'
        repos_file = f'{self.dl_dir}/repo.json'

        # skip if recently downloaded
        if os.path.exists(index_file) and self.age(repo) < 60 * 12:
            return self.quick_load(repo)

        # download repos list
        if not os.path.exists(f"{self.dl_dir}/repo.json"):
            repos_url = "https://gitlab.com/AuroraOSS/auroradroid/-/raw/master/app/src/main/assets/repo.json"
            download(repos_url, self.dl_dir)

        # load repo file
        with open(repos_file) as f:
            repos_data = json.load(f)
        ext = "json"
        for repo_ in repos_data:
            if repo == repo_["repoName"]:
                repo_url = repo_["repoUrl"]
                response = requests.get(f"{repo_url}/index-v1.{ext}")
                if response.status_code != 200:
                    ext = "jar"
                index_file = f'{self.dl_dir}/{repo}/index-v1.{ext}'

        # download index
        if not os.path.exists(f"{self.dl_dir}/{repo}/{os.path.basename(index_file)}"):
            download(f"{repo_url}/{os.path.basename(index_file)}", f"{self.dl_dir}/{repo}")
            # for f-droid, index is in a jar, unzip it and clean up
            if ext == "jar":
                with zipfile.ZipFile(f"{self.dl_dir}/{repo}/{os.path.basename(index_file)}", "r") as zf:
                    zf.extractall(f"{self.dl_dir}/{repo}/")
                os.remove(f"{self.dl_dir}/{repo}/{os.path.basename(index_file)}")
                shutil.rmtree(f"{self.dl_dir}/{repo}/META-INF")

        # open index
        return self.quick_load(repo)

    def address(self, repo=None):
        """
        Returns base url for specified repo. If no repo is specified returns base url for
        currently loaded repo.
        :param repo:
        :return: repo base url
        """
        if repo:
            self.quick_load(repo)
        return self.data['repo']['address']

    def quick_load(self, repo):
        """
        Reads already downloaded repo index
        :param repo:
        :return: loaded repo name
        """
        index_file = f'{self.dl_dir}/{repo}/index-v1.json'
        with open(index_file) as f:
            self.data = json.load(f)
        self.name = repo
        return self.name

    def apps(self) -> dict:
        """
        Collects all apps from subscribed repos
        :return: dict with package name as key and
        values: name, packageName, suggestedVersionCode, description, summary
        """
        apps_list = {}
        for repo in self.subscribed_repos():
            self.quick_load(repo)
            for app in self.data["apps"]:
                description = ""
                summary = ""
                version = get(app, "suggestedVersionCode")
                package_name = get(app, "packageName")
                name = get(app, "name")
                if "localized" in app:
                    localized = app["localized"]
                    en = get(localized, "en-US", get(localized, "en-GB"))
                    if not name:
                        name = get(en, "name")
                    description = get(en, "description")
                    summary = get(en, "summary", get(app, "description"))
                apps_list[package_name] = {
                    "name": name,
                    "packageName": package_name,
                    "suggestedVersionCode": version,
                    "description": description,
                    "summary": summary,
                }
        return apps_list

    def packages(self, app: str) -> list:
        """
        returns packages for specified app
        :param app: app package name
        :return: list of packages
        """
        packages_list = []
        for repo in self.subscribed_repos():
            self.quick_load(repo)
            for package in self.data["packages"]:
                if app == package:
                    packages_list.extend(
                        {
                            "apkName": get(apk, "apkName"),
                            "versionName": get(apk, "versionName"),
                            "versionCode": get(apk, "versionCode"),
                            "size": get(apk, "size"),
                            "hash": get(apk, "hash"),
                            "hashType": get(apk, "hashType"),
                            "nativecode": get(apk, "nativecode", "all"),
                            "minSdkVersion": get(apk, "minSdkVersion", "all"),
                            "targetSdkVersion": get(apk, "targetSdkVersion", "all"),
                            "repo": self.name,
                        } for apk in self.data["packages"][app])
        return packages_list

    def suggested_package(self, app: str, user: User):
        """
        Searches packages for suggested version and cpu architecture
        :param user: user object
        :param app: app package name
        :return: suggested package
        """
        for repo in self.subscribed_repos():
            self.quick_load(repo)
            if app in self.apps():
                for package in self.packages(app):
                    cpu_ok = user.cpu() in package["nativecode"] or package["nativecode"] == "all"
                    sdk_ok = package["minSdkVersion"] <= int(user.sdk())
                    # suggested = str(self.apps()[app]["suggestedVersionCode"]) == str(package["versionCode"])
                    # ignore suggested if cpu and sdk are ok
                    # as some repos give different suggested version number depending on sdk
                    # which would result on no match. example: bromite repo
                    if cpu_ok and sdk_ok:
                        return package

    def latest_package(self, app: str, arch: str):
        """
        Return latest package matching the cpu abi
        :param app: app package name
        :param arch: cpu architecture
        :return:
        """
        for package in self.packages(app):
            if arch in package["nativecode"]:
                return package

    def search(self, term: str) -> list:
        """
        Search all subscribed repos
        :param term: Search term
        :return: List of apps fuzzy matching the term
        """
        from thefuzz import fuzz
        apps_list = self.apps()
        return [
            apps_list[app]
            for app in apps_list
            if fuzz.token_set_ratio(term, str(apps_list[app])) == 100
        ]

    def version_code(self, app: str, version_name: str) -> int:
        """
        Return version code for respective version name
        :param app: app package name
        :param version_name: version name (ex 1.0)
        :return:
        """
        for package in self.packages(app):
            if app == package:
                for apk in self.data["packages"][app]:
                    if apk["versionName"] == version_name:
                        return apk["versionCode"]

    def subscribe(self, repo: str) -> None:
        """
        Subscribe to a repo
        :param repo: Repo to subscribe
        """
        repo_ = self.load(repo)
        cache_put("REPO_SUBS", repo_, "1")

    @staticmethod
    def subscribed_repos() -> list:
        """
        :return: Returns list of subscribed repos
        """
        return list(filter(
            lambda sub: cache_get("REPO_SUBS", sub) == "1",
            cache_get_all("REPO_SUBS")
        ))

    @staticmethod
    def unsubscribe(repo: str) -> None:
        """
        Unsubscribe from repo
        :param repo: Repo to unsubscribe
        """
        cache_put("REPO_SUBS", repo, "0")

    @staticmethod
    def age(repo: str) -> int:
        """
        :param repo: Repo to check age
        :return: Returns minutes since repo was last updated
        """
        dl_dir = f"{share_dir()}/repos"
        time_now = int(time.time())
        time_modified = int(os.path.getmtime(f'{dl_dir}/{repo}/index-v1.json'))
        return int((time_now - time_modified) / 60)

    @staticmethod
    def available():
        repos_file = f'{share_dir()}/repos/repo.json'
        with open(repos_file) as f:
            repos_data = json.load(f)
        return list(map(
            lambda repo_:repo_['repoName'],
            repos_data
        ))


class Installer:

    def __init__(self):
        self.repo = Repo()
        self.user = User()

    @staticmethod
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

    def suggested_outdated(self, id_: str) -> int:
        """
        Returns newer 'suggested' version if available, 0 otherwise
        :param id_: Package name
        :return: Newer 'suggested' version if available, 0 otherwise
        """
        for r in self.repo.subscribed_repos():
            self.repo.quick_load(r)
            if self.repo.suggested_package(id_, self.user) is not None:
                version = self.repo.suggested_package(id_, self.user)["versionCode"]
                return version if self.installed_package_version(id_) < version else 0

    def latest_outdated(self, id_: str):
        """
        Returns newer 'latest' version if available, 0 otherwise
        :param id_: Package name
        :return: Newer 'latest' version if available, 0 otherwise
        """
        for r in self.repo.subscribed_repos():
            self.repo.quick_load(r)
            version = self.repo.latest_package(id_, self.user.cpu())
            if self.installed_package_version(id_) < self.repo.latest_package(id_, self.user.cpu())["versionCode"]:
                return version
            return 0

    def outdated_packages(self, suggested: bool = True) -> list:
        """
        Returns list of outdated packages
        :param suggested: Package versions. True=suggested, False=latest
        :return: List of outdated packages
        """
        packages = []
        for package_id in self.user.installed_packages('fdroid.cli'):
            if suggested:
                if new_version := self.suggested_outdated(package_id):
                    packages.append(f"https://f-droid.org/repo/{package_id}_{new_version}.apk")
            if not suggested and self.latest_outdated(package_id):
                if new_version := self.latest_outdated(package_id):
                    packages.append(f"https://f-droid.org/repo/{package_id}_{new_version}.apk")
        return packages

    def installed_package_version(self, id_: str) -> int:
        """
        Returns installed package version for package name
        :param id_: Package name
        :return: Installed package version if found, 0 otherwise
        """
        if adb_connected():
            try:
                output = command(f"adb shell dumpsys package {id_} | grep versionName")
                version_name = output.strip("\n").split("=")[1]
                return self.repo.version_code(id_, version_name)
            except subprocess.CalledProcessError as e:
                print(f"Failed to check package version for '{id_}'", e.output)
        return 0

    def apk_url(self, id_: str):
        """
        Get apk url of suggested version for given package name
        :param id_: List of package names
        :return: list[str]:
        """
        package = self.repo.suggested_package(id_, self.user)
        address = self.repo.address(package['repo'])
        if "/repo" not in address:
            address = "".join([address, 'repo'])
        return f"{address}/{package['apkName']}"

    def apk_urls(self, ids: list) -> list[str]:
        """
        Get apk url of suggested version for given package names
        :param ids: List of package names
        :return: list[str]:
        """
        __urls = []
        pbar = tqdm(total=len(ids), desc="Getting url for apk", colour='blue')
        results = ThreadPool(4).imap_unordered(self.apk_url, ids)
        for r in results:
            __urls.append(r)
            pbar.update(1)
        pbar.close()
        return __urls

    def install_all(self, ids: list) -> None:
        """
        Installs app with given url
        :param ids: List of package names to install
        :return:None
        """
        package_urls = self.apk_urls(ids)
        self.download_multiple(package_urls)
        if adb_connected():
            results = ThreadPool(4).imap_unordered(self.install, package_urls)
            with tqdm(total=len(ids), desc="Installing apk", colour='blue') as pbar:
                for _ in results:
                    pbar.update(1)
            pbar.close()

    @staticmethod
    def install(url: str) -> (str, bool):
        """
        Installs app with given url
        :param url: APK file url
        :return:(str, bool): package name, install status
        """
        file_name = url.split("/")[-1]
        id_ = file_name.replace(".apk", "")
        install_reason = "--install-reason 4"
        user_id = "--user 0"
        installer = "-i kshib.fdroid.cli"
        params = f"{install_reason} {user_id} {installer}"
        try:
            output = command(f"adb install {params} {download_dir()}/{file_name}")
            return id_, "Success" in output
        except subprocess.CalledProcessError as e:
            print(f"Failed to install'{id_}'", e.output)
            return id_, False

    @staticmethod
    def uninstall(id_: str) -> (str, bool):
        """
        Uninstalls app with given package name
        :param id_: Package names of app to uninstall
        :return:(str, bool): package name, uninstall status
        """
        user_id = "--user 0"
        params = f"{user_id} {id_}"
        try:
            output = command(f"adb uninstall {params}")
            return id_, "Success" in output
        except subprocess.CalledProcessError as e:
            print(f"Failed to uninstall' {id_}'", e.output)
        return id_, False

    def uninstall_all(self, ids: list) -> None:
        """
        Uninstalls all apps in given package names list
        :param ids: List of package names of apps to uninstall
        :return:None
        """
        if adb_connected():
            pbar = tqdm(total=len(ids), desc="Uninstalling app", colour='blue')
            results = ThreadPool(4).imap_unordered(self.uninstall, ids)
            for _ in results:
                pbar.update(1)
            pbar.close()

import json
import os
import shutil
import subprocess
import time
import zipfile
from multiprocessing.pool import ThreadPool

from tqdm import tqdm

from util import download, share_dir, get, adb_connected, command, download_dir, cache_put, cache_get, cache_get_all


class User:

    @staticmethod
    def installed_packages(installer_keyword, user=0) -> list:
        """
        :param installer_keyword: Package installer, can be partial package name
        :param user: User id
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
                print(f"Failed to check package version for", e.output)
        return packages

    @staticmethod
    def cpu():
        if adb_connected():
            try:
                cpu = cache_get("USER", "cpu")
                if cpu is not None:
                    return cpu
                else:
                    cpu = command("adb shell getprop ro.product.cpu.abi")
                    cache_put("USER", "cpu", cpu)
            except subprocess.CalledProcessError as e:
                print(f"Failed to cpu type for", e.output)

    # return if user is using android
    @staticmethod
    def android() -> bool:
        return "android" in str(os.environ).lower()


class Repo:

    def __init__(self):
        self.dl_dir = f"{share_dir()}/repos"
        self.data = {}
        self.load("F-Droid")

    def load(self, repo: str):
        """
        Downloads repo index
        :param repo:
        """
        if not os.path.exists(self.dl_dir):
            os.makedirs(self.dl_dir)
        repos_url = "https://gitlab.com/AuroraOSS/auroradroid/-/raw/master/app/src/main/assets/repo.json"
        repo_url = "https://f-droid.org/repo"
        index_file = f'{self.dl_dir}/{repo}/index-v1.json'
        repos_file = f'{self.dl_dir}/repo.json'

        # skip if recently downloaded
        if os.path.exists(index_file) and self.age(repo) < 60 * 12:
            return self.quick_load(repo)

        # download repos list
        if not os.path.exists(f"{self.dl_dir}/repo.json"):
            download(repos_url, self.dl_dir)

        # open repos list
        f = open(f"{repos_file}")
        repos_data = json.load(f)
        for repo_ in repos_data:
            if repo == repo_["repoName"]:
                repo_url = repo_["repoUrl"]
                if repo != "F-Droid":
                    index_file = f'{self.dl_dir}/{repo}/index-v1.json'
                else:
                    index_file = f'{self.dl_dir}/{repo}/index-v1.jar'

        # download index
        if not os.path.exists(f"{self.dl_dir}/{repo}/{os.path.basename(index_file)}"):
            download(f"{repo_url}/{os.path.basename(index_file)}", f"{self.dl_dir}/{repo}")
            # for f-droid, index is in a jar, unzip it and clean up
            if repo == "F-Droid":
                with zipfile.ZipFile(f"{self.dl_dir}/{repo}/{os.path.basename(index_file)}", "r") as zf:
                    zf.extractall(f"{self.dl_dir}/{repo}/")
                os.remove(f"{self.dl_dir}/{repo}/{os.path.basename(index_file)}")
                shutil.rmtree(f"{self.dl_dir}/{repo}/META-INF")

        # open index
        return self.quick_load(repo)

    def address(self, repo=None):
        if repo:
            self.quick_load(repo)
        return self.data['repo']['address']

    def quick_load(self, repo):
        index_file = f'{self.dl_dir}/{repo}/index-v1.json'
        f = open(index_file)
        self.data = json.load(f)
        f.close()
        return index_file.split("/")[-2]

    def apps(self):
        apps_list = {}
        for repo in self.subscribed_repos():
            self.quick_load(repo)
            for app in self.data["apps"]:
                version = get(app, "suggestedVersionCode")
                package_name = get(app, "packageName")
                name = get(app, "name")
                if "localized" in app:
                    localized = app["localized"]
                    if "en-US" in localized:
                        en = localized["en-US"]
                    elif "en-GB" in localized:
                        en = localized["en-GB"]
                    else:
                        continue
                    if not name:
                        name = get(en, "name")
                    description = get(en, "description")
                    summary = get(en, "summary")
                    if summary == "":
                        summary = get(app, "description")
                    apps_list[package_name] = {
                        "name": name,
                        "packageName": package_name,
                        "suggestedVersionCode": version,
                        "description": description,
                        "summary": summary,
                    }
        return apps_list

    def packages(self, app: str):
        packages_list = []
        for repo in self.subscribed_repos():
            self.quick_load(repo)
            for package in self.data["packages"]:
                if app == package:
                    for apk in self.data["packages"][app]:
                        packages_list.append({
                            "apkName": apk["apkName"],
                            "versionName": apk["versionName"],
                            "versionCode": apk["versionCode"],
                            "size": apk["size"],
                            "hash": apk["hash"],
                            "hashType": apk["hashType"],
                            "nativecode": get(apk,"nativecode", "all"),
                            "repo": repo,
                        })
        return packages_list

    def suggested_package(self, app: str, arch: str):
        for package in self.packages(app):
            if arch in package["nativecode"] or package["nativecode"]=="all":
                if str(self.apps()[app]["suggestedVersionCode"]) == str(package["versionCode"]):
                    return package

    def latest_package(self, app: str, arch: str):
        for package in self.packages(app):
            if arch in package["nativecode"]:
                return package

    def search(self, term):
        from thefuzz import fuzz
        results = []
        apps_list = self.apps()
        for app in apps_list:
            if fuzz.token_set_ratio(term, str(apps_list[app])) == 100:
                results.append(apps_list[app])
        return results

    def version_code(self, app, version_name):
        for package in self.packages(app):
            if app == package:
                for apk in self.data["packages"][app]:
                    if apk["versionName"] == version_name:
                        return apk["versionCode"]

    def subscribe(self, repo: str):
        repo_ = self.load(repo)
        cache_put("REPO_SUBS", repo_, "1")

    def load_subscribed(self):
        subs = cache_get_all("REPO_SUBS")
        if not subs:
            self.subscribe("F-Droid")
        subs = cache_get_all("REPO_SUBS")
        for repo_sub in subs:
            self.quick_load(repo_sub)

    @staticmethod
    def subscribed_repos():
        return cache_get_all("REPO_SUBS")

    @staticmethod
    def age(repo):
        dl_dir = f"{share_dir()}/repos"
        time_now = int(time.time())
        time_modified = int(os.path.getmtime(f'{dl_dir}/{repo}/index-v1.json'))
        return int((time_now - time_modified) / 60)


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
        version = self.repo.suggested_package(id_, self.user.cpu())["versionCode"]
        if self.installed_package_version(id_) < version:
            return version
        else:
            return 0

    def latest_outdated(self, id_: str):
        """
        Returns newer 'latest' version if available, 0 otherwise
        :param id_: Package name
        :return: Newer 'latest' version if available, 0 otherwise
        """
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
                new_version = self.suggested_outdated(package_id)
                if new_version:
                    packages.append(f"https://f-droid.org/repo/{package_id}_{new_version}.apk")
            if not suggested and self.latest_outdated(package_id):
                new_version = self.latest_outdated(package_id)
                if new_version:
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
        :param repo_name:
        :param id_: List of package names
        :return: list[str]:
        """
        # self.repo.load(repo_name)
        package = self.repo.suggested_package(id_, self.user.cpu())
        address = self.repo.address(package['repo'])
        if not "/repo" in address:
            address.join('/repo')
        url = f"{address}/{package['apkName']}"
        print(url)
        return url

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
            with tqdm(total=len(ids), desc=f"Installing apk", colour='blue') as pbar:
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
        user_id = f"--user 0"
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
        user_id = f"--user 0"
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

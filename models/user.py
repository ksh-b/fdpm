import os
import subprocess

from models.package import Package
from helpers.util import command, adb_connected


def installed_packages(installer_keyword, user=0) -> list:
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
                        packages.append(Package(
                            id_=package_id,
                            installer=installer
                        ))
        except subprocess.CalledProcessError as e:
            print(f"Failed to check package version for", e.output)
    return packages


def package_installed(package) -> bool:
    for installed_package in installed_packages('fdroid.cli'):
        if package.id_ == installed_package.id_:
            return True
    return False


# return if user is using android
def android() -> bool:
    return "android" in str(os.environ).lower()

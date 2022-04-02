import argparse
import getopt
import glob
import os
import sys

from fdpm.box import main_menu, dialog_clear
from fdpm.util import download_dir
from fdpm.models import Repo
from fdpm.models import Installer
from fdpm.models import User

version = "0.0.77"

def main():
    options, remainder = getopt.getopt(
        sys.argv[1:],
        'acdhi:ln:rs:vu',
        ['add', 'clean', 'dialog', 'help', 'install=', 'list', 'uninstall=', 'version', 'search=', 'update']
    )

    for opt, arg in options:
        if opt in ('-a', '--add'):
            if len(sys.argv) == 2:
                for r in Repo().available():
                    print(r)
                sys.exit(0)
            repo = str(sys.argv[2:]).strip("[]").replace("'", "").replace(",", "")
            Repo().subscribe(repo)

        elif opt in ('-r', '--remove'):
            repo = str(sys.argv[2:]).strip("[]").replace("'", "").replace(",", "")
            Repo().unsubscribe(repo)

        elif opt in ('-d', '--dialog'):
            main_menu()
            dialog_clear()

        elif opt in ('-v', '--version'):
            print(version)

        elif opt in ('-s', '--search'):
            search_term = str(sys.argv[2:]).strip("[]").replace("'", "").replace(",", "")
            print(f"Searching for '{search_term}'...")
            apps = Repo().search(search_term)
            for app in apps:
                print("~", app["name"], f'- {app["packageName"]}')
                print(app["summary"].replace("\n", ""), "\n")

        elif opt in ('-i', '--install'):
            ids = (sys.argv[2:])
            Installer().install_all(ids)

        elif opt in ('-n', '--uninstall'):
            ids = (sys.argv[2:])
            Installer().uninstall_all(ids)

        elif opt in ('-u', '--update'):
            if packages := Installer().outdated_packages():
                Installer().install_all(packages)
            else:
                print("Already up to date")

        elif opt in ('-c', '--clean'):
            files = glob.glob(f"{download_dir()}/*.apk")
            for file in files:
                os.remove(file)

        elif opt in ('-l', '--installed'):
            print(
                str(User().installed_packages('fdroid.cli'))
                .replace(", ", "\n")
                .replace("'", "")
                .strip("[]")
            )

        else:
            parser = argparse.ArgumentParser(description='fdroid-cli ~ Install packages from f-droid',
                                             prog='python __main__.py')
            parser.add_argument('-a', '--add', required=False, help='Add repository', action="store")
            parser.add_argument('-c', '--clean', required=False, help='Empty download directory', action="store_false")
            parser.add_argument('-d', '--dialog', required=False, help='Use dialog interface', action="store_false")
            parser.add_argument('-i', '--install', required=False, help='Install apps from package names',
                                action="extend",
                                nargs='+', type=list)
            parser.add_argument('-l', '--installed', required=False, help='View installed apps', action="store_false")
            parser.add_argument('-n', '--uninstall', required=False, help='Uninstall apps from package names',
                                action="extend",
                                nargs='+')
            parser.add_argument('-r', '--remove', required=False, help='Remove repository', action="store")
            parser.add_argument('-s', '--search', required=False, help='Search for apps', action="store")
            parser.add_argument('-u', '--update', required=False, help='Update outdated apps', action="store_false")
            parser.parse_args()


if __name__ == "__main__":
    sys.exit(main())

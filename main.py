import argparse
import getopt
import glob
import os
import sys

from helpers.util import download_dir
from models import user
from models.fdroid import search
from models.installer import install_all, uninstall_all, outdated_packages
from views.box import main_menu, dialog_clear

options, remainder = getopt.getopt(
    sys.argv[1:],
    'cdhi:ln:s:u',
    ['clean', 'dialog', 'help', 'install=', 'list', 'uninstall=', 'search=', 'update']
)

for opt, arg in options:
    if opt in ('-d', '--dialog'):
        main_menu()
        dialog_clear()
    elif opt in ('-s', '--search'):
        packages = search(arg)
        for package in packages:
            print(package.name, f"({package.id_})")
            print(package.description, "\n")
    elif opt in ('-i', '--install'):
        ids = (sys.argv[2:])
        install_all(ids)
    elif opt in ('-n', '--uninstall'):
        ids = (sys.argv[2:])
        uninstall_all(ids)
    elif opt in ('-u', '--update'):
        install_all(outdated_packages())
    elif opt in ('-c', '--clean'):
        files = glob.glob(f"{download_dir()}/*.apk")
        for f in files:
            os.remove(f)
    elif opt in ('-l', '--installed'):
        print(
            str(user.installed_packages('fdroid.cli'))
            .replace(", ", "\n")
            .replace("'", "")
            .strip("[]")
        )

    else:
        parser = argparse.ArgumentParser(description='fdroid-cli ~ Install packages from f-droid',
                                         prog='python main.py')
        parser.add_argument('-c', '--clean', required=False, help='Empty download directory', action="store_false")
        parser.add_argument('-d', '--dialog', required=False, help='Use dialog interface', action="store_false")
        parser.add_argument('-i', '--install', required=False, help='Install apps from package names', action="extend",
                            nargs='+', type=list)
        parser.add_argument('-l', '--installed', required=False, help='View installed apps', action="store_false")
        parser.add_argument('-n', '--uninstall', required=False, help='Uninstall apps from package names',
                            action="extend",
                            nargs='+')
        parser.add_argument('-s', '--search', required=False, help='Search for apps', action="store")
        parser.add_argument('-u', '--update', required=False, help='Update outdated apps', action="store_false")
        parser.parse_args()

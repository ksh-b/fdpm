import getopt
import glob
import os
import sys

from helpers.util import download_dir
from models.fdroid import search
from models.installer import install, uninstall, update_outdated_packages, outdated_packages
from models.package import Package
from views.box import main_menu, dialog_clear

options, remainder = getopt.getopt(
    sys.argv[1:],
    'cdi:n:s:u',
    ['clean','dialog', 'install=', 'uninstall=', 'search=', 'update']
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
        for id_ in ids:
            app = Package(id_=id_)
            if install(app):
                print(f"Installed {id_}")
            else:
                print(f"Failed to install {id_}")
    elif opt in ('-n', '--uninstall'):
        ids = (sys.argv[2:])
        for id_ in ids:
            app = Package(id_=id_)
            if uninstall(app):
                print(f"Un-installed {id_}")
            else:
                print(f"Failed to un-install {id_}")
    elif opt in ('-u', '--update'):
        if sys.argv[2:]:
            packages = outdated_packages()
            for package in packages:
                if install(package):
                    print(f"Updated {package.id_}")
                else:
                    print(f"Failed to update {package.id_}")
        else:
            print(f"Downloading updates for {outdated_packages()}")
            if update_outdated_packages():
                print(f"Updated outdated packages")
            else:
                print(f"Failed to update packages")
    elif opt in ('-c', '--clean'):
        files = glob.glob(f"{download_dir()}/*.apk")
        for f in files:
            os.remove(f)
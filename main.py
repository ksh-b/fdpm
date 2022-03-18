import getopt
import os
import sys

from dialog import Dialog

from models import fdroid, installer
from models.fdroid import search
from models.installer import install, uninstall, update_outdated_packages, outdated_packages
from models.package import Package
from models.user import installed_packages

options, remainder = getopt.getopt(
    sys.argv[1:],
    'di:n:s:u',
    ['dialog', 'install=', 'uninstall=', 'search=', 'update']
)

d = Dialog(dialog="dialog")


# TODO: Add description box
def dialog_search(select_multiple=False):
    i = 0
    choices = []
    code_, value = d.inputbox(text="Search for app")
    if not value:
        say("No search term was entered")
        main_menu()
        return
    d.gauge_start(f"Searching for {value} on f-droid...", percent=0)
    __packages = fdroid.search(value)
    d.gauge_update(percent=100)
    d.gauge_stop()
    for __package in __packages:
        i += 1
        choices.append((__package.url.split("/")[-1], __package.name, False, __package.description))
    if select_multiple:
        code_, tag = d.checklist(
            text=f"Search results for '{value}'",
            choices=choices,
            item_help=True
        )
    else:
        code_, tag = d.radiolist(
            text=f"Search results for '{value}'",
            choices=choices,
            item_help=True
        )
    return code_, tag


def dialog_install():
    code, __ids = dialog_search(True)
    selected = len(__ids)
    if not selected:
        say("No apps were selected to install")
        main_menu()
        return
    if code == "ok":
        d.gauge_start(f"Installing {selected} apps...", percent=0)
        for __id in __ids:
            __app = Package(id_=__id)
            # TODO: Check return code for install
            installer.install(__app)
            selected -= 1
            d.gauge_update(
                text=f"Installing {__app.name}...",
                percent=int(100 / selected)
            )
        d.gauge_stop()
        say("Installed app(s)")
    else:
        say("Install failed")
    main_menu()


def dialog_uninstall():
    i = 0
    __ids = []
    __packages = installed_packages('fdroid')
    if not __packages:
        say("No packages to uninstall")
        main_menu()
        return
    for __package in __packages:
        i += 1
        __ids.append(
            (__package.id_, __package.name, False, f"Installed with {__package.installer}"))
    if not __ids:
        say("No packages to uninstall")
        main_menu()
        return
    code_, tags = d.checklist(
        text=f"Select apps to uninstall",
        choices=__ids,
        item_help=True
    )
    if not tags:
        say("No packages selected to uninstall")
        main_menu()
        return
    if code_ == "ok":
        selected = len(tags)
        d.gauge_start(f"Un-installing {selected} apps...", percent=0)
        for __id in tags:
            __app = Package(id_=__id)
            installer.uninstall(__app)
            selected -= 1
            d.gauge_update(
                text=f"Uninstalling {__app.name}...",
                percent=int(100 / selected)
            )
        d.gauge_stop()
        say("Uninstalled app(s)")
    else:
        say("Failed to uninstall app(s)")
    main_menu()


def dialog_update():
    clear()
    __packages = outdated_packages()
    if not __packages:
        say("All packages up to date 😊")
        main_menu()
        return

    __choices = []
    for __package in __packages:
        __choices.append((__package.id_, __package.name, True, __package.installer))

    code_, tags = d.checklist(
        text=f"Select apps to update",
        choices=__choices,
        item_help=True
    )
    if not tags:
        say("No packages selected to update")
        main_menu()
        return
    if code_ == "ok":
        selected = len(tags)
        d.gauge_start(f"Updating {selected} apps...", percent=0)
        for __id in tags:
            __app = Package(id_=__id)
            installer.install(__app)
            selected -= 1
            d.gauge_update(
                text=f"Updating {__app.name}",
                percent=int(100 / selected)
            )
        d.gauge_stop()
        say("Updated app(s)")
    else:
        say("Failed to update app(s)")
    main_menu()
    return


def say(msg):
    d.msgbox(msg)


def clear():
    os.system("clear")


def main_menu():
    code_, tag = d.radiolist(
        text="fdroid-cli",
        choices=(
            ("Search", "Search apps on fdroid", False),
            ("Install", "Install apps from fdroid", True),
            ("Update", "Update apps installed from fdroid", False),
            ("Uninstall", "Uninstall apps installed from fdroid", False),
            ("Exit", "Close dialog", False),
        )
    )
    if tag == "Search":
        dialog_search()
    if tag == "Install":
        dialog_install()
    if tag == "Uninstall":
        dialog_uninstall()
    if tag == "Update":
        dialog_update()
    if tag == "Exit":
        clear()


for opt, arg in options:
    if opt in ('-d', '--dialog'):
        main_menu()
        clear()
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

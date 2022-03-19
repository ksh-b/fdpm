import os

from dialog import Dialog

from models import fdroid, installer
from models.installer import outdated_packages
from models.package import Package
from models.user import installed_packages

d = Dialog(dialog="dialog")


# TODO: Add description box
def dialog_search(select_multiple=False):
    i = 0
    choices = []
    code_, value = d.inputbox(text="Search for app")
    if not value:
        dialog_say("No search term was entered")
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
        dialog_say("No apps were selected to install")
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
        dialog_say("Installed app(s)")
    else:
        dialog_say("Install failed")
    main_menu()


def dialog_uninstall():
    i = 0
    __ids = []
    __packages = installed_packages('fdroid')
    if not __packages:
        dialog_say("No packages to uninstall")
        main_menu()
        return
    for __package in __packages:
        i += 1
        __ids.append(
            (__package.id_, __package.name, False, f"Installed with {__package.installer}"))
    if not __ids:
        dialog_say("No packages to uninstall")
        main_menu()
        return
    code_, tags = d.checklist(
        text=f"Select apps to uninstall",
        choices=__ids,
        item_help=True
    )
    if not tags:
        dialog_say("No packages selected to uninstall")
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
        dialog_say("Uninstalled app(s)")
    else:
        dialog_say("Failed to uninstall app(s)")
    main_menu()


def dialog_update():
    dialog_clear()
    __packages = outdated_packages()
    if not __packages:
        dialog_say("All packages up to date 😊")
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
        dialog_say("No packages selected to update")
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
        dialog_say("Updated app(s)")
    else:
        dialog_say("Failed to update app(s)")
    main_menu()
    return


def dialog_say(msg):
    d.msgbox(msg)


def dialog_clear():
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
        dialog_clear()
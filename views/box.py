import os

from dialog import Dialog

from models import fdroid
from models.installer import outdated_packages, install_all, uninstall_all
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
        choices.append((__package, __packages[__package][0][0], False, __packages[__package][1][0]))
    if select_multiple:
        code_, tag = d.checklist(
            text=f"Search results for '{value}'",
            choices=choices,
            item_help=True,
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
    if code != "ok":
        dialog_say(f"Some error occurred (code={code})")
        main_menu()
    else:
        dialog_clear()
        install_all(__ids)


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
            (__package, "", False))
    if not __ids:
        dialog_say("No packages to uninstall")
        main_menu()
        return
    code_, tags = d.checklist(
        text="Select apps to uninstall",
        choices=__ids,
    )
    if not tags:
        dialog_say("No packages selected to uninstall")
        main_menu()
        return
    if code_ != "ok":
        dialog_say(f"Some error occurred (code={code_})")
        main_menu()
    else:
        dialog_clear()
        uninstall_all(tags)


def dialog_update():
    d.gauge_start(f"Checking for outdated packages...", percent=0)
    __packages = outdated_packages()
    d.gauge_update(100)
    d.gauge_stop()
    __choices = []
    if not __packages:
        dialog_say("All packages up to date 😊")
        main_menu()
        return

    for __package in __packages:
        __choices.append((__package, "", True,))
    code_, tags = d.checklist(
        text="Select apps to update",
        choices=__choices,
    )
    if not tags:
        dialog_say("No packages selected to update")
        main_menu()
        return
    if code_ != "ok":
        dialog_say(f"Some error occurred (code={code_})")
        main_menu()
    else:
        dialog_clear()
        install_all(tags)


def dialog_say(msg):
    d.msgbox(msg)


def dialog_clear():
    os.system("clear")


def main_menu():
    code_, tag = d.radiolist(
        text="fdroid-cli",
        choices=(
            # ("Search", "Search apps", False),
            ("Install", "Search and install apps", True),
            ("Update", "Update installed apps", False),
            ("Uninstall", "Uninstall/View installed apps", False),
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

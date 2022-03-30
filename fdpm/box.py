import os

from dialog import Dialog
from fdpm.models import Repo
from fdpm.models import Installer
from fdpm.models import User

d = Dialog(dialog="dialog")


def dialog_search(select_multiple=False):
    code_, value = d.inputbox(text="Search for app")
    if not value:
        dialog_say("No search term was entered")
        main_menu()
        return
    d.gauge_start(f"Searching for {value}...", percent=0)
    __packages = Repo().search(value)
    d.gauge_update(percent=100)
    d.gauge_stop()
    choices = [
        (
            __package["packageName"],
            __package["name"],
            False,
            __package["summary"],
        )
        for __package in __packages
    ]

    if select_multiple:
        return d.checklist(
            text=f"Search results for '{value}'",
            choices=choices,
            item_help=True,
        )
    code_, tag = d.radiolist(
        text=f"Search results for '{value}'",
        choices=choices,
        item_help=True
    )
    if code_ == "ok":
        for __package in __packages:
            if __package["packageName"] == tag:
                d.msgbox(str(__package["description"]), width=150, height=150)
                d.radiolist(
                    text=f"Search results for '{value}'",
                    choices=choices,
                    item_help=True
                )


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
        input()
        dialog_clear()
        Installer().install_all(__ids)


def dialog_uninstall():
    __packages = User().installed_packages('fdroid')
    if not __packages:
        dialog_say("No packages to uninstall")
        main_menu()
        return
    __ids = [(__package, "", False) for __package in __packages]
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
        Installer().uninstall_all(tags)


def dialog_update():
    d.gauge_start("Checking for outdated packages...", percent=0)
    __packages = Installer().outdated_packages()
    d.gauge_update(100)
    d.gauge_stop()
    if not __packages:
        dialog_say("All packages up to date 😊")
        main_menu()
        return

    __choices = [(__package, "", True,) for __package in __packages]
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
        Installer().install_all(tags)


def dialog_subscriptions():
    all_repos = Repo().available()
    sub_repos = Repo().subscribed_repos()
    __choices = [(repo, "", repo in sub_repos,) for repo in all_repos]
    code_, tags = d.checklist(
        text="Select apps to update",
        choices=__choices,
    )
    dialog_clear()
    for repo in all_repos:
        if repo in tags and repo not in sub_repos:
            Repo().subscribe(repo)
        elif repo not in tags and repo in sub_repos:
            Repo().unsubscribe(repo)


def dialog_say(msg):
    d.msgbox(msg)


def dialog_clear():
    os.system("clear")


def main_menu():
    code_, tag = d.radiolist(
        text="fdroid-cli",
        choices=(
            ("Search", "Search apps", False),
            ("Install", "Search and install apps", True),
            ("Subscribe", "Subscribe to repos", True),
            ("Update", "Update installed apps", False),
            ("Uninstall", "Uninstall/View installed apps", False),
            ("Exit", "Close dialog", False),
        )
    )
    if tag == "Search":
        dialog_search()
    if tag == "Install":
        dialog_install()
    if tag == "Subscribe":
        dialog_subscriptions()
    if tag == "Uninstall":
        dialog_uninstall()
    if tag == "Update":
        dialog_update()
    if tag == "Exit":
        dialog_clear()

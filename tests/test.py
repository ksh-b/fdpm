import glob
import os

from fdpm.models import User
from fdpm.models import Repo
from fdpm.models import Installer
from fdpm.util import adb_connected, cache_get, download_dir

test_app_1 = "fly.speedmeter.grub"
test_app_2 = "net.basov.lws.fdroid"

u = User()
r = Repo()
i = Installer()

# check if adb is connected
assert adb_connected()

# search
search_results = str(r.search("speedmeter"))
assert test_app_1 in search_results

# subscribe
r.subscribe("Bromite")
assert "Bromite" in r.subscribed_repos()

# subscription search
search_results = str(r.search("bromite"))
assert "org.bromite" in search_results

# unsubscribe
r.unsubscribe("Bromite")
assert "Bromite" not in r.subscribed_repos()

# install
i.install_all([test_app_1, test_app_2])
installed = u.installed_packages("fdroid")
assert test_app_1 in installed
assert test_app_2 in installed

# uninstall
i.uninstall_all([test_app_1, test_app_2])
installed = u.installed_packages("fdroid")
assert test_app_1 not in installed
assert test_app_2 not in installed

# cache
assert cache_get("USER", "cpu")
assert cache_get("USER", "sdk")
assert cache_get("REPO_SUBS", "Bromite") == "0"

# clean up apks
files = glob.glob(f"{download_dir()}/*.apk")
map(lambda f: os.remove(f), files)

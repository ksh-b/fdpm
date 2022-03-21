from helpers.util import verify_apk
from models.fdroid import search
from models.installer import install_all, uninstall_all

# ids=["com.donnnno.arcticons","com.donnnno.arcticons.light"]
# assert "A monotone line-based icon pack" in str(search(ids[0].split(".")[-1]))
# install_all(ids)
# uninstall_all(ids)

print(verify_apk("/home/ksyko/Downloads/fdroid-cli/com.ketanolab.nusimi_6.apk", 4620865))

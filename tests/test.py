from fdpm.models.fdroid import search
from fdpm.models import install_all, uninstall_all

ids=["com.donnnno.arcticons","com.donnnno.arcticons.light"]
assert "A monotone line-based icon pack" in str(search(ids[0].split(".")[-1]))
install_all(ids)
uninstall_all(ids)

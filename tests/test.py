from models.installer import search_install
from models.package import Package
from models.user import package_installed

package = Package(id_="org.woheller69.eggtimer")
app = package.id_
assert search_install(app)
assert package_installed(package)
# assert uninstall(package)

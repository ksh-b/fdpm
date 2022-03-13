from installer import search_install, uninstall
from package import Package
from user import package_installed

package = Package(id_="org.woheller69.eggtimer")
app = package.id_
assert search_install(app)
assert package_installed(package)
assert uninstall(package)

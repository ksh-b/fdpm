from urllib.parse import quote_plus as encode

import requests
from bs4 import BeautifulSoup as bs

from package import Package


def search(query: str) -> list:
    packages = []
    query = encode(query, safe='')
    response = requests.get(f"https://search.f-droid.org/?q={query}").content
    soup = bs(response, 'html.parser')
    results = soup.find_all(class_="package-header")
    for result in results:
        packages.append(Package(
            name=result.find(class_="package-name").text.strip(),
            description=result.find(class_="package-summary").text.strip(),
            url=result.get('href')
        ))
    return packages


def versions(package):
    return requests.get(f"https://f-droid.org/api/v1/packages/{package.id_}").json()["packages"]


def latest_version(package):
    return versions(package)[0]["versionCode"]


def suggested_version(package):
    return requests.get(f"https://f-droid.org/api/v1/packages/{package.id_}").json()["suggestedVersionCode"]


def version_code(package, version_name):
    for version in versions(package):
        if version_name == version["versionName"]:
            return version["versionCode"]


# TODO
# noinspection PyUnusedLocal
def add_repo(package):
    pass

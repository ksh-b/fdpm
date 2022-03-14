from urllib.parse import quote_plus as encode

import requests
from bs4 import BeautifulSoup as bs

from models.package import Package


def search(query: str) -> list[Package]:
    """
    Performs search for the given query
        Parameters:
                query (str): Search term

        Returns:
                packages (list[Package]): List of Packages found for the query
    """
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


def versions(package: Package) -> list:
    """
    Finds all versions for given package
        Parameters:
                package (Package): Package

        Returns:
                packages (list): List of suggested and latest versions for the given package
    """
    return requests.get(f"https://f-droid.org/api/v1/packages/{package.id_}").json()["packages"]


def latest_version(package: Package) -> int:
    """
    Finds latest version for given package
        Parameters:
                package (Package): Package

        Returns:
                str : Returns latest version Code
    """
    return versions(package)[0]["versionCode"]


def suggested_version(package: Package) -> int:
    """
    Returns suggested version for given package
        Parameters:
                package (Package): Package

        Returns:
                str : Returns suggested version code
    """
    return requests.get(f"https://f-droid.org/api/v1/packages/{package.id_}").json()["suggestedVersionCode"]


def version_code(package: Package, version_name: str) -> int:
    """
    Returns corresponding version code for version name
        Parameters:
                package (Package): Package
                version_name (str): Version name of the package
        Returns:
                int : Returns version Code
    """
    for version in versions(package):
        if version_name == version["versionName"]:
            return version["versionCode"]


# TODO
# noinspection PyUnusedLocal
def add_repo(repo):
    """
    Add repo to check to search packages from
    """
    pass

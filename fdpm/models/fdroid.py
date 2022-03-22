from urllib.parse import quote_plus as encode

import requests
from bs4 import BeautifulSoup as bs


def search(query: str) -> dict:
    """
    Performs search for the given query
        Parameters:
                query (str): Search term

        Returns:
                packages (list[Package]): List of Packages found for the query
    """
    packages = {}
    query = encode(query, safe='')
    response = requests.get(f"https://search.f-droid.org/?q={query}")
    if response.status_code == 200:
        soup = bs(response.content, 'html.parser')
        results = soup.find_all(class_="package-header")
        for result in results:
            name = result.find(class_="package-name").text.strip(),
            description = result.find(class_="package-summary").text.strip(),
            url = result.get('href')
            id_ = url.split("/")[-1]
            packages[id_] = (name, description, url)
        return packages
    else:
        return {}


def versions(id_: str) -> list:
    """
    Finds all versions for given package
        Parameters:
                id_ (str): Package id

        Returns:
                packages (list): List of suggested and latest versions for the given package
    """
    response = requests.get(f"https://f-droid.org/api/v1/packages/{id_}")
    if response.status_code == 200:
        return response.json()["packages"]
    else:
        return []


def latest_version(id_) -> int:
    """
    Finds latest version for given package
        Parameters:
                id_ (str): Package id

        Returns:
                str : Returns latest version Code
    """
    versions_ = versions(id_)
    if versions_:
        return versions_[0]["versionCode"]
    else:
        return 0


def suggested_version(id_) -> int:
    """
    Returns suggested version for given package
        Parameters:
                id_ (str): Package id

        Returns:
                str : Returns suggested version code
    """

    response = requests.get(f"https://f-droid.org/api/v1/packages/{id_}")
    if response.status_code == 200:
        return response.json()["suggestedVersionCode"]
    else:
        return 0


def version_code(id_, version_name: str) -> int:
    """
    Returns corresponding version code for version name
        Parameters:
                id_ (str): Package id
                version_name (str): Version name of the package
        Returns:
                int : Returns version Code
    """
    versions_ = versions(id_)
    if versions_:
        for version in versions_:
            if version_name == version["versionName"]:
                return version["versionCode"]
    else:
        return 0

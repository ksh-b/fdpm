import json
import os

from fdpm.helpers.util import download_dir, download

data = {}


def load(repo: str = "F-Droid"):
    """
    Downloads repo index
    :param repo:
    """
    repos_url = "https://gitlab.com/AuroraOSS/auroradroid/-/raw/master/app/src/main/assets/repo.json"
    repo_url = "https://f-droid.org/repo"
    index_file = f'repos/{repo}/index-v1.json'
    repos_file = f'repos/repo.json'
    dl_dir = download_dir()

    # download repos list
    if not os.path.exists(repos_file):
        download(repos_url, repos_file)

    # open repos list
    f = open(f"{dl_dir}/{repos_file}")
    print(f"{dl_dir}/{repos_file}")
    repos_data = json.load(f)
    for repo_ in repos_data:
        if repo.lower() in repo_["repoName"].lower():
            repo = repo_["repoName"]
            repo_url = repo_["repoUrl"]

    # download index
    if not os.path.exists(f"{dl_dir}/{index_file}"):
        download(f"{repo_url}/index-v1.json", index_file)

    # open index
    global data
    f = open(f"{dl_dir}/{index_file}")
    data = json.load(f)
    f.close()


def address():
    return data['repo']['address']


def apps():
    i = 0
    apps_list = {}
    for app in data["apps"]:
        i += 1
        version = app["suggestedVersionCode"]
        name = app["packageName"]
        if "localized" in app:
            localized = app["localized"]
            if "en-US" in localized:
                en = localized["en-US"]
            elif "en-GB" in localized:
                en = localized["en-GB"]
            else:
                continue
            if "description" in en:
                description = en["description"]
            else:
                description = ""
            if "summary" in en:
                summary = en["summary"]
            else:
                summary = app["description"]
            apps_list[name] = {
                "name": name,
                "version": version,
                "description": description,
                "summary": summary,
            }
    return apps_list



def search(term):
    results = []
    apps_list = apps()
    for app in apps_list:
        if term in str(app):
            results.append(apps_list[app])
    return results

import requests
import re
from heroku_client.constants import HEROKU_API_URL
from heroku_client.exceptions import HerokuException
from heroku_client import authorization

HEROKU_API_KEY = authorization.get_api_key()

headers = {
    "Accept": "application/vnd.heroku+json; version=3",
    "Authorization": f"Bearer {HEROKU_API_KEY}",
}


def handle_error(response):

    try:
        response.raise_for_status()
    except requests.exceptions.RequestException as exc:
        # Show error from API
        print(response.json())
        raise HerokuException(f"{exc.args}") from exc


def create_app(app_name):
    """
    app_name should conform to the pattern as specified in the Heroku API.
    Returns the response from the server.
    """

    name_regex = re.compile(r"^[a-z][a-z0-9-]{1,28}[a-z0-9]$")
    if name_regex.search(app_name) is None:
        raise ValueError(
            "Improper name configuration. Names must begin with an alphabet, can consist of numbers and hyphens as seperators."
        )
    payload = {"name": app_name}
    response = requests.post(HEROKU_API_URL, headers=headers, data=payload)
    handle_error(response)
    return response.json()


def get_app_info(app_name_or_id):
    """
    Gets the details about an app given its app_name_or_id.
    """
    response = requests.get(f"{HEROKU_API_URL}/{app_name_or_id}", headers=headers)
    handle_error(response)
    return response.json()


def get_commit_sha(git_url, branch="main"):
    """
    github_url => URL of the Github repository.
    branch => repository branch name

    Returns the recent commit SHA of the code.
    """

    headers = {"Accept": "application/vnd.github.v3+json"}
    github_regex = re.compile(
        r"(?:https?://)?(?:www.)?github.com/(?P<user>.*)/(?P<repo>.*)/?"
    )
    parser = github_regex.search(git_url)
    if parser is not None:
        m = parser.groupdict()
        response = requests.get(
            f'https://api.github.com/repos/{m["user"]}/{m["repo"]}/branches/{branch}',
            headers=headers,
        )
        handle_error(response)
        data = response.json()
        return data["commit"]["sha"]
    raise ValueError(
        "Improperly configured GitHub URL. Check to see the link is correct"
    )


def build_from_source(git_url, app_name_or_id, branch="main", version=None):
    """
    git_url => github repository url of the source code.
    app_name_or_id => the application's name or id on Heroku. Use the `get_app_info` utility
                        to get the application's details.
    branch => the git branch to get the source code from. Defaults to `main`.
    version => A piece of metadata that you use to track what version of your
                source code originated this build. If version is not specified,
                will use the commit hash from the git_url as the version.
    ==========================================================================

    This will cause Heroku to fetch the source tarball, unpack it and start a
    build, just as if the source code had been pushed to Heroku using git. If
    the build completes successfully, the resulting slug will be deployed
    automatically to the app in a new release.

    (https://devcenter.heroku.com/articles/build-and-release-using-the-api#creating-builds)
    ==========================================================================
    """

    payload = {"source_blob": {"url": f"{git_url}/tarball/{branch}"}}

    if version is not None:
        payload["source_blob"]["version"] = version
    else:
        version = get_commit_sha(git_url, branch)
        payload["source_blob"]["version"] = version

    response = requests.post(
        f"{HEROKU_API_URL}/{app_name_or_id}/builds", headers=headers, json=payload
    )
    handle_error(response)
    return response.json()

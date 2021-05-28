import requests
import json
from .exceptions import HerokuException
import re


def handle_error(response):

    try:
        response.raise_for_status()
    except requests.exceptions.RequestException as exc:
        try:
            # Show error from API
            message = response.json()
        except json.JSONDecodeError:
            raise HerokuException(f"{exc.args}") from exc
        else:
            raise HerokuException(message) from exc


def get_commit_sha(git_url, branch="main"):
    """
    github_url => URL of the Github repository.
    branch => repository branch name

    Returns the recent commit SHA of the code.
    """

    headers = {"Accept": "application/vnd.github.v3+json"}
    github_regex = re.compile(
        r"^(?:https?://)?(?:www\.)?github.com/(?P<user>.*)/(?P<repo>.*)/?$"
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
        "Improperly configured GitHub URL. Check to see the repository URL is correct and is a public repository."
    )

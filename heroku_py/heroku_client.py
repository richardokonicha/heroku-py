import requests
import re
import time
from .constants import HEROKU_API_URL
from . import authorization
from .utilities import get_commit_sha, handle_error


class HerokuClient:
    def __init__(self, api_key=None):
        """
        Create an instance of a heroku client for making API requests.
        If api_key is None, will try to load API key from .netrc file in
        current user's home directory or load from environment variable
        HEROKU_API_KEY.
        """

        if api_key is None:
            self.HEROKU_API_KEY = authorization.get_api_key()
        else:
            self.HEROKU_API_KEY = api_key

        self.headers = {
            "Accept": "application/vnd.heroku+json; version=3",
            "Authorization": f"Bearer {self.HEROKU_API_KEY}",
        }

    def create_app(self, app_name):
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
        response = requests.post(HEROKU_API_URL, headers=self.headers, json=payload)
        handle_error(response)
        return response.json()

    def get_app_info(self, app_name_or_id):
        """
        Gets the details about an app given its app_name_or_id.
        """
        response = requests.get(
            f"{HEROKU_API_URL}/{app_name_or_id}", headers=self.headers
        )
        handle_error(response)
        return response.json()

    def delete_app(self, app_name_or_id):
        """
        Deletes an app given its app_name_or_id.
        """
        _headers = self.headers.copy()
        _headers["Content-Type"] = "application/json"

        response = requests.delete(
            f"{HEROKU_API_URL}/{app_name_or_id}", headers=_headers
        )
        handle_error(response)
        return response.json()

    def list_apps(self):
        """
        List existing apps.
        """
        response = requests.get(f"{HEROKU_API_URL}", headers=self.headers)
        handle_error(response)
        return response.json()

    def build_from_git(
        self, git_url, app_name_or_id, branch="main", version=None, delay=1.5
    ):
        """
        git_url => github repository url of the source code.
        app_name_or_id => the application's name or id on Heroku. Use the `get_app_info` utility
                            to get the application's details.
        branch => the git branch to get the source code from. Defaults to `main`.
        version => A piece of metadata that you use to track what version of your
                    source code originated this build. If version is not specified,
                    will use the commit hash from the git_url as the version.
        delay => How long it takes in seconds to get the build status change from
                `pending` to `succeeded` or `failed`.
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
            f"{HEROKU_API_URL}/{app_name_or_id}/builds",
            headers=self.headers,
            json=payload,
        )
        handle_error(response)
        build_details = response.json()
        # Poll the API until app status changes from pending to either "succeeded" or "failed"
        status = build_details["status"]
        app_id = build_details["app"]["id"]
        build_id = build_details["id"]

        while status == "pending":
            time.sleep(delay)
            response = requests.get(
                f"{HEROKU_API_URL}/{app_id}/builds/{build_id}", headers=self.headers
            )
            handle_error(response)
            build_details = response.json()
            status = build_details["status"]

        return build_details

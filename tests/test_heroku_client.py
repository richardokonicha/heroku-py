"""
Test execution matters as app creation is intended first and app deletion should
be the last test to execute.
"""

from heroku_py.heroku_client import HerokuClient

hk = HerokuClient()
git_url = "https://github.com/elfkuzco/heroku-py-testing-repo"
repo_sha = str(hash(git_url)).strip("-")
app_name = "wonder-beetle-" + repo_sha[:6]


def test_create_app():
    app = hk.create_app(app_name)
    assert app["name"] == app_name


def test_get_app_info():
    app = hk.get_app_info(app_name)
    assert app["name"] == app_name


def test_build_from_git():
    build_details = hk.build_from_git(git_url, app_name)
    assert build_details["status"] in ["succeeded", "failed"]


def test_delete_app():
    app = hk.delete_app(app_name)
    assert app["name"] == app_name

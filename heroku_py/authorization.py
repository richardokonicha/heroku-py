import netrc
import os
from .constants import HEROKU_API_BASE, HEROKU_API_KEY
from . import exceptions


def get_api_key_from_netrc():
    """Loads HEROKU_API_KEY from .netrc file in  the user's home directory.
    Returns the key if it the file exists, else None."""
    n = netrc.netrc()
    if HEROKU_API_BASE in n.hosts:
        return n.authenticators(HEROKU_API_BASE)[2]
    return None


def get_api_key_from_env():
    """Returns value from HEROKU_API_KEY user environment variable.
    if variable exist else None.
    """
    api_key = os.environ.get(HEROKU_API_KEY)
    return api_key if api_key is not None else None


def get_api_key():
    api_key = get_api_key_from_env()
    if api_key is None:
        # load from .netrc file
        try:
            api_key = get_api_key_from_netrc()
        except netrc.NetrcParseError as exc:
            raise exceptions.HerokuException(
                "Could not parse the .netrc file."
            ) from exc
        except FileNotFoundError as exc:
            raise exceptions.HerokuException(
                "Ensure that a .netrc file exists in your home directory."
            ) from exc
        else:
            # If api_key is still None, raise HerokuException
            if api_key is None:
                raise exceptions.HerokuException(
                    (
                        "Could not load the API key to be used for making requests."
                        " Ensure that you either have a .netrc file in your home directory"
                        " or set your API key to the user environment variable $HEROKU_API_KEY."
                    )
                )
    return api_key

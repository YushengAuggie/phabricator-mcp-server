"""Compatibility module for different versions of the phabricator package."""

import sys
from typing import Any


def get_phabricator_class():
    """Get the Phabricator class from various possible locations."""
    # Try different import patterns
    attempts = [
        lambda: __import__('phabricator').Phabricator,
        lambda: __import__('phabricator.client', fromlist=['Phabricator']).Phabricator,
        lambda: __import__('phabricator', fromlist=['Phabricator']).Phabricator,
    ]

    for attempt in attempts:
        try:
            return attempt()
        except (ImportError, AttributeError):
            continue

    # If we get here, check what's actually in the phabricator module
    try:
        import phabricator

        print(f"phabricator module contents: {dir(phabricator)}", file=sys.stderr)

        # Try to find any class that might be the client
        for attr_name in dir(phabricator):
            attr = getattr(phabricator, attr_name)
            if isinstance(attr, type) and 'phabricator' in attr_name.lower():
                return attr
    except ImportError:
        pass

    raise ImportError(
        "Could not find Phabricator class in the phabricator package. "
        "The installed version may be incompatible."
    )


def create_phabricator_client(host: str, token: str) -> Any:
    """Create a Phabricator client instance compatible with different package versions."""
    Phabricator = get_phabricator_class()

    # Try different initialization patterns
    try:
        # Standard pattern
        client = Phabricator(host=host, token=token)
    except TypeError:
        try:
            # Alternative pattern with different parameter names
            client = Phabricator(api_host=host, api_token=token)
        except TypeError:
            try:
                # Another alternative
                client = Phabricator()
                client.host = host
                client.token = token
            except Exception as e:
                raise ImportError(f"Could not initialize Phabricator client: {e}")

    # Try to update interfaces if the method exists
    if hasattr(client, 'update_interfaces'):
        try:
            client.update_interfaces()
        except Exception:
            # Some versions might not need this or might do it automatically
            pass

    return client

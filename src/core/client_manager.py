"""Client manager for handling Phabricator API client with hybrid authentication."""

import os

from .client import PhabricatorAPIError, PhabricatorClient


class ClientManager:
    """Manages PhabricatorClient instances with hybrid authentication.

    Features:
    - Supports both personal API tokens and environment variable fallback
    - Personal tokens take precedence for user attribution
    - Environment variable used as fallback for shared/default usage
    - Lazy initialization for both approaches
    """

    def __init__(self):
        """Initialize the client manager."""
        self._default_client: PhabricatorClient | None = None

    def get_client(self, api_token: str | None = None) -> PhabricatorClient:
        """Get or create a PhabricatorClient instance.

        Args:
            api_token: Optional personal API token. If provided, creates a client with this token.
                      If None, uses environment variable as fallback.

        Returns:
            PhabricatorClient instance

        Raises:
            ValueError: If no token provided and environment variable not set
            PhabricatorAPIError: If client initialization fails
        """
        # If personal token provided, create client with that token
        if api_token and api_token.strip():
            try:
                return PhabricatorClient(token=api_token.strip())
            except Exception as e:
                raise PhabricatorAPIError(
                    f"Failed to create client with provided token: {str(e)}"
                ) from e

        # Otherwise, use default client with environment variable
        if self._default_client is None:
            env_token = os.getenv("PHABRICATOR_TOKEN")
            if not env_token or not env_token.strip():
                # Provide more helpful error message with debugging info
                available_env_vars = [
                    var
                    for var in os.environ.keys()
                    if 'PHAB' in var.upper() or 'TOKEN' in var.upper()
                ]
                error_msg = (
                    "No API token provided and PHABRICATOR_TOKEN environment variable is not set.\n"
                    "Solutions:\n"
                    "1. For HTTP/SSE transport: Set PHABRICATOR_TOKEN in your MCP client environment configuration\n"
                    "2. For stdio transport: Set PHABRICATOR_TOKEN in your MCP client environment configuration\n"
                    "3. Pass api_token parameter directly to tool calls\n"
                    "4. Create a .env file with PHABRICATOR_TOKEN=your-token-here\n"
                )
                if available_env_vars:
                    error_msg += f"\nEnvironment variables found: {', '.join(available_env_vars)}"
                else:
                    error_msg += "\nNo Phabricator-related environment variables found."

                raise ValueError(error_msg)

            try:
                self._default_client = PhabricatorClient(token=env_token.strip())
            except Exception as e:
                raise PhabricatorAPIError(f"Failed to create default client: {str(e)}") from e

        return self._default_client

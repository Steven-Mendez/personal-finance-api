from typing import Any, cast

from botocore.exceptions import ClientError
from structlog.stdlib import BoundLogger

from app.core.config import Settings

from ...exceptions import AuthenticationError
from ...logic import Authenticator


class CognitoAuthenticator(Authenticator):
    """
    Cognito implementation for user authentication.
    """

    def __init__(
        self,
        settings: Settings,
        logger: BoundLogger,
        cognito_client: Any,
    ) -> None:
        self.settings = settings
        self.logger = logger
        self.cognito_client = cognito_client

    async def login(self, email: str, password: str) -> dict[str, Any]:
        """Authenticate a user and return tokens."""
        self.logger.info("Authenticating user", email=email)
        try:
            response = self.cognito_client.initiate_auth(
                ClientId=self.settings.cognito_app_client_id,
                AuthFlow="USER_PASSWORD_AUTH",
                AuthParameters={
                    "USERNAME": email,
                    "PASSWORD": password,
                },
            )
            self.logger.info("User authenticated successfully", email=email)
            return cast(dict[str, Any], response["AuthenticationResult"])
        except ClientError as e:
            self.logger.error(
                "Failed to authenticate user in Cognito",
                email=email,
                error=str(e),
            )
            msg = e.response["Error"]["Message"]
            raise AuthenticationError(f"Authentication failed: {msg}") from e

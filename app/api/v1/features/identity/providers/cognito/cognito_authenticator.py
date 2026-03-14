from typing import Any

from botocore.exceptions import ClientError
from structlog.stdlib import BoundLogger

from app.api.v1.features.identity.exceptions import AuthenticationError
from app.api.v1.features.identity.logic import Authenticator
from app.api.v1.features.identity.schemas import TokenResponse
from app.core.config import Settings


class CognitoAuthenticator(Authenticator):
    """
    Cognito-based implementation of the Authenticator interface.
    Handles user login via AWS Cognito.
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

    async def login(self, email: str, password: str) -> TokenResponse:
        try:
            response = self.cognito_client.initiate_auth(
                AuthFlow="USER_PASSWORD_AUTH",
                AuthParameters={
                    "USERNAME": email,
                    "PASSWORD": password,
                },
                ClientId=self.settings.cognito_app_client_id,
            )
            auth_result = response["AuthenticationResult"]
            return TokenResponse(
                AccessToken=auth_result["AccessToken"],
                IdToken=auth_result["IdToken"],
                RefreshToken=auth_result["RefreshToken"],
                ExpiresIn=auth_result["ExpiresIn"],
                TokenType=auth_result["TokenType"],
            )
        except ClientError as e:
            self.logger.error("Cognito login failed", error=str(e))
            raise AuthenticationError(
                message=e.response["Error"]["Message"],
                data={"code": e.response["Error"]["Code"]},
            ) from e

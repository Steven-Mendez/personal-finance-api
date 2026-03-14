from typing import Any, cast

from botocore.exceptions import ClientError
from structlog.stdlib import BoundLogger

from app.core.config import Settings
from app.core.exceptions import UserManagementError
from app.services.auth import UserManager


class CognitoUserManager(UserManager):
    """
    Cognito implementation for user management.
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

    async def create_user(self, email: str, password: str) -> dict[str, Any]:
        """Create a user in Cognito User Pool."""
        self.logger.info("Creating new Cognito user", email=email)
        try:
            response = self.cognito_client.admin_create_user(
                UserPoolId=self.settings.cognito_user_pool_id,
                Username=email,
                UserAttributes=[
                    {"Name": "email", "Value": email},
                    {"Name": "email_verified", "Value": "true"},
                ],
                TemporaryPassword=password,
                MessageAction="SUPPRESS",
            )
            self.logger.info("Cognito user created successfully", email=email)
            return cast(dict[str, Any], response["User"])
        except ClientError as e:
            self.logger.error(
                "Failed to create user in Cognito",
                email=email,
                error=str(e),
            )
            msg = e.response["Error"]["Message"]
            raise UserManagementError(f"User creation failed: {msg}") from e

    async def list_users(self) -> list[dict[str, Any]]:
        """List all users in the configured Cognito User Pool."""
        self.logger.info(
            "Listing Cognito users",
            user_pool_id=self.settings.cognito_user_pool_id,
        )
        try:
            response = self.cognito_client.list_users(
                UserPoolId=self.settings.cognito_user_pool_id,
            )
            return cast(list[dict[str, Any]], response.get("Users", []))
        except ClientError as e:
            self.logger.error(
                "Failed to list users from Cognito",
                user_pool_id=self.settings.cognito_user_pool_id,
                error=str(e),
            )
            msg = e.response["Error"]["Message"]
            raise UserManagementError(f"Listing users failed: {msg}") from e

from typing import Any

from botocore.exceptions import ClientError
from structlog.stdlib import BoundLogger

from app.api.v1.features.identity.exceptions import UserManagementError
from app.api.v1.features.identity.logic import UserManager
from app.api.v1.features.identity.schemas import UserResponse
from app.core.config import Settings


class CognitoUserManager(UserManager):
    """
    Cognito-based implementation of the UserManager interface.
    Handles user creation and listing via AWS Cognito.
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

    async def create_user(self, email: str, password: str) -> UserResponse:
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
            user_data = response["User"]
            return UserResponse(
                Username=user_data["Username"],
                Attributes=user_data.get("Attributes"),
                UserCreateDate=user_data.get("UserCreateDate"),
                UserLastModifiedDate=user_data.get("UserLastModifiedDate"),
                Enabled=user_data.get("Enabled"),
                UserStatus=user_data.get("UserStatus"),
            )
        except ClientError as e:
            self.logger.error("Cognito user creation failed", error=str(e))
            raise UserManagementError(
                message=e.response["Error"]["Message"],
                data={"code": e.response["Error"]["Code"]},
            ) from e

    async def list_users(self) -> list[UserResponse]:
        try:
            response = self.cognito_client.list_users(
                UserPoolId=self.settings.cognito_user_pool_id,
            )
            users = response.get("Users", [])
            return [
                UserResponse(
                    Username=u["Username"],
                    Attributes=u.get("Attributes"),
                    UserCreateDate=u.get("UserCreateDate"),
                    UserLastModifiedDate=u.get("UserLastModifiedDate"),
                    Enabled=u.get("Enabled"),
                    UserStatus=u.get("UserStatus"),
                )
                for u in users
            ]
        except ClientError as e:
            self.logger.error("Cognito user listing failed", error=str(e))
            raise UserManagementError(
                message=e.response["Error"]["Message"],
                data={"code": e.response["Error"]["Code"]},
            ) from e

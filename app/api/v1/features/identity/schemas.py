from pydantic import BaseModel, EmailStr, SecretStr


class UserCreate(BaseModel):
    email: EmailStr
    password: SecretStr

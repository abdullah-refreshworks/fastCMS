"""
Pydantic schemas for OAuth2 endpoints.
"""

from pydantic import BaseModel, Field


class OAuthAccountResponse(BaseModel):
    """Schema for OAuth account response."""

    id: str
    provider: str = Field(..., description="OAuth provider name (google, github, microsoft)")
    provider_user_id: str = Field(..., description="User ID from OAuth provider")
    created: str

    class Config:
        from_attributes = True


class OAuthAccountsList(BaseModel):
    """Schema for list of OAuth accounts."""

    accounts: list[OAuthAccountResponse]


class OAuthUnlinkRequest(BaseModel):
    """Schema for unlinking OAuth account."""

    provider: str = Field(
        ..., description="OAuth provider to unlink (google, github, microsoft)"
    )

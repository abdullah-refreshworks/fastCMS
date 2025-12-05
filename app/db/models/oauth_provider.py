"""OAuth2 provider configuration model - like PocketBase's auth providers."""

from datetime import datetime, timezone
from sqlalchemy import Boolean, String, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.db.models.base import BaseModel


class OAuthProviderType:
    """Supported OAuth2 provider types (matching PocketBase's 25+ providers)."""

    # Social & Tech Platforms
    APPLE = "apple"
    DISCORD = "discord"
    FACEBOOK = "facebook"
    GITHUB = "github"
    GITLAB = "gitlab"
    GOOGLE = "google"
    INSTAGRAM = "instagram"
    KAKAO = "kakao"
    SPOTIFY = "spotify"
    STRAVA = "strava"
    TWITCH = "twitch"
    TWITTER = "twitter"
    YANDEX = "yandex"
    VK = "vk"

    # Development & Productivity
    BITBUCKET = "bitbucket"
    BOX = "box"
    GITEA = "gitea"
    GITEE = "gitee"
    LINEAR = "linear"
    LIVECHAT = "livechat"
    MONDAY = "monday"
    NOTION = "notion"
    PATREON = "patreon"
    PLANNINGCENTER = "planningcenter"
    WAKATIME = "wakatime"

    # Enterprise & Self-Hosted
    MAILCOW = "mailcow"
    OIDC = "oidc"  # Generic OpenID Connect
    LARK = "lark"
    MICROSOFT = "microsoft"

    @classmethod
    def all_types(cls) -> list:
        """Return all provider types."""
        return [
            cls.APPLE, cls.DISCORD, cls.FACEBOOK, cls.GITHUB, cls.GITLAB,
            cls.GOOGLE, cls.INSTAGRAM, cls.KAKAO, cls.SPOTIFY, cls.STRAVA,
            cls.TWITCH, cls.TWITTER, cls.YANDEX, cls.VK, cls.BITBUCKET,
            cls.BOX, cls.GITEA, cls.GITEE, cls.LINEAR, cls.LIVECHAT,
            cls.MONDAY, cls.NOTION, cls.PATREON, cls.PLANNINGCENTER,
            cls.WAKATIME, cls.MAILCOW, cls.OIDC, cls.LARK, cls.MICROSOFT,
        ]


# Provider metadata (display names, auth URLs, required fields)
PROVIDER_METADATA = {
    "apple": {
        "name": "Apple",
        "auth_url": "https://appleid.apple.com/auth/authorize",
        "token_url": "https://appleid.apple.com/auth/token",
        "required_fields": ["client_id", "client_secret", "team_id", "key_id"],
        "optional_fields": ["private_key"],
        "scopes": ["name", "email"],
    },
    "discord": {
        "name": "Discord",
        "auth_url": "https://discord.com/api/oauth2/authorize",
        "token_url": "https://discord.com/api/oauth2/token",
        "required_fields": ["client_id", "client_secret"],
        "scopes": ["identify", "email"],
    },
    "facebook": {
        "name": "Facebook",
        "auth_url": "https://www.facebook.com/v18.0/dialog/oauth",
        "token_url": "https://graph.facebook.com/v18.0/oauth/access_token",
        "required_fields": ["client_id", "client_secret"],
        "scopes": ["email", "public_profile"],
    },
    "github": {
        "name": "GitHub",
        "auth_url": "https://github.com/login/oauth/authorize",
        "token_url": "https://github.com/login/oauth/access_token",
        "required_fields": ["client_id", "client_secret"],
        "scopes": ["user:email"],
    },
    "gitlab": {
        "name": "GitLab",
        "auth_url": "https://gitlab.com/oauth/authorize",
        "token_url": "https://gitlab.com/oauth/token",
        "required_fields": ["client_id", "client_secret"],
        "optional_fields": ["custom_url"],  # For self-hosted GitLab
        "scopes": ["read_user", "email"],
    },
    "google": {
        "name": "Google",
        "discovery_url": "https://accounts.google.com/.well-known/openid-configuration",
        "required_fields": ["client_id", "client_secret"],
        "scopes": ["openid", "email", "profile"],
    },
    "instagram": {
        "name": "Instagram",
        "auth_url": "https://api.instagram.com/oauth/authorize",
        "token_url": "https://api.instagram.com/oauth/access_token",
        "required_fields": ["client_id", "client_secret"],
        "scopes": ["user_profile", "user_media"],
    },
    "kakao": {
        "name": "Kakao",
        "auth_url": "https://kauth.kakao.com/oauth/authorize",
        "token_url": "https://kauth.kakao.com/oauth/token",
        "required_fields": ["client_id", "client_secret"],
        "scopes": ["profile_nickname", "account_email"],
    },
    "spotify": {
        "name": "Spotify",
        "auth_url": "https://accounts.spotify.com/authorize",
        "token_url": "https://accounts.spotify.com/api/token",
        "required_fields": ["client_id", "client_secret"],
        "scopes": ["user-read-email", "user-read-private"],
    },
    "strava": {
        "name": "Strava",
        "auth_url": "https://www.strava.com/oauth/authorize",
        "token_url": "https://www.strava.com/oauth/token",
        "required_fields": ["client_id", "client_secret"],
        "scopes": ["read", "profile:read_all"],
    },
    "twitch": {
        "name": "Twitch",
        "auth_url": "https://id.twitch.tv/oauth2/authorize",
        "token_url": "https://id.twitch.tv/oauth2/token",
        "required_fields": ["client_id", "client_secret"],
        "scopes": ["user:read:email"],
    },
    "twitter": {
        "name": "Twitter/X",
        "auth_url": "https://twitter.com/i/oauth2/authorize",
        "token_url": "https://api.twitter.com/2/oauth2/token",
        "required_fields": ["client_id", "client_secret"],
        "scopes": ["users.read", "tweet.read"],
    },
    "yandex": {
        "name": "Yandex",
        "auth_url": "https://oauth.yandex.com/authorize",
        "token_url": "https://oauth.yandex.com/token",
        "required_fields": ["client_id", "client_secret"],
        "scopes": ["login:email", "login:info"],
    },
    "vk": {
        "name": "VK",
        "auth_url": "https://oauth.vk.com/authorize",
        "token_url": "https://oauth.vk.com/access_token",
        "required_fields": ["client_id", "client_secret"],
        "scopes": ["email"],
    },
    "bitbucket": {
        "name": "Bitbucket",
        "auth_url": "https://bitbucket.org/site/oauth2/authorize",
        "token_url": "https://bitbucket.org/site/oauth2/access_token",
        "required_fields": ["client_id", "client_secret"],
        "scopes": ["email", "account"],
    },
    "box": {
        "name": "Box",
        "auth_url": "https://account.box.com/api/oauth2/authorize",
        "token_url": "https://api.box.com/oauth2/token",
        "required_fields": ["client_id", "client_secret"],
        "scopes": [],
    },
    "gitea": {
        "name": "Gitea",
        "required_fields": ["client_id", "client_secret", "custom_url"],
        "optional_fields": [],
        "scopes": ["read:user", "user:email"],
    },
    "gitee": {
        "name": "Gitee",
        "auth_url": "https://gitee.com/oauth/authorize",
        "token_url": "https://gitee.com/oauth/token",
        "required_fields": ["client_id", "client_secret"],
        "scopes": ["user_info", "emails"],
    },
    "linear": {
        "name": "Linear",
        "auth_url": "https://linear.app/oauth/authorize",
        "token_url": "https://api.linear.app/oauth/token",
        "required_fields": ["client_id", "client_secret"],
        "scopes": ["read"],
    },
    "livechat": {
        "name": "LiveChat",
        "auth_url": "https://accounts.livechat.com/",
        "token_url": "https://accounts.livechat.com/token",
        "required_fields": ["client_id", "client_secret"],
        "scopes": [],
    },
    "monday": {
        "name": "Monday.com",
        "auth_url": "https://auth.monday.com/oauth2/authorize",
        "token_url": "https://auth.monday.com/oauth2/token",
        "required_fields": ["client_id", "client_secret"],
        "scopes": ["me:read"],
    },
    "notion": {
        "name": "Notion",
        "auth_url": "https://api.notion.com/v1/oauth/authorize",
        "token_url": "https://api.notion.com/v1/oauth/token",
        "required_fields": ["client_id", "client_secret"],
        "scopes": [],
    },
    "patreon": {
        "name": "Patreon",
        "auth_url": "https://www.patreon.com/oauth2/authorize",
        "token_url": "https://www.patreon.com/api/oauth2/token",
        "required_fields": ["client_id", "client_secret"],
        "scopes": ["identity", "identity[email]"],
    },
    "planningcenter": {
        "name": "Planning Center",
        "auth_url": "https://api.planningcenteronline.com/oauth/authorize",
        "token_url": "https://api.planningcenteronline.com/oauth/token",
        "required_fields": ["client_id", "client_secret"],
        "scopes": ["people"],
    },
    "wakatime": {
        "name": "WakaTime",
        "auth_url": "https://wakatime.com/oauth/authorize",
        "token_url": "https://wakatime.com/oauth/token",
        "required_fields": ["client_id", "client_secret"],
        "scopes": ["email", "read_logged_time"],
    },
    "mailcow": {
        "name": "Mailcow",
        "required_fields": ["client_id", "client_secret", "custom_url"],
        "scopes": ["profile"],
    },
    "oidc": {
        "name": "OpenID Connect",
        "required_fields": ["client_id", "client_secret", "discovery_url"],
        "optional_fields": ["custom_scopes"],
        "scopes": ["openid", "email", "profile"],
    },
    "lark": {
        "name": "Lark/Feishu",
        "auth_url": "https://open.feishu.cn/open-apis/authen/v1/authorize",
        "token_url": "https://open.feishu.cn/open-apis/authen/v1/access_token",
        "required_fields": ["client_id", "client_secret"],
        "scopes": [],
    },
    "microsoft": {
        "name": "Microsoft",
        "discovery_url": "https://login.microsoftonline.com/common/v2.0/.well-known/openid-configuration",
        "required_fields": ["client_id", "client_secret"],
        "optional_fields": ["tenant"],  # For single-tenant apps
        "scopes": ["openid", "email", "profile"],
    },
}


class OAuthProvider(BaseModel):
    """OAuth2 provider configuration stored in database."""

    __tablename__ = "oauth_providers"

    # Provider identification
    provider_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)  # Display name

    # Enable/disable
    enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # OAuth credentials
    client_id: Mapped[str] = mapped_column(Text, nullable=False)
    client_secret: Mapped[str] = mapped_column(Text, nullable=False)

    # Additional configuration (JSON for flexibility)
    # Includes: custom_url, team_id, key_id, private_key, tenant, etc.
    extra_config: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)

    # Custom scopes (override default)
    custom_scopes: Mapped[str] = mapped_column(Text, nullable=True)

    # Collection restriction (None = all auth collections)
    collection_id: Mapped[str] = mapped_column(String(36), nullable=True, index=True)

    # Display order for UI
    display_order: Mapped[int] = mapped_column(default=0, nullable=False)

    def __repr__(self) -> str:
        return f"<OAuthProvider({self.provider_type}, enabled={self.enabled})>"

    def to_dict(self) -> dict:
        """Convert to dictionary (excluding secrets for API responses)."""
        return {
            "id": self.id,
            "provider_type": self.provider_type,
            "name": self.name,
            "enabled": self.enabled,
            "client_id": self.client_id,  # May want to mask this
            "has_secret": bool(self.client_secret),
            "extra_config": {k: v for k, v in (self.extra_config or {}).items()
                           if k not in ("private_key",)},  # Hide sensitive fields
            "custom_scopes": self.custom_scopes,
            "collection_id": self.collection_id,
            "display_order": self.display_order,
            "created": self.created.isoformat() if self.created else None,
            "updated": self.updated.isoformat() if self.updated else None,
        }

    def get_scopes(self) -> list:
        """Get scopes for this provider."""
        if self.custom_scopes:
            return [s.strip() for s in self.custom_scopes.split(",")]
        metadata = PROVIDER_METADATA.get(self.provider_type, {})
        return metadata.get("scopes", [])

    def get_auth_url(self) -> str:
        """Get authorization URL for this provider."""
        # Check custom URL first
        if self.extra_config and self.extra_config.get("custom_url"):
            base = self.extra_config["custom_url"].rstrip("/")
            if self.provider_type == "gitea":
                return f"{base}/login/oauth/authorize"
            elif self.provider_type == "gitlab":
                return f"{base}/oauth/authorize"
            elif self.provider_type == "mailcow":
                return f"{base}/oauth/authorize"

        metadata = PROVIDER_METADATA.get(self.provider_type, {})
        return metadata.get("auth_url", "")

    def get_token_url(self) -> str:
        """Get token URL for this provider."""
        if self.extra_config and self.extra_config.get("custom_url"):
            base = self.extra_config["custom_url"].rstrip("/")
            if self.provider_type == "gitea":
                return f"{base}/login/oauth/access_token"
            elif self.provider_type == "gitlab":
                return f"{base}/oauth/token"
            elif self.provider_type == "mailcow":
                return f"{base}/oauth/token"

        metadata = PROVIDER_METADATA.get(self.provider_type, {})
        return metadata.get("token_url", "")

    def get_discovery_url(self) -> str:
        """Get OIDC discovery URL if available."""
        if self.provider_type == "oidc" and self.extra_config:
            return self.extra_config.get("discovery_url", "")
        metadata = PROVIDER_METADATA.get(self.provider_type, {})
        return metadata.get("discovery_url", "")

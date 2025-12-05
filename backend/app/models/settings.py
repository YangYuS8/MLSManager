"""System settings model for panel configuration."""

from datetime import datetime, timezone

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class SystemSettings(Base):
    """System settings model for panel configuration.
    
    This is a key-value store for system-wide settings.
    Only SUPERADMIN can modify these settings.
    """

    __tablename__ = "system_settings"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    key: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    value: Mapped[str] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self) -> str:
        return f"<SystemSettings(key={self.key}, value={self.value[:50]}...)>"


# Default settings keys
class SettingsKey:
    """Constants for settings keys."""
    
    SITE_NAME = "site_name"
    SITE_DESCRIPTION = "site_description"
    PRIMARY_COLOR = "primary_color"
    DARK_MODE = "dark_mode"
    ALLOW_REGISTRATION = "allow_registration"
    MAX_UPLOAD_SIZE_MB = "max_upload_size_mb"
    DEFAULT_USER_ROLE = "default_user_role"
    MAINTENANCE_MODE = "maintenance_mode"
    ANNOUNCEMENT = "announcement"
    LOGO_URL = "logo_url"


# Default values for settings
DEFAULT_SETTINGS = {
    SettingsKey.SITE_NAME: {
        "value": "ML Server Manager",
        "description": "Site name displayed in the header"
    },
    SettingsKey.SITE_DESCRIPTION: {
        "value": "A lightweight multi-node ML workspace management system",
        "description": "Site description for SEO and display"
    },
    SettingsKey.PRIMARY_COLOR: {
        "value": "#1890ff",
        "description": "Primary theme color (hex format)"
    },
    SettingsKey.DARK_MODE: {
        "value": "false",
        "description": "Enable dark mode by default"
    },
    SettingsKey.ALLOW_REGISTRATION: {
        "value": "true",
        "description": "Allow new user registration"
    },
    SettingsKey.MAX_UPLOAD_SIZE_MB: {
        "value": "100",
        "description": "Maximum file upload size in MB"
    },
    SettingsKey.DEFAULT_USER_ROLE: {
        "value": "member",
        "description": "Default role for new users"
    },
    SettingsKey.MAINTENANCE_MODE: {
        "value": "false",
        "description": "Enable maintenance mode"
    },
    SettingsKey.ANNOUNCEMENT: {
        "value": "",
        "description": "System announcement message"
    },
    SettingsKey.LOGO_URL: {
        "value": "/logo.svg",
        "description": "Custom logo URL"
    },
}

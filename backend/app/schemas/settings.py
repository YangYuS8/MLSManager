"""Pydantic schemas for system settings."""

from pydantic import BaseModel, Field


class SettingBase(BaseModel):
    """Base schema for a single setting."""

    key: str = Field(..., description="Setting key")
    value: str = Field(..., description="Setting value")


class SettingCreate(SettingBase):
    """Schema for creating a setting."""

    description: str | None = Field(None, description="Setting description")


class SettingUpdate(BaseModel):
    """Schema for updating a setting."""

    value: str = Field(..., description="New setting value")


class SettingResponse(SettingBase):
    """Schema for setting response."""

    description: str | None = Field(None, description="Setting description")

    model_config = {"from_attributes": True}


class SettingsResponse(BaseModel):
    """Schema for all settings response."""

    settings: dict[str, str] = Field(..., description="All settings as key-value pairs")


class SettingsBatchUpdate(BaseModel):
    """Schema for batch updating settings."""

    settings: dict[str, str] = Field(..., description="Settings to update as key-value pairs")


class PanelConfig(BaseModel):
    """Public panel configuration for frontend."""

    site_name: str = Field(default="ML Server Manager", description="Site name")
    site_description: str = Field(default="", description="Site description")
    primary_color: str = Field(default="#1890ff", description="Primary theme color")
    dark_mode: bool = Field(default=False, description="Dark mode enabled")
    allow_registration: bool = Field(default=True, description="Allow registration")
    maintenance_mode: bool = Field(default=False, description="Maintenance mode")
    announcement: str = Field(default="", description="System announcement")
    logo_url: str = Field(default="/logo.svg", description="Logo URL")

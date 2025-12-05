"""Settings API endpoints for panel configuration."""

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.api.deps import DbSession, SuperAdminUser, CurrentUser
from app.models.settings import SystemSettings, DEFAULT_SETTINGS, SettingsKey
from app.schemas.settings import (
    SettingResponse,
    SettingsResponse,
    SettingsBatchUpdate,
    PanelConfig,
)

router = APIRouter()


async def get_setting_value(db: DbSession, key: str) -> str | None:
    """Get a single setting value from database."""
    result = await db.execute(
        select(SystemSettings).where(SystemSettings.key == key)
    )
    setting = result.scalar_one_or_none()
    if setting:
        return setting.value
    # Return default value if exists
    if key in DEFAULT_SETTINGS:
        return DEFAULT_SETTINGS[key]["value"]
    return None


async def ensure_default_settings(db: DbSession) -> None:
    """Ensure all default settings exist in database."""
    for key, data in DEFAULT_SETTINGS.items():
        result = await db.execute(
            select(SystemSettings).where(SystemSettings.key == key)
        )
        if not result.scalar_one_or_none():
            setting = SystemSettings(
                key=key,
                value=data["value"],
                description=data["description"],
            )
            db.add(setting)
    await db.commit()


@router.get("/config", response_model=PanelConfig)
async def get_panel_config(db: DbSession) -> PanelConfig:
    """
    Get public panel configuration.
    
    This endpoint is public and returns the panel configuration
    needed by the frontend to render the UI.
    """
    await ensure_default_settings(db)
    
    result = await db.execute(select(SystemSettings))
    settings_list = result.scalars().all()
    settings_dict = {s.key: s.value for s in settings_list}
    
    # Fill in defaults for any missing settings
    for key, data in DEFAULT_SETTINGS.items():
        if key not in settings_dict:
            settings_dict[key] = data["value"]
    
    return PanelConfig(
        site_name=settings_dict.get(SettingsKey.SITE_NAME, "ML Server Manager"),
        site_description=settings_dict.get(SettingsKey.SITE_DESCRIPTION, ""),
        primary_color=settings_dict.get(SettingsKey.PRIMARY_COLOR, "#1890ff"),
        dark_mode=settings_dict.get(SettingsKey.DARK_MODE, "false").lower() == "true",
        allow_registration=settings_dict.get(SettingsKey.ALLOW_REGISTRATION, "true").lower() == "true",
        maintenance_mode=settings_dict.get(SettingsKey.MAINTENANCE_MODE, "false").lower() == "true",
        announcement=settings_dict.get(SettingsKey.ANNOUNCEMENT, ""),
        logo_url=settings_dict.get(SettingsKey.LOGO_URL, "/logo.svg"),
    )


@router.get("", response_model=SettingsResponse)
async def get_all_settings(
    db: DbSession,
    current_user: SuperAdminUser,
) -> SettingsResponse:
    """
    Get all system settings.
    
    Requires SUPERADMIN privileges.
    """
    await ensure_default_settings(db)
    
    result = await db.execute(select(SystemSettings))
    settings_list = result.scalars().all()
    settings_dict = {s.key: s.value for s in settings_list}
    
    return SettingsResponse(settings=settings_dict)


@router.get("/{key}", response_model=SettingResponse)
async def get_setting(
    key: str,
    db: DbSession,
    current_user: SuperAdminUser,
) -> SettingResponse:
    """
    Get a specific setting by key.
    
    Requires SUPERADMIN privileges.
    """
    result = await db.execute(
        select(SystemSettings).where(SystemSettings.key == key)
    )
    setting = result.scalar_one_or_none()
    
    if not setting:
        # Check if it's a default setting
        if key in DEFAULT_SETTINGS:
            return SettingResponse(
                key=key,
                value=DEFAULT_SETTINGS[key]["value"],
                description=DEFAULT_SETTINGS[key]["description"],
            )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Setting '{key}' not found",
        )
    
    return SettingResponse(
        key=setting.key,
        value=setting.value,
        description=setting.description,
    )


@router.put("/{key}", response_model=SettingResponse)
async def update_setting(
    key: str,
    value: str,
    db: DbSession,
    current_user: SuperAdminUser,
) -> SettingResponse:
    """
    Update a specific setting.
    
    Requires SUPERADMIN privileges.
    """
    result = await db.execute(
        select(SystemSettings).where(SystemSettings.key == key)
    )
    setting = result.scalar_one_or_none()
    
    if not setting:
        # Create the setting if it doesn't exist but is a known default
        if key in DEFAULT_SETTINGS:
            setting = SystemSettings(
                key=key,
                value=value,
                description=DEFAULT_SETTINGS[key]["description"],
            )
            db.add(setting)
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Setting '{key}' not found",
            )
    else:
        setting.value = value
    
    await db.commit()
    await db.refresh(setting)
    
    return SettingResponse(
        key=setting.key,
        value=setting.value,
        description=setting.description,
    )


@router.put("", response_model=SettingsResponse)
async def batch_update_settings(
    settings_update: SettingsBatchUpdate,
    db: DbSession,
    current_user: SuperAdminUser,
) -> SettingsResponse:
    """
    Batch update multiple settings.
    
    Requires SUPERADMIN privileges.
    """
    await ensure_default_settings(db)
    
    for key, value in settings_update.settings.items():
        result = await db.execute(
            select(SystemSettings).where(SystemSettings.key == key)
        )
        setting = result.scalar_one_or_none()
        
        if setting:
            setting.value = value
        elif key in DEFAULT_SETTINGS:
            # Create new setting from defaults
            new_setting = SystemSettings(
                key=key,
                value=value,
                description=DEFAULT_SETTINGS[key]["description"],
            )
            db.add(new_setting)
        # Ignore unknown keys for batch update
    
    await db.commit()
    
    # Return all settings after update
    result = await db.execute(select(SystemSettings))
    settings_list = result.scalars().all()
    settings_dict = {s.key: s.value for s in settings_list}
    
    return SettingsResponse(settings=settings_dict)


@router.post("/reset", response_model=SettingsResponse)
async def reset_settings(
    db: DbSession,
    current_user: SuperAdminUser,
) -> SettingsResponse:
    """
    Reset all settings to defaults.
    
    Requires SUPERADMIN privileges.
    """
    # Delete all existing settings
    result = await db.execute(select(SystemSettings))
    settings_list = result.scalars().all()
    for setting in settings_list:
        await db.delete(setting)
    
    # Recreate with defaults
    await db.commit()
    await ensure_default_settings(db)
    
    # Return all settings
    result = await db.execute(select(SystemSettings))
    settings_list = result.scalars().all()
    settings_dict = {s.key: s.value for s in settings_list}
    
    return SettingsResponse(settings=settings_dict)

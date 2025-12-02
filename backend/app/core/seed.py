"""Database seeding utilities."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import get_password_hash
from app.models.user import User


async def seed_default_admin(db: AsyncSession) -> bool:
    """
    Create default admin user if no users exist.
    
    Returns True if admin was created, False if skipped.
    """
    # Check if any users exist
    result = await db.execute(select(User).limit(1))
    if result.scalar_one_or_none():
        return False
    
    # Create default superadmin
    admin = User(
        username=settings.default_admin_username,
        email=settings.default_admin_email,
        hashed_password=get_password_hash(settings.default_admin_password),
        full_name="System Administrator",
        role="superadmin",
        is_active=True,
    )
    db.add(admin)
    await db.commit()
    
    return True

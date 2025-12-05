"""User management endpoints."""

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.api.deps import AdminUser, CurrentUser, DbSession
from app.core.security import get_password_hash, verify_password
from app.models.user import User
from app.schemas.user import UserRead, UserUpdate, UserProfileUpdate, PasswordChange

router = APIRouter()


@router.get(
    "/me",
    response_model=UserRead,
    summary="Get current user",
    description="Retrieve the profile information of the currently authenticated user.",
)
async def get_current_user_info(current_user: CurrentUser) -> User:
    """Get current authenticated user's profile information."""
    return current_user


@router.patch(
    "/me",
    response_model=UserRead,
    summary="Update current user profile",
    description="Update the profile of the currently authenticated user.",
)
async def update_current_user(
    db: DbSession,
    current_user: CurrentUser,
    user_in: UserProfileUpdate,
) -> User:
    """Update current user's profile (email, full_name only)."""
    update_data = user_in.model_dump(exclude_unset=True)
    
    # Check if email is being changed and is unique
    if "email" in update_data and update_data["email"]:
        existing = await db.execute(
            select(User).where(
                User.email == update_data["email"],
                User.id != current_user.id
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )
    
    for field, value in update_data.items():
        setattr(current_user, field, value)
    
    await db.commit()
    await db.refresh(current_user)
    return current_user


@router.post(
    "/me/password",
    summary="Change password",
    description="Change the password of the currently authenticated user.",
)
async def change_password(
    db: DbSession,
    current_user: CurrentUser,
    password_data: PasswordChange,
) -> dict:
    """Change current user's password."""
    # Verify current password
    if not verify_password(password_data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect current password",
        )
    
    # Update password
    current_user.hashed_password = get_password_hash(password_data.new_password)
    await db.commit()
    
    return {"message": "Password changed successfully"}


@router.get(
    "/",
    response_model=list[UserRead],
    summary="List all users",
    description="Retrieve a paginated list of all users. **Admin only.**",
    responses={
        200: {"description": "List of users"},
        403: {"description": "Not authorized (admin required)"},
    },
)
async def list_users(
    db: DbSession,
    admin_user: AdminUser,
    skip: int = 0,
    limit: int = 100,
) -> list[User]:
    """
    List all users with pagination.

    - **skip**: Number of records to skip (default: 0)
    - **limit**: Maximum number of records to return (default: 100)
    """
    result = await db.execute(select(User).offset(skip).limit(limit))
    return list(result.scalars().all())


@router.get(
    "/{user_id}",
    response_model=UserRead,
    summary="Get user by ID",
    description="Retrieve a specific user's information by their ID. **Admin only.**",
    responses={
        200: {"description": "User found"},
        404: {"description": "User not found"},
        403: {"description": "Not authorized (admin required)"},
    },
)
async def get_user(
    db: DbSession,
    admin_user: AdminUser,
    user_id: int,
) -> User:
    """Get user details by ID. Requires admin privileges."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user


@router.patch(
    "/{user_id}",
    response_model=UserRead,
    summary="Update user",
    description="Update a user's profile information. **Admin only.**",
    responses={
        200: {"description": "User updated successfully"},
        404: {"description": "User not found"},
        403: {"description": "Not authorized (admin required)"},
    },
)
async def update_user(
    db: DbSession,
    admin_user: AdminUser,
    user_id: int,
    user_in: UserUpdate,
) -> User:
    """
    Update user information. Requires admin privileges.

    Only provided fields will be updated.
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    update_data = user_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field == "role" and value:
            setattr(user, field, value.value)
        else:
            setattr(user, field, value)

    await db.commit()
    await db.refresh(user)
    return user

from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database.connection import get_db
from app.models import User, UserRole
from app.schemas import UserDisplay, UserUpdate
from app.services import (
    get_users, get_user_by_id, update_user, verify_user, 
    deactivate_user, get_users_by_role, get_unverified_users,
    delete_user
)
from app.auth.jwt import get_current_verified_user

router = APIRouter(tags=["Users"], prefix="/users")

# Route for getting the current user
@router.get("/me", response_model=UserDisplay)
def read_users_me(current_user: User = Depends(get_current_verified_user)):
    """
    Get the current logged-in user
    """
    return current_user

# Routes for admins
@router.get("", response_model=List[UserDisplay])
def read_users(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user)
):
    """
    Get a list of all users (admin only)
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    return get_users(db, skip=skip, limit=limit)

@router.get("/unverified", response_model=List[UserDisplay])
def read_unverified_users(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user)
):
    """
    Get a list of unverified users (admin only)
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    return get_unverified_users(db, skip=skip, limit=limit)

@router.get("/role/{role}", response_model=List[UserDisplay])
def read_users_by_role(
    role: UserRole,
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user)
):
    """
    Get a list of users by role (admin only)
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    return get_users_by_role(db, role=role, skip=skip, limit=limit)

@router.get("/{user_id}", response_model=UserDisplay)
def read_user(
    user_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user)
):
    """
    Get a user by ID
    """
    # Admins can access any user
    if current_user.role == UserRole.ADMIN:
        return get_user_by_id(db, user_id)
    
    # Teachers can access their students
    if current_user.role == UserRole.TEACHER:
        # TODO: Implement check to see if the user is a student of the teacher
        pass
    
    # Users can access their own data
    if current_user.id == user_id:
        return current_user
    
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Not enough permissions"
    )

@router.put("/{user_id}", response_model=UserDisplay)
def update_user_data(
    user_id: int, 
    user_data: UserUpdate, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user)
):
    """
    Update a user
    """
    # Add logging for debugging
    print(f"Updating user {user_id}, data: {user_data}")
    
    # Admins can update any user
    if current_user.role == UserRole.ADMIN:
        try:
            user = update_user(db, user_id, user_data)
            print(f"User {user_id} updated successfully with group_id: {user.group_id}")
            return user
        except Exception as e:
            print(f"Error updating user {user_id}: {str(e)}")
            raise
    
    # Users can update their own data, but not role, is_active, or is_verified
    if current_user.id == user_id:
        # Remove sensitive fields
        user_data_dict = user_data.dict(exclude_unset=True)
        
        if "role" in user_data_dict:
            del user_data_dict["role"]
        
        if "is_active" in user_data_dict:
            del user_data_dict["is_active"]
        
        if "is_verified" in user_data_dict:
            del user_data_dict["is_verified"]
        
        try:
            user = update_user(db, user_id, UserUpdate(**user_data_dict))
            print(f"User {user_id} updated their own data successfully")
            return user
        except Exception as e:
            print(f"Error updating user {user_id}: {str(e)}")
            raise
    
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Not enough permissions"
    )

@router.put("/{user_id}/verify", response_model=UserDisplay)
def verify_user_account(
    user_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user)
):
    """
    Verify a user (admin only)
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    return verify_user(db, user_id)

@router.put("/{user_id}/deactivate", response_model=UserDisplay)
def deactivate_user_account(
    user_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user)
):
    """
    Deactivate a user (admin only)
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    return deactivate_user(db, user_id)

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user_account(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user)
):
    """
    Permanently delete a user (admin only)
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Prevent self-deletion
    if current_user.id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot delete your own account"
        )
    
    delete_user(db, user_id)
    return None 
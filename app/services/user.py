from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from typing import List, Optional

from app.models import User, UserRole, Group
from app.schemas import UserUpdate
from app.auth.password import hash_password

def get_users(db: Session, skip: int = 0, limit: int = 100) -> List[User]:
    """
    Get a list of users
    """
    return db.query(User).offset(skip).limit(limit).all()

def get_user_by_id(db: Session, user_id: int) -> User:
    """
    Get a user by their ID
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {user_id} not found"
        )
    return user

def get_user_by_username(db: Session, username: str) -> User:
    """
    Get a user by their username
    """
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with username {username} not found"
        )
    return user

def update_user(db: Session, user_id: int, user_data: UserUpdate) -> User:
    """
    Update a user's details
    """
    # Get the user
    user = get_user_by_id(db, user_id)
    print(f"Updating user: id={user.id}, username={user.username}, role={user.role}, current group_id={user.group_id}")
    
    # Update username if provided
    if user_data.username is not None:
        existing_username = db.query(User).filter(User.username == user_data.username).first()
        if existing_username and existing_username.id != user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )
        user.username = user_data.username
    
    # Update email if provided
    if user_data.email is not None:
        existing_email = db.query(User).filter(User.email == user_data.email).first()
        if existing_email and existing_email.id != user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already taken"
            )
        user.email = user_data.email
    
    # Update full name if provided
    if user_data.full_name is not None:
        user.full_name = user_data.full_name
    
    # Update password if provided
    if user_data.password is not None:
        user.hashed_password = hash_password(user_data.password)
    
    # Update is_active if provided
    if user_data.is_active is not None:
        user.is_active = user_data.is_active
    
    # Update is_verified if provided
    if user_data.is_verified is not None:
        user.is_verified = user_data.is_verified
    
    # Update group_id if provided (for students)
    if user_data.group_id is not None:
        print(f"Attempting to update group_id to {user_data.group_id}")
        
        # Check if user is a student
        if user.role != UserRole.STUDENT:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only students can be assigned to groups"
            )
        
        # Check if group exists if not null
        if user_data.group_id is not None:
            group = db.query(Group).filter(Group.id == user_data.group_id).first()
            if not group:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Group with ID {user_data.group_id} not found"
                )
            print(f"Found group: {group.name} (id={group.id})")
        
        user.group_id = user_data.group_id
        print(f"Updated group_id to {user.group_id}")
    
    db.commit()
    db.refresh(user)
    print(f"User updated successfully: id={user.id}, group_id={user.group_id}")
    
    return user

def verify_user(db: Session, user_id: int) -> User:
    """
    Verify a user (usually done by an admin)
    """
    user = get_user_by_id(db, user_id)
    user.is_verified = True
    
    db.commit()
    db.refresh(user)
    
    return user

def deactivate_user(db: Session, user_id: int) -> User:
    """
    Deactivate a user
    """
    user = get_user_by_id(db, user_id)
    user.is_active = False
    
    db.commit()
    db.refresh(user)
    
    return user

def get_users_by_role(db: Session, role: UserRole, skip: int = 0, limit: int = 100) -> List[User]:
    """
    Get users by their role
    """
    return db.query(User).filter(User.role == role).offset(skip).limit(limit).all()

def get_unverified_users(db: Session, skip: int = 0, limit: int = 100) -> List[User]:
    """
    Get users that are not yet verified
    """
    return db.query(User).filter(User.is_verified == False).offset(skip).limit(limit).all()

def delete_user(db: Session, user_id: int) -> None:
    """
    Completely delete a user from the database
    """
    user = get_user_by_id(db, user_id)
    
    # Don't allow deleting the last admin
    if user.role == UserRole.ADMIN:
        admin_count = db.query(User).filter(User.role == UserRole.ADMIN).count()
        if admin_count <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete the last admin user"
            )
    
    # Delete the user
    db.delete(user)
    db.commit()
    
    return None 
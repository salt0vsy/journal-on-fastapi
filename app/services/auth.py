from sqlalchemy.orm import Session
from datetime import timedelta
from fastapi import HTTPException, status

from app.models import User, UserRole
from app.schemas import UserCreate, UserLogin
from app.auth.password import hash_password, verify_password
from app.auth.jwt import create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES

def register_user(db: Session, user: UserCreate) -> User:
    """
    Register a new user with the given details
    """
    # Check if the user with the given username or email already exists
    existing_username = db.query(User).filter(User.username == user.username).first()
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    existing_email = db.query(User).filter(User.email == user.email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    db_user = User(
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        hashed_password=hash_password(user.password),
        role=user.role,
        is_active=True,
        is_verified=False,  # New users need to be verified by an admin
        group_id=user.group_id if user.role == UserRole.STUDENT else None
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user

def authenticate_user(db: Session, user: UserLogin) -> User:
    """
    Authenticate a user with the given username and password
    """
    # Get the user from the database
    db_user = db.query(User).filter(User.username == user.username).first()
    
    # Check if the user exists and the password is correct
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if the user is active
    if not db_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    return db_user

def login_user(db: Session, user: UserLogin):
    """
    Login a user and return an access token
    """
    # Authenticate the user
    db_user = authenticate_user(db, user)
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": db_user.username},
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer", "user": db_user} 
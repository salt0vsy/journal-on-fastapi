from datetime import datetime, timedelta
from typing import Optional
import os

from jose import jwt, JWTError
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2
from fastapi.openapi.models import OAuthFlows as OAuthFlowsModel
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models import User
from app.schemas.token import TokenData

# Secret key and algorithm configuration loaded from environment variables
# Raise an error if secret key is not provided to prevent using insecure defaults
SECRET_KEY = os.environ.get("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY environment variable is not set. Cannot start application securely.")

ALGORITHM = os.environ.get("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# OAuth2 bearer token scheme for FastAPI
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Custom OAuth2 scheme that doesn't raise an exception for optional authentication
class OAuth2PasswordBearerOptional(OAuth2):
    def __init__(self, tokenUrl: str, auto_error: bool = False):
        flows = OAuthFlowsModel(password={"tokenUrl": tokenUrl, "scopes": {}})
        super().__init__(flows=flows, scheme_name="OAuth2PasswordBearer", auto_error=auto_error)

oauth2_scheme_optional = OAuth2PasswordBearerOptional(tokenUrl="token")

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    return encoded_jwt

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    """
    Validate the token and return the current user
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Decode the token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        
        if username is None:
            raise credentials_exception
        
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    
    # Get the user from the database
    user = db.query(User).filter(User.username == token_data.username).first()
    
    if user is None:
        raise credentials_exception
    
    return user

def get_current_user_optional(token: str = Depends(oauth2_scheme_optional), db: Session = Depends(get_db), request: Request = None) -> Optional[User]:
    """
    Validate the token and return the current user, but don't require authentication
    """
    # First check if user is already in request state (set by middleware)
    if request and hasattr(request.state, 'user'):
        return request.state.user
        
    if token is None:
        return None
        
    try:
        # Decode the token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        
        if username is None:
            return None
        
        token_data = TokenData(username=username)
    except JWTError:
        return None
    
    # Get the user from the database
    user = db.query(User).filter(User.username == token_data.username).first()
    
    return user

def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Check if the current user is active
    """
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    
    return current_user

def get_current_verified_user(current_user: User = Depends(get_current_active_user)) -> User:
    """
    Check if the current user is verified
    """
    if not current_user.is_verified:
        raise HTTPException(status_code=400, detail="User not verified")
    
    return current_user 
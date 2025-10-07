from fastapi import APIRouter, Depends, status, Response, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from typing import Optional

from app.database.connection import get_db
from app.models import User, UserRole
from app.schemas import UserCreate, UserLogin, Token, UserDisplay
from app.services import register_user, login_user
from app.auth.jwt import get_current_user_optional

router = APIRouter(tags=["Authentication"])
templates = Jinja2Templates(directory="app/templates")

@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request, current_user: Optional[User] = Depends(get_current_user_optional)):
    """
    Show the login page
    """
    if current_user:
        return RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)
        
    return templates.TemplateResponse(
        "login.html", 
        {"request": request, "user": None}
    )

@router.post("/register", response_model=UserDisplay, status_code=status.HTTP_201_CREATED)
def register(user: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user
    """
    return register_user(db, user)

@router.post("/token", response_model=Token)
def get_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Get an access token (OAuth2 compatible endpoint)
    """
    user = UserLogin(username=form_data.username, password=form_data.password)
    result = login_user(db, user)
    return Token(access_token=result["access_token"], token_type=result["token_type"])

@router.post("/login")
def login(user: UserLogin, response: Response, db: Session = Depends(get_db)):
    """
    Login and get an access token
    """
    result = login_user(db, user)
    
    # Set the token in a cookie (optional)
    response.set_cookie(
        key="access_token",
        value=f"Bearer {result['access_token']}",
        httponly=False,  # Allow JavaScript access
        max_age=1800,
        expires=1800,
        samesite="lax",  # Allow cookie to be sent for cross-site navigation
        secure=False,  # No HTTPS required for local development
        path="/"  # Set cookie for all paths
    )
    
    # Get the user data
    db_user = result["user"]
    
    # Return the token and user data
    return {
        "access_token": result["access_token"],
        "token_type": result["token_type"],
        "user": {
            "id": db_user.id,
            "username": db_user.username,
            "full_name": db_user.full_name,
            "email": db_user.email,
            "role": db_user.role.value,
            "is_verified": db_user.is_verified,
            "group_id": db_user.group_id,
            "is_active": db_user.is_active
        }
    }

@router.post("/logout")
def logout(response: Response):
    """
    Logout by clearing the cookie
    """
    response.delete_cookie(key="access_token")
    return {"message": "Successfully logged out"} 
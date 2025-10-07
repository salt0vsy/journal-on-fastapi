from pydantic import BaseModel, EmailStr
from typing import Optional, List, TYPE_CHECKING

if TYPE_CHECKING:
    from app.schemas.journal import FacultyBase
from app.models.users import UserRole

class UserBase(BaseModel):
    username: str
    email: EmailStr
    full_name: str
    role: UserRole

class UserCreate(UserBase):
    password: str
    group_id: Optional[int] = None

class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None
    group_id: Optional[int] = None

class UserDisplay(UserBase):
    id: int
    is_active: bool
    is_verified: bool
    group_id: Optional[int] = None
    
    class Config:
        from_attributes = True

class UserWithFaculties(UserDisplay):
    faculties: List["FacultyBase"] = []
    
    model_config = {"from_attributes": True}

class UserLogin(BaseModel):
    username: str
    password: str

class UserVerify(BaseModel):
    id: int
    is_verified: bool = True

class UserLoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserDisplay 
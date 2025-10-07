from fastapi import FastAPI, Request, Depends, HTTPException, status, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.security import HTTPBearer
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy.orm import Session
import os
from typing import Optional
import urllib.parse
from starlette.middleware.base import BaseHTTPMiddleware
from datetime import datetime
import secrets

from app.database.connection import get_db, engine
from app.models import Base
from app.routes import auth_router, users_router, journal_router
from app.auth.jwt import get_current_user, get_current_user_optional
from app.models import User, Faculty, Group, Subject, SubjectGroup, UserRole
from app.schemas import JournalView
from app.services import get_journal_view
from app.auth.password import hash_password
from sqlalchemy import text
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create tables in the database with proper enum handling
def init_database():
    try:
        with engine.connect() as conn:
            # Use advisory lock to prevent concurrent database initialization
            result = conn.execute(text("SELECT pg_try_advisory_lock(1234567890)")).fetchone()
            
            if not result[0]:
                logger.info("Another process is initializing the database, waiting...")
                conn.execute(text("SELECT pg_advisory_lock(1234567890)"))
                conn.execute(text("SELECT pg_advisory_unlock(1234567890)"))
                logger.info("Database initialization completed by another process")
                return
            
            try:
                # Check if tables already exist
                table_exists = conn.execute(text(
                    "SELECT 1 FROM information_schema.tables WHERE table_name = 'users'"
                )).fetchone()
                
                if table_exists:
                    logger.info("Database tables already exist, skipping initialization")
                else:
                    logger.info("Initializing database tables")
                    # Create all tables using SQLAlchemy (handles enums automatically)
                    Base.metadata.create_all(bind=engine)
                    logger.info("Database tables created successfully")
                
                # Create default admin user if it doesn't exist
                from sqlalchemy.orm import sessionmaker
                Session = sessionmaker(bind=engine)
                db = Session()
                
                try:
                    admin = db.query(User).filter(User.username == "admin").first()
                    if not admin:
                        admin = User(
                            username="admin",
                            email="admin@example.com",
                            full_name="Адміністратор системи",
                            hashed_password=hash_password("admin"),
                            role=UserRole.ADMIN,
                            is_active=True,
                            is_verified=True
                        )
                        db.add(admin)
                        db.commit()
                        logger.info("Created default admin user: username=admin, password=admin")
                    else:
                        logger.info("Default admin user already exists")
                finally:
                    db.close()
                    
            finally:
                # Always release the advisory lock
                conn.execute(text("SELECT pg_advisory_unlock(1234567890)"))
                conn.commit()
        
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise

# Only initialize database if this is the main module or main worker
if __name__ == "__main__" or os.getenv("INIT_DB", "true").lower() == "true":
    init_database()

# Create FastAPI app
app = FastAPI(title="Student Journal")

# Add session middleware for flash messages and CSRF
app.add_middleware(
    SessionMiddleware,
    secret_key=secrets.token_hex(32),
    session_cookie="session",
    max_age=14 * 24 * 60 * 60,  # 14 days
    same_site="lax",
    https_only=False
)

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Set up Jinja2 templates
templates = Jinja2Templates(directory="app/templates")

# Add custom filters to Jinja2
def format_date(value):
    if isinstance(value, str):
        try:
            value = datetime.strptime(value, "%Y-%m-%d")
        except ValueError:
            return value
    if isinstance(value, datetime):
        return value.strftime("%d.%m.%Y")
    return value

templates.env.filters["date"] = format_date

# Helper function to get flash messages
def get_flash_messages(request: Request):
    messages = request.session.get("flash_messages", [])
    request.session["flash_messages"] = []
    return messages

# Add global template context
@app.middleware("http")
async def add_template_context(request: Request, call_next):
    response = await call_next(request)
    
    # Add CSRF token to template context
    if "csrf_token" not in request.session:
        request.session["csrf_token"] = secrets.token_hex(32)
    
    # Add flash messages to template context
    if "flash_messages" not in request.session:
        request.session["flash_messages"] = []
    
    return response

# Helper function to add flash messages
def flash(request: Request, message: str, category: str = "info"):
    if "flash_messages" not in request.session:
        request.session["flash_messages"] = []
    request.session["flash_messages"].append({"message": message, "category": category})

# Add API routers - these must be added BEFORE the journal page route
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(journal_router)

# Home page
@app.get("/", response_class=HTMLResponse)
async def home(request: Request, current_user: Optional[User] = Depends(get_current_user_optional)):
    return templates.TemplateResponse(
        "index.html", 
        {
            "request": request, 
            "user": current_user,
            "get_flash_messages": get_flash_messages
        }
    )

# Registration page
@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request, current_user: Optional[User] = Depends(get_current_user_optional)):
    if current_user:
        return RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)
    
    return templates.TemplateResponse(
        "register.html", 
        {
            "request": request, 
            "user": None,
            "get_flash_messages": get_flash_messages
        }
    )

# Admin panel
@app.get("/admin", response_class=HTMLResponse)
async def admin_panel(request: Request, current_user: Optional[User] = Depends(get_current_user_optional)):
    if not current_user:
        return RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)
    
    if current_user.role != UserRole.ADMIN:
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "user": current_user,
                "error": "You do not have permission to access the admin panel.",
                "status_code": 403,
                "get_flash_messages": get_flash_messages
            }
        )
    
    return templates.TemplateResponse(
        "admin.html", 
        {
            "request": request, 
            "user": current_user,
            "get_flash_messages": get_flash_messages
        }
    )

# Journal view page - Add a specific route for journal access
@app.get("/journal/{faculty}/{group}/{subject}", response_class=HTMLResponse)
async def journal_explicit_page(
    request: Request, 
    faculty: str,
    group: str,
    subject: str,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    # Try to URL decode parameters (in case they're already decoded, this won't change them)
    try:
        faculty = urllib.parse.unquote(faculty)
        group = urllib.parse.unquote(group)
        subject = urllib.parse.unquote(subject)
    except Exception as e:
        print(f"Error decoding URL parameters: {e}")
    
    # Debug information
    print(f"Accessing journal explicit page with: faculty={faculty}, group={group}, subject={subject}")
    print(f"Current user: {current_user}")
    
    if not current_user:
        print("No current user, redirecting to login")
        return RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)
    
    if not current_user.is_verified:
        print("User not verified")
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "user": current_user,
                "error": "Your account has not been verified yet. Please wait for an admin to verify your account.",
                "get_flash_messages": get_flash_messages
            }
        )
    
    try:
        # Get the faculty, group, and subject by name
        print(f"Looking for faculty: {faculty}")
        db_faculty = db.query(Faculty).filter(Faculty.name == faculty).first()
        if not db_faculty:
            print(f"Faculty '{faculty}' not found")
            return templates.TemplateResponse(
                "error.html",
                {
                    "request": request,
                    "user": current_user,
                    "error": f"Faculty '{faculty}' not found",
                    "status_code": 404,
                    "get_flash_messages": get_flash_messages
                },
                status_code=404
            )
        print(f"Found faculty: {db_faculty.name} (ID: {db_faculty.id})")
        
        print(f"Looking for group: {group} in faculty {db_faculty.id}")
        db_group = db.query(Group).filter(Group.name == group, Group.faculty_id == db_faculty.id).first()
        if not db_group:
            print(f"Group '{group}' not found in faculty {db_faculty.name}")
            return templates.TemplateResponse(
                "error.html",
                {
                    "request": request,
                    "user": current_user,
                    "error": f"Group '{group}' not found in faculty '{faculty}'",
                    "status_code": 404,
                    "get_flash_messages": get_flash_messages
                },
                status_code=404
            )
        print(f"Found group: {db_group.name} (ID: {db_group.id})")
        
        print(f"Looking for subject: {subject} in faculty {db_faculty.id}")
        db_subject = db.query(Subject).filter(Subject.name == subject, Subject.faculty_id == db_faculty.id).first()
        if not db_subject:
            print(f"Subject '{subject}' not found in faculty {db_faculty.name}")
            return templates.TemplateResponse(
                "error.html",
                {
                    "request": request,
                    "user": current_user,
                    "error": f"Subject '{subject}' not found in faculty '{faculty}'",
                    "status_code": 404,
                    "get_flash_messages": get_flash_messages
                },
                status_code=404
            )
        print(f"Found subject: {db_subject.name} (ID: {db_subject.id})")
        
        # Get subject-group relationship
        print(f"Looking for subject-group relationship: subject_id={db_subject.id}, group_id={db_group.id}")
        subject_group = db.query(SubjectGroup).filter(
            SubjectGroup.subject_id == db_subject.id,
            SubjectGroup.group_id == db_group.id
        ).first()
        
        if not subject_group:
            print(f"No relationship between subject '{subject}' and group '{group}'")
            return templates.TemplateResponse(
                "error.html",
                {
                    "request": request,
                    "user": current_user,
                    "error": f"No relationship between subject '{subject}' and group '{group}'",
                    "status_code": 404,
                    "get_flash_messages": get_flash_messages
                },
                status_code=404
            )
        print(f"Found subject-group relationship: ID={subject_group.id}")
        
        # Check permissions
        if current_user.role == UserRole.STUDENT:
            # Students can only view journals for their own group
            if current_user.group_id != db_group.id:
                print(f"Student not in group {db_group.name}")
                return templates.TemplateResponse(
                    "error.html",
                    {
                        "request": request,
                        "user": current_user,
                        "error": "Not enough permissions",
                        "status_code": 403,
                        "get_flash_messages": get_flash_messages
                    },
                    status_code=403
                )
        elif current_user.role == UserRole.TEACHER:
            # Teachers can only view journals for subjects they teach
            teacher_subjects = [s.id for s in current_user.subjects]
            if db_subject.id not in teacher_subjects:
                print(f"Teacher does not teach subject {db_subject.name}")
                return templates.TemplateResponse(
                    "error.html",
                    {
                        "request": request,
                        "user": current_user,
                        "error": "You don't have access to this subject",
                        "status_code": 403,
                        "get_flash_messages": get_flash_messages
                    },
                    status_code=403
                )
        
        # Get journal data
        print("Getting journal view data")
        try:
            journal = get_journal_view(db, db_subject.id, db_group.id)
            print("Journal data retrieved successfully")
        except Exception as journal_error:
            print(f"Error retrieving journal data: {str(journal_error)}")
            error_detail = str(journal_error) if str(journal_error) else "Unknown error retrieving journal data"
            return templates.TemplateResponse(
                "error.html",
                {
                    "request": request,
                    "user": current_user,
                    "error": f"Error loading journal: {error_detail}",
                    "status_code": 500,
                    "get_flash_messages": get_flash_messages
                },
                status_code=500
            )
        
        return templates.TemplateResponse(
            "journal.html", 
            {
                "request": request, 
                "user": current_user, 
                "journal": journal,
                "subject_group_id": subject_group.id,
                "get_flash_messages": get_flash_messages
            }
        )
    except Exception as e:
        error_message = str(e) if str(e) else "Unknown error"
        print(f"Error in journal_page: {error_message}")
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "user": current_user,
                "error": f"An error occurred while loading the journal: {error_message}",
                "status_code": 500,
                "get_flash_messages": get_flash_messages
            },
            status_code=500
        )

# As a fallback, keep the original route but redirect to the new format
@app.get("/{faculty}/{group}/{subject}", response_class=HTMLResponse)
async def journal_page_redirect(
    request: Request, 
    faculty: str,
    group: str,
    subject: str
):
    # Redirect to the explicit journal page
    encoded_faculty = urllib.parse.quote(faculty)
    encoded_group = urllib.parse.quote(group)
    encoded_subject = urllib.parse.quote(subject)
    redirect_url = f"/journal/{encoded_faculty}/{encoded_group}/{encoded_subject}"
    return RedirectResponse(redirect_url, status_code=status.HTTP_302_FOUND)

# Debug route
@app.get("/debug/database", response_class=HTMLResponse)
async def debug_database(
    request: Request,
    db: Session = Depends(get_db),
):
    """Debug route to check database entries"""
    faculties = db.query(Faculty).all()
    faculty_data = []
    
    for faculty in faculties:
        groups = db.query(Group).filter(Group.faculty_id == faculty.id).all()
        group_data = []
        
        for group in groups:
            subject_groups = db.query(SubjectGroup).filter(SubjectGroup.group_id == group.id).all()
            subject_ids = [sg.subject_id for sg in subject_groups]
            subjects = db.query(Subject).filter(Subject.id.in_(subject_ids)).all()
            
            subject_data = [{"id": subject.id, "name": subject.name} for subject in subjects]
            
            group_data.append({
                "id": group.id,
                "name": group.name,
                "subjects": subject_data
            })
        
        faculty_data.append({
            "id": faculty.id,
            "name": faculty.name,
            "groups": group_data
        })
    
    return templates.TemplateResponse(
        "debug.html",
        {
            "request": request,
            "faculties": faculty_data
        }
    )

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    error_messages = {
        400: "Неправильний запит",
        401: "Необхідна авторизація",
        403: "Доступ заборонено",
        404: "Сторінку не знайдено",
        405: "Метод не дозволено",
        500: "Внутрішня помилка сервера"
    }
    
    return templates.TemplateResponse(
        "error.html",
        {
            "request": request,
            "user": None,
            "error_title": f"Помилка {exc.status_code}",
            "error_message": exc.detail or error_messages.get(exc.status_code, "Невідома помилка"),
            "error_details": None,
            "get_flash_messages": get_flash_messages
        },
        status_code=exc.status_code
    )

@app.exception_handler(404)
async def not_found_exception_handler(request: Request, exc: HTTPException):
    return templates.TemplateResponse(
        "error.html",
        {
            "request": request,
            "user": None,
            "error_title": "Помилка 404",
            "error_message": "Сторінку не знайдено",
            "error_details": None,
            "get_flash_messages": get_flash_messages
        },
        status_code=404
    )

@app.exception_handler(500)
async def server_error_exception_handler(request: Request, exc: Exception):
    return templates.TemplateResponse(
        "error.html",
        {
            "request": request,
            "user": None,
            "error_title": "Помилка 500",
            "error_message": "Внутрішня помилка сервера",
            "error_details": str(exc) if app.debug else None,
            "get_flash_messages": get_flash_messages
        },
        status_code=500
    )

# Middleware to get the current user for all requests
@app.middleware("http")
async def get_user_middleware(request: Request, call_next):
    # Skip API routes and public endpoints
    if request.url.path.startswith(("/api/", "/token", "/login", "/register", "/static", "/public", "/docs", "/openapi.json")):
        return await call_next(request)
    
    # Debug - print the path
    print(f"Accessing path: {request.url.path}")
    
    # Try to get the token from cookies
    token = None
    
    # Check all cookies for debugging
    print(f"Cookies: {request.cookies}")
    
    # Get the token from cookies
    token = request.cookies.get("access_token")
    if token and token.startswith("Bearer "):
        token = token[7:]  # Remove "Bearer " prefix
        print(f"Found token in cookies: {token[:10]}...")
    
    # If no token in cookies, try to get from Authorization header
    if not token:
        auth_header = request.headers.get("Authorization")
        print(f"Authorization header: {auth_header}")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:]  # Remove "Bearer " prefix
            print(f"Found token in headers: {token[:10]}...")
    
    # Also check for localStorage token if it's sent in the request headers
    if not token:
        ls_token = request.headers.get("X-Auth-Token")
        print(f"X-Auth-Token header: {ls_token}")
        if ls_token:
            # If X-Auth-Token has the Bearer prefix, remove it
            if ls_token.startswith("Bearer "):
                ls_token = ls_token[7:]  # Remove "Bearer " prefix
            token = ls_token
            print(f"Found token in X-Auth-Token header: {token[:10]}...")
    
    # Set user in request state if token exists
    db = None
    if token:
        try:
            db = next(get_db())
            user = get_current_user(token=token, db=db)
            request.state.user = user
            print(f"Authenticated user: {user.username}, role: {user.role}")
            
            # Also add the token to the request state for convenience
            request.state.token = token
        except Exception as e:
            print(f"Authentication error: {str(e)}")
            # Continue without setting user
            if db:
                db.close()
    
    try:
        # Call the next middleware/route handler
        response = await call_next(request)
        return response
    except Exception as e:
        # Log the error
        print(f"Error in middleware chain: {str(e)}")
        # Return a 500 error response
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "user": getattr(request.state, "user", None),
                "error": "An internal server error occurred.",
                "status_code": 500,
                "get_flash_messages": get_flash_messages
            },
            status_code=500
        )
    finally:
        # Make sure to close the db connection if it was opened
        if db:
            db.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

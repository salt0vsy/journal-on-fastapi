from sqlalchemy import Column, Integer, String, Boolean, Enum, ForeignKey, Table
from sqlalchemy.orm import relationship
import enum

from app.database.connection import Base

class UserRole(enum.Enum):
    ADMIN = "admin"
    TEACHER = "teacher"
    STUDENT = "student"

# Many-to-many relationship between users and faculties (for teachers and admins)
user_faculty = Table(
    "user_faculty",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id")),
    Column("faculty_id", Integer, ForeignKey("faculties.id"))
)

# Many-to-many relationship between teachers and subjects
teacher_subject = Table(
    "teacher_subject",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id")),
    Column("subject_id", Integer, ForeignKey("subjects.id"))
)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    full_name = Column(String)
    hashed_password = Column(String)
    role = Column(Enum(UserRole))
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    
    # Relationships
    faculties = relationship("Faculty", secondary=user_faculty, back_populates="users")
    
    # Teacher-specific relationships
    subjects = relationship("Subject", secondary=teacher_subject, back_populates="teachers")
    
    # Student-specific relationships
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=True)
    group = relationship("Group", back_populates="students")
    
    # One-to-many relationship with grades (for students)
    grades = relationship("Grade", back_populates="student")
    
    # One-to-many relationship with attendance (for students)
    attendance = relationship("Attendance", back_populates="student")
    
    # Student-specific relationships
    student_subjects = relationship("StudentSubject", foreign_keys="[StudentSubject.student_id]", back_populates="student") 
from sqlalchemy import Column, Integer, String, ForeignKey, Date, Text, Boolean
from sqlalchemy.orm import relationship
from datetime import date

from app.database.connection import Base
from app.models.users import user_faculty, teacher_subject

class Faculty(Base):
    __tablename__ = "faculties"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    
    # Relationships
    users = relationship("User", secondary=user_faculty, back_populates="faculties")
    groups = relationship("Group", back_populates="faculty")
    subjects = relationship("Subject", back_populates="faculty")

class Group(Base):
    __tablename__ = "groups"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    faculty_id = Column(Integer, ForeignKey("faculties.id"))
    
    # Relationships
    faculty = relationship("Faculty", back_populates="groups")
    students = relationship("User", back_populates="group")
    subject_groups = relationship("SubjectGroup", back_populates="group")

class Subject(Base):
    __tablename__ = "subjects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    faculty_id = Column(Integer, ForeignKey("faculties.id", ondelete="CASCADE"), nullable=False)
    
    # Relationships
    faculty = relationship("Faculty", back_populates="subjects")
    subject_groups = relationship("SubjectGroup", back_populates="subject", cascade="all, delete-orphan")
    teachers = relationship("User", secondary="teacher_subject", back_populates="subjects")
    student_subjects = relationship("StudentSubject", foreign_keys="[StudentSubject.subject_id]", back_populates="subject")

class SubjectGroup(Base):
    __tablename__ = "subject_groups"
    
    id = Column(Integer, primary_key=True, index=True)
    subject_id = Column(Integer, ForeignKey("subjects.id"))
    group_id = Column(Integer, ForeignKey("groups.id"))
    
    # Relationships
    subject = relationship("Subject", back_populates="subject_groups")
    group = relationship("Group", back_populates="subject_groups")
    grades = relationship("Grade", back_populates="subject_group")
    attendance = relationship("Attendance", back_populates="subject_group")

class Grade(Base):
    __tablename__ = "grades"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id"))
    subject_group_id = Column(Integer, ForeignKey("subject_groups.id"))
    grade = Column(Integer)
    date = Column(Date, default=date.today)
    description = Column(Text, nullable=True)
    
    # Relationships
    student = relationship("User", back_populates="grades")
    subject_group = relationship("SubjectGroup", back_populates="grades")

class Attendance(Base):
    __tablename__ = "attendance"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id"))
    subject_group_id = Column(Integer, ForeignKey("subject_groups.id"))
    date = Column(Date, default=date.today)
    is_present = Column(Boolean, default=True)
    
    # Relationships
    student = relationship("User", back_populates="attendance")
    subject_group = relationship("SubjectGroup", back_populates="attendance")

class StudentSubject(Base):
    __tablename__ = "student_subjects"
    
    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    subject_id = Column(Integer, ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False)
    
    # Relationships
    student = relationship("User", foreign_keys=[student_id], back_populates="student_subjects")
    subject = relationship("Subject", foreign_keys=[subject_id], back_populates="student_subjects") 
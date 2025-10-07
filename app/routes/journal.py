from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from sqlalchemy import and_
import urllib.parse

from app.database.connection import get_db
from app.models import User, UserRole, Group, Subject, SubjectGroup, Grade, Attendance, Faculty, StudentSubject
from app.schemas import (
    FacultyCreate, FacultyDisplay,
    GroupCreate, GroupDisplay,
    SubjectCreate, SubjectDisplay,
    SubjectGroupCreate, SubjectGroupDisplay,
    GradeCreate, GradeUpdate, GradeDisplay,
    AttendanceCreate, AttendanceUpdate, AttendanceDisplay,
    JournalView, StudentSubjectCreate, StudentSubjectDisplay
)
from app.services import (
    create_faculty, get_faculties, get_faculty_by_id,
    create_group, get_groups, get_group_by_id,
    create_subject, get_subjects, get_subject_by_id,
    create_subject_group, get_subject_groups, get_subject_group_by_id,
    create_grade, get_grades, update_grade,
    create_attendance, get_attendance, update_attendance,
    get_journal_view, assign_subject_to_teacher, remove_subject_from_teacher,
    get_teacher_subjects
)
from app.auth.jwt import get_current_verified_user

router = APIRouter(tags=["Journal"], prefix="/api/journal")

# Faculty routes
@router.post("/faculties", response_model=FacultyDisplay, status_code=status.HTTP_201_CREATED)
def create_faculty_endpoint(
    faculty: FacultyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user)
):
    """
    Create a new faculty (admin only)
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    return create_faculty(db, faculty)

@router.get("/faculties", response_model=List[FacultyDisplay])
def read_faculties(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user)
):
    """
    Get a list of faculties
    """
    return get_faculties(db, skip=skip, limit=limit)

@router.get("/faculties/{faculty_id}", response_model=FacultyDisplay)
def read_faculty(
    faculty_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user)
):
    """
    Get a faculty by ID
    """
    return get_faculty_by_id(db, faculty_id)

@router.delete("/faculties/{faculty_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_faculty_endpoint(
    faculty_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user)
):
    """
    Delete a faculty (admin only)
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Get the faculty to check if it exists
    faculty = get_faculty_by_id(db, faculty_id)
    
    # Delete all associated groups
    groups = db.query(Group).filter(Group.faculty_id == faculty_id).all()
    for group in groups:
        # Delete all subject-group relationships for this group
        subject_groups = db.query(SubjectGroup).filter(SubjectGroup.group_id == group.id).all()
        for subject_group in subject_groups:
            # Delete all grades and attendance records for this subject-group
            db.query(Grade).filter(Grade.subject_group_id == subject_group.id).delete()
            db.query(Attendance).filter(Attendance.subject_group_id == subject_group.id).delete()
            
            # Delete the subject-group relationship
            db.delete(subject_group)
        
        # Delete the group
        db.delete(group)
    
    # Delete all associated subjects
    subjects = db.query(Subject).filter(Subject.faculty_id == faculty_id).all()
    for subject in subjects:
        # Delete all student-subject relationships for this subject
        db.query(StudentSubject).filter(StudentSubject.subject_id == subject.id).delete()
        
        # Delete all subject-group relationships for this subject
        subject_groups = db.query(SubjectGroup).filter(SubjectGroup.subject_id == subject.id).all()
        for subject_group in subject_groups:
            # Delete all grades and attendance records for this subject-group
            db.query(Grade).filter(Grade.subject_group_id == subject_group.id).delete()
            db.query(Attendance).filter(Attendance.subject_group_id == subject_group.id).delete()
            
            # Delete the subject-group relationship
            db.delete(subject_group)
        
        # Delete the subject
        db.delete(subject)
    
    # Delete the faculty
    db.delete(faculty)
    db.commit()
    
    return None

# Public faculty endpoint for registration
@router.get("/public/faculties", response_model=List[FacultyDisplay])
def read_public_faculties(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Get a list of faculties without authentication (for registration)
    """
    return get_faculties(db, skip=skip, limit=limit)

# Group routes
@router.post("/groups", response_model=GroupDisplay, status_code=status.HTTP_201_CREATED)
def create_group_endpoint(
    group: GroupCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user)
):
    """
    Create a new group (admin only)
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    return create_group(db, group)

@router.get("/groups", response_model=List[GroupDisplay])
def read_groups(
    faculty_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user)
):
    """
    Get a list of groups, optionally filtered by faculty
    """
    return get_groups(db, faculty_id=faculty_id, skip=skip, limit=limit)

@router.get("/groups/{group_id}", response_model=GroupDisplay)
def read_group(
    group_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user)
):
    """
    Get a group by ID
    """
    return get_group_by_id(db, group_id)

@router.delete("/groups/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_group_endpoint(
    group_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user)
):
    """
    Delete a group (admin only)
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Get the group to check if it exists
    group = get_group_by_id(db, group_id)
    
    # Check if any students are in this group
    students_in_group = db.query(User).filter(
        User.group_id == group_id, 
        User.role == UserRole.STUDENT
    ).count()
    
    if students_in_group > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete group with ID {group_id} because it has students assigned to it"
        )
    
    # Delete all subject-group relationships for this group
    subject_groups = db.query(SubjectGroup).filter(SubjectGroup.group_id == group_id).all()
    for subject_group in subject_groups:
        # Delete all grades and attendance records for this subject-group
        db.query(Grade).filter(Grade.subject_group_id == subject_group.id).delete()
        db.query(Attendance).filter(Attendance.subject_group_id == subject_group.id).delete()
        
        # Delete the subject-group relationship
        db.delete(subject_group)
    
    # Delete the group
    db.delete(group)
    db.commit()
    
    return None

# Public groups endpoint for registration
@router.get("/public/groups", response_model=List[GroupDisplay])
def read_public_groups(
    faculty_id: Optional[int] = Query(None),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Get a list of groups without authentication (for registration)
    """
    return get_groups(db, faculty_id=faculty_id, skip=skip, limit=limit)

# Subject routes
@router.post("/subjects", response_model=SubjectDisplay, status_code=status.HTTP_201_CREATED)
def create_subject_endpoint(
    subject: SubjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user)
):
    """
    Create a new subject (admin only)
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    return create_subject(db, subject)

@router.get("/subjects", response_model=List[SubjectDisplay])
def read_subjects(
    faculty_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user)
):
    """
    Get a list of subjects, optionally filtered by faculty
    """
    # For teachers, only return subjects they have access to
    if current_user.role == UserRole.TEACHER:
        teacher_subjects = current_user.subjects
        if faculty_id:
            return [s for s in teacher_subjects if s.faculty_id == faculty_id]
        return teacher_subjects
        
    return get_subjects(db, faculty_id=faculty_id, skip=skip, limit=limit)

@router.get("/subjects/{subject_id}", response_model=SubjectDisplay)
def read_subject(
    subject_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user)
):
    """
    Get a subject by ID
    """
    # For teachers, check if they have access to this subject
    if current_user.role == UserRole.TEACHER:
        teacher_subjects = [s.id for s in current_user.subjects]
        if subject_id not in teacher_subjects:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this subject"
            )
    
    return get_subject_by_id(db, subject_id)

@router.delete("/subjects/{subject_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_subject_endpoint(
    subject_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user)
):
    """
    Delete a subject (admin only)
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Get the subject to check if it exists
    subject = get_subject_by_id(db, subject_id)
    
    # Delete all student-subject relationships for this subject
    db.query(StudentSubject).filter(StudentSubject.subject_id == subject_id).delete()
    
    # Delete all subject-group relationships for this subject
    subject_groups = db.query(SubjectGroup).filter(SubjectGroup.subject_id == subject_id).all()
    for subject_group in subject_groups:
        # Delete all grades and attendance records for this subject-group
        db.query(Grade).filter(Grade.subject_group_id == subject_group.id).delete()
        db.query(Attendance).filter(Attendance.subject_group_id == subject_group.id).delete()
        
        # Delete the subject-group relationship
        db.delete(subject_group)
    
    # Delete the subject
    db.delete(subject)
    db.commit()
    
    return None

# Subject-Group routes
@router.post("/subject-groups", response_model=SubjectGroupDisplay, status_code=status.HTTP_201_CREATED)
def create_subject_group_endpoint(
    subject_group: SubjectGroupCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user)
):
    """
    Create a new subject-group relationship (admin only)
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    return create_subject_group(db, subject_group)

@router.get("/subject-groups", response_model=List[SubjectGroupDisplay])
def read_subject_groups(
    subject_id: Optional[int] = None,
    group_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user)
):
    """
    Get a list of subject-group relationships, optionally filtered by subject or group
    """
    return get_subject_groups(db, subject_id=subject_id, group_id=group_id, skip=skip, limit=limit)

@router.get("/subject-groups/{subject_group_id}", response_model=SubjectGroupDisplay)
def read_subject_group(
    subject_group_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user)
):
    """
    Get a subject-group relationship by ID
    """
    return get_subject_group_by_id(db, subject_group_id)

@router.delete("/subject-groups/{subject_group_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_subject_group_endpoint(
    subject_group_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user)
):
    """
    Delete a subject-group relationship (admin only)
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Get the subject-group to check if it exists
    subject_group = get_subject_group_by_id(db, subject_group_id)
    
    # Delete all grades and attendance records for this subject-group
    db.query(Grade).filter(Grade.subject_group_id == subject_group_id).delete()
    db.query(Attendance).filter(Attendance.subject_group_id == subject_group_id).delete()
    
    # Delete the subject-group relationship
    db.delete(subject_group)
    db.commit()
    
    return None

# Grade routes
@router.post("/grades", response_model=GradeDisplay, status_code=status.HTTP_201_CREATED)
def create_grade_endpoint(
    grade: GradeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user)
):
    """
    Create a new grade (teachers only)
    """
    if current_user.role != UserRole.TEACHER and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Check if the teacher has access to the subject
    if current_user.role == UserRole.TEACHER:
        # Get the subject_group to find the subject
        subject_group = get_subject_group_by_id(db, grade.subject_group_id)
        
        # Get teacher's assigned subjects
        teacher_subject_ids = [s.id for s in current_user.subjects]
        
        # Check if teacher has access to this subject
        if subject_group.subject_id not in teacher_subject_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this subject"
            )
    
    return create_grade(db, grade)

@router.get("/grades", response_model=List[GradeDisplay])
def read_grades(
    student_id: Optional[int] = None,
    subject_group_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user)
):
    """
    Get a list of grades, optionally filtered by student or subject-group
    """
    # Students can only see their own grades
    if current_user.role == UserRole.STUDENT:
        student_id = current_user.id
    
    return get_grades(db, student_id=student_id, subject_group_id=subject_group_id, skip=skip, limit=limit)

@router.put("/grades/{grade_id}", response_model=GradeDisplay)
def update_grade_endpoint(
    grade_id: int,
    grade_data: GradeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user)
):
    """
    Update a grade (teachers only)
    """
    if current_user.role != UserRole.TEACHER and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Fetch the grade to check subject access
    existing_grade = db.query(Grade).filter(Grade.id == grade_id).first()
    if not existing_grade:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Grade with ID {grade_id} not found"
        )
    
    # Check if the teacher has access to the subject
    if current_user.role == UserRole.TEACHER:
        # Get the subject_group to find the subject
        subject_group = get_subject_group_by_id(db, existing_grade.subject_group_id)
        
        # Get teacher's assigned subjects
        teacher_subject_ids = [s.id for s in current_user.subjects]
        
        # Check if teacher has access to this subject
        if subject_group.subject_id not in teacher_subject_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this subject"
            )
    
    return update_grade(db, grade_id, grade_data)

@router.delete("/grades/{grade_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_grade_endpoint(
    grade_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user)
):
    """
    Delete a grade (teachers only)
    """
    if current_user.role != UserRole.TEACHER and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Get the grade to check if it exists and if teacher has access
    grade = db.query(Grade).filter(Grade.id == grade_id).first()
    if not grade:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Grade with ID {grade_id} not found"
        )
    
    # Check if the teacher has access to the subject
    if current_user.role == UserRole.TEACHER:
        # Get the subject_group to find the subject
        subject_group = get_subject_group_by_id(db, grade.subject_group_id)
        
        # Get teacher's assigned subjects
        teacher_subject_ids = [s.id for s in current_user.subjects]
        
        # Check if teacher has access to this subject
        if subject_group.subject_id not in teacher_subject_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this subject"
            )
    
    # Delete the grade
    db.delete(grade)
    db.commit()
    
    return None

# Attendance routes
@router.post("/attendance", response_model=AttendanceDisplay, status_code=status.HTTP_201_CREATED)
def create_attendance_endpoint(
    attendance: AttendanceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user)
):
    """
    Create a new attendance record (teachers only)
    """
    if current_user.role != UserRole.TEACHER and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Check if the teacher has access to the subject
    if current_user.role == UserRole.TEACHER:
        # Get the subject_group to find the subject
        subject_group = get_subject_group_by_id(db, attendance.subject_group_id)
        
        # Get teacher's assigned subjects
        teacher_subject_ids = [s.id for s in current_user.subjects]
        
        # Check if teacher has access to this subject
        if subject_group.subject_id not in teacher_subject_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this subject"
            )
    
    return create_attendance(db, attendance)

@router.get("/attendance", response_model=List[AttendanceDisplay])
def read_attendance_records(
    student_id: Optional[int] = None,
    subject_group_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user)
):
    """
    Get a list of attendance records, optionally filtered by student or subject-group
    """
    # Students can only see their own attendance
    if current_user.role == UserRole.STUDENT:
        student_id = current_user.id
    
    return get_attendance(db, student_id=student_id, subject_group_id=subject_group_id, skip=skip, limit=limit)

@router.put("/attendance/{attendance_id}", response_model=AttendanceDisplay)
def update_attendance_endpoint(
    attendance_id: int,
    attendance_data: AttendanceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user)
):
    """
    Update an attendance record (teachers only)
    """
    if current_user.role != UserRole.TEACHER and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Fetch the attendance record to check subject access
    existing_attendance = db.query(Attendance).filter(Attendance.id == attendance_id).first()
    if not existing_attendance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Attendance record with ID {attendance_id} not found"
        )
    
    # Check if the teacher has access to the subject
    if current_user.role == UserRole.TEACHER:
        # Get the subject_group to find the subject
        subject_group = get_subject_group_by_id(db, existing_attendance.subject_group_id)
        
        # Get teacher's assigned subjects
        teacher_subject_ids = [s.id for s in current_user.subjects]
        
        # Check if teacher has access to this subject
        if subject_group.subject_id not in teacher_subject_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this subject"
            )
    
    return update_attendance(db, attendance_id, attendance_data)

@router.delete("/attendance/{attendance_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_attendance_endpoint(
    attendance_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user)
):
    """
    Delete an attendance record (teachers only)
    """
    if current_user.role != UserRole.TEACHER and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Get the attendance record to check if it exists and if teacher has access
    attendance = db.query(Attendance).filter(Attendance.id == attendance_id).first()
    if not attendance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Attendance record with ID {attendance_id} not found"
        )
    
    # Check if the teacher has access to the subject
    if current_user.role == UserRole.TEACHER:
        # Get the subject_group to find the subject
        subject_group = get_subject_group_by_id(db, attendance.subject_group_id)
        
        # Get teacher's assigned subjects
        teacher_subject_ids = [s.id for s in current_user.subjects]
        
        # Check if teacher has access to this subject
        if subject_group.subject_id not in teacher_subject_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this subject"
            )
    
    # Delete the attendance record
    db.delete(attendance)
    db.commit()
    
    return None

# Journal view route
@router.get("/{faculty}/{group}/{subject}", response_model=JournalView)
def read_journal(
    faculty: str,
    group: str,
    subject: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user)
):
    """
    Get a structured view of the journal for a specific faculty, group, and subject
    """
    # Get the faculty, group, and subject by name
    db_faculty = db.query(Faculty).filter(Faculty.name == faculty).first()
    if not db_faculty:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Faculty '{faculty}' not found"
        )
    
    db_group = db.query(Group).filter(Group.name == group, Group.faculty_id == db_faculty.id).first()
    if not db_group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Group '{group}' not found in faculty '{faculty}'"
        )
    
    db_subject = db.query(Subject).filter(Subject.name == subject, Subject.faculty_id == db_faculty.id).first()
    if not db_subject:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Subject '{subject}' not found in faculty '{faculty}'"
        )
    
    # Check permissions
    if current_user.role == UserRole.STUDENT:
        # Students can only view journals for their own group
        if current_user.group_id != db_group.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions"
            )
    elif current_user.role == UserRole.TEACHER:
        # Teachers can only view journals for subjects they teach
        teacher_subjects = [s.id for s in current_user.subjects]
        if db_subject.id not in teacher_subjects:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this subject"
            )
    
    return get_journal_view(db, db_subject.id, db_group.id)

# Teacher-Subject routes
@router.get("/teacher-subjects", response_model=List[dict])
def read_all_teacher_subjects(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user)
):
    """
    Get a list of all teacher-subject relationships (admin only)
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Get all teachers
    teachers = db.query(User).filter(User.role == UserRole.TEACHER).all()
    
    # Collect all teacher-subject relationships
    teacher_subjects = []
    for teacher in teachers:
        for subject in teacher.subjects:
            teacher_subjects.append({
                "teacher_id": teacher.id,
                "subject_id": subject.id
            })
    
    return teacher_subjects

@router.get("/teachers/{teacher_id}/subjects", response_model=List[SubjectDisplay])
def read_teacher_subjects(
    teacher_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user)
):
    """
    Get a list of subjects assigned to a teacher (admin or the teacher themselves)
    """
    if current_user.role != UserRole.ADMIN and current_user.id != teacher_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    return get_teacher_subjects(db, teacher_id)

@router.post("/teachers/{teacher_id}/subjects/{subject_id}", status_code=status.HTTP_200_OK)
def assign_subject(
    teacher_id: int,
    subject_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user)
):
    """
    Assign a subject to a teacher (admin only)
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    assign_subject_to_teacher(db, teacher_id, subject_id)
    return {"message": "Subject assigned to teacher successfully"}

@router.delete("/teachers/{teacher_id}/subjects/{subject_id}", status_code=status.HTTP_200_OK)
def remove_subject(
    teacher_id: int,
    subject_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user)
):
    """
    Remove a subject from a teacher (admin only)
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    remove_subject_from_teacher(db, teacher_id, subject_id)
    return {"message": "Subject removed from teacher successfully"}

# Student-Subject routes
@router.get("/student-subjects", response_model=List[StudentSubjectDisplay])
def read_student_subjects(
    student_id: Optional[int] = None,
    subject_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user)
):
    """
    Get a list of student-subject relationships
    """
    # If no student_id is provided and the current user is a student, use their ID
    if not student_id and current_user.role == UserRole.STUDENT:
        student_id = current_user.id
    
    query = db.query(StudentSubject)
    
    if student_id:
        query = query.filter(StudentSubject.student_id == student_id)
    
    if subject_id:
        query = query.filter(StudentSubject.subject_id == subject_id)
    
    # Add debug logging
    print(f"Fetching student subjects for student_id={student_id}, subject_id={subject_id}")
    results = query.offset(skip).limit(limit).all()
    print(f"Found {len(results)} student subjects")
    
    return results

@router.post("/student-subjects", status_code=status.HTTP_201_CREATED)
def create_student_subject(
    student_subject: StudentSubjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user)
):
    """
    Create a new student-subject relationship (admin only)
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Check if student exists and is a student
    student = db.query(User).filter(
        User.id == student_subject.student_id,
        User.role == UserRole.STUDENT
    ).first()
    
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student with ID {student_subject.student_id} not found"
        )
    
    # Check if subject exists
    subject = db.query(Subject).filter(Subject.id == student_subject.subject_id).first()
    
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Subject with ID {student_subject.subject_id} not found"
        )
    
    # Check if the relationship already exists
    existing = db.query(StudentSubject).filter(
        and_(
            StudentSubject.student_id == student_subject.student_id,
            StudentSubject.subject_id == student_subject.subject_id
        )
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Student is already assigned to this subject"
        )
    
    # Get the student's group
    if not student.group_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Student must be assigned to a group before being assigned to a subject"
        )
    
    # Get the group info
    group = db.query(Group).filter(Group.id == student.group_id).first()
    if not group:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Group with ID {student.group_id} not found"
        )
    
    # Get the faculty info
    faculty = db.query(Faculty).filter(Faculty.id == group.faculty_id).first()
    if not faculty:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Faculty with ID {group.faculty_id} not found"
        )
    
    # Check if a subject-group relationship exists
    subject_group = db.query(SubjectGroup).filter(
        and_(
            SubjectGroup.subject_id == student_subject.subject_id,
            SubjectGroup.group_id == student.group_id
        )
    ).first()
    
    # Create a subject-group relationship if it doesn't exist
    if not subject_group:
        subject_group = SubjectGroup(
            subject_id=student_subject.subject_id,
            group_id=student.group_id
        )
        db.add(subject_group)
        db.commit()
        db.refresh(subject_group)
    
    # Create the student-subject relationship
    db_student_subject = StudentSubject(
        student_id=student_subject.student_id,
        subject_id=student_subject.subject_id
    )
    
    db.add(db_student_subject)
    db.commit()
    db.refresh(db_student_subject)
    
    # Return the created student-subject and info for the journal
    return {
        "student_subject": StudentSubjectDisplay.model_validate(db_student_subject),
        "journal_info": {
            "faculty": faculty.name,
            "group": group.name,
            "subject": subject.name,
            "journal_url": f"/journal/{urllib.parse.quote(faculty.name)}/{urllib.parse.quote(group.name)}/{urllib.parse.quote(subject.name)}"
        }
    }

@router.delete("/student-subjects/{student_subject_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_student_subject(
    student_subject_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user)
):
    """
    Delete a student-subject relationship (admin only)
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Get the relationship
    student_subject = db.query(StudentSubject).filter(StudentSubject.id == student_subject_id).first()
    
    if not student_subject:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student-subject relationship with ID {student_subject_id} not found"
        )
    
    # Delete the relationship
    db.delete(student_subject)
    db.commit()
    
    return None 